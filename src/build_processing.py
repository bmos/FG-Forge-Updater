import itertools
import logging
import re
from pathlib import Path, PurePath
from zipfile import ZipFile

from bs4 import BeautifulSoup
from markdown import markdown

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")

README_FILE_NAME: str = "README.md"


def table_styling(soup: BeautifulSoup) -> BeautifulSoup:
    """Style tables for better legibility"""
    colors = itertools.cycle(["#FFFFFF", "#E6E6E6"])
    for html_table in soup.find_all("table"):
        for col in html_table.find_all("td"):
            col["style"] = "border:1px solid #000; padding:0.5em;"
        for row in html_table.find_all("tr"):
            row["style"] = f"background-color: {next(colors)}; border:1px solid #000;"
    return soup


def strip_images(soup: BeautifulSoup) -> BeautifulSoup:
    """Replace all images with boilerplate text"""
    for img in soup.find_all("img"):
        new_tag = soup.new_tag("a", href=img["src"])
        new_tag.string = img.get("alt", "[IMG]")
        img.replace_with(new_tag)
    return soup


def readme_html(readme) -> str:
    """returns an html-formatted string"""
    markdown_text = readme.read(README_FILE_NAME).decode("UTF-8")
    markdown_text_clean = re.sub("!\[]\(.+\)", "", markdown_text)
    markdown_html = markdown(markdown_text_clean, extensions=["extra", "nl2br", "smarty"])
    soup = BeautifulSoup(markdown_html, "html.parser")
    soup = strip_images(soup)
    soup = table_styling(soup)
    return str(soup)


def get_readme(new_files: list[Path]) -> str:
    """Parses the first README.md found in the new files and returns an html-formatted string"""
    return next((readme_html(ZipFile(file)) for file in new_files if README_FILE_NAME in ZipFile(file).namelist()), None)


def get_build(file_path: PurePath, env_file: str) -> Path:
    """Combines PurePath and file name into a Path object, ensure that a file exists there, and returns the Path"""
    new_file = Path(file_path, env_file)
    logging.info("File upload path determined to be: %s", new_file)
    if not new_file.is_file():
        raise FileNotFoundError(f"File at {str(new_file)} is not found.")
    return new_file
