"""A Streamlit web UI for the Tetris game.

This module is interactive and excluded from coverage measurement, same as
cli.py; the game logic it drives lives in board.py and game.py (fully unit
tested), and the HTML rendering it uses lives in streamlit_render.py (also
unit tested, since it has no dependency on streamlit itself).

Run with:
    uv run streamlit run src/tetris/streamlit_app.py
"""

from __future__ import annotations

import time

import streamlit as st

from tetris.game import Game
from tetris.streamlit_render import render_board_html, render_next_piece_html


def _new_game() -> Game:
    return Game()


def _init_state() -> None:
    if "game" not in st.session_state:
        st.session_state.game = _new_game()
    if "auto_drop" not in st.session_state:
        st.session_state.auto_drop = False
    if "speed" not in st.session_state:
        st.session_state.speed = 0.8


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
