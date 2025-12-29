"""Tests for main.py."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.forge_api import ForgeItem, ForgeReleaseChannel, ForgeURLs
from src.main import construct_objects, get_bool_env, main


class TestGetBoolEnv:
    """Tests for get_bool_env function."""

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            ("TRUE", True),
            ("true", True),
            ("1", True),
            ("YES", True),
            ("yes", True),
            ("ON", True),
            ("on", True),
            ("FALSE", False),
            ("false", False),
            ("0", False),
            ("NO", False),
            ("no", False),
            ("OFF", False),
            ("random", False),
            ("", False),
        ],
    )
    def test_get_bool_env_with_values(self, env_value: str, expected: bool, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_bool_env correctly parses various boolean string values."""
        monkeypatch.setenv("TEST_VAR", env_value)
        assert get_bool_env("TEST_VAR") == expected

    @pytest.mark.parametrize(
        ("default", "expected"),
        [
            (True, True),
            (False, False),
        ],
    )
    def test_get_bool_env_missing_key(self, default: bool, expected: bool, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_bool_env uses default value when key is missing."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        assert get_bool_env("NONEXISTENT_VAR", default=default) == expected

    def test_get_bool_env_default_is_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_bool_env defaults to False when no default specified."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        assert get_bool_env("NONEXISTENT_VAR") is False


class TestConstructObjects:
    """Tests for construct_objects function."""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
        """Set up environment variables for testing."""
        env_vars = {
            "FG_UL_FILE": "test1.pak,test2.pak",
            "FG_USER_NAME": "testuser",
            "FG_USER_PASS": "testpass",
            "FG_ITEM_ID": "12345",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    @pytest.mark.usefixtures("mock_env_vars")
    @patch("src.main.build_processing.get_build")
    def test_construct_objects_from_env(self, mock_get_build: Mock) -> None:
        """Test construct_objects successfully creates objects from environment variables."""
        mock_path = Path("/fake/path/file.pak")
        mock_get_build.return_value = mock_path

        new_files, item, urls = construct_objects()

        assert len(new_files) == 2
        assert all(f == mock_path for f in new_files)
        assert isinstance(item, ForgeItem)
        assert item.item_id == "12345"
        assert item.creds.username == "testuser"
        assert item.creds.password == "testpass"
        assert isinstance(urls, ForgeURLs)
        assert mock_get_build.call_count == 2

    @patch("src.main.build_processing.get_build")
    @patch("builtins.input")
    @patch("getpass.getpass")
    def test_construct_objects_from_input(
        self,
        mock_getpass: Mock,
        mock_input: Mock,
        mock_get_build: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test construct_objects prompts for input when env vars missing."""
        # Remove env vars
        for key in ["FG_UL_FILE", "FG_USER_NAME", "FG_USER_PASS", "FG_ITEM_ID"]:
            monkeypatch.delenv(key, raising=False)

        mock_input.side_effect = ["file.pak", "inputuser", "67890"]
        mock_getpass.return_value = "inputpass"
        mock_get_build.return_value = Path("/fake/file.pak")

        new_files, item, _urls = construct_objects()

        assert len(new_files) == 1
        assert item.creds.username == "inputuser"
        assert item.creds.password == "inputpass"
        assert item.item_id == "67890"
        assert mock_input.call_count == 3
        assert mock_getpass.call_count == 1

    @patch("src.main.build_processing.get_build")
    def test_construct_objects_multiple_files(self, mock_get_build: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test construct_objects handles multiple comma-separated files."""
        monkeypatch.setenv("FG_UL_FILE", "a.pak,b.pak,c.pak")
        monkeypatch.setenv("FG_USER_NAME", "user")
        monkeypatch.setenv("FG_USER_PASS", "pass")
        monkeypatch.setenv("FG_ITEM_ID", "123")

        mock_get_build.return_value = Path("/fake/file.pak")

        new_files, _, _ = construct_objects()

        assert len(new_files) == 3
        assert mock_get_build.call_count == 3


@pytest.fixture
def mock_forge_objects() -> tuple[list[Path], Mock, Mock]:
    """Create mock ForgeItem, files, and URLs."""
    mock_files = [Path("/fake/file.pak")]
    mock_item = Mock(spec=ForgeItem)
    mock_item.login.return_value = {"Cookie": "test"}
    mock_urls = Mock(spec=ForgeURLs)
    return mock_files, mock_item, mock_urls


@pytest.fixture
def mock_playwright_setup() -> tuple[Mock, Mock, Mock]:
    """Create and configure mock Playwright browser, context, and page."""
    mock_page = Mock()
    mock_context = Mock()
    mock_context.new_page.return_value = mock_page
    mock_browser = Mock()
    mock_browser.new_context.return_value = mock_context
    return mock_browser, mock_context, mock_page


@pytest.fixture
def _mock_load_dotenv() -> Generator[MagicMock | AsyncMock, Any, None]:
    """Mock load_dotenv to prevent .env file loading."""
    with patch("src.main.load_dotenv") as mock:
        yield mock


@pytest.fixture
def mock_construct_objects(mock_forge_objects: tuple[list[Path], Mock, Mock]) -> Generator[MagicMock | AsyncMock, Any, None]:
    """Mock construct_objects to return test objects."""
    with patch("src.main.construct_objects") as mock:
        mock.return_value = mock_forge_objects
        yield mock


@pytest.fixture
def mock_playwright(mock_playwright_setup: tuple[Mock, Mock, Mock]) -> Generator[MagicMock | AsyncMock, Any, None]:
    """Mock sync_playwright with configured browser."""
    mock_browser, _, _ = mock_playwright_setup
    with patch("src.main.sync_playwright") as mock:
        mock.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        yield mock


class TestMain:
    """Tests for main function."""

    @pytest.mark.usefixtures("_mock_load_dotenv", "mock_construct_objects", "mock_playwright")
    @patch("src.main.get_bool_env")
    def test_main_upload_only(
        self,
        mock_get_bool_env: Mock,
        mock_forge_objects: tuple[list[Path], Mock, Mock],
        mock_playwright_setup: tuple[Mock, Mock, Mock],
    ) -> None:
        """Test main function with upload enabled and readme disabled."""
        _, mock_item, _ = mock_forge_objects
        _, mock_context, _ = mock_playwright_setup

        mock_get_bool_env.side_effect = lambda key, **_kwargs: key == "FG_UPLOAD_BUILD"

        main()

        mock_item.login.assert_called_once()
        mock_item.upload_and_publish.assert_called_once()
        mock_item.update_description.assert_not_called()
        mock_context.close.assert_called_once()

    @pytest.mark.usefixtures("_mock_load_dotenv", "mock_construct_objects", "mock_playwright")
    @patch("src.main.get_bool_env")
    @patch("src.main.build_processing.get_readme")
    def test_main_readme_only(
        self,
        mock_get_readme: Mock,
        mock_get_bool_env: Mock,
        mock_forge_objects: tuple[list[Path], Mock, Mock],
        mock_playwright_setup: tuple[Mock, Mock, Mock],
    ) -> None:
        """Test main function with readme update enabled and upload disabled."""
        _, mock_item, _ = mock_forge_objects
        _, _mock_context, _ = mock_playwright_setup

        mock_get_readme.return_value = "<p>Test readme</p>"
        mock_get_bool_env.side_effect = lambda key, **_kwargs: key == "FG_README_UPDATE"

        main()

        mock_item.login.assert_called_once()
        mock_item.upload_and_publish.assert_not_called()
        mock_item.update_description.assert_called_once()
        mock_get_readme.assert_called_once()

    @pytest.mark.usefixtures("_mock_load_dotenv", "mock_construct_objects", "mock_playwright")
    @patch("src.main.os.environ.get")
    @patch("src.main.get_bool_env")
    @patch("src.main.build_processing.get_readme")
    def test_main_both_operations(
        self,
        mock_get_readme: Mock,
        mock_get_bool_env: Mock,
        mock_env_get: Mock,
        mock_forge_objects: tuple[list[Path], Mock, Mock],
    ) -> None:
        """Test main function with both upload and readme update enabled."""
        _, mock_item, _ = mock_forge_objects

        mock_get_readme.return_value = "<p>Test readme</p>"
        mock_get_bool_env.return_value = True
        mock_env_get.return_value = "LIVE"

        main()

        mock_item.login.assert_called_once()
        mock_item.upload_and_publish.assert_called_once()
        mock_item.update_description.assert_called_once()

    @pytest.mark.usefixtures("_mock_load_dotenv", "mock_construct_objects", "mock_playwright")
    @patch("src.main.get_bool_env")
    def test_main_closes_browser_on_exception(
        self,
        mock_get_bool_env: Mock,
        mock_forge_objects: tuple[list[Path], Mock, Mock],
        mock_playwright_setup: tuple[Mock, Mock, Mock],
    ) -> None:
        """Test main function properly closes browser even when exception occurs."""
        _, mock_item, _ = mock_forge_objects
        _, mock_context, _ = mock_playwright_setup

        mock_item.login.side_effect = Exception("Login failed")
        mock_get_bool_env.return_value = True

        with pytest.raises(Exception, match="Login failed"):
            main()

        mock_context.close.assert_called_once()

    @pytest.mark.usefixtures("_mock_load_dotenv", "mock_construct_objects", "mock_playwright")
    @patch("src.main.os.environ.get")
    @patch("src.main.get_bool_env")
    def test_main_respects_release_channel(
        self,
        mock_get_bool_env: Mock,
        mock_env_get: Mock,
        mock_forge_objects: tuple[list[Path], Mock, Mock],
    ) -> None:
        """Test main function correctly parses and passes release channel."""
        _, mock_item, _ = mock_forge_objects

        mock_env_get.side_effect = lambda key, default=None: "TEST" if key == "FG_RELEASE_CHANNEL" else default
        mock_get_bool_env.side_effect = lambda key, default=False: key == "FG_UPLOAD_BUILD"  # noqa: ARG005

        main()

        call_args = mock_item.upload_and_publish.call_args
        assert call_args[0][3] == ForgeReleaseChannel.TEST
