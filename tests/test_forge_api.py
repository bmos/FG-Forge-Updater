"""Tests for forge_api."""

from unittest.mock import Mock

import pytest
from patchright.sync_api import BrowserContext, Page, Response

from src.forge_api import ForgeCredentials, ForgeLoginError, ForgeURLs


@pytest.fixture
def credentials() -> ForgeCredentials:
    """Create a ForgeCredentials instance for testing."""
    return ForgeCredentials(username="test_user", password="test_pass")


@pytest.fixture
def urls() -> ForgeURLs:
    """Create ForgeURLs instance."""
    return ForgeURLs()


@pytest.fixture
def mock_setup() -> tuple[Mock, Mock, Mock]:
    """Create and configure all mocks needed for CSRF token tests."""
    mock_context = Mock(spec=BrowserContext)
    mock_page = Mock(spec=Page)
    mock_response = Mock(spec=Response)
    mock_response.ok = True

    mock_context.new_page.return_value = mock_page
    mock_page.goto.return_value = mock_response

    return mock_context, mock_page, mock_response


class TestForgeCredentials:
    """Test suite for ForgeCredentials class."""

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
