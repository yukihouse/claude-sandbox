# claude-sandbox

Python repo with three uv projects: Tetris game (`src/tetris/`, root),
`antarctica-viz/` (Streamlit data viewer) and `version-checker/` (Windows exe
version checker). `unittest`, ruff (line length 100), 100% coverage required.

## Checks (run in each project you touched and show the output)

- Root: `uv run ruff check . && uv run ruff format --check . && uv run coverage run -m unittest discover -s tests && uv run coverage report -m`
- `antarctica-viz/`, `version-checker/`: `uv run coverage run -m unittest discover -s tests -t . && uv run coverage report -m`

Before a PR, run `/code-review`. Review rules: [`REVIEW.md`](REVIEW.md).
