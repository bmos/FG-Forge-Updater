"""Automation to enable uploading a new fantasygrounds mod or ext file to the FG Forge and publishing it to the Live channel"""

import logging
import os
from pathlib import Path, PurePath
from zipfile import ZipFile

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from markdown import markdown
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from forge_api import ForgeItem, ForgeCredentials, ForgeURLs, ReleaseChannel

logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")
load_dotenv(Path(PurePath(__file__).parents[1], ".env"))

TIMEOUT_SECONDS: float = 15


def configure_headless_chrome() -> webdriver.ChromeOptions:
    """Prepare and return chrome options for using selenium for testing via headless systems like Github Actions"""
    options = webdriver.ChromeOptions()
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1024")
    return options


def get_readme_html(new_file: Path) -> str:
    """Parses the README.md from the new build and returns an html-formatted string with image width limited"""
    zip_file = ZipFile(new_file)
    if "README.md" in zip_file.namelist():
        markdown_text = zip_file.read("README.md").decode("UTF-8")
        soup = BeautifulSoup(markdown(markdown_text), "html.parser")
        for img in soup.find_all("img"):
            img["style"] = "max-width: 100%;"
        return str(soup)


def get_build_file(file_path: PurePath, env_file: str) -> Path:
    """Combines PurePath and file name into a Path object, ensure that a file exists there, and returns the Path"""
    new_file = Path(file_path, env_file)
    logging.debug("File upload path determined to be: %s", new_file)
    if not new_file.is_file():
        raise FileNotFoundError(f"File at {str(new_file)} is not found.")
    return new_file


def construct_objects() -> (Path, ForgeItem, ForgeURLs):
    """Gets the various objects needed to start uploading builds to the FG Forge"""
    new_file = get_build_file(PurePath(__file__).parents[1], os.environ["FG_UL_FILE"])
    creds = ForgeCredentials(os.environ["FG_USER_NAME"], os.environ["FG_USER_PASS"])
    item = ForgeItem(creds, os.environ["FG_ITEM_ID"], TIMEOUT_SECONDS)
    urls = ForgeURLs()
    return new_file, item, urls


def main() -> None:
    """Hey, I just met you, and this is crazy, but I'm the main function, so call me maybe."""
    new_file, item, urls = construct_objects()

    with webdriver.Chrome(service=Service(), options=configure_headless_chrome()) as driver:
        item.upload_and_publish(driver, urls, new_file, ReleaseChannel.LIVE)
        readme_text = get_readme_html(new_file)
        if readme_text and "FG_README_UPDATE" not in os.environ or os.environ["FG_README_UPDATE"] != "FALSE":
            item.update_description(driver, urls, readme_text)


if __name__ == "__main__":
    main()
