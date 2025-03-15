"""Automation to enable uploading a new fantasygrounds mod or ext file to the FG Forge and publishing it to the Live channel."""

import getpass
import logging
import os
from pathlib import Path, PurePath

import requestium
from dotenv import load_dotenv
from selenium import webdriver

import src.build_processing as build_processing
from src.forge_api import ForgeCredentials, ForgeItem, ForgeReleaseChannel, ForgeURLs
from src.users_graph import graph_users

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")

TIMEOUT_SECONDS: float = 7
CHROME_ARGS: list[str] = [
    "--remote-debugging-port=9222",
    "--headless=new",
    "--window-size=1280,1024",
    "--no-sandbox",
]


def configure_headless_chrome() -> webdriver.ChromeOptions:
    """Prepare and return chrome options for using selenium for testing via headless systems like Github Actions."""
    options = webdriver.ChromeOptions()
    for arg in CHROME_ARGS:
        options.add_argument(arg)
    return options


def construct_objects() -> tuple[list[Path], ForgeItem, ForgeURLs]:
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

    with requestium.Session(driver=webdriver.Chrome(options=configure_headless_chrome())) as s:
        item.login(s, urls)
        if os.environ.get("FG_GRAPH_SALES", "FALSE") == "TRUE":
            graph_users(item.get_sales(s, urls))
        if os.environ.get("FG_UPLOAD_BUILD", "TRUE") == "TRUE":
            channel = ForgeReleaseChannel[os.environ.get("FG_RELEASE_CHANNEL", "LIVE").upper()]
            item.upload_and_publish(s, urls, new_files, channel)
        if os.environ.get("FG_README_UPDATE", "FALSE") == "TRUE":
            readme_text = build_processing.get_readme(new_files, os.environ.get("FG_README_NO_IMAGES", "FALSE") == "TRUE")
            item.update_description(s, urls, readme_text)


if __name__ == "__main__":
    main()
