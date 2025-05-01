import tempfile

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from matplotlib import font_manager, rcParams

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/lexend/Lexend%5Bwght%5D.ttf?raw=true"


with tempfile.NamedTemporaryFile(delete=False, suffix=".ttf") as tmp_font:
    tmp_font.write(requests.get(FONT_URL).content)
    font_manager.fontManager.addfont(tmp_font.name)
    rcParams["font.family"] = "Lexend"


def graph_users(sales: list[dict[str, str | int | None]]) -> None:
    sales_df = pd.DataFrame(sales)
    sales_df["created_at"] = pd.to_datetime(sales_df["created_at"])
    sales_df.set_index("created_at", inplace=True)

    sales_count = sales_df.resample("W").size().cumsum()
    sales_count = sales_count.loc[sales_count != 0]

    plt.style.use("https://raw.githubusercontent.com/h4pZ/rose-pine-matplotlib/main/themes/rose-pine-moon.mplstyle")

    plt.figure(figsize=(25, 7))
    sns.lineplot(data=pd.DataFrame(sales_count), linewidth=2.5, color="pink", legend=False)

    plt.title("Cumulative Users", fontsize=26, pad=20)
    plt.xlabel("Date", fontsize=20, labelpad=20)
    plt.ylabel("Number of Users", fontsize=20, labelpad=20)

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    sns.despine(left=True)

    plt.savefig("cumulative_users.png", dpi=300, bbox_inches="tight", transparent=True)
