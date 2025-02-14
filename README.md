# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/bmos/FG-Forge-Updater/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                        |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/\_\_init\_\_.py                                         |        0 |        0 |        0 |        0 |    100% |           |
| src/build\_processing.py                                    |       39 |        1 |       10 |        0 |     98% |        46 |
| src/dropzone.py                                             |       50 |        0 |        2 |        1 |     98% |  49->exit |
| src/forge\_api.py                                           |      137 |       58 |        4 |        0 |     57% |113-118, 122-129, 133-138, 142-153, 157-165, 170-180, 184-187, 191-194, 198-211, 216-220 |
| src/main.py                                                 |       43 |       13 |       10 |        1 |     62% | 48-60, 64 |
| src/users\_graph.py                                         |       28 |       15 |        0 |        0 |     46% |     20-41 |
| tests/\_\_init\_\_.py                                       |        0 |        0 |        0 |        0 |    100% |           |
| tests/dropzone/\_\_init\_\_.py                              |        0 |        0 |        0 |        0 |    100% |           |
| tests/dropzone/test\_add\_file\_to\_dropzone.py             |       41 |        1 |        4 |        1 |     96% |        33 |
| tests/dropzone/test\_dropzone\_error\_handling.py           |       56 |        3 |       10 |        3 |     91% |29, 52, 74 |
| tests/forge\_api/\_\_init\_\_.py                            |        0 |        0 |        0 |        0 |    100% |           |
| tests/forge\_api/forge\_item/\_\_init\_\_.py                |        0 |        0 |        0 |        0 |    100% |           |
| tests/forge\_api/forge\_item/test\_forge\_item\_creation.py |       14 |        0 |        0 |        0 |    100% |           |
| tests/forge\_api/forge\_item/test\_forge\_item\_login.py    |       62 |        0 |        4 |        0 |    100% |           |
| tests/forge\_api/test\_forge\_credentials.py                |       14 |        0 |        0 |        0 |    100% |           |
| tests/forge\_api/test\_forge\_release\_channels.py          |        5 |        0 |        0 |        0 |    100% |           |
| tests/forge\_api/test\_forge\_urls.py                       |        9 |        0 |        0 |        0 |    100% |           |
| tests/main/\_\_init\_\_.py                                  |        0 |        0 |        0 |        0 |    100% |           |
| tests/main/test\_build\_text.py                             |        8 |        0 |        0 |        0 |    100% |           |
| tests/main/test\_configure\_headless\_chrome.py             |       12 |        0 |        0 |        0 |    100% |           |
| tests/main/test\_construct\_objects.py                      |       14 |        0 |        0 |        0 |    100% |           |
| tests/main/test\_get\_build\_file.py                        |       11 |        0 |        0 |        0 |    100% |           |
|                                                   **TOTAL** |  **543** |   **91** |   **44** |    **6** | **82%** |           |


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