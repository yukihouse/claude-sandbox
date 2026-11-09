# Review guide

## What failure looks like here

- Game logic gives wrong collision, rotation, line clear or score.
- antarctica-viz parsers mis-read data (units, dates, missing values) and the chart lies.
- Build scripts or workflows pass without really checking anything.
- Tests pass without asserting behavior; README commands no longer work.

## Rules

- Give `file:line` and a concrete failing input as evidence, not a guess from a name.
- Tag each comment Important, Nit or Pre-existing. At most 3 Nits. Skip style ruff enforces.
- Do not repeat findings already posted; after the first round, review only new commits.
- Start the summary with a count (e.g. `1 Important, 2 Nit`), or say `No issues found.`

## Skip

`uv.lock`, `*/uv.lock`, `antarctica-viz/tests/fixtures/`
