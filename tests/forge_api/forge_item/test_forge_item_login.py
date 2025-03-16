import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requestium
from dotenv import load_dotenv
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement

from src.forge_api import ForgeCredentials, ForgeItem, ForgeLoginException, ForgeURLs
from src.main import configure_headless_chrome
from tests.forge_api.test_forge_credentials import ForgeCredentialsFactory


def mock_element() -> MagicMock:
    """Construct a mock WebElement."""
    element = MagicMock(spec=WebElement)
    element.click.return_value = None
    element.is_displayed.return_value = True
    element.send_keys.return_value = None
    return element


def test_csrf_extraction() -> None:
    mock_session = MagicMock(spec=requestium.Session)
    mock_session.headers = MagicMock(spec=CaseInsensitiveDict)
    mock_session.driver = MagicMock(spec=webdriver.Chrome)
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
    mock_session.get.return_value.content = """<html><head></head></html>"""

    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "1337", 1)
    assert item.creds.get_csrf_token(mock_session, ForgeURLs()) is None


def test_forge_item_login_successful() -> None:
    load_dotenv(Path(__file__).parents[3] / ".env")
    creds = ForgeCredentials(os.environ.get("FG_USER_NAME") or "", os.environ.get("FG_USER_PASS") or "")
    item = ForgeItem(creds, os.environ.get("FORGE_ITEM_ID") or "", 7)
    with webdriver.Chrome(options=configure_headless_chrome()) as forge_webdriver, requestium.Session(driver=forge_webdriver) as s:
        item.login(s, ForgeURLs())
        assert True


def test_forge_item_login_unsuccessful() -> None:
    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "1337", 1)
    with webdriver.Chrome(options=configure_headless_chrome()) as forge_webdriver, requestium.Session(driver=forge_webdriver) as s:
        try:
            item.login(s, ForgeURLs())
            pytest.fail("Logging in with bad credentials didn't result in ForgeLoginException")
        except ForgeLoginException:
            assert True
