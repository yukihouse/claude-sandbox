# Review guide

Read by the automated reviewer (`.github/workflows/claude-review.yml`), by
`/code-review`, and by humans. Keep it short; when the same comment keeps coming
up in reviews, add it here (or turn it into a lint rule) instead.

## What failure looks like here

- **Game logic** (`src/tetris/board.py`, `game.py`, `shapes.py`): wrong collision,
  rotation, line-clear or scoring behavior; state that the UI and logic disagree on.
- **antarctica-viz parsers/sources**: data silently mis-parsed (wrong units, dates,
  missing-value markers) so the chart lies instead of failing.
- **Build scripts / workflows** (`scripts/`, `.github/workflows/`): a build that
  passes without actually checking the binary, wrong version embedded, or a
  workflow that runs on the wrong paths / with more permissions than it needs.
- **Docs**: README commands that no longer work.
- **Tests**: tests that pass without asserting the behavior, or coverage kept at
  100% by `pragma: no cover` instead of a test.

## How to report

- Every finding needs evidence: `file:line` and a concrete input/state that
  produces the wrong result. No guesses from a name.
- Tag each comment **Important** (bug, security, data correctness, broken
  build), **Nit** (optional polish), or **Pre-existing** (a real bug this PR did
  not introduce).
- At most **3 Nits** per review. Do not comment on pure style that ruff already
  enforces.
- Flag the class of bug: if the same mistake appears in several places, list all
  of them in one comment.
- On a bug fix, check that it fixes the root cause, not just the symptom.
- Start the summary with a count, e.g. `2 Important, 1 Nit`. If there is nothing
  to fix, say `No issues found.` plainly.

## Skip

- `uv.lock`, `*/uv.lock` (review the `pyproject.toml` change instead)
- `antarctica-viz/tests/fixtures/**`
- Dependabot version-bump PRs unless CI is red.

## Re-review rounds

- Do not repeat a finding that is already posted on the PR.
- After the first review, review only the commits pushed since your last review.
- If this is the 3rd round or later and Important findings remain, ask the
  author to step back and reconsider the approach instead of adding more comments.

## Risk tiers (for human approval)

| Tier | Examples | Human approvals |
|---|---|---|
| Low | docs, tests only, refactors inside one module with tests green | 0 (author may merge once CI and review are green) |
| Medium | behavior changes in game / parsers / CLIs | 1 |
| High | `.github/workflows/`, `scripts/` (build & release), `pyproject.toml` dependency or build-system changes | 1, from a CODEOWNER |

The tier comes from what the change touches, not from who wrote it. A bot
approval never counts as a human one.
