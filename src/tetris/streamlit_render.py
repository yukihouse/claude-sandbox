"""Pure HTML-rendering helpers for the Streamlit UI.

Kept separate from streamlit_app.py (and free of any Streamlit import) so
this logic can be unit tested without the streamlit package installed,
mirroring how board.py/game.py are tested independently of cli.py.
"""

from __future__ import annotations

from . import shapes
from .game import PIECE_IDS, Game

COLORS = {
    "I": "#00f0f0",
    "O": "#f0f000",
    "T": "#a000f0",
    "S": "#00f000",
    "Z": "#f00000",
    "J": "#0000f0",
    "L": "#f0a000",
}
_ID_TO_COLOR = {PIECE_IDS[name]: color for name, color in COLORS.items()}
_CELL_PX = 24
_BACKGROUND = "#111318"


def grid_with_current(game: Game) -> list[list[int]]:
    """Return the locked board grid with the falling piece overlaid."""
    grid = [row[:] for row in game.board.grid]
    if game.current is not None and not game.game_over:
        for r, c in game.current.cells():
            row, col = r + game.current.row, c + game.current.col
            if game.board.in_bounds(row, col):
                grid[row][col] = game.current.piece_id
    return grid


def _cell_div(color: str, size: int, border: str) -> str:
    return (
        f'<div style="width:{size}px;height:{size}px;background:{color};'
        f'box-sizing:border-box;border:{border};"></div>'
    )


def render_board_html(game: Game) -> str:
    grid = grid_with_current(game)
    rows_html = []
    for row in grid:
        cells_html = [
            _cell_div(
                _ID_TO_COLOR.get(value, _BACKGROUND),
                _CELL_PX,
                "1px solid #333" if value == 0 else "1px solid rgba(0,0,0,0.35)",
            )
            for value in row
        ]
        rows_html.append(f'<div style="display:flex;">{"".join(cells_html)}</div>')
    width = game.board.width * _CELL_PX
    return (
        f'<div style="display:inline-block;border:3px solid #444;background:{_BACKGROUND};'
        f'width:{width}px;">{"".join(rows_html)}</div>'
    )


def render_next_piece_html(next_name: str) -> str:
    size = shapes.box_size(next_name)
    cells = set(shapes.get_cells(next_name, 0))
    color = COLORS[next_name]
    cell = 20
    rows_html = []
    for r in range(size):
        cells_html = [
            _cell_div(color if (r, c) in cells else _BACKGROUND, cell, "1px solid #222")
            for c in range(size)
        ]
        rows_html.append(f'<div style="display:flex;">{"".join(cells_html)}</div>')
    width = size * cell
    return f'<div style="display:inline-block;background:{_BACKGROUND};width:{width}px;">{"".join(rows_html)}</div>'
