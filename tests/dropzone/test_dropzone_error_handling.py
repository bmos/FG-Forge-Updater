from unittest.mock import MagicMock

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from dropzone import DropzoneErrorHandling, DropzoneException, LongUploadException, ToastErrorException


def mock_element() -> MagicMock:
    """Construct a mock WebElement"""
    element = MagicMock(spec=WebElement)
    element.find_elements.return_value = [mock_element, mock_element]
    return element


def test_check_report_toast_error() -> None:
    """Ensure that toast errors raise an exception containing the error text"""
    error_text = "Never send a boy to do a woman's job."

    def find_element(by, value) -> MagicMock:
        """Returns a mock WebElement for a toast error where all child elements have a return value containing the error text"""
        if by == By.XPATH and value == "//*[@class='toast toast-error']":
            element = mock_element()
            element.find_element.return_value.text = error_text
            return element

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    with pytest.raises(ToastErrorException, match=error_text):
        error_handling = DropzoneErrorHandling(mock_driver)
        error_handling.check_report_toast_error()


def test_check_report_dropzone_upload_error() -> None:
    error_text = "We have no names, man. No names. We are nameless!"

    def find_element(by, value) -> MagicMock:
        """Returns a mock WebElement for a dropzone tooltip error or error message based on the (by, value) pairs"""
        if by == By.CLASS_NAME and value == "dz-error-message":
            element = mock_element()
            element.value_of_css_property.return_value = "block"
            element.find_element.side_effect = find_element
            return element
        if by == By.TAG_NAME and value == "span":
            element = mock_element()
            element.get_attribute.return_value = error_text
            return element

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    with pytest.raises(DropzoneException, match=error_text):
        error_handling = DropzoneErrorHandling(mock_driver)
        error_handling.check_report_dropzone_upload_error()


def test_check_report_upload_percentage() -> None:
    error_text = r"File upload timed out at \d+%"

    def find_element(by, value) -> MagicMock:
        """Returns a mock WebElement with all css properties returning sizes in pixels depending on the (by, value) pairs"""
        if by == By.CLASS_NAME and value == "dz-upload":
            element = mock_element()
            element.value_of_css_property.return_value = "55px"
            return element
        if by == By.CLASS_NAME and value == "dz-progress":
            element = mock_element()
            element.value_of_css_property.return_value = "80px"
            return element

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    with pytest.raises(LongUploadException, match=error_text):
        error_handling = DropzoneErrorHandling(mock_driver)
        error_handling.check_report_upload_percentage()
