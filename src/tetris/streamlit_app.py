"""A Streamlit web UI for the Tetris game.

This module is interactive and excluded from coverage measurement, same as
cli.py; the game logic it drives lives in board.py and game.py, which are
fully unit tested.

Run with:
    uv run streamlit run src/tetris/streamlit_app.py
"""

from __future__ import annotations

import time

import streamlit as st

from tetris import shapes
from tetris.game import PIECE_IDS, Game

_COLORS = {
    "I": "#00f0f0",
    "O": "#f0f000",
    "T": "#a000f0",
    "S": "#00f000",
    "Z": "#f00000",
    "J": "#0000f0",
    "L": "#f0a000",
}
_ID_TO_COLOR = {PIECE_IDS[name]: color for name, color in _COLORS.items()}
_CELL_PX = 24


def _new_game() -> Game:
    return Game()


def _init_state() -> None:
    if "game" not in st.session_state:
        st.session_state.game = _new_game()
    if "auto_drop" not in st.session_state:
        st.session_state.auto_drop = False
    if "speed" not in st.session_state:
        st.session_state.speed = 0.8


def _grid_with_current(game: Game) -> list[list[int]]:
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
    grid = _grid_with_current(game)
    rows_html = []
    for row in grid:
        cells_html = [
            _cell_div(
                _ID_TO_COLOR.get(value, "#111318"),
                _CELL_PX,
                "1px solid #333" if value == 0 else "1px solid rgba(0,0,0,0.35)",
            )
            for value in row
        ]
        rows_html.append(f'<div style="display:flex;">{"".join(cells_html)}</div>')
    width = game.board.width * _CELL_PX
    return (
        f'<div style="display:inline-block;border:3px solid #444;background:#111318;'
        f'width:{width}px;">{"".join(rows_html)}</div>'
    )


def render_next_piece_html(next_name: str) -> str:
    size = shapes.box_size(next_name)
    cells = set(shapes.get_cells(next_name, 0))
    color = _COLORS[next_name]
    cell = 20
    rows_html = []
    for r in range(size):
        cells_html = [
            _cell_div(color if (r, c) in cells else "#111318", cell, "1px solid #222")
            for c in range(size)
        ]
        rows_html.append(f'<div style="display:flex;">{"".join(cells_html)}</div>')
    width = size * cell
    return f'<div style="display:inline-block;background:#111318;width:{width}px;">{"".join(rows_html)}</div>'


def main() -> None:  # pragma: no cover - exercised manually, not in CI
    st.set_page_config(page_title="Tetris", page_icon="\U0001f9f1", layout="centered")
    _init_state()
    game: Game = st.session_state.game

    st.title("\U0001f9f1 Tetris (Streamlit)")

    with st.sidebar:
        st.header("設定")
        if st.button("\U0001f504 新しいゲーム", use_container_width=True):
            st.session_state.game = _new_game()
            game = st.session_state.game
        st.session_state.auto_drop = st.checkbox("自動落下", value=st.session_state.auto_drop)
        st.session_state.speed = st.slider(
            "落下間隔（秒）", min_value=0.2, max_value=2.0, value=st.session_state.speed, step=0.1
        )
        st.markdown("### 次のピース")
        st.markdown(render_next_piece_html(game.next_name), unsafe_allow_html=True)

    col_board, col_info = st.columns([2, 1])

    with col_info:
        st.metric("スコア", game.score)
        st.metric("ライン", game.lines_cleared)
        st.metric("レベル", game.level)
        if game.game_over:
            st.error("ゲームオーバー")

    with col_board:
        st.markdown(render_board_html(game), unsafe_allow_html=True)

    st.write("")
    disabled = game.game_over
    b_left, b_rotate, b_right, b_soft, b_hard = st.columns(5)
    if b_left.button("⬅️", use_container_width=True, disabled=disabled):
        game.move_left()
    if b_rotate.button("⟳", use_container_width=True, disabled=disabled):
        game.rotate()
    if b_right.button("➡️", use_container_width=True, disabled=disabled):
        game.move_right()
    if b_soft.button("⬇️", use_container_width=True, disabled=disabled):
        game.soft_drop()
    if b_hard.button("⏬", use_container_width=True, disabled=disabled):
        game.hard_drop()

    if st.session_state.auto_drop and not game.game_over:
        time.sleep(st.session_state.speed)
        game.tick()
        st.rerun()


if __name__ == "__main__":  # pragma: no cover
    main()
