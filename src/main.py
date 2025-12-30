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

logging.basicConfig(level=logging.INFO, format="%(levelname)s : fg-forge-updater:%(name)s : %(message)s")
logger = logging.getLogger(__name__)


def get_bool_env(key: str, *, default: bool = False) -> bool:
    """Parse boolean from environment variable."""
    value = os.environ.get(key, str(default).upper())
    return value.upper() in ("TRUE", "1", "YES", "ON")


def resolve_file_paths(path_string: str, project_root: Path) -> list[Path]:
    """
    Resolve file or directory paths that may be absolute or relative.

    Supports comma-separated paths. Each path can be:
    - A single file: returns that file
    - A directory: returns all files within it (non-recursive)
    - Multiple comma-separated paths: returns all resolved files

    Args:
        path_string: Comma-separated file or directory path string(s) to resolve
        project_root: The project root directory for resolving relative paths

    Returns:
        List of resolved absolute Path objects

    Raises:
        FileNotFoundError: If any resolved path does not exist
        ValueError: If any path is a directory but contains no files

    """
    all_files: list[Path] = []

    for path_segment in path_string.split(","):
        path_segment_cleaned = path_segment.strip()
        if not path_segment_cleaned:
            continue

        input_path = Path(path_segment_cleaned)
        resolved_path = input_path.resolve() if input_path.is_absolute() else (project_root / input_path).resolve()

        if not resolved_path.exists():
            error_msg = f"Path at {resolved_path!s} does not exist."
            raise FileNotFoundError(error_msg)

        if resolved_path.is_file():
            logger.info("File upload path determined to be: %s", resolved_path)
            all_files.append(resolved_path)
        elif resolved_path.is_dir():
            files = [f for f in resolved_path.iterdir() if f.is_file()]
            if not files:
                error_msg = f"Directory at {resolved_path!s} contains no files."
                raise ValueError(error_msg)
            logger.info("Directory upload path determined to be: %s (contains %d files)", resolved_path, len(files))
            for file in files:
                logger.info("  - %s", file.name)
            all_files.extend(files)
        else:
            error_msg = f"Path at {resolved_path!s} is neither a file nor a directory."
            raise ValueError(error_msg)

    return all_files


def construct_objects() -> tuple[list[Path], ForgeItem, ForgeURLs]:
    """Construct necessary objects from environment variables or user input."""
    file_names = os.environ.get("FG_UL_FILE") or input("Files/directories to include in build (relative or absolute; comma-separated or directory): ")
    new_files = resolve_file_paths(file_names, Path(PurePath(__file__).parents[1]))

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

            if get_bool_env("FG_UPLOAD_BUILD", default=True):
                channel = ForgeReleaseChannel[os.environ.get("FG_RELEASE_CHANNEL", "LIVE").upper()]
                item.upload_and_publish(headers, urls, new_files, channel)

            if get_bool_env("FG_README_UPDATE", default=False):
                readme_text = build_processing.get_readme(new_files, no_images=get_bool_env("FG_README_NO_IMAGES", default=False))
                item.update_description(page, context, urls, readme_text)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
