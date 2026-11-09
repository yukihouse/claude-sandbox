# claude-sandbox

Small Python demo repo: a terminal/Streamlit Tetris game (`src/tetris/`), plus two
independent uv projects — `antarctica-viz/` (Streamlit viewer for Antarctic data)
and `version-checker/` (Windows PE version-resource checker).

Goal: keep the code small, readable and fully covered. Non-goals: new runtime
dependencies for the game, platform-specific code outside `scripts/` and
`version-checker/`.

## Checks to run before saying "done"

Show the output; do not just claim it passed. Run them in each project you touched.

| Project | Directory | Commands |
|---|---|---|
| tetris | `.` | `uv run ruff check . && uv run ruff format --check . && uv run coverage run -m unittest discover -s tests && uv run coverage report -m` |
| antarctica-viz | `antarctica-viz/` | `uv run coverage run -m unittest discover -s tests -t . && uv run coverage report -m` |
| version-checker | `version-checker/` | `uv run coverage run -m unittest discover -s tests -t . && uv run coverage report -m` |

## Conventions

- Python ≥ 3.11, `unittest` (not pytest), ruff with line length 100.
- Coverage is `fail_under = 100` for tetris and version-checker: new code needs tests.
- Keep game logic in `board.py` / `game.py`; UIs (`cli.py`, `streamlit_*.py`) only render.
- Each sub-project has its own `pyproject.toml` and `uv.lock`; update the lock with `uv lock`.
- Update `README.md` when commands, build steps or workflows change.

## Before opening a PR

1. Run the checks above.
2. Run `/code-review` and `/security-review` (or a fresh-context subagent review of the diff).
3. Fill in every section of `.github/pull_request_template.md`.

Review rules live in [`REVIEW.md`](REVIEW.md).
