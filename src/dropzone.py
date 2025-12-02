"""Provides an error-handling class and file-upload function to allow interaction with dropzones (from DropzoneJS)."""

import logging
import time
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class ToastErrorException(BaseException):
    """Exception to be raised when toast error messages are shown."""


class DropzoneException(BaseException):
    """Exception to be raised when dropzone error messages are shown."""


class LongUploadException(BaseException):
    """Exception to be raised when file uploads time out."""


def check_report_toast_error(driver: WebDriver, timeout_seconds: float = 7) -> None:
    """Wait for timeout window and, if toast error message appears first, raise an exception with the content of the toast message."""
    try:
        toast_error_box = WebDriverWait(driver, timeout_seconds).until(ec.presence_of_element_located((By.XPATH, "//*[@class='toast toast-error']")))
        toast_message = toast_error_box.find_element(By.CLASS_NAME, "toast-message").text
        raise ToastErrorException(toast_message)
    except TimeoutException:
        logger.info("No toast message found")
    except NoSuchElementException:
        logger.info("No toast error or error message found")


def check_report_dropzone_upload_error(driver: WebDriver, timeout_seconds: float = 7) -> None:
    """Wait for timeout window and, if dropzone error message appears first, raise an exception with the content of the error message."""
    try:
        dropzone_error_box = WebDriverWait(driver, timeout_seconds).until(ec.presence_of_element_located((By.CLASS_NAME, "dz-error-message")))
        dropzone_error_box_visible = bool(dropzone_error_box.value_of_css_property("display") == "block")
        if dropzone_error_box_visible:
            dropzone_error_message = dropzone_error_box.find_element(By.TAG_NAME, "span").get_attribute("innerHTML")
            raise DropzoneException(dropzone_error_message)
    except TimeoutException:
        logger.info("No dropzone error found")


def check_report_upload_percentage(driver: WebDriver) -> None:
    """Check if dropzone progress bar is present and, if so, raise an exception with the current progress percentage."""
    try:
        upload_progress_bar_width_filled = driver.find_element(By.CLASS_NAME, "dz-upload").value_of_css_property("width").replace("px", "")
        upload_progress_bar_width = driver.find_element(By.CLASS_NAME, "dz-progress").value_of_css_property("width").replace("px", "")
        upload_progress = float(upload_progress_bar_width_filled) / float(upload_progress_bar_width)
        error_msg = f"File upload timed out at {upload_progress:.0f}%"
        raise LongUploadException(error_msg)
    except NoSuchElementException:
        logger.info("No file progress bars found")


def add_file_to_dropzone(driver: WebDriver, timeout: float, upload_file: Path) -> None:
    """Open the uploads tab, add file to second upload dropzone found after short pause, and ensure file progress bar appears."""
    driver.execute_script("window.scrollTo(0, document.body.scrollTop);")
    uploads_tab = WebDriverWait(driver, timeout).until(ec.element_to_be_clickable((By.XPATH, "//a[@id='manage-build-uploads-tab']")))
    uploads_tab.click()

    WebDriverWait(driver, timeout).until(ec.presence_of_element_located((By.CLASS_NAME, "dz-hidden-input")))
    time.sleep(0.5)
    dz_inputs = driver.find_elements(By.CLASS_NAME, "dz-hidden-input")
    dz_inputs[1].send_keys(str(upload_file))

    try:
        WebDriverWait(driver, timeout).until(ec.presence_of_element_located((By.CLASS_NAME, "dz-upload")))
        logger.info("File queued in dropzone")
    except TimeoutException as e:
        error_msg = "File drag and drop didn't work!"
        raise TimeoutException(error_msg) from e
