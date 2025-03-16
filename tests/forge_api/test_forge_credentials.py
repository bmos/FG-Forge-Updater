from dataclasses import FrozenInstanceError

import pytest
from polyfactory.factories import DataclassFactory

from src.forge_api import ForgeCredentials


class ForgeCredentialsFactory(DataclassFactory[ForgeCredentials]):
    """Represents a ForgeCredentials object for the purposes of testing ForgeItem objects."""

    __model__ = ForgeCredentials


def test_forge_credentials_creation() -> None:
    """Ensures that provided username and password are found in the ForgeCredentials object and that attempts at modifying values are not allowed."""
    creds = ForgeCredentials("eugene", "i_Love md5!")
    assert creds.username == "eugene"
    assert creds.password == "i_Love md5!"

    creds = ForgeCredentials("acid_burn", "scr3wl1keUtype")
    assert creds.username == "acid_burn"
    assert creds.password == "scr3wl1keUtype"

    with pytest.raises(FrozenInstanceError):
        creds.password = "god"  # type: ignore[misc]
