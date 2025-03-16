from unittest.mock import MagicMock

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.dropzone import (
    DropzoneException,
    LongUploadException,
    ToastErrorException,
    check_report_dropzone_upload_error,
    check_report_toast_error,
    check_report_upload_percentage,
)


def mock_element() -> MagicMock:
    """Construct a mock WebElement."""
    element = MagicMock(spec=WebElement)
    element.find_elements.return_value = [mock_element, mock_element]
    return element


def test_check_report_toast_error() -> None:
    """Ensure that toast errors raise an exception containing the error text."""
    error_text = "Never send a boy to do a woman's job."

    def find_element(by: By, value: str) -> MagicMock | None:
        """Return a mock WebElement for a toast error where all child elements have a return value containing the error text."""
        if (by, value) == (By.XPATH, "//*[@class='toast toast-error']"):
            element = mock_element()
            element.find_element.return_value.text = error_text
            return element
        return None

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    with pytest.raises(ToastErrorException, match=error_text):
        check_report_toast_error(mock_driver)


def test_check_report_dropzone_upload_error() -> None:
    error_text = "We have no names, man. No names. We are nameless!"

    def find_element(by: By, value: str) -> MagicMock | None:
        """Return a mock WebElement for a dropzone tooltip error or error message based on the (by, value) pairs."""
        if (by, value) == (By.CLASS_NAME, "dz-error-message"):
            element = mock_element()
            element.value_of_css_property.return_value = "block"
            element.find_element.side_effect = find_element
            return element
        if (by, value) == (By.TAG_NAME, "span"):
            element = mock_element()
            element.get_attribute.return_value = error_text
            return element
        return None

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    with pytest.raises(DropzoneException, match=error_text):
        check_report_dropzone_upload_error(mock_driver)


def test_check_report_upload_percentage() -> None:
    error_text = r"File upload timed out at \d+%"

    def find_element(by: By, value: str) -> MagicMock | None:
        """Return a mock WebElement with all css properties. Return sizes in pixels depending on the (by, value) pairs."""
        if (by, value) == (By.CLASS_NAME, "dz-upload"):
            element = mock_element()
            element.value_of_css_property.return_value = "55px"
            return element
        if (by, value) == (By.CLASS_NAME, "dz-progress"):
            element = mock_element()
            element.value_of_css_property.return_value = "80px"
            return element
        return None

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    with pytest.raises(LongUploadException, match=error_text):
        check_report_upload_percentage(mock_driver)
