"""Provides classes for authenticating to and managing items on the FantasyGrounds Forge marketplace."""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import requests
from bs4 import BeautifulSoup, Tag
from patchright.sync_api import BrowserContext, Cookie, Page
from patchright.sync_api import TimeoutError as PlaywrightTimeoutError

from .shared_constants import UI_INTERACTION_DELAY, get_user_agent

if TYPE_CHECKING:
    from patchright.sync_api import ElementHandle


logger = logging.getLogger(__name__)


class BuildInfo(TypedDict):
    """Dictionary of string-formated information about a single Forge Build."""

    id: str
    build_num: str
    upload_date: str
    channel: str


class ForgeLoginError(Exception):
    """Exception to be raised when forge login is unsuccessful."""

    def __init__(self, username: str) -> None:
        """Create error message including what user you were trying to login as."""
        self.message = f"Attempted login as {username} was unsuccessful"
        super().__init__(self.message)


class ForgeUploadError(Exception):
    """Exception to be raised when file upload fails."""


class ForgeReleaseChannel(Enum):
    """Constants representing the strings used to represent each release channel in build-management comboboxes."""

    LIVE = "1"
    TEST = "2"
    NONE = "0"


@dataclass(frozen=True, init=False)
class ForgeURLs:
    """Contains URL strings for webpages used on the forge."""

    FORGE_LOGIN: str = "https://forge.fantasygrounds.com/login"
    MANAGE_CRAFT: str = "https://forge.fantasygrounds.com/crafter/manage-craft"
    API_BASE: str = "https://forge.fantasygrounds.com/api"
    API_CRAFTER_ITEMS: str = f"{API_BASE}/crafter/items"
    API_SALES: str = f"{API_BASE}/transactions/data-table"


@dataclass(frozen=True)
class ForgeCredentials:
    """Dataclass used to store the authentication credentials used on FG Forge."""

    username: str
    password: str

    @staticmethod
    def get_csrf_token(context: BrowserContext, urls: ForgeURLs) -> str:
        """Retrieve the csrf token from the page header. Return None if not found."""
        page = context.new_page()
        response = page.goto(urls.MANAGE_CRAFT)

        if not response:
            page.close()
            error_msg = "Empty response when fetching CSRF token"
            raise ForgeLoginError(error_msg)

        if not response.ok:
            page.close()
            error_msg = "HTML failure code when fetching CSRF token"
            raise ForgeLoginError(error_msg)

        content = page.content()
        page.close()

        soup = BeautifulSoup(content, "html.parser")
        token_element = soup.find(attrs={"name": "csrf-token"})
        if not isinstance(token_element, Tag):
            error_msg = "CSRF token html element not found or invalid"
            raise ForgeLoginError(error_msg)

        content = str(token_element.get("content"))
        if not content:
            error_msg = "CSRF token content attribute is empty"
            raise ForgeLoginError(error_msg)

        return content


def _build_headers(cookies: list[Cookie], csrf_token: str) -> dict[str, str]:
    """Build request headers with cookies and CSRF token."""
    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    return {
        "Cookie": cookie_header,
        "X-CSRF-TOKEN": csrf_token,
        "User-Agent": get_user_agent(),
    }


def _wait_for_element(page: Page, selector: str, timeout: float, element_description: str | None = None) -> "ElementHandle":
    """Wait for an element and raise descriptive error if not found."""
    element = page.wait_for_selector(selector, timeout=timeout * 1000)
    if not element:
        description = element_description or selector
        error_msg = f"{description} not found"
        raise PlaywrightTimeoutError(error_msg)
    return cast("ElementHandle", element)


@dataclass(frozen=True)
class ForgeItem:
    """Dataclass used to interact with an item on the FG Forge."""

    creds: ForgeCredentials
    item_id: str
    timeout: float

    def _get_auth_headers(self, context: BrowserContext, urls: ForgeURLs) -> dict[str, str]:
        """Get authentication headers with cookies and CSRF token."""
        cookies = context.cookies()
        csrf_token = self.creds.get_csrf_token(context, urls)
        return _build_headers(cookies, csrf_token)

    def _is_already_logged_in(self, page: Page, urls: ForgeURLs) -> bool:
        """Check if user is already logged in by looking for the items table."""
        page.goto(urls.FORGE_LOGIN)

        try:
            alert_div = _wait_for_element(page, "div[class='alert alert-info text-center']", self.timeout, "Message confirming not logged in")
            return not alert_div.inner_text().__contains__("You are not logged in")
        except PlaywrightTimeoutError:
            return True

    def _perform_login(self, page: Page, urls: ForgeURLs) -> None:
        """Fill in and submit login form."""
        page.goto(urls.FORGE_LOGIN)

        try:
            username_field = _wait_for_element(page, "input[name='vb_login_username']", self.timeout, "Username field")
            password_field = _wait_for_element(page, "input[name='vb_login_password']", self.timeout, "Password field")

            time.sleep(UI_INTERACTION_DELAY)
            username_field.fill(self.creds.username)
            password_field.fill(self.creds.password)

            login_button = _wait_for_element(page, "//a[@class='registerbtn']", self.timeout, "Login button")
            login_button.click()
            time.sleep(UI_INTERACTION_DELAY)

        except PlaywrightTimeoutError as e:
            error_msg = "Login form not found or not interactive"
            raise PlaywrightTimeoutError(error_msg) from e

    def _login_failed(self, page: Page) -> bool:
        """Check if login failed by looking for error indicator."""
        try:
            alert_div = _wait_for_element(page, "//div[@class='blockrow restore']", self.timeout, "Login failure message")
            return not alert_div.inner_text().__contains__("You have entered an invalid username or password")

        except PlaywrightTimeoutError:
            return False

    def login(self, page: Page, context: BrowserContext, urls: ForgeURLs) -> dict[str, str]:
        """Open manage-craft and login if prompted. Returns headers dict with cookies and CSRF token."""
        if self._is_already_logged_in(page, urls):
            logger.info("Already logged in")
            return self._get_auth_headers(context, urls)

        self._perform_login(page, urls)

        if self._login_failed(page):
            raise ForgeLoginError(self.creds.username)

        logger.info("Logged in as %s", self.creds.username)
        return self._get_auth_headers(context, urls)

    def upload_and_publish(self, headers: dict[str, str], urls: ForgeURLs, new_files: list[Path], channel: ForgeReleaseChannel) -> None:
        """Upload and publish a new build to the FG Forge using direct API calls."""
        logger.info("Uploading new build to Forge item")
        self.upload_build_direct(headers, urls, new_files)

        if channel is ForgeReleaseChannel.NONE:
            logger.info("Target channel is set to none, not setting new build to a release channel.")
            return

        logger.info("Assigning new build to Forge channel: %s: %s", channel, channel.value)
        latest_build_id = max(self.get_item_builds(headers, urls), key=lambda build: int(build["build_num"]))["id"]
        self.set_build_channel(headers, urls, latest_build_id, channel)

    def upload_build_direct(self, headers: dict[str, str], urls: ForgeURLs, new_builds: list[Path]) -> None:
        """Upload new build(s) to this Forge item via direct API call."""
        upload_url = f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/upload"

        files = {}
        for idx, build in enumerate(new_builds):
            file_bytes = build.read_bytes()
            files[f"buildFiles[{idx}]"] = (build.name, file_bytes, "application/octet-stream")

        upload_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
        upload_headers.update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://forge.fantasygrounds.com",
                "Referer": "https://forge.fantasygrounds.com/crafter/manage-craft",
            }
        )

        response = requests.post(upload_url, files=files, headers=upload_headers, timeout=30)

        if response.text or not response.ok:
            error_msg = f"Build upload failed with status {response.status_code}: {response.text}"
            raise ForgeUploadError(error_msg)

        logger.info("Build upload complete for all files")

    def get_item_builds(self, headers: dict[str, str], urls: ForgeURLs) -> list[BuildInfo]:
        """Retrieve a list of builds for this Forge item, with ID, build number, upload date, and current channel."""
        response = requests.post(f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/data-table", headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def set_build_channel(self, headers: dict[str, str], urls: ForgeURLs, build_id: str, channel: ForgeReleaseChannel) -> bool:
        """Set the build channel of this Forge item to the specified value, returning True on 200 OK."""
        response = requests.post(f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/{build_id}/channels/{channel.value}", headers=headers, timeout=30)
        return response.ok

    def replace_description(self, page: Page, description_text: str) -> None:
        """Replace the existing item description with a new HTML-formatted full description."""
        page.evaluate("window.scrollTo(0, document.body.scrollTop)")

        uploads_tab = _wait_for_element(page, "//a[@id='manage-item-tab']", self.timeout, "Manage item tab")
        uploads_tab.click()

        submit_button = _wait_for_element(page, "#save-item-button", self.timeout, "Save item button")

        description_field = page.locator("//div[@id='manage-item']").locator(".note-editable").first
        description_field.evaluate("el => el.innerHTML = ''")
        logger.info("Forge item description cleared")

        page.evaluate("([field, text]) => { field.innerHTML = text; }", [description_field.element_handle(), description_text])
        time.sleep(UI_INTERACTION_DELAY)

        submit_button.click()
        time.sleep(UI_INTERACTION_DELAY)
        logger.info("Forge item description uploaded")

    def update_description(self, page: Page, context: BrowserContext, urls: ForgeURLs, description: str) -> None:
        """Coordinates sequential use of other class methods to update the item description for an item on the FG Forge."""
        self.login(page, context, urls)
        logger.info("Updating Forge item description")

        page.goto(urls.MANAGE_CRAFT)
        _wait_for_element(page, "select[name='items-table_length']", self.timeout, "Item table")

        item_link = _wait_for_element(page, f"//a[@data-item-id='{self.item_id}']", self.timeout, f"Item link for item ID {self.item_id}")
        item_link.click()
        self.replace_description(page, description)
