[![CodeQL](https://github.com/bmos/FG-Forge-Updater/actions/workflows/github-code-scanning/codeql/badge.svg?branch=main)](https://github.com/bmos/FG-Forge-Updater/actions/workflows/github-code-scanning/codeql)
[![Python checks](https://github.com/bmos/FG-Forge-Updater/actions/workflows/python.yml/badge.svg?branch=main)](https://github.com/bmos/FG-Forge-Updater/actions/workflows/python.yml)
[![Coverage badge](https://raw.githubusercontent.com/bmos/FG-Forge-Updater/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10361/badge)](https://www.bestpractices.dev/projects/10361)

# Forge 

Uploads new builds to FantasyGrounds Forge and updates item page descriptions without requiring user input.

> [!WARNING]
> Markdown parsing is not quite as permissive as GitHub.
> If you use tables, you must have an empty line directly before them.

> [!WARNING]
> FG Forge does not allow inline images.
> To work around this, images are replaced by links using the image's alt text.
> To ensure this can work, be sure to configure alt text on your README images and reference them via URL (not relative file paths).

## Usage (GitHub Action)

<!-- start usage -->
```yaml
    - uses: bmos/FG-Forge-Updater@v2
      with:
        # The item id of the forge listing you want to publish to.
        # Required.
        item-id: 34

        # The FantasyGrounds username to use when logging in.
        # Required.
        username: 'bmos'

        # The FantasyGrounds password to use when logging in.
        # Required.
        password: 'TopSecretP@ssword'

        # The path to the build file (ending in .ext or .mod).
        # Required.
        file-path: 'FG-Aura-Effect.ext'

        # The release channel you want to publish to ('Live' or 'Test').
        # Optional, defaults to 'Live'.
        release-channel: 'Live'

        # Whether to update the Forge item description from the contents of your README.md file.
        # Optional, defaults to 'TRUE'.
        update-readme: 'TRUE'
```
<!-- end usage -->

## Usage (manual)

### Getting Started

To run this code, you'll need to have Python 3.11+ installed on your machine.
These instructions also assume you have `uv` installed in your environment.
You can install `uv`  like this:

```shell
python -m pip install -U pip uv
```

### Publishing a Build

1. Put the ext file to upload into the project folder.

2. [OPTIONAL] Create a `.env` file in the project folder containing the following (but with your information):

> [!NOTE]
> You can add these values directly to your environment variables.
> If no environment variables are set and no .env file is found, command line will prompt for Forge login credentials and item ID.
> Build will be uploaded and added to LIVE. Description will not be updated.

```env
# your FG forum username
FG_USER_NAME=**********

# your FG forum password
FG_USER_PASS=**********

# the item ID of the FG Forge item you want to modify
FG_ITEM_ID=33

# the file(s) you want to upload
# supported file types: ext, pak, mod
# can be relative to project folder or absolute paths
# if uploading multiple files to a single build, use a comma-separated list or path to directory
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
uv run src/main.py
```
