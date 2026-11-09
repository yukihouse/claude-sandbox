# claude-sandbox

Monorepo: every app lives under `apps/<name>/`. Python apps are standalone uv
projects (no root `pyproject.toml`, not a uv workspace): `apps/tetris/`
(Tetris game), `apps/antarctica-viz/` (Streamlit data viewer) and
`apps/version-checker/` (Windows exe version checker). `apps/hyogen-no-hoka/`
is a single HTML file. `unittest`, ruff (shared root `ruff.toml`, line length
100), 100% coverage required.

## Checks (run inside each Python app you touched and show the output)

- `apps/tetris/`: `uv run ruff check . && uv run ruff format --check . && uv run coverage run -m unittest discover -s tests && uv run coverage report -m`
- `apps/antarctica-viz/`, `apps/version-checker/`: `uv run ruff check . && uv run ruff format --check . && uv run coverage run -m unittest discover -s tests -t . && uv run coverage report -m`

Before a PR, run `/code-review`. Review rules: [`REVIEW.md`](REVIEW.md).
