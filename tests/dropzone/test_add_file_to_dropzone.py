from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from dropzone import add_file_to_dropzone

TEST_ELEMENTS = [
    (By.XPATH, "//a[@id='manage-build-uploads-tab']"),
    (By.CLASS_NAME, "dz-hidden-input"),
    (By.CLASS_NAME, "dz-upload"),
]


def mock_element() -> MagicMock:
    """Construct a mock WebElement"""
    element = MagicMock(spec=WebElement)
    element.click.return_value = None
    element.is_displayed.return_value = True
    element.send_keys.return_value = None
    element.find_elements.side_effect = find_elements
    return element


def find_element(by: str, value: str) -> MagicMock:
    """Return a mock_element if the (by, value) pair isn't found in TEST_ELEMENTS"""
    if (by, value) in TEST_ELEMENTS:
        return mock_element()


def find_elements(by, value) -> list[MagicMock]:
    """Return two mock_elements if the (by, value) pair isn't found in TEST_ELEMENTS"""
    element = find_element(by, value)
    return [element, element]


def test_add_file_to_dropzone() -> None:
    """Ensure that element location calls are made correctly"""

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element
    mock_driver.find_elements.side_effect = find_elements

    add_file_to_dropzone(mock_driver, 1, Path(__file__))

    expected_find_element = [call(by, value) for (by, value) in TEST_ELEMENTS]
    assert mock_driver.find_element.mock_calls == expected_find_element
    mock_driver.find_elements.assert_called_once_with(By.CLASS_NAME, "dz-hidden-input")


def test_add_file_to_dropzone_timeout() -> None:
    """Ensure that timeout is raised if progress bar is not found after attempt to add file"""

    def find_element_unsuccessful(by: str, value: str) -> MagicMock:
        """Construct the WebElement mock object, but only if matching the first two definitions in TEST_ELEMENTS"""
        if (by, value) in [TEST_ELEMENTS[0], TEST_ELEMENTS[1]]:
            return mock_element()

    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element_unsuccessful
    mock_driver.find_elements.side_effect = find_elements

    with pytest.raises(TimeoutException):
        add_file_to_dropzone(mock_driver, 1, Path(__file__))
