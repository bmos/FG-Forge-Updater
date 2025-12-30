"""Tests for main.py."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.forge_api import ForgeItem, ForgeReleaseChannel, ForgeURLs
from src.main import construct_objects, get_bool_env, main, resolve_file_paths


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


class TestResolveFilePaths:
    """Tests for resolve_file_paths function."""

    def test_resolve_single_file_absolute(self, tmp_path: Path) -> None:
        """Test resolving an absolute path to a single file."""
        test_file = tmp_path / "test.pak"
        test_file.write_text("test content")

        result = resolve_file_paths(str(test_file), tmp_path)

        assert len(result) == 1
        assert result[0] == test_file
        assert result[0].is_file()

    def test_resolve_single_file_relative(self, tmp_path: Path) -> None:
        """Test resolving a relative path to a single file."""
        test_file = tmp_path / "test.pak"
        test_file.write_text("test content")

        result = resolve_file_paths("test.pak", tmp_path)

        assert len(result) == 1
        assert result[0] == test_file
        assert result[0].is_file()

    def test_resolve_directory_with_files(self, tmp_path: Path) -> None:
        """Test resolving a directory path returns all files in the directory."""
        test_dir = tmp_path / "builds"
        test_dir.mkdir()

        file1 = test_dir / "build1.pak"
        file2 = test_dir / "build2.pak"
        file3 = test_dir / "build3.ext"

        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")

        result = resolve_file_paths(str(test_dir), tmp_path)

        assert len(result) == 3
        assert all(f.is_file() for f in result)
        assert set(result) == {file1, file2, file3}

    def test_resolve_directory_ignores_subdirectories(self, tmp_path: Path) -> None:
        """Test that directory resolution only returns files, not subdirectories."""
        test_dir = tmp_path / "builds"
        test_dir.mkdir()

        file1 = test_dir / "build1.pak"
        file1.write_text("content1")

        subdir = test_dir / "subdir"
        subdir.mkdir()
        nested_file = subdir / "nested.pak"
        nested_file.write_text("nested content")

        result = resolve_file_paths(str(test_dir), tmp_path)

        assert len(result) == 1
        assert result[0] == file1
        assert nested_file not in result

    def test_resolve_directory_empty_raises_error(self, tmp_path: Path) -> None:
        """Test that an empty directory raises a ValueError."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ValueError, match="contains no files"):
            resolve_file_paths(str(empty_dir), tmp_path)

    def test_resolve_nonexistent_path_raises_error(self, tmp_path: Path) -> None:
        """Test that a nonexistent path raises a FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="does not exist"):
            resolve_file_paths("nonexistent.pak", tmp_path)

    def test_resolve_directory_relative(self, tmp_path: Path) -> None:
        """Test resolving a relative directory path."""
        test_dir = tmp_path / "builds"
        test_dir.mkdir()

        file1 = test_dir / "build1.pak"
        file1.write_text("content1")

        result = resolve_file_paths("builds", tmp_path)

        assert len(result) == 1
        assert result[0] == file1

    def test_resolve_comma_separated_files(self, tmp_path: Path) -> None:
        """Test resolving comma-separated file paths."""
        file1 = tmp_path / "file1.pak"
        file2 = tmp_path / "file2.pak"
        file1.write_text("content1")
        file2.write_text("content2")

        result = resolve_file_paths(f"{file1},{file2}", tmp_path)

        assert len(result) == 2
        assert set(result) == {file1, file2}

    def test_resolve_comma_separated_with_spaces(self, tmp_path: Path) -> None:
        """Test that comma-separated paths with spaces are handled correctly."""
        file1 = tmp_path / "file1.pak"
        file2 = tmp_path / "file2.pak"
        file1.write_text("content1")
        file2.write_text("content2")

        result = resolve_file_paths(f"{file1} , {file2}", tmp_path)

        assert len(result) == 2
        assert set(result) == {file1, file2}

    def test_resolve_mixed_files_and_directories(self, tmp_path: Path) -> None:
        """Test resolving a mix of files and directories in comma-separated list."""
        single_file = tmp_path / "single.pak"
        single_file.write_text("single content")

        test_dir = tmp_path / "builds"
        test_dir.mkdir()

        dir_file1 = test_dir / "build1.pak"
        dir_file2 = test_dir / "build2.pak"
        dir_file1.write_text("content1")
        dir_file2.write_text("content2")

        result = resolve_file_paths(f"{single_file},{test_dir}", tmp_path)

        assert len(result) == 3
        assert set(result) == {single_file, dir_file1, dir_file2}

    def test_resolve_empty_string_segments(self, tmp_path: Path) -> None:
        """Test that empty string segments from trailing commas are ignored."""
        test_file = tmp_path / "test.pak"
        test_file.write_text("test content")

        result = resolve_file_paths(f"{test_file},", tmp_path)

        assert len(result) == 1
        assert result[0] == test_file

    def test_resolve_multiple_directories(self, tmp_path: Path) -> None:
        """Test resolving multiple directories in comma-separated list."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        file1 = dir1 / "file1.pak"
        file2 = dir1 / "file2.pak"
        file3 = dir2 / "file3.pak"

        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")

        result = resolve_file_paths(f"{dir1},{dir2}", tmp_path)

        assert len(result) == 3
        assert set(result) == {file1, file2, file3}


class TestConstructObjects:
    """Tests for construct_objects function."""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
        """Set up environment variables for testing."""
        test_file = tmp_path / "test.pak"
        test_file.write_text("content")

        monkeypatch.setenv("FG_UL_FILE", str(test_file))
        monkeypatch.setenv("FG_USER_NAME", "testuser")
        monkeypatch.setenv("FG_USER_PASS", "testpass")
        monkeypatch.setenv("FG_ITEM_ID", "12345")

        return test_file

    def test_construct_objects_from_env(self, mock_env_vars: Path) -> None:
        """Test that construct_objects correctly reads from environment variables."""
        new_files, item, _urls = construct_objects()

        assert len(new_files) == 1
        assert new_files[0] == mock_env_vars
        assert item.creds.username == "testuser"
        assert item.creds.password == "testpass"
        assert item.item_id == "12345"

    def test_construct_objects_with_comma_separated_files(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test that construct_objects handles comma-separated file list."""
        file1 = tmp_path / "file1.pak"
        file2 = tmp_path / "file2.pak"
        file1.write_text("content1")
        file2.write_text("content2")

        monkeypatch.setenv("FG_UL_FILE", f"{file1},{file2}")
        monkeypatch.setenv("FG_USER_NAME", "testuser")
        monkeypatch.setenv("FG_USER_PASS", "testpass")
        monkeypatch.setenv("FG_ITEM_ID", "12345")

        new_files, _item, _urls = construct_objects()

        assert len(new_files) == 2
        assert set(new_files) == {file1, file2}

    def test_construct_objects_with_directory(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test that construct_objects handles directory paths."""
        test_dir = tmp_path / "builds"
        test_dir.mkdir()

        file1 = test_dir / "build1.pak"
        file2 = test_dir / "build2.pak"
        file1.write_text("content1")
        file2.write_text("content2")

        monkeypatch.setenv("FG_UL_FILE", str(test_dir))
        monkeypatch.setenv("FG_USER_NAME", "testuser")
        monkeypatch.setenv("FG_USER_PASS", "testpass")
        monkeypatch.setenv("FG_ITEM_ID", "12345")

        new_files, _item, _urls = construct_objects()

        assert len(new_files) == 2
        assert set(new_files) == {file1, file2}

    @patch("builtins.input")
    def test_construct_objects_from_input(self, mock_input: MagicMock, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test that construct_objects correctly reads from user input when env vars are not set."""
        test_file = tmp_path / "test.pak"
        test_file.write_text("content")

        monkeypatch.delenv("FG_UL_FILE", raising=False)
        monkeypatch.delenv("FG_USER_NAME", raising=False)
        monkeypatch.delenv("FG_USER_PASS", raising=False)
        monkeypatch.delenv("FG_ITEM_ID", raising=False)

        mock_input.side_effect = [str(test_file), "testuser", "12345"]

        with patch("getpass.getpass", return_value="testpass"):
            new_files, item, _urls = construct_objects()

        assert len(new_files) == 1
        assert new_files[0] == test_file
        assert item.creds.username == "testuser"
        assert item.creds.password == "testpass"
        assert item.item_id == "12345"


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
