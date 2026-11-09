# claude-sandbox

A monorepo of small demo apps. Each app lives in its own directory under
[`apps/`](apps/) and is an independent project with its own README, tests and
(for Python apps) its own `pyproject.toml` and `uv.lock`.

| App | What it is |
|---|---|
| [`apps/tetris/`](apps/tetris/) | Terminal (and Streamlit) Tetris game, used to demo PR test-coverage visualization |
| [`apps/antarctica-viz/`](apps/antarctica-viz/) | Streamlit web UI for exploring public Antarctic observation data |
| [`apps/version-checker/`](apps/version-checker/) | CLI that checks a Windows `.exe` has version information embedded |
| [`apps/hyogen-no-hoka/`](apps/hyogen-no-hoka/) | 氷原の烽火, a single-file browser real-time strategy game set in Antarctica |

## Layout conventions

- New apps go directly under `apps/<name>/`, grouped by app rather than by language.
- Python apps are standalone [uv](https://docs.astral.sh/uv/) projects (not a uv
  workspace), so each one resolves and locks its own dependencies. Run `uv`
  commands from inside the app's directory.
- Ruff settings are shared through the root [`ruff.toml`](ruff.toml); each
  app's `pyproject.toml` pulls them in with `extend = "../../ruff.toml"`.
- CI workflows in [`.github/workflows/`](.github/workflows/) are per app and
  filtered by path, except [`lint.yml`](.github/workflows/lint.yml), which
  runs ruff in every Python app.

## Code review

Based on [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/):
[`CLAUDE.md`](CLAUDE.md) (checks), [`REVIEW.md`](REVIEW.md) (review rules), a ruff hook in `.claude/settings.json`, and
[`claude-review.yml`](.github/workflows/claude-review.yml), which reviews PRs
using a Claude subscription token (`claude setup-token` → repository secret
`CLAUDE_CODE_OAUTH_TOKEN`; skipped when unset).
