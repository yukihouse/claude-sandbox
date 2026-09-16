import random

import pytest

from tetris import shapes
from tetris.board import Board
from tetris.game import ActivePiece, Game


def make_game(width=10, height=20, seed=0):
    return Game(width=width, height=height, rng=random.Random(seed))


def test_game_starts_with_a_current_and_next_piece():
    game = make_game()
    assert game.current is not None
    assert game.next_name in shapes.SHAPE_NAMES
    assert not game.game_over
    assert game.score == 0
    assert game.lines_cleared == 0
    assert game.level == 0


def test_spawn_piece_centers_the_piece_horizontally():
    game = make_game(width=10, height=20)
    game.next_name = "O"
    game.spawn_piece()
    size = shapes.box_size("O")
    assert game.current.col == (10 - size) // 2


def test_seven_bag_produces_each_shape_once_before_repeating():
    game = make_game(seed=7)
    seen = set()
    for _ in range(7):
        seen.add(game.next_name)
        game.next_name = game._draw_from_bag()
    assert seen == set(shapes.SHAPE_NAMES)


def test_move_left_and_right_within_open_board():
    game = make_game(width=10, height=20)
    game.board = Board(width=10, height=20)
    game.current = ActivePiece(name="O", rotation=0, row=5, col=5)
    assert game.move_left() is True
    assert game.current.col == 4
    assert game.move_right() is True
    assert game.current.col == 5


def test_move_left_blocked_by_wall():
    game = make_game(width=10, height=20)
    game.board = Board(width=10, height=20)
    game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
    assert game.move_left() is False
    assert game.current.col == 0


def test_moves_return_false_after_game_over():
    game = make_game()
    game.game_over = True
    assert game.move_left() is False
    assert game.move_right() is False
    assert game.rotate() is False
    assert game.hard_drop() == 0


def test_soft_drop_locks_piece_when_it_reaches_the_floor():
    game = make_game(width=4, height=3)
    game.board = Board(width=4, height=3)
    game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
    game.next_name = "O"
    assert game.soft_drop() is True  # moves from row 0 to row 1
    assert game.soft_drop() is False  # can't move further, locks and spawns
    assert game.board.grid[1][0] != 0
    assert game.board.grid[2][0] != 0
    assert game.current is not None  # a new piece spawned


def test_hard_drop_moves_piece_to_the_bottom_and_scores():
    game = make_game(width=4, height=6)
    game.board = Board(width=4, height=6)
    game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
    game.next_name = "O"
    distance = game.hard_drop()
    assert distance == 4  # falls from row 0 to row 4 (board height 6, piece height 2)
    assert game.score == 4
    assert game.board.grid[5][0] != 0
    assert game.board.grid[5][1] != 0


def test_line_clear_with_i_piece_completes_and_clears_bottom_row():
    game = make_game(width=4, height=4)
    game.board = Board(width=4, height=4)
    game.board.grid[3] = [9, 9, 9, 0]  # one cell short of a full bottom row
    # Vertical I piece (rotation 1) occupies local column 2; col=1 lines it
    # up with the empty cell in board column 3.
    game.current = ActivePiece(name="I", rotation=1, row=0, col=1)
    game.next_name = "O"
    game.hard_drop()
    assert game.lines_cleared == 1
    assert game.score >= 100
    # The completed filler row is gone and a fresh empty row was inserted at
    # the top; the I piece's remaining cells shifted down by one row.
    assert game.board.grid[0] == [0, 0, 0, 0]
    assert 9 not in [cell for row in game.board.grid for cell in row]


def test_level_increases_after_ten_lines():
    game = make_game()
    game.lines_cleared = 9
    game.board = Board(width=4, height=4)
    game.board.grid[3] = [9, 9, 9, 0]
    game.current = ActivePiece(name="I", rotation=1, row=0, col=1)
    game.next_name = "O"
    game.hard_drop()
    assert game.lines_cleared == 10
    assert game.level == 1


def test_game_over_when_spawn_position_is_blocked():
    game = make_game(width=4, height=4)
    for row in range(2):
        game.board.grid[row] = [9, 9, 9, 9]
    game.next_name = "O"
    game.spawn_piece()
    assert game.game_over is True


def test_rotate_succeeds_in_open_space():
    game = make_game(width=10, height=10)
    game.board = Board(width=10, height=10)
    game.current = ActivePiece(name="O", rotation=0, row=5, col=5)
    assert game.rotate() is True
    assert game.current.rotation == 1


def test_rotate_uses_a_wall_kick_when_the_default_position_collides():
    game = make_game(width=10, height=10)
    game.board = Board(width=10, height=10)
    piece = ActivePiece(name="I", rotation=0, row=0, col=0)
    game.current = piece
    target_cells = shapes.get_cells("I", 1)
    for r, c in target_cells:
        if game.board.in_bounds(r, c):
            game.board.grid[r][c] = 9
    assert game.rotate() is True
    assert game.current.rotation == 1
    assert game.current.col != 0


def test_rotate_returns_false_when_no_kick_position_fits():
    game = make_game(width=4, height=4)
    game.board = Board(width=4, height=4)
    for r in range(4):
        for c in range(4):
            game.board.grid[r][c] = 9
    piece = ActivePiece(name="T", rotation=0, row=0, col=0)
    for r, c in piece.cells():
        game.board.grid[r][c] = 0
    game.current = piece
    assert game.rotate() is False
    assert game.current.rotation == 0


def test_tick_advances_gravity_by_one_row():
    game = make_game(width=10, height=10)
    game.board = Board(width=10, height=10)
    game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
    game.tick()
    assert game.current.row == 1


def test_tick_does_nothing_after_game_over():
    game = make_game()
    game.game_over = True
    game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
    game.tick()
    assert game.current.row == 0


def test_active_piece_id_is_stable_per_shape():
    a = ActivePiece(name="T", rotation=0, row=0, col=0)
    b = ActivePiece(name="T", rotation=2, row=3, col=1)
    assert a.piece_id == b.piece_id
