# claude-sandbox

A terminal Tetris game, used as a small demo project for visualizing Python
unit test coverage on pull requests.

![Coverage badge](https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data/badge.svg)

This repository also hosts [`antarctica-viz/`](antarctica-viz/), a Streamlit
web UI for exploring public Antarctic observation data (sea-ice extent, South
Pole CO₂, research-station temperatures).

[`hyogen-no-hoka/`](hyogen-no-hoka/) is 氷原の烽火, a single-file browser
real-time strategy game set in Antarctica: send crew from station to station
to retake bases, with a five-chapter story. Open `hyogen-no-hoka/index.html`
in a browser to play.

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

## Code review

Based on [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/):
[`CLAUDE.md`](CLAUDE.md) (checks), [`REVIEW.md`](REVIEW.md) (review rules), a ruff hook in `.claude/settings.json`, and
[`claude-review.yml`](.github/workflows/claude-review.yml), which reviews PRs
using a Claude subscription token (`claude setup-token` → repository secret
`CLAUDE_CODE_OAUTH_TOKEN`; skipped when unset).
