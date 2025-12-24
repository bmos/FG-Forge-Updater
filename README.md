# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                     |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/\_\_init\_\_.py      |        0 |        0 |        0 |        0 |    100% |           |
| src/build\_processing.py |       39 |        0 |       10 |        0 |    100% |           |
| src/dropzone.py          |       47 |        0 |        2 |        1 |     98% |  45->exit |
| src/forge\_api.py        |      136 |       63 |        4 |        0 |     54% |30-31, 80, 113, 119-125, 129-136, 140-145, 149-160, 164-172, 177-190, 194-197, 201-204, 208-221, 226-230 |
| src/main.py              |       29 |        0 |        2 |        0 |    100% |           |
| src/users\_graph.py      |       27 |       15 |        0 |        0 |     44% |     19-40 |
| **TOTAL**                |  **278** |   **78** |   **18** |    **1** | **73%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/bmos/FG-Forge-Updater/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/bmos/FG-Forge-Updater/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fbmos%2FFG-Forge-Updater%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.