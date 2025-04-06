from unittest.mock import MagicMock, call

import requestium
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.forge_api import ForgeItem, ForgeURLs
from tests.forge_api.test_forge_credentials import ForgeCredentialsFactory

TEST_CALLS = [
    (By.NAME, "vb_login_username"),
    (By.NAME, "vb_login_password"),
    (By.XPATH, "//a[@class='registerbtn']"),
]


def mock_element() -> MagicMock:
    """Construct a mock WebElement."""
    element = MagicMock(spec=WebElement)
    element.click.return_value = None
    element.is_displayed.return_value = True
    element.send_keys.return_value = None
    return element


def find_element(by: str, value: str) -> MagicMock | None:
    """Return a mock_element if the (by, value) pair isn't found in TEST_ELEMENTS."""
    if (by, value) in TEST_CALLS:
        return mock_element()
    return None


def test_csrf_extraction() -> None:
    mock_session = MagicMock(spec=requestium.Session)
    mock_session.headers = MagicMock(spec=CaseInsensitiveDict)
    mock_session.driver = MagicMock(spec=webdriver.Chrome)
    mock_session.driver.find_element.side_effect = find_element
    mock_session.get.return_value.content = """
        <html><head><meta name='csrf-token' content='2343c8fd56djfkl65f7ea74d518e19598ecb8150a84653a1c66d6a724bea39fb'></head></html>
    """

    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "1337", 1)
    assert item.creds.get_csrf_token(mock_session, ForgeURLs()) == "2343c8fd56djfkl65f7ea74d518e19598ecb8150a84653a1c66d6a724bea39fb"


def test_csrf_extraction_missing() -> None:
    mock_session = MagicMock(spec=requestium.Session)
    mock_session.headers = MagicMock(spec=CaseInsensitiveDict)
    mock_session.driver = MagicMock(spec=webdriver.Chrome)
    mock_session.driver.find_element.side_effect = find_element
    mock_session.get.return_value.content = """<html><head></head></html>"""

    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "1337", 1)
    assert item.creds.get_csrf_token(mock_session, ForgeURLs()) is None


def test_forge_item_login_calls() -> None:
    mock_session = MagicMock(spec=requestium.Session)
    mock_session.headers = MagicMock(spec=CaseInsensitiveDict)
    mock_session.driver = MagicMock(spec=webdriver.Chrome)
    mock_session.driver.find_element.side_effect = find_element
    mock_session.get.return_value.content = """
        <html><head><meta name='csrf-token' content='2343c8fd56djfkl65f7ea74d518e19598ecb8150a84653a1c66d6a724bea39fb'></head></html>
    """

    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "1337", 1)
    item.login(mock_session, ForgeURLs())
    expected_find_elements = [call(by, value) for (by, value) in TEST_CALLS]
    expected_find_elements.append(call(By.XPATH, "//div[@class='blockrow restore']"))  # login failure message
    for expected_find_element in expected_find_elements:
        assert expected_find_element in mock_session.driver.find_element.mock_calls
