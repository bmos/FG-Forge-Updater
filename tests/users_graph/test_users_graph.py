import os
from pathlib import Path

import requestium
from dotenv import load_dotenv
from selenium import webdriver

from src.forge_api import ForgeCredentials, ForgeItem, ForgeURLs
from src.main import configure_headless_chrome
from src.users_graph import graph_users


def test_create_graph() -> None:
    """Ensure an image file is created."""
    load_dotenv(Path(__file__).parents[2] / ".env")
    user_name = os.environ.get("FG_USER_NAME") or ""
    user_pass = os.environ.get("FG_USER_PASS") or ""
    creds = ForgeCredentials(user_name, user_pass)
    item_id = os.environ.get("FG_ITEM_ID") or ""
    item = ForgeItem(creds, item_id, 7)
    urls = ForgeURLs()

    with requestium.Session(driver=webdriver.Chrome(options=configure_headless_chrome())) as s:
        item.login(s, urls)
        sales = item.get_sales(s, urls)

    graph_users(sales)
    assert Path("cumulative_users.png").is_file()
