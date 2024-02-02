"""Provides classes for authenticating to and managing items on the FantasyGrounds Forge marketplace"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from dropzone import DropzoneErrorHandling, add_file_to_dropzone

logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")


@dataclass(frozen=True, init=False)
class ForgeURLs:
    """Contains URL strings for webpages used on the forge"""

    MANAGE_CRAFT: str = "https://forge.fantasygrounds.com/crafter/manage-craft"
    API_CRAFTER_ITEMS: str = "https://forge.fantasygrounds.com/api/crafter/items"


@dataclass(frozen=True, init=False)
class ReleaseChannel:
    """Constants representing the strings used to represent each release channel in build-management comboboxes"""

    LIVE: str = "Live"
    TEST: str = "Test"
    NONE: str = "No Channel"


@dataclass(frozen=True)
class ForgeCredentials:
    """Dataclass used to store the authentication credentials used on FG Forge"""

    username: str
    password: str


@dataclass(frozen=True)
class ForgeItem:
    """Dataclass used to interact with an item on the FG Forge"""

    creds: ForgeCredentials
    item_id: str
    timeout: float

    def login(self, driver: webdriver, urls: ForgeURLs) -> None:
        """Open manage-craft and login if prompted"""
        driver.get(urls.MANAGE_CRAFT)

        try:
            username_field = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.NAME, "vb_login_username")))
            password_field = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.NAME, "vb_login_password")))
            username_field.send_keys(self.creds.username)
            password_field.send_keys(self.creds.password)
            login_button = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.CLASS_NAME, "registerbtn")))
            login_button.click()
        except TimeoutException:
            pass

    def open_items_list(self, driver: webdriver, urls: ForgeURLs) -> None:
        """Open the manage craft page, raising an exception if the item table size selector isn't found."""
        driver.get(urls.MANAGE_CRAFT)

        try:
            items_per_page = Select(WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.NAME, "items-table_length"))))
            items_per_page.select_by_visible_text("100")
        except TimeoutException as e:
            raise TimeoutException("Could not load the Manage Craft page!") from e

    def open_item_page(self, driver: webdriver) -> None:
        """Open the management page for a specific forge item, raising an exception if a link matching the item_id isn't found."""

        try:
            item_link = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.XPATH, f"//a[@data-item-id='{self.item_id}']")))
            item_link.click()
        except TimeoutException as e:
            raise TimeoutException("Could not find item page, is FORGE_ITEM_ID correct?") from e

    def upload_and_publish(self, driver: webdriver, urls: ForgeURLs, new_file: Path, channel: str) -> None:
        """Coordinates sequential use of other class methods to upload and publish a new build to the FG Forge"""
        self.login(driver, urls)
        self.open_items_list(driver, urls)
        self.open_item_page(driver)
        self.add_build(driver, new_file)
        self.open_items_list(driver, urls)
        self.open_item_page(driver)
        self.set_latest_build_channel(driver, channel)

    def add_build(self, driver: webdriver, new_build: Path) -> None:
        """Uploads a new build to this Forge item, raising an exception if the new_build isn't added to the dropzone or doesn't upload successfully."""

        add_file_to_dropzone(driver, self.timeout, new_build)

        submit_button = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.ID, "submit-build-button")))
        submit_button.click()

        dropzone_errors = DropzoneErrorHandling(driver, self.timeout)
        dropzone_errors.check_report_toast_error()
        dropzone_errors.check_report_dropzone_upload_error()
        dropzone_errors.check_report_upload_percentage()

    def set_latest_build_channel(self, driver: webdriver, channel: str) -> None:
        """Set the latest build as active on the Live release channel, raising an exception if the build selector isn't found."""

        try:
            item_builds_latest = Select(
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.XPATH, "//select[@class='form-control item-build-channel item-build-option']"))
                )
            )
            item_builds_latest.select_by_visible_text(channel)
        except TimeoutException as e:
            raise TimeoutException(f"Could not find item page, is {self.item_id} the correct item id?") from e

    def replace_description(self, driver: webdriver, description_text: str) -> None:
        """Replaces the existing item description with a new HTML-formatted full description"""
        uploads_tab = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.XPATH, "//a[@id='manage-item-tab']")))
        uploads_tab.click()

        submit_button = WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable((By.ID, "save-item-button")))

        description_field = driver.find_element(By.XPATH, "//div[@id='manage-item']").find_element(By.CLASS_NAME, "note-editable")
        description_field.clear()
        driver.execute_script("arguments[0].innerHTML = arguments[1];", description_field, description_text)
        time.sleep(2.5)

        submit_button.click()
        time.sleep(0.5)

    def update_description(self, driver: webdriver, urls: ForgeURLs, description: str) -> None:
        """Coordinates sequential use of other class methods to update the item description for an item on the FG Forge"""
        self.login(driver, urls)
        self.open_items_list(driver, urls)
        self.open_item_page(driver)
        self.replace_description(driver, description)
