# version-checker

A small CLI tool that checks whether a Windows `.exe` (PE) file has
version information embedded in it (the `VS_VERSION_INFO` resource that
tools like `resourcehacker` or Windows Explorer's "Details" tab read),
without any external dependencies.

![Coverage badge](https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data-version-checker/badge.svg)

- Prints `ok` and exits with status `0` if version info is embedded.
- Prints `ng` and exits with status `1` if it is not.
- Prints an error to stderr and exits with status `2` if the file cannot
  be read or is not a valid PE file.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --dev
uv run pytest --cov=version_checker --cov-report=term-missing
uv run version-checker path/to/app.exe
```

## Coverage on pull requests

The [`version-checker-coverage.yml`](../.github/workflows/version-checker-coverage.yml)
workflow runs this project's test suite with coverage whenever a pull
request or push to `main` touches `version-checker/`, and posts (and updates)
its own coverage summary comment on the pull request, separate from the
root Tetris project's coverage comment, using
[py-cov-action/python-coverage-comment-action](https://github.com/py-cov-action/python-coverage-comment-action)'s
`SUBPROJECT_ID` support.
