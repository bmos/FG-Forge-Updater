"""Provides classes for authenticating to and managing items on the FantasyGrounds Forge marketplace."""

import importlib.metadata
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, cast

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from patchright.sync_api import BrowserContext, Page
from patchright.sync_api import TimeoutError as PlaywrightTimeoutError

if TYPE_CHECKING:
    from patchright.sync_api import ElementHandle


logger = logging.getLogger(__name__)
HTTP_OK = 200


class ForgeLoginException(BaseException):
    """Exception to be raised when forge login is unsuccessful."""

    def __init__(self, username: str) -> None:
        """Create error message including what user you were trying to login as."""
        self.message = f"Attempted login as {username} was unsuccessful"
        super().__init__(self.message)


class ForgeUploadException(BaseException):
    """Exception to be raised when file upload fails."""


class ForgeTransactionType(Enum):
    """Constants representing the strings used to represent each type of transaction for a Forge item."""

    TREASURE_CHEST = "1"
    PURCHASE = "2"
    GIFT = "5"
    OWNER = "7"
    DONOR = "9"


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

        if not response or response.status != HTTP_OK:
            page.close()
            error_msg = "Empty response when fetching CSRF token"
            raise ForgeLoginException(error_msg)

        content = page.content()
        page.close()

        soup = BeautifulSoup(content, "html.parser")
        token_element = soup.find(attrs={"name": "csrf-token"})
        if not token_element or isinstance(token_element, NavigableString):
            error_msg = "CSRF token html element not found or invalid"
            raise ForgeLoginException(error_msg)
        return str(token_element.get("content"))


@dataclass(frozen=True)
class ForgeItem:
    """Dataclass used to interact with an item on the FG Forge."""

    creds: ForgeCredentials
    item_id: str
    timeout: float

    def login(self, page: Page, context: BrowserContext, urls: ForgeURLs) -> dict[str, str]:
        """Open manage-craft and login if prompted. Returns headers dict with cookies and CSRF token."""
        page.goto(urls.FORGE_LOGIN)

        try:
            username_field = cast("ElementHandle", page.wait_for_selector("input[name='vb_login_username']", timeout=self.timeout * 1000))
            password_field = cast("ElementHandle", page.wait_for_selector("input[name='vb_login_password']", timeout=self.timeout * 1000))

            time.sleep(0.25)
            username_field.fill(self.creds.username)
            password_field.fill(self.creds.password)

            login_button = cast("ElementHandle", page.wait_for_selector("//a[@class='registerbtn']", timeout=self.timeout * 1000))
            login_button.click()
            time.sleep(0.25)

            try:
                page.wait_for_selector("//div[@class='blockrow restore']", timeout=self.timeout * 1000)
                raise ForgeLoginException(self.creds.username)
            except PlaywrightTimeoutError:
                logger.info("Logged in as %s", self.creds.username)

                # Get cookies and prepare headers
                cookies = context.cookies()
                cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                csrf_token = self.creds.get_csrf_token(context, urls)

                return {
                    "Cookie": cookie_header,
                    "X-CSRF-TOKEN": csrf_token,
                    "User-Agent": f"Mozilla/5.0 (compatible; FG-Forge-Updater/{importlib.metadata.version('fg-forge-updater')}; +https://github.com/bmos/FG-Forge-Updater)",
                }

        except PlaywrightTimeoutError:
            try:
                page.wait_for_selector("select[name='items-table_length']", timeout=self.timeout * 1000)
                logger.info("Already logged in")

                # Still need to get cookies and headers
                cookies = context.cookies()
                cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                csrf_token = self.creds.get_csrf_token(context, urls)

                return {
                    "Cookie": cookie_header,
                    "X-CSRF-TOKEN": csrf_token,
                    "User-Agent": f"Mozilla/5.0 (compatible; FG-Forge-Updater/{importlib.metadata.version('fg-forge-updater')}; +https://github.com/bmos/FG-Forge-Updater)",
                }
            except PlaywrightTimeoutError as e:
                error_msg = "No username or password field found, or login button is not clickable."
                raise PlaywrightTimeoutError(error_msg) from e

    def upload_and_publish(self, headers: dict[str, str], urls: ForgeURLs, new_files: list[Path], channel: ForgeReleaseChannel) -> None:
        """Upload and publish a new build to the FG Forge using direct API calls."""
        logger.info("Uploading new build to Forge item")
        self.upload_build_direct(headers, urls, new_files)

        if channel is ForgeReleaseChannel.NONE:
            logger.info("Target channel is set to none, not setting new build to a release channel.")
            return
        latest_build_id = max(self.get_item_builds(headers, urls), key=lambda build: int(build["build_num"]))["id"]
        logger.info("Assigning new build to Forge channel: %s: %s", channel, channel.value)
        self.set_build_channel(headers, urls, latest_build_id, channel)

    def upload_build_direct(self, headers: dict[str, str], urls: ForgeURLs, new_builds: list[Path]) -> None:
        """Upload new build(s) to this Forge item via direct API call."""
        upload_url = f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/upload"

        # Build the files dict with all files at once, matching browser behavior
        files = {}
        for idx, build in enumerate(new_builds):
            file_bytes = build.read_bytes()
            files[f"buildFiles[{idx}]"] = (build.name, file_bytes, "application/octet-stream")

        # Remove Content-Type from headers to let requests set it with boundary
        # Add browser-specific headers that the API expects
        upload_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
        upload_headers.update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://forge.fantasygrounds.com",
                "Referer": "https://forge.fantasygrounds.com/crafter/manage-craft",
            }
        )

        response = requests.post(upload_url, files=files, headers=upload_headers)

        if response.text or response.status_code != HTTP_OK:
            error_msg = f"Build upload failed with status {response.status_code}: {response.text}"
            raise ForgeUploadException(error_msg)

        logger.info("Build upload complete for all files")

    def get_sales(self, headers: dict[str, str], urls: ForgeURLs, limit_count: int = -1) -> list:
        """Retrieve a list of sales for this Forge item, filter it by item_id and return the filtered list."""
        request_headers = {
            **headers,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(urls.API_SALES, data=f"draw=1&length={limit_count}", headers=request_headers)
        sales = response.json()["data"]

        def is_sale_type(sale: dict[str, str], sale_type: ForgeTransactionType) -> bool:
            return sale["item_id"] == self.item_id and sale["transaction_type_id"] == sale_type.value

        sales = [sale for sale in sales if is_sale_type(sale, ForgeTransactionType.PURCHASE)]
        logger.info("Found %s transactions with transaction type %s for Forge item %s", len(sales), ForgeTransactionType.PURCHASE, self.item_id)

        return sales

    def get_item_builds(self, headers: dict[str, str], urls: ForgeURLs) -> dict:
        """Retrieve a list of builds for this Forge item, with ID, build number, upload date, and current channel."""
        response = requests.post(f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/data-table", headers=headers)
        return response.json()["data"]

    def set_build_channel(self, headers: dict[str, str], urls: ForgeURLs, build_id: str, channel: ForgeReleaseChannel) -> bool:
        """Set the build channel of this Forge item to the specified value, returning True on 200 OK."""
        response = requests.post(f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/{build_id}/channels/{channel.value}", headers=headers)
        return response.status_code == HTTP_OK

    def replace_description(self, page: Page, description_text: str) -> None:
        """Replace the existing item description with a new HTML-formatted full description."""
        page.evaluate("window.scrollTo(0, document.body.scrollTop)")
        uploads_tab = page.wait_for_selector("//a[@id='manage-item-tab']", timeout=self.timeout * 1000)
        if not uploads_tab:
            error_msg = "//a[@id='manage-item-tab'] not found"
            raise PlaywrightTimeoutError(error_msg)
        uploads_tab.click()

        submit_button = page.wait_for_selector("#save-item-button", timeout=self.timeout * 1000)
        if not submit_button:
            error_msg = "#save-item-button not found"
            raise PlaywrightTimeoutError(error_msg)

        description_field = page.locator("//div[@id='manage-item']").locator(".note-editable").first
        description_field.evaluate("el => el.innerHTML = ''")
        logger.info("Forge item description cleared")

        page.evaluate("([field, text]) => { field.innerHTML = text; }", [description_field.element_handle(), description_text])
        time.sleep(0.25)

        submit_button.click()
        time.sleep(0.25)
        logger.info("Forge item description uploaded")

    def update_description(self, page: Page, context: BrowserContext, urls: ForgeURLs, description: str) -> None:
        """Coordinates sequential use of other class methods to update the item description for an item on the FG Forge."""
        self.login(page, context, urls)
        logger.info("Updating Forge item description")
        # Note: Still need to navigate to the page for description updates
        page.goto(urls.MANAGE_CRAFT)
        page.wait_for_selector("select[name='items-table_length']", timeout=self.timeout * 1000)
        item_link = page.wait_for_selector(f"//a[@data-item-id='{self.item_id}']", timeout=self.timeout * 1000)
        if not item_link:
            error_msg = "//a[@data-item-id='{self.item_id}'] not found"
            raise PlaywrightTimeoutError(error_msg)
        item_link.click()
        self.replace_description(page, description)
