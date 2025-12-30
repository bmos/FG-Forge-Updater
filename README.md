[![CodeQL](https://github.com/bmos/FG-Forge-Updater/actions/workflows/github-code-scanning/codeql/badge.svg?branch=main)](https://github.com/bmos/FG-Forge-Updater/actions/workflows/github-code-scanning/codeql)
[![Python checks](https://github.com/bmos/FG-Forge-Updater/actions/workflows/python.yml/badge.svg?branch=main)](https://github.com/bmos/FG-Forge-Updater/actions/workflows/python.yml)
[![Coverage badge](https://raw.githubusercontent.com/bmos/FG-Forge-Updater/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10361/badge)](https://www.bestpractices.dev/projects/10361)

# Forge Updater

Uploads new builds to FantasyGrounds Forge and updates item page descriptions without requiring user input.
It is intended for use in CI release workflows such as one I
use [here](https://github.com/FG-Unofficial-Developers-Guild/FG-CoreRPG-Extraplanar-Containers/blob/main/.github/workflows/release.yml).

> [!WARNING]
> At the moment, this will only work for the first page of 100 items found on a Forge account.

> [!WARNING]
> Markdown parsing is not quite as permissive as GitHub. If you use tables, you must have an empty line directly before
> them.

> [!WARNING]
> FG Forge does not allow inline images. To work around this, images are replaced by links using the image's alt text.
> To ensure this can work, be sure to configure alt text on your README images and reference them via URL (not relative
> file paths).

## Getting Started / Before Using

To run this code, you'll need to have Python 3.11, 3.12, or 3.13 installed on your machine. You'll also need to
install the required packages by running the following commands from inside the project folder:

```shell
pip install -U pip uv
```

```shell
uv venv
```

```shell
source .venv/bin/activate # Linux or macOS
.venv\Scripts\activate # Windows
```

```shell
uv pip install .
```

## Usage

1. Put the ext file to upload into the project folder.

2. [OPTIONAL] Create a `.env` file in the project folder containing the following (but with your information):

    > [!NOTE]
    > You can add these values directly to your environment variables.

    ```env
    # your FG forum username
    FG_USER_NAME=**********
    # your FG forum password
    FG_USER_PASS=**********
    # the item ID of the FG Forge item you want to modify
    FG_ITEM_ID=33
    # the name(s) of the (supported -- ext, pak, mod, etc) file(s) you want to upload (can be comma-separated list)
    FG_UL_FILE=path/to/file.ext

    # [OPTIONAL] set this to FALSE to skip build uploading
    FG_UPLOAD_BUILD=TRUE
    # [OPTIONAL] set this to "TEST" or "NONE" if you would rather target those channels
    FG_RELEASE_CHANNEL=LIVE

    # [OPTIONAL] set this to TRUE to prevent replacing the description with the contents of README.md
    FG_README_UPDATE=FALSE
    # [OPTIONAL] set this to TRUE to remove images instead of creating links
    FG_README_NO_IMAGES=FALSE
    ```

3. Run the following command from inside the project folder:

```shell
fg-forge-uploader
```
