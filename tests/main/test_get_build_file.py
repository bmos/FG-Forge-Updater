from pathlib import Path, PurePath

import pytest

from main import get_build_file


def test_get_build_file() -> None:
    """Ensure that the file path is constructed, file existence is checked, and the file Path object is returned properly"""
    assert isinstance(get_build_file(PurePath(__file__).parent, PurePath(__file__).name), Path)


def test_get_build_file_path_is_not_folder() -> None:
    """Ensure that providing the path of a the as the parent folder raises the FileNotFoundError exception"""
    with pytest.raises(FileNotFoundError):
        get_build_file(PurePath(__file__), PurePath(__file__).name)


def test_get_build_file_does_not_exist() -> None:
    """Ensure that providing the wrong file name raises the FileNotFoundError exception"""
    with pytest.raises(FileNotFoundError):
        get_build_file(PurePath(__file__).parents[1], "file-does-not-exist")
