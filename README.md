# claude-sandbox

A Tetris game, used as a small demo project for visualizing Python unit test
coverage on pull requests.

![Coverage badge](https://raw.githubusercontent.com/yukihouse/claude-sandbox/python-coverage-comment-action-data/badge.svg)

This repository also hosts [`antarctica-viz/`](antarctica-viz/), a Streamlit
web UI for exploring public Antarctic observation data (sea-ice extent, South
Pole CO₂, research-station temperatures).

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --dev
uv run coverage run -m unittest discover -s tests
uv run coverage report -m
```

## Playing in the browser (Streamlit)

```bash
uv sync --extra streamlit
uv run streamlit run src/tetris/streamlit_app.py
```

Controls are on-screen buttons (move left/right, rotate, soft drop, hard
drop), plus an optional auto-drop toggle and speed slider in the sidebar.

## Coverage on pull requests

The [`coverage.yml`](.github/workflows/coverage.yml) workflow runs the test
suite with coverage on every push and pull request, then uses
[py-cov-action/python-coverage-comment-action](https://github.com/py-cov-action/python-coverage-comment-action)
to post (and update) a coverage summary comment on the pull request, along
with a diff-coverage report and the badge shown above.
