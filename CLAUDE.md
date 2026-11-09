# claude-sandbox

Monorepo: every app lives under `apps/<name>/`. Python apps are standalone uv
projects (no root `pyproject.toml`, not a uv workspace): `apps/tetris/`
(Tetris game), `apps/antarctica-viz/` (Streamlit data viewer) and
`apps/version-checker/` (Windows exe version checker). Python: `unittest`,
ruff (shared root `ruff.toml`, line length 100), 100% coverage required.
`apps/hyogen-no-hoka/` is a TypeScript + Vite browser game (npm, Vitest;
100% coverage of game logic, data, save, view math and PWA helpers;
GitHub Pages deploy from main).

## Checks (run inside each app you touched and show the output)

- `apps/tetris/`: `uv run ruff check . && uv run ruff format --check . && uv run coverage run -m unittest discover -s tests && uv run coverage report -m`
- `apps/antarctica-viz/`, `apps/version-checker/`: `uv run ruff check . && uv run ruff format --check . && uv run coverage run -m unittest discover -s tests -t . && uv run coverage report -m`
- `apps/hyogen-no-hoka/`: `npm ci && npm run typecheck && npm run coverage && npm run build`

Before a PR, run `/code-review`. Review rules: [`REVIEW.md`](REVIEW.md).
