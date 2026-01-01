"""Tests for forge_api."""

import re
from unittest.mock import ANY, Mock

import pytest
from patchright.sync_api import BrowserContext, Page, Response
from patchright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.forge_api import ForgeCredentials, ForgeItem, ForgeLoginError, ForgeURLs, _wait_for_element
from src.shared_constants import get_user_agent


@pytest.fixture
def credentials() -> ForgeCredentials:
    """Create a ForgeCredentials instance for testing."""
    return ForgeCredentials(username="test_user", password="test_pass")


@pytest.fixture
def urls() -> ForgeURLs:
    """Create ForgeURLs instance."""
    return ForgeURLs()


class TestWaitForElement:
    """Tests for _wait_for_element utility function."""

    @pytest.mark.parametrize(
        ("selector", "timeout"),
        [
            ("button#submit", 5),
            (
                "div.container",
                10,
            ),
            ("input[name='username']", 1.5),
            ("//a[@class='link']", 0.5),
            ("select[name='items-table_length']", 7.0),
        ],
    )
    def test_element_found_successfully(
        self,
        selector: str,
        timeout: float,
    ) -> None:
        """Test that element is returned when found within timeout."""
        mock_page = Mock(spec=["wait_for_selector"])
        mock_element = Mock(spec=["inner_text", "click", "fill"])
        mock_page.wait_for_selector.return_value = mock_element

        result = _wait_for_element(mock_page, selector, timeout)

        assert result == mock_element
        mock_page.wait_for_selector.assert_called_once_with(selector, timeout=timeout * 1000)

    @pytest.mark.parametrize(
        ("selector", "timeout", "element_description", "expected_error"),
        [
            ("button#submit", 5.0, "Submit button", "Submit button not found"),
            ("div.container", 10.0, "Container div", "Container div not found"),
            ("input[name='username']", 7.0, "Username field", "Username field not found"),
            ("//a[@id='manage-item-tab']", 3.0, "Manage item tab", "Manage item tab not found"),
        ],
    )
    def test_element_not_found_with_custom_description(
        self,
        selector: str,
        timeout: float,
        element_description: str,
        expected_error: str,
    ) -> None:
        """Test that PlaywrightTimeoutError is raised with custom description when element not found."""
        mock_page = Mock(spec=["wait_for_selector"])
        mock_page.wait_for_selector.return_value = None

        with pytest.raises(PlaywrightTimeoutError, match=expected_error):
            _wait_for_element(mock_page, selector, timeout, element_description)

        mock_page.wait_for_selector.assert_called_once_with(selector, timeout=timeout * 1000)

    @pytest.mark.parametrize(
        ("selector", "timeout"),
        [
            ("button#submit", 5.0),
            ("div.container", 10.0),
            ("input[name='username']", 7.0),
            ("//a[@class='registerbtn']", 3.5),
        ],
    )
    def test_element_not_found_without_custom_description(
        self,
        selector: str,
        timeout: float,
    ) -> None:
        """Test that PlaywrightTimeoutError is raised with selector as description when element not found and no description provided."""
        mock_page = Mock(spec=["wait_for_selector"])
        mock_page.wait_for_selector.return_value = None

        with pytest.raises(PlaywrightTimeoutError, match=re.escape(f"{selector} not found")):
            _wait_for_element(mock_page, selector, timeout)

        mock_page.wait_for_selector.assert_called_once_with(selector, timeout=timeout * 1000)

    @pytest.mark.parametrize(
        "timeout",
        [
            0.1,
            0.5,
            1,
            7.0,
            15.5,
            30.0,
            30,
        ],
    )
    def test_timeout_conversion_to_milliseconds(
        self,
        timeout: float,
    ) -> None:
        """Test that timeout in seconds is correctly converted to milliseconds."""
        mock_page = Mock(spec=["wait_for_selector"])
        mock_element = Mock()
        mock_page.wait_for_selector.return_value = mock_element
        selector = "div.test"

        _wait_for_element(mock_page, selector, timeout)

        mock_page.wait_for_selector.assert_called_once_with(selector, timeout=timeout * 1000)


class TestForgeCredentials:
    """Test suite for ForgeCredentials class."""

    @pytest.fixture
    def mock_setup(self) -> tuple[Mock, Mock, Mock]:
        """Create and configure all mocks needed for CSRF token tests."""
        mock_context = Mock(spec=BrowserContext)
        mock_page = Mock(spec=Page)
        mock_response = Mock(spec=Response)
        mock_response.ok = True

        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = mock_response

        return mock_context, mock_page, mock_response

    def test_credentials_immutable(self, credentials: ForgeCredentials) -> None:
        """Test that ForgeCredentials is frozen (immutable)."""
        with pytest.raises(AttributeError):
            credentials.username = "new_user"  # type: ignore[misc]

    def test_credentials_initialization(self) -> None:
        """Test that credentials are properly initialized."""
        creds = ForgeCredentials(username="user123", password="pass456")
        assert creds.username == "user123"
        assert creds.password == "pass456"

    @pytest.mark.parametrize(
        ("html_content", "expected_token"),
        [
            ('<html><head><meta name="csrf-token" content="abc123"></head></html>', "abc123"),
            ('<html><head><meta name="csrf-token" content="xyz789-token"></head></html>', "xyz789-token"),
            ('<html><head><meta name="csrf-token" content="special!@#$%chars"></head></html>', "special!@#$%chars"),
        ],
    )
    def test_get_csrf_token_success(
        self,
        credentials: ForgeCredentials,
        mock_setup: tuple[Mock, Mock, Mock],
        urls: ForgeURLs,
        html_content: str,
        expected_token: str,
    ) -> None:
        """Test successful CSRF token retrieval with various token formats."""
        mock_context, mock_page, _ = mock_setup
        mock_page.content.return_value = html_content

        token = credentials.get_csrf_token(mock_context, urls)

        assert token == expected_token
        mock_context.new_page.assert_called_once()
        mock_page.goto.assert_called_once_with(urls.MANAGE_CRAFT)
        mock_page.content.assert_called_once()
        mock_page.close.assert_called_once()

    def test_get_csrf_token_empty_response(self, credentials: ForgeCredentials, mock_setup: tuple[Mock, Mock, Mock], urls: ForgeURLs) -> None:
        """Test that ForgeLoginError is raised when response is None."""
        mock_context, mock_page, _ = mock_setup
        mock_page.goto.return_value = None

        with pytest.raises(ForgeLoginError, match="Empty response when fetching CSRF token"):
            credentials.get_csrf_token(mock_context, urls)

        mock_page.close.assert_called_once()

    def test_get_csrf_token_response_not_ok(self, credentials: ForgeCredentials, mock_setup: tuple[Mock, Mock, Mock], urls: ForgeURLs) -> None:
        """Test that ForgeLoginError is raised when response is not OK."""
        mock_context, mock_page, mock_response = mock_setup
        mock_response.ok = False

        with pytest.raises(ForgeLoginError, match="HTML failure code when fetching CSRF token"):
            credentials.get_csrf_token(mock_context, urls)

        mock_page.close.assert_called_once()

    @pytest.mark.parametrize(
        ("html_content", "error_match"),
        [
            ("<html><head></head><body>No token here</body></html>", "CSRF token html element not found or invalid"),
            ('<html><head><meta name="csrf-token" content=""></head></html>', "CSRF token content attribute is empty"),
        ],
    )
    def test_get_csrf_token_invalid_html(
        self,
        credentials: ForgeCredentials,
        mock_setup: tuple[Mock, Mock, Mock],
        urls: ForgeURLs,
        html_content: str,
        error_match: str,
    ) -> None:
        """Test that ForgeLoginError is raised for various invalid HTML conditions."""
        mock_context, mock_page, _ = mock_setup
        mock_page.content.return_value = html_content

        with pytest.raises(ForgeLoginError, match=error_match):
            credentials.get_csrf_token(mock_context, urls)

        mock_page.close.assert_called_once()

    def test_get_csrf_token_page_closes_on_success(self, credentials: ForgeCredentials, mock_setup: tuple[Mock, Mock, Mock], urls: ForgeURLs) -> None:
        """Test that page is properly closed after successful token retrieval."""
        mock_context, mock_page, _ = mock_setup
        mock_page.content.return_value = '<html><head><meta name="csrf-token" content="token123"></head></html>'

        credentials.get_csrf_token(mock_context, urls)

        mock_page.close.assert_called_once()

    def test_get_csrf_token_page_closes_on_error(self, credentials: ForgeCredentials, mock_setup: tuple[Mock, Mock, Mock], urls: ForgeURLs) -> None:
        """Test that page is properly closed even when an error occurs."""
        mock_context, mock_page, _ = mock_setup
        mock_page.goto.return_value = None

        with pytest.raises(ForgeLoginError):
            credentials.get_csrf_token(mock_context, urls)

        mock_page.close.assert_called_once()


class TestForgeItem:
    """Test suite for ForgeItem class."""

    @pytest.fixture
    def forge_item(self, credentials: ForgeCredentials) -> ForgeItem:
        """Create a ForgeItem instance for testing."""
        return ForgeItem(creds=credentials, item_id="12345", timeout=7.0)

    def test_forge_item_initialization(self, forge_item: ForgeItem, credentials: ForgeCredentials) -> None:
        """Test that ForgeItem is properly initialized with all attributes."""
        assert forge_item.creds == credentials
        assert forge_item.item_id == "12345"
        assert forge_item.timeout == 7.0

    def test_is_already_logged_in_true(self, forge_item: ForgeItem, urls: ForgeURLs) -> None:
        """Test _is_already_logged_in returns True when no login prompt is present."""
        mock_page = Mock(spec=Page)
        mock_page.goto.return_value = None
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = forge_item._is_already_logged_in(mock_page, urls)

        assert result is True
        mock_page.goto.assert_called_once_with(urls.FORGE_LOGIN)
        mock_page.wait_for_selector.assert_called_once_with(
            "div[class='alert alert-info text-center']",
            timeout=ANY,
        )

    def test_is_already_logged_in_false(self, forge_item: ForgeItem, urls: ForgeURLs) -> None:
        """Test _is_already_logged_in returns False when login prompt is present."""
        mock_page = Mock(spec=Page)
        mock_element = Mock()
        mock_element.inner_text.return_value = "You are not logged in"

        mock_page.goto.return_value = None
        mock_page.wait_for_selector.return_value = mock_element

        result = forge_item._is_already_logged_in(mock_page, urls)

        assert result is False

    def test_login_failed_true(self, forge_item: ForgeItem) -> None:
        """Test _login_failed returns True when error message is present."""
        mock_page = Mock(spec=Page)
        mock_element = Mock()
        mock_element.inner_text.return_value = "You have entered an invalid username or password"

        mock_page.wait_for_selector.return_value = mock_element

        result = forge_item._login_failed(mock_page)

        assert result is True

    def test_login_failed_false(self, forge_item: ForgeItem) -> None:
        """Test _login_failed returns False when no error message is found."""
        mock_page = Mock(spec=Page)
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = forge_item._login_failed(mock_page)

        assert result is False

    def test_get_auth_headers(self, forge_item: ForgeItem, urls: ForgeURLs) -> None:
        """Test _get_auth_headers constructs proper header dictionary."""
        csrf_token = {"name": "csrf-token", "value": "csrf_token_value"}
        mock_context = Mock(spec=BrowserContext)
        mock_cookies = [
            {"name": "session_id", "value": "abc123"},
            {"name": "user_token", "value": "xyz789"},
        ]
        mock_context.cookies.return_value = mock_cookies

        mock_page = Mock(spec=Page)
        mock_response = Mock(spec=Response)
        mock_response.ok = True
        mock_page.goto.return_value = mock_response
        mock_page.content.return_value = f'<html><head><meta name="{csrf_token["name"]}" content="{csrf_token["value"]}"></head></html>'
        mock_context.new_page.return_value = mock_page

        headers = forge_item._get_auth_headers(mock_context, urls)

        assert "Cookie" in headers
        assert headers["Cookie"] == f"{mock_cookies[0]['name']}={mock_cookies[0]['value']}; {mock_cookies[1]['name']}={mock_cookies[1]['value']}"

        assert "X-CSRF-TOKEN" in headers
        assert headers["X-CSRF-TOKEN"] == csrf_token["value"]

        assert "User-Agent" in headers
        assert headers["User-Agent"] == get_user_agent()
