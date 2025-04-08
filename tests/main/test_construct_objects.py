import os
from pathlib import Path

from src.forge_api import ForgeItem, ForgeURLs
from src.main import construct_objects


def test_construct_objects() -> None:
    """Ensures that the object construction function provides objects of the right type in the right order."""
    os.environ["FG_USER_NAME"] = "lmurphy"
    os.environ["FG_USER_PASS"] = "god"
    os.environ["FG_ITEM_ID"] = "7"
    os.environ["FG_UL_FILE"] = "README.md"
    new_file, item, urls = construct_objects()
    assert isinstance(new_file, list)
    assert isinstance(new_file[0], Path)
    assert isinstance(item, ForgeItem)
    assert isinstance(urls, ForgeURLs)
