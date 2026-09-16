# exe-checker

A small CLI tool that checks whether a Windows `.exe` (PE) file has
version information embedded in it (the `VS_VERSION_INFO` resource that
tools like `resourcehacker` or Windows Explorer's "Details" tab read),
without any external dependencies.

- Prints `ok` and exits with status `0` if version info is embedded.
- Prints `ng` and exits with status `1` if it is not.
- Prints an error to stderr and exits with status `2` if the file cannot
  be read or is not a valid PE file.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --dev
uv run pytest --cov=exe_checker --cov-report=term-missing
uv run exe-checker path/to/app.exe
```
