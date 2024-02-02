from dataclasses import FrozenInstanceError

import pytest

from forge_api import ForgeItem
from ..test_forge_credentials import ForgeCredentialsFactory


def test_forge_item_creation() -> None:
    """Ensures that provided item id and timeout limit are found in the ForgeItems object and that attempts at modifying values are not allowed"""
    item_string = "33"
    timeout_string = float(3.14159)

    creds = ForgeCredentialsFactory.build()
    item = ForgeItem(creds, item_string, timeout_string)

    assert item.creds == creds
    assert item.item_id == item_string
    assert item.timeout == timeout_string
    with pytest.raises(FrozenInstanceError):
        item.item_id = "7"
