# Review guide

## What failure looks like here

- Game logic gives wrong collision, rotation, line clear or score.
- antarctica-viz parsers mis-read data (units, dates, missing values) and the chart lies.
- hyogen-no-hoka game rules or AI break (wrong combat, resources, win/lose), a change to the
  saved format silently resets players' progress (`src/save.ts`), or the PWA service worker serves a stale or broken build offline.
- penguin-zoku season rules break (food, breeding, events, win/lose), or a save that no longer
  matches `isGameState` in `src/save.ts` silently drops a game in progress.
- version-checker mis-parses a PE file (wrong offsets, truncated or malformed input) and
  reports version info as present when it is not, or crashes; the Windows build relies on it.
- Build scripts or workflows pass without really checking anything.
- Tests pass without asserting behavior; README commands no longer work.

## Rules

- Give `file:line` and a concrete failing input as evidence, not a guess from a name.
- Tag each comment Important, Nit or Pre-existing. At most 3 Nits. Skip style ruff enforces.
- Do not repeat findings already posted; after the first round, review only new commits.
- Start the summary with a count (e.g. `1 Important, 2 Nit`), or say `No issues found.`

## Skip

`apps/*/uv.lock`, `apps/antarctica-viz/tests/fixtures/`
