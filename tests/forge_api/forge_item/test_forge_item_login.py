from unittest.mock import MagicMock, call

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from forge_api import ForgeItem, ForgeURLs
from ..test_forge_credentials import ForgeCredentialsFactory

TEST_CALLS = [
    (By.NAME, "vb_login_username"),
    (By.NAME, "vb_login_password"),
    (By.CLASS_NAME, "registerbtn"),
]


def mock_element() -> MagicMock:
    """Construct a mock WebElement"""
    element = MagicMock(spec=WebElement)
    element.click.return_value = None
    element.is_displayed.return_value = True
    element.send_keys.return_value = None
    return element


def find_element(by: str, value: str) -> MagicMock:
    """Return a mock_element if the (by, value) pair isn't found in TEST_ELEMENTS"""
    if (by, value) in TEST_CALLS:
        return mock_element()


def test_forge_item_login() -> None:
    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.find_element.side_effect = find_element

    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "33", 1)
    item.login(mock_driver, ForgeURLs())
    expected_find_element = [call(by, value) for (by, value) in TEST_CALLS]
    assert mock_driver.find_element.mock_calls == expected_find_element
