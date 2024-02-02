from dataclasses import FrozenInstanceError

import pytest

from forge_api import ForgeURLs


def test_forge_urls() -> None:
    """Ensure set values in ForgeURLs have not been changed"""
    urls = ForgeURLs()
    assert urls.MANAGE_CRAFT == "https://forge.fantasygrounds.com/crafter/manage-craft"
    assert urls.API_CRAFTER_ITEMS == "https://forge.fantasygrounds.com/api/crafter/items"
    with pytest.raises(FrozenInstanceError):
        urls.MANAGE_CRAFT = "https://www.ellingson-mineral.com/"
