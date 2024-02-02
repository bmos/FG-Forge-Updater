from dataclasses import FrozenInstanceError

import pytest
from polyfactory.factories import DataclassFactory

from forge_api import ForgeCredentials


class ForgeCredentialsFactory(DataclassFactory[ForgeCredentials]):
    """Represents a ForgeCredentials object for the purposes of testing ForgeItem objects"""

    __model__ = ForgeCredentials


def test_forge_credentials_creation() -> None:
    """Ensures that provided username and password are found in the ForgeCredentials object and that attempts at modifying values are not allowed"""
    user_string = "eugene"
    user_pass = "i_Love md5!"

    creds = ForgeCredentials(user_string, "i_Love md5!")

    assert creds.username == user_string
    assert creds.password == user_pass
    with pytest.raises(FrozenInstanceError):
        creds.password = "god"
