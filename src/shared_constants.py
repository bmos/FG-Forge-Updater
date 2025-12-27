"""Shared constants used across the application."""

import importlib.metadata

TIMEOUT_SECONDS: float = 7.0
UI_INTERACTION_DELAY: float = 0.25


def get_user_agent() -> str:
    """Get standardized user agent string."""
    version = importlib.metadata.version("fg-forge-updater")
    return f"Mozilla/5.0 (compatible; FG-Forge-Updater/{version}; +https://github.com/bmos/FG-Forge-Updater)"
