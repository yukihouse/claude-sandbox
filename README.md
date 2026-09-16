# claude-sandbox

A terminal Tetris game, used as a small demo project for visualizing Python
unit test coverage on pull requests.

![Coverage badge](https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data/badge.svg)

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --dev
uv run pytest --cov=tetris --cov-report=term-missing
uv run tetris   # play the game in a terminal
```

## Building a standalone executable

Requires [uv](https://docs.astral.sh/uv/). Run the script matching your OS to
produce a single-file binary that doesn't need Python installed:

```bash
scripts/build_macos.sh   # on macOS -> dist/macos/tetris
scripts/build_linux.sh   # on Linux -> dist/linux/tetris
```

Each also writes a distributable
`dist/<os>/tetris-<version>-<os>-<arch>.zip`.

## Coverage on pull requests

The [`coverage.yml`](.github/workflows/coverage.yml) workflow runs the test
suite with coverage on every push and pull request, then uses
[py-cov-action/python-coverage-comment-action](https://github.com/py-cov-action/python-coverage-comment-action)
to post (and update) a coverage summary comment on the pull request, along
with a diff-coverage report and the badge shown above.
