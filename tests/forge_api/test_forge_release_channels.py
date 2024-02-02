from forge_api import ReleaseChannel


def test_forge_urls() -> None:
    """Ensure set values in ForgeURLs have not been changed"""
    assert ReleaseChannel.LIVE == "Live"
    assert ReleaseChannel.TEST == "Test"
    assert ReleaseChannel.NONE == "No Channel"
