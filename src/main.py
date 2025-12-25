"""Automation to enable uploading a new fantasygrounds mod or ext file to the FG Forge and publishing it to the Live channel."""

import getpass
import logging
import os
from pathlib import Path, PurePath

from dotenv import load_dotenv
from patchright.sync_api import ViewportSize, sync_playwright

from src import build_processing
from src.forge_api import ForgeCredentials, ForgeItem, ForgeReleaseChannel, ForgeURLs
from src.shared_constants import TIMEOUT_SECONDS, get_user_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")


def construct_objects() -> tuple[list[Path], ForgeItem, ForgeURLs]:
    """Construct necessary objects from environment variables or user input."""
    file_names = os.environ.get("FG_UL_FILE") or input("Files to include in build (comma-separated and within project folder): ")
    new_files = [build_processing.get_build(PurePath(__file__).parents[1], file) for file in file_names.split(",")]

    user_name = os.environ.get("FG_USER_NAME") or input("FantasyGrounds username: ")
    user_pass = os.environ.get("FG_USER_PASS") or getpass.getpass("FantasyGrounds password: ")
    creds = ForgeCredentials(user_name, user_pass)

    item_id = os.environ.get("FG_ITEM_ID") or input("Forge item ID: ")
    item = ForgeItem(creds, item_id, TIMEOUT_SECONDS)
    urls = ForgeURLs()

    return new_files, item, urls


def main() -> None:
    """Hey, I just met you, and this is crazy, but I'm the main function, so call me maybe."""
    load_dotenv(Path(PurePath(__file__).parents[1], ".env"))
    new_files, item, urls = construct_objects()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--window-size=1280,1024"])

        context = browser.new_context(
            user_agent=get_user_agent(),
            viewport=ViewportSize(width=1280, height=1024),
        )

        page = context.new_page()

        try:
            headers = item.login(page, context, urls)

            if os.environ.get("FG_UPLOAD_BUILD", "TRUE") == "TRUE":
                channel = ForgeReleaseChannel[os.environ.get("FG_RELEASE_CHANNEL", "LIVE").upper()]
                item.upload_and_publish(headers, urls, new_files, channel)

            if os.environ.get("FG_README_UPDATE", "FALSE") == "TRUE":
                readme_text = build_processing.get_readme(new_files, no_images=os.environ.get("FG_README_NO_IMAGES", "FALSE") == "TRUE")
                item.update_description(page, context, urls, readme_text)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
