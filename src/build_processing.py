import itertools
import logging
import re
from pathlib import Path, PurePath
from zipfile import ZipFile

import mdformat
from bs4 import BeautifulSoup
from markdown import markdown


def apply_styles_to_table(soup: BeautifulSoup) -> BeautifulSoup:
    """Style tables for better legibility."""
    colors = itertools.cycle(["#000000", "#1C1C1E"])
    for html_table in soup.find_all("table"):
        for col in html_table.find_all("td"):
            col["style"] = "border:1px solid #FFFFFF; padding:0.5em;"
        for row in html_table.find_all("tr"):
            row["style"] = f"background-color: {next(colors)}; border:1px solid #FFFFFF;"
    return soup


def replace_images_with_link(soup: BeautifulSoup, no_images: bool) -> BeautifulSoup:
    """Replace all images with boilerplate text."""
    for img in soup.find_all("img"):
        link_url = img.parent.get("href") if img.parent.get("href") else img.get("src")
        new_tag = soup.new_tag("a", href=link_url)
        new_tag.string = "" if no_images else img.get("alt", "[IMG]")
        img.replace_with(new_tag)
    return soup


def readme_html(markdown_text: str, no_images: bool = False) -> str:
    """Return an html-formatted string from a string formatted as markdown."""
    markdown_text = re.sub(r"!\[]\(\..+?\)", "", markdown_text)
    markdown_text = mdformat.text(markdown_text)
    html = markdown(markdown_text, extensions=["extra", "nl2br", "smarty"])
    soup = BeautifulSoup(html, "html.parser")
    soup = replace_images_with_link(soup, no_images)
    soup = apply_styles_to_table(soup)
    return str(soup)


def get_readme(new_files: list[Path], no_images: bool = False, readme_name: str = "README.md") -> str:
    """Read the first README.md found in the new zip files and call readme_html() returning the result."""
    return next((readme_html(ZipFile(file).read(readme_name).decode("UTF-8"), no_images) for file in new_files if readme_name in ZipFile(file).namelist()), "")


def get_build(file_path: PurePath, env_file: str) -> Path:
    """Combine PurePath and file name into a Path object, ensure that a file exists there, and return the Path."""
    new_file = Path(file_path / env_file)
    logging.info("File upload path determined to be: %s", new_file)
    if not new_file.is_file():
        error_msg = f"File at {new_file!s} is not found."
        raise FileNotFoundError(error_msg)
    return new_file
