from pathlib import Path, PurePath

import pytest

from src.build_processing import get_build


def test_get_build_file() -> None:
    """Ensure that the file path is constructed and the file Path object is returned properly."""
    assert get_build(PurePath(__file__).parent, PurePath(__file__).name) == Path(__file__)


def test_get_build_file_does_not_exist() -> None:
    """Ensure that providing the wrong file name raises the FileNotFoundError exception."""
    with pytest.raises(FileNotFoundError):
        get_build(PurePath(__file__).parent, "file-does-not-exist")
