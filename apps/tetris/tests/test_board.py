import unittest

from tetris.board import Board


class TestBoard(unittest.TestCase):
    def test_new_board_is_empty(self):
        board = Board(width=10, height=20)
        self.assertTrue(all(cell == 0 for row in board.grid for cell in row))

    def test_invalid_dimensions_raise(self):
        for width, height in [(0, 10), (10, 0), (-1, 5)]:
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError):
                    Board(width=width, height=height)

    def test_in_bounds(self):
        board = Board(width=4, height=4)
        self.assertTrue(board.in_bounds(0, 0))
        self.assertTrue(board.in_bounds(3, 3))
        self.assertFalse(board.in_bounds(-1, 0))
        self.assertFalse(board.in_bounds(0, 4))
        self.assertFalse(board.in_bounds(4, 0))

    def test_can_place_within_empty_board(self):
        board = Board(width=4, height=4)
        cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
        self.assertTrue(board.can_place(cells, 0, 0))

    def test_can_place_rejects_out_of_bounds(self):
        board = Board(width=4, height=4)
        cells = [(0, 0), (0, 1)]
        self.assertFalse(board.can_place(cells, 0, 3))
        self.assertFalse(board.can_place(cells, -1, 0))
        self.assertFalse(board.can_place(cells, 4, 0))

    def test_can_place_rejects_collision(self):
        board = Board(width=4, height=4)
        board.lock([(0, 0)], 0, 0, piece_id=1)
        self.assertFalse(board.can_place([(0, 0)], 0, 0))

    def test_lock_writes_piece_id(self):
        board = Board(width=4, height=4)
        board.lock([(0, 0), (0, 1)], 0, 0, piece_id=5)
        self.assertEqual(board.grid[0][0], 5)
        self.assertEqual(board.grid[0][1], 5)

    def test_lock_out_of_bounds_raises(self):
        board = Board(width=4, height=4)
        with self.assertRaises(ValueError):
            board.lock([(10, 10)], 0, 0, piece_id=1)

    def test_full_rows_detects_complete_lines(self):
        board = Board(width=3, height=3)
        for col in range(3):
            board.grid[1][col] = 1
        self.assertEqual(board.full_rows(), [1])

    def test_clear_rows_removes_and_shifts_down(self):
        board = Board(width=2, height=3)
        board.grid[2] = [1, 1]
        board.grid[1] = [1, 0]
        cleared = board.clear_rows([2])
        self.assertEqual(cleared, 1)
        self.assertEqual(board.grid, [[0, 0], [0, 0], [1, 0]])

    def test_clear_rows_with_no_rows_is_noop(self):
        board = Board(width=2, height=2)
        snapshot = [row[:] for row in board.grid]
        self.assertEqual(board.clear_rows([]), 0)
        self.assertEqual(board.grid, snapshot)

    def test_is_row_empty(self):
        board = Board(width=2, height=2)
        self.assertTrue(board.is_row_empty(0))
        board.grid[0][0] = 1
        self.assertFalse(board.is_row_empty(0))

    def test_top_is_blocked(self):
        board = Board(width=2, height=4)
        self.assertFalse(board.top_is_blocked(rows=2))
        board.grid[0][0] = 1
        self.assertTrue(board.top_is_blocked(rows=1))
        self.assertTrue(board.top_is_blocked(rows=4))

    def test_is_free(self):
        board = Board(width=2, height=2)
        self.assertTrue(board.is_free(0, 0))
        board.grid[0][0] = 1
        self.assertFalse(board.is_free(0, 0))
        self.assertFalse(board.is_free(-1, 0))

    def test_str_renders_grid(self):
        board = Board(width=2, height=1)
        board.grid[0][0] = 1
        self.assertEqual(str(board), "#.")


if __name__ == "__main__":
    unittest.main()
