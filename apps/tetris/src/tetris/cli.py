"""A minimal terminal renderer for manually playing the game.

This module is interactive and excluded from coverage measurement;
the game logic it drives lives in board.py and game.py, which are
fully unit tested.
"""

from __future__ import annotations

import os
import sys
import time

from .game import Game

_SYMBOLS = " IOTSZJL"


def render(game: Game) -> str:
    lines = [f"score: {game.score}  lines: {game.lines_cleared}  level: {game.level}"]
    grid = [row[:] for row in game.board.grid]
    if game.current is not None and not game.game_over:
        for r, c in game.current.cells():
            row, col = r + game.current.row, c + game.current.col
            if game.board.in_bounds(row, col):
                grid[row][col] = game.current.piece_id
    for row in grid:
        lines.append("|" + "".join(_SYMBOLS[cell] if cell else "." for cell in row) + "|")
    lines.append("+" + "-" * game.board.width + "+")
    return "\n".join(lines)


def run() -> None:  # pragma: no cover - exercised manually, not in CI
    game = Game()
    try:
        while not game.game_over:
            os.system("cls" if os.name == "nt" else "clear")
            print(render(game))
            game.tick()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        print(render(game))
        print("Game over!" if game.game_over else "Bye!")
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    run()
