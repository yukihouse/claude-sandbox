# claude-sandbox

A terminal Tetris game, used as a small demo project for visualizing Python
unit test coverage on pull requests.

![Coverage badge](https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data/badge.svg)

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --dev
uv run coverage run -m unittest discover -s tests
uv run coverage report -m
uv run tetris   # play the game in a terminal
```

## Playing in the browser (Streamlit)

A Streamlit UI is available alongside the terminal version, sharing the same
game logic in `board.py` / `game.py`:

```bash
uv sync --extra streamlit
uv run streamlit run src/tetris/streamlit_app.py
```

Controls are on-screen buttons (move left/right, rotate, soft drop, hard
drop), plus an optional auto-drop toggle and speed slider in the sidebar.

## Building a standalone executable

Requires [uv](https://docs.astral.sh/uv/). Run the script matching your OS to
produce a single-file binary that doesn't need Python installed:

```bash
scripts/build_macos.sh          # on macOS -> dist/macos/tetris
scripts/build_linux.sh          # on Linux -> dist/linux/tetris
pwsh scripts/build_windows.ps1  # on Windows -> dist/windows/tetris.exe
```

Each also writes a distributable
`dist/<os>/tetris-<version>-<os>-<arch>.zip`.

Every build script verifies the binary it just produced before packaging
it, failing the build if the check doesn't pass:

- **Windows**: embeds version information (via
  [`scripts/version_info.txt`](scripts/version_info.txt)) into `tetris.exe`
  and confirms it with [`version-checker`](version-checker/) — a
  Windows-only PE resource, so this check only applies there. The
  [`windows-build.yml`](.github/workflows/windows-build.yml) workflow runs
  this same build and check on every push/PR that touches the game, the
  build scripts, or version-checker.
- **All platforms**: `tetris --version` is checked to print the expected
  `tetris <version>`, since macOS (Mach-O) and Linux (ELF) binaries have no
  OS-level "version resource" equivalent to Windows' — a runtime
  `--version` flag is the portable convention instead.

## Coverage on pull requests

The [`coverage.yml`](.github/workflows/coverage.yml) workflow runs the test
suite with coverage on every push and pull request, then uses
[py-cov-action/python-coverage-comment-action](https://github.com/py-cov-action/python-coverage-comment-action)
to post (and update) a coverage summary comment on the pull request, along
with a diff-coverage report and the badge shown above.
