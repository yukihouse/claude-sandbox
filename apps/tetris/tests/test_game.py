import random
import unittest

from tetris import shapes
from tetris.board import Board
from tetris.game import ActivePiece, Game


def make_game(width=10, height=20, seed=0):
    return Game(width=width, height=height, rng=random.Random(seed))


class TestGame(unittest.TestCase):
    def test_game_starts_with_a_current_and_next_piece(self):
        game = make_game()
        self.assertIsNotNone(game.current)
        self.assertIn(game.next_name, shapes.SHAPE_NAMES)
        self.assertFalse(game.game_over)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.lines_cleared, 0)
        self.assertEqual(game.level, 0)

    def test_spawn_piece_centers_the_piece_horizontally(self):
        game = make_game(width=10, height=20)
        game.next_name = "O"
        game.spawn_piece()
        size = shapes.box_size("O")
        self.assertEqual(game.current.col, (10 - size) // 2)

    def test_seven_bag_produces_each_shape_once_before_repeating(self):
        game = make_game(seed=7)
        seen = {game.current.name, game.next_name}
        for _ in range(5):
            game.spawn_piece()
            seen.add(game.next_name)
        self.assertEqual(seen, set(shapes.SHAPE_NAMES))

    def test_move_left_and_right_within_open_board(self):
        game = make_game(width=10, height=20)
        game.board = Board(width=10, height=20)
        game.current = ActivePiece(name="O", rotation=0, row=5, col=5)
        self.assertTrue(game.move_left())
        self.assertEqual(game.current.col, 4)
        self.assertTrue(game.move_right())
        self.assertEqual(game.current.col, 5)

    def test_move_left_blocked_by_wall(self):
        game = make_game(width=10, height=20)
        game.board = Board(width=10, height=20)
        game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
        self.assertFalse(game.move_left())
        self.assertEqual(game.current.col, 0)

    def test_moves_return_false_after_game_over(self):
        game = make_game()
        game.game_over = True
        self.assertFalse(game.move_left())
        self.assertFalse(game.move_right())
        self.assertFalse(game.rotate())
        self.assertEqual(game.hard_drop(), 0)

    def test_soft_drop_locks_piece_when_it_reaches_the_floor(self):
        game = make_game(width=4, height=3)
        game.board = Board(width=4, height=3)
        game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
        game.next_name = "O"
        self.assertTrue(game.soft_drop())  # moves from row 0 to row 1
        self.assertFalse(game.soft_drop())  # can't move further, locks and spawns
        self.assertNotEqual(game.board.grid[1][0], 0)
        self.assertNotEqual(game.board.grid[2][0], 0)
        self.assertIsNotNone(game.current)  # a new piece spawned

    def test_hard_drop_moves_piece_to_the_bottom_and_scores(self):
        game = make_game(width=4, height=6)
        game.board = Board(width=4, height=6)
        game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
        game.next_name = "O"
        distance = game.hard_drop()
        self.assertEqual(distance, 4)  # falls from row 0 to row 4 (board height 6, piece height 2)
        self.assertEqual(game.score, 4)
        self.assertNotEqual(game.board.grid[5][0], 0)
        self.assertNotEqual(game.board.grid[5][1], 0)

    def test_line_clear_with_i_piece_completes_and_clears_bottom_row(self):
        game = make_game(width=4, height=4)
        game.board = Board(width=4, height=4)
        game.board.grid[3] = [9, 9, 9, 0]  # one cell short of a full bottom row
        # Vertical I piece (rotation 1) occupies local column 2; col=1 lines it
        # up with the empty cell in board column 3.
        game.current = ActivePiece(name="I", rotation=1, row=0, col=1)
        game.next_name = "O"
        game.hard_drop()
        self.assertEqual(game.lines_cleared, 1)
        self.assertGreaterEqual(game.score, 100)
        # The completed filler row is gone and a fresh empty row was inserted at
        # the top; the I piece's remaining cells shifted down by one row.
        self.assertEqual(game.board.grid[0], [0, 0, 0, 0])
        self.assertNotIn(9, [cell for row in game.board.grid for cell in row])

    def test_level_increases_after_ten_lines(self):
        game = make_game()
        game.lines_cleared = 9
        game.board = Board(width=4, height=4)
        game.board.grid[3] = [9, 9, 9, 0]
        game.current = ActivePiece(name="I", rotation=1, row=0, col=1)
        game.next_name = "O"
        game.hard_drop()
        self.assertEqual(game.lines_cleared, 10)
        self.assertEqual(game.level, 1)

    def test_game_over_when_spawn_position_is_blocked(self):
        game = make_game(width=4, height=4)
        for row in range(2):
            game.board.grid[row] = [9, 9, 9, 9]
        game.next_name = "O"
        game.spawn_piece()
        self.assertTrue(game.game_over)

    def test_rotate_succeeds_in_open_space(self):
        game = make_game(width=10, height=10)
        game.board = Board(width=10, height=10)
        game.current = ActivePiece(name="O", rotation=0, row=5, col=5)
        self.assertTrue(game.rotate())
        self.assertEqual(game.current.rotation, 1)

    def test_rotate_uses_a_wall_kick_when_the_default_position_collides(self):
        game = make_game(width=10, height=10)
        game.board = Board(width=10, height=10)
        piece = ActivePiece(name="I", rotation=0, row=0, col=0)
        game.current = piece
        target_cells = shapes.get_cells("I", 1)
        for r, c in target_cells:
            game.board.grid[r][c] = 9
        self.assertTrue(game.rotate())
        self.assertEqual(game.current.rotation, 1)
        self.assertNotEqual(game.current.col, 0)

    def test_rotate_returns_false_when_no_kick_position_fits(self):
        game = make_game(width=4, height=4)
        game.board = Board(width=4, height=4)
        for r in range(4):
            for c in range(4):
                game.board.grid[r][c] = 9
        piece = ActivePiece(name="T", rotation=0, row=0, col=0)
        for r, c in piece.cells():
            game.board.grid[r][c] = 0
        game.current = piece
        self.assertFalse(game.rotate())
        self.assertEqual(game.current.rotation, 0)

    def test_tick_advances_gravity_by_one_row(self):
        game = make_game(width=10, height=10)
        game.board = Board(width=10, height=10)
        game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
        game.tick()
        self.assertEqual(game.current.row, 1)

    def test_tick_does_nothing_after_game_over(self):
        game = make_game()
        game.game_over = True
        game.current = ActivePiece(name="O", rotation=0, row=0, col=0)
        game.tick()
        self.assertEqual(game.current.row, 0)

    def test_active_piece_id_is_stable_per_shape(self):
        a = ActivePiece(name="T", rotation=0, row=0, col=0)
        b = ActivePiece(name="T", rotation=2, row=3, col=1)
        self.assertEqual(a.piece_id, b.piece_id)


if __name__ == "__main__":
    unittest.main()
