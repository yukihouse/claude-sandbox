import pytest

from tetris.board import Board


def test_new_board_is_empty():
    board = Board(width=10, height=20)
    assert all(cell == 0 for row in board.grid for cell in row)


@pytest.mark.parametrize("width,height", [(0, 10), (10, 0), (-1, 5)])
def test_invalid_dimensions_raise(width, height):
    with pytest.raises(ValueError):
        Board(width=width, height=height)


def test_in_bounds():
    board = Board(width=4, height=4)
    assert board.in_bounds(0, 0)
    assert board.in_bounds(3, 3)
    assert not board.in_bounds(-1, 0)
    assert not board.in_bounds(0, 4)
    assert not board.in_bounds(4, 0)


def test_can_place_within_empty_board():
    board = Board(width=4, height=4)
    cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert board.can_place(cells, 0, 0)


def test_can_place_rejects_out_of_bounds():
    board = Board(width=4, height=4)
    cells = [(0, 0), (0, 1)]
    assert not board.can_place(cells, 0, 3)
    assert not board.can_place(cells, -1, 0)
    assert not board.can_place(cells, 4, 0)


def test_can_place_rejects_collision():
    board = Board(width=4, height=4)
    board.lock([(0, 0)], 0, 0, piece_id=1)
    assert not board.can_place([(0, 0)], 0, 0)


def test_lock_writes_piece_id():
    board = Board(width=4, height=4)
    board.lock([(0, 0), (0, 1)], 0, 0, piece_id=5)
    assert board.grid[0][0] == 5
    assert board.grid[0][1] == 5


def test_lock_out_of_bounds_raises():
    board = Board(width=4, height=4)
    with pytest.raises(ValueError):
        board.lock([(10, 10)], 0, 0, piece_id=1)


def test_full_rows_detects_complete_lines():
    board = Board(width=3, height=3)
    for col in range(3):
        board.grid[1][col] = 1
    assert board.full_rows() == [1]


def test_clear_rows_removes_and_shifts_down():
    board = Board(width=2, height=3)
    board.grid[2] = [1, 1]
    board.grid[1] = [1, 0]
    cleared = board.clear_rows([2])
    assert cleared == 1
    assert board.grid == [[0, 0], [0, 0], [1, 0]]


def test_clear_rows_with_no_rows_is_noop():
    board = Board(width=2, height=2)
    snapshot = [row[:] for row in board.grid]
    assert board.clear_rows([]) == 0
    assert board.grid == snapshot


def test_is_row_empty():
    board = Board(width=2, height=2)
    assert board.is_row_empty(0)
    board.grid[0][0] = 1
    assert not board.is_row_empty(0)


def test_top_is_blocked():
    board = Board(width=2, height=4)
    assert not board.top_is_blocked(rows=2)
    board.grid[0][0] = 1
    assert board.top_is_blocked(rows=1)
    assert board.top_is_blocked(rows=4)


def test_is_free():
    board = Board(width=2, height=2)
    assert board.is_free(0, 0)
    board.grid[0][0] = 1
    assert not board.is_free(0, 0)
    assert not board.is_free(-1, 0)


def test_str_renders_grid():
    board = Board(width=2, height=1)
    board.grid[0][0] = 1
    assert str(board) == "#."
