# Repository Coverage (version-checker)

[Full report](https://htmlpreview.github.io/?https://github.com/yukihouse/claude-sandbox/blob/python-coverage-comment-action-data-version-checker/htmlcov/index.html)

| Name                                 |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/version\_checker/\_\_init\_\_.py |        3 |        0 |        0 |        0 |    100% |           |
| src/version\_checker/cli.py          |       26 |        0 |        2 |        0 |    100% |           |
| src/version\_checker/pe.py           |       99 |       14 |       50 |       16 |     79% |46-\>39, 48, 53-\>46, 55, 57-\>53, 69, 72, 93, 100, 105-108, 112, 131, 142-\>140, 144, 150, 158 |
| **TOTAL**                            |  **128** |   **14** |   **52** |   **16** | **82%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data-version-checker/badge.svg)](https://htmlpreview.github.io/?https://github.com/yukihouse/claude-sandbox/blob/python-coverage-comment-action-data-version-checker/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data-version-checker/endpoint.json)](https://htmlpreview.github.io/?https://github.com/yukihouse/claude-sandbox/blob/python-coverage-comment-action-data-version-checker/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fyukihouse%2Fclaude-sandbox%2Fpython-coverage-comment-action-data-version-checker%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/yukihouse/claude-sandbox/blob/python-coverage-comment-action-data-version-checker/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.