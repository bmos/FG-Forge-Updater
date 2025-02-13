"""Provides classes for authenticating to and managing items on the FantasyGrounds Forge marketplace"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requestium
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from src.dropzone import DropzoneErrorHandling, add_file_to_dropzone


class ForgeTransactionType(Enum):
    """Constants representing the strings used to represent each type of transaction for a Forge item"""

    TREASURE_CHEST = "1"
    PURCHASE = "2"
    # TODO: What is #3?
    # TODO: What is #4?
    GIFT = "5"
    # TODO: What is #6?
    OWNER = "7"
    # TODO: What is #8?
    DONOR = "9"


class ForgeReleaseChannel(Enum):
    """Constants representing the strings used to represent each release channel in build-management comboboxes"""

    LIVE = "1"
    TEST = "2"
    NONE = "0"


@dataclass(frozen=True, init=False)
class ForgeURLs:
    """Contains URL strings for webpages used on the forge"""

    FORGE_LOGIN: str = "https://forge.fantasygrounds.com/login"
    MANAGE_CRAFT: str = "https://forge.fantasygrounds.com/crafter/manage-craft"
    API_BASE: str = "https://forge.fantasygrounds.com/api"
    API_CRAFTER_ITEMS: str = f"{API_BASE}/crafter/items"
    API_SALES: str = f"{API_BASE}/transactions/data-table"


@dataclass(frozen=True)
class ForgeCredentials:
    """Dataclass used to store the authentication credentials used on FG Forge"""

    username: str
    password: str

    @staticmethod
    def get_csrf_token(session: requestium.Session, urls: ForgeURLs) -> str | None:
        """Retrieves the csrf token from the page header. Returns string "None" if not found."""
        response = session.get(
            urls.MANAGE_CRAFT,
        )
        soup = BeautifulSoup(response.content, "html.parser")
        token_element = soup.find(attrs={"name": "csrf-token"})
        if not token_element or isinstance(token_element, NavigableString):
            return str(token_element)
        return str(token_element.get("content"))


@dataclass(frozen=True)
class ForgeItem:
    """Dataclass used to interact with an item on the FG Forge"""

    creds: ForgeCredentials
    item_id: str
    timeout: float

    def login(self, session: requestium.Session, urls: ForgeURLs) -> None:
        """Open manage-craft and login if prompted"""
        session.driver.get(urls.FORGE_LOGIN)

        try:
            username_field = WebDriverWait(session.driver, self.timeout).until(EC.element_to_be_clickable((By.NAME, "vb_login_username")))
            password_field = WebDriverWait(session.driver, self.timeout).until(EC.element_to_be_clickable((By.NAME, "vb_login_password")))
            time.sleep(0.25)
            username_field.send_keys(self.creds.username)
            password_field.send_keys(self.creds.password)
            login_button = WebDriverWait(session.driver, self.timeout).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='registerbtn']")))
            login_button.click()
            time.sleep(0.25)

            try:
                WebDriverWait(session.driver, self.timeout).until(EC.presence_of_element_located((By.XPATH, "//div[@class='blockrow restore']")))
                error_msg = f"Attempted login as {self.creds.username} was unsuccessful"
                raise Exception(error_msg)
            except TimeoutException:
                logging.info("Logged in as %s", self.creds.username)
                session.transfer_driver_cookies_to_session(copy_user_agent=True)
                session.headers.update({"X-CSRF-TOKEN": self.creds.get_csrf_token(session, urls)})

        except TimeoutException:
            try:
                WebDriverWait(session.driver, self.timeout).until(EC.presence_of_element_located((By.NAME, "items-table_length")))
                logging.info("Already logged in")
            except TimeoutException as e:
                error_msg = "No username or password field found, or login button is not clickable."
                raise TimeoutException(error_msg) from e

    def open_items_list(self, driver: WebDriver, urls: ForgeURLs) -> None:
        """Open the manage craft page, raising an exception if the item table size selector isn't found."""
        driver.get(urls.MANAGE_CRAFT)

        try:
            items_per_page = Select(WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.NAME, "items-table_length"))))
            items_per_page.select_by_visible_text("100")
        except TimeoutException as e:
            error_msg = "Could not load the Manage Craft page!"
            raise TimeoutException(error_msg) from e

    def open_item_page(self, driver: WebDriver) -> None:
        """Open the management page for a specific forge item, raising an exception if a link matching the item_id isn't found."""
        try:
            item_link = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.XPATH, f"//a[@data-item-id='{self.item_id}']")))
            item_link.click()
        except TimeoutException as e:
            error_msg = f"Could not find item page, is {self.item_id} the right FORGE_ITEM_ID?"
            raise TimeoutException(error_msg) from e

    def upload_and_publish(self, session: requestium.Session, urls: ForgeURLs, new_files: list[Path], channel: ForgeReleaseChannel) -> None:
        """Coordinates sequential use of other class methods to upload and publish a new build to the FG Forge"""
        self.login(session, urls)
        logging.info("Uploading new build to Forge item")
        self.open_items_list(session.driver, urls)
        self.open_item_page(session.driver)
        self.add_build(session.driver, new_files)

        if channel is ForgeReleaseChannel.NONE:
            logging.info("Target channel is set to none, not setting new build to a release channel.")
            return
        latest_build_id = max(self.get_item_builds(session, urls), key=lambda build: int(build["build_num"]))["id"]
        logging.info("Assigning new build to Forge channel: %s: %s", channel, channel.value)
        self.set_build_channel(session, urls, latest_build_id, channel)

    def add_build(self, driver: WebDriver, new_builds: list[Path]) -> None:
        """Uploads new build(s) to this Forge item via dropzone web element."""
        for build in new_builds:
            add_file_to_dropzone(driver, self.timeout, build)

        submit_button = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.ID, "submit-build-button")))
        submit_button.click()

        dropzone_errors = DropzoneErrorHandling(driver, self.timeout)
        dropzone_errors.check_report_toast_error()
        dropzone_errors.check_report_dropzone_upload_error()
        dropzone_errors.check_report_upload_percentage()
        logging.info("Build upload complete")

    def get_sales(self, session: requestium.Session, urls: ForgeURLs, limit_count: int = -1) -> list:
        """Retrieve a list of sales for this Forge item, filter it by item_id and return the filtered list."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = session.post(urls.API_SALES, data=f"draw=1&length={limit_count}", headers=headers)
        sales = response.json()["data"]

        def is_sale_type(sale, sale_type: ForgeTransactionType):
            return sale["item_id"] == self.item_id and sale["transaction_type_id"] == sale_type.value

        sales = [sale for sale in sales if is_sale_type(sale, ForgeTransactionType.PURCHASE)]
        logging.info("Found %s transactions with transaction type %s for Forge item %s", len(sales), ForgeTransactionType.PURCHASE, self.item_id)

        return sales

    def get_item_builds(self, session: requestium.Session, urls: ForgeURLs) -> dict:
        """Retrieve a list of builds for this Forge item, with ID, build number, upload date, and current channel"""
        response = session.post(
            f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/data-table",
        )
        return response.json()["data"]

    def set_build_channel(self, session: requestium.Session, urls: ForgeURLs, build_id: str, channel: ForgeReleaseChannel) -> bool:
        """Sets the build channel of this Forge item to the specified value, returning True on 200 OK"""
        response = session.post(
            f"{urls.API_CRAFTER_ITEMS}/{self.item_id}/builds/{build_id}/channels/{channel.value}",
        )
        return response.status_code == 200

    def replace_description(self, driver: WebDriver, description_text: str) -> None:
        """Replaces the existing item description with a new HTML-formatted full description"""
        driver.execute_script("window.scrollTo(0, document.body.scrollTop);")
        uploads_tab = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.XPATH, "//a[@id='manage-item-tab']")))
        uploads_tab.click()

        submit_button = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.ID, "save-item-button")))

        description_field = driver.find_element(By.XPATH, "//div[@id='manage-item']").find_element(By.CLASS_NAME, "note-editable")
        description_field.clear()
        logging.info("Forge item description cleared")
        driver.execute_script("arguments[0].innerHTML = arguments[1];", description_field, description_text)
        time.sleep(0.25)

        submit_button.click()
        time.sleep(0.25)
        logging.info("Forge item description uploaded")

    def update_description(self, session: requestium.Session, urls: ForgeURLs, description: str) -> None:
        """Coordinates sequential use of other class methods to update the item description for an item on the FG Forge"""
        self.login(session, urls)
        logging.info("Updating Forge item description")
        self.open_items_list(session.driver, urls)
        self.open_item_page(session.driver)
        self.replace_description(session.driver, description)
