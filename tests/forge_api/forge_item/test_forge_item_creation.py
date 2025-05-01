from dataclasses import FrozenInstanceError

import pytest

from src.forge_api import ForgeItem
from tests.forge_api.test_forge_credentials import ForgeCredentialsFactory


def test_forge_item_creation() -> None:
    """Ensure that provided item id and timeout limit are found in the ForgeItems object."""
    creds = ForgeCredentialsFactory.build()
    item_data = {"33": 3.14159, "56": 22}
    for item_number, timeout in item_data.items():
        item = ForgeItem(creds, item_number, timeout)

        assert item.creds == creds
        assert item.item_id == item_number
        assert item.timeout == timeout


def test_forge_item_object_immutable() -> None:
    """Ensure that attempts at modifying values are not allowed."""
    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, "5", 7)
    with pytest.raises(FrozenInstanceError):
        item.item_id = "15"  # type: ignore[misc]
