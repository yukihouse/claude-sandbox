import random
import unittest

from tetris import shapes
from tetris.game import Game
from tetris.streamlit_render import (
    COLORS,
    grid_with_current,
    render_board_html,
    render_next_piece_html,
)


def make_game(width=10, height=20, seed=0):
    return Game(width=width, height=height, rng=random.Random(seed))


class TestStreamlitRender(unittest.TestCase):
    def test_grid_with_current_overlays_the_falling_piece(self):
        game = make_game()
        game.next_name = "O"
        game.spawn_piece()
        piece = game.current

        grid = grid_with_current(game)

        for r, c in piece.cells():
            self.assertEqual(grid[r + piece.row][c + piece.col], piece.piece_id)

    def test_grid_with_current_preserves_locked_cells(self):
        game = make_game()
        game.board.grid[5][2] = 3
        grid = grid_with_current(game)
        self.assertEqual(grid[5][2], 3)

    def test_grid_with_current_does_not_mutate_the_board(self):
        game = make_game()
        grid = grid_with_current(game)
        grid[0][0] = 9
        self.assertEqual(game.board.grid[0][0], 0)

    def test_grid_with_current_omits_piece_when_game_over(self):
        game = make_game()
        game.game_over = True
        grid = grid_with_current(game)
        self.assertTrue(all(cell == 0 for row in grid for cell in row))

    def test_grid_with_current_skips_out_of_bounds_cells(self):
        game = make_game()
        game.current.col = -100
        grid = grid_with_current(game)
        self.assertTrue(all(cell == 0 for row in grid for cell in row))

    def test_render_board_html_has_one_row_div_per_board_row(self):
        game = make_game(width=4, height=6)
        html = render_board_html(game)
        self.assertEqual(html.count('display:flex;'), game.board.height)
        self.assertIn(f"width:{game.board.width * 24}px", html)

    def test_render_board_html_includes_current_piece_color(self):
        game = make_game()
        game.next_name = "I"
        game.spawn_piece()
        html = render_board_html(game)
        self.assertIn(COLORS["I"], html)

    def test_render_next_piece_html_uses_the_pieces_color_and_box_size(self):
        for name in shapes.SHAPE_NAMES:
            with self.subTest(name=name):
                html = render_next_piece_html(name)
                size = shapes.box_size(name)
                self.assertEqual(html.count('display:flex;'), size)
                self.assertIn(COLORS[name], html)
                self.assertIn(f"width:{size * 20}px", html)


if __name__ == "__main__":
    unittest.main()
