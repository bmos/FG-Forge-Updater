from dataclasses import FrozenInstanceError

import pytest
from polyfactory.factories import DataclassFactory

from src.forge_api import ForgeCredentials


class ForgeCredentialsFactory(DataclassFactory[ForgeCredentials]):
    """Represent a ForgeCredentials object for the purposes of testing ForgeItem objects."""

    __model__ = ForgeCredentials


def test_forge_credentials_creation() -> None:
    """Ensure that provided username and password are found in the ForgeCredentials object."""
    users = {"eugene": "i_Love md5!", "acid_burn": "scr3wl1keUtype"}
    for username, password in users.items():
        creds = ForgeCredentials(username, password)
        assert creds.username == username
        assert creds.password == password


def test_forge_credentials_immutable() -> None:
    """Ensure attempts at modifying values are not allowed."""
    creds = ForgeCredentials("lmurphy", "god")
    with pytest.raises(FrozenInstanceError):
        creds.password = "g0d"  # type: ignore[misc]
