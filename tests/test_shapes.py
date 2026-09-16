import unittest

from tetris import shapes


class TestShapes(unittest.TestCase):
    def test_shape_names_cover_all_seven_tetrominoes(self):
        self.assertEqual(set(shapes.SHAPE_NAMES), {"I", "O", "T", "S", "Z", "J", "L"})

    def test_every_rotation_has_four_cells(self):
        for name in shapes.SHAPE_NAMES:
            with self.subTest(name=name):
                for rotation in range(4):
                    self.assertEqual(len(shapes.get_cells(name, rotation)), 4)

    def test_rotation_wraps_around(self):
        for name in shapes.SHAPE_NAMES:
            with self.subTest(name=name):
                self.assertEqual(shapes.get_cells(name, 0), shapes.get_cells(name, 4))
                self.assertEqual(shapes.get_cells(name, -1), shapes.get_cells(name, 3))

    def test_o_piece_is_identical_in_every_rotation(self):
        base = shapes.get_cells("O", 0)
        for rotation in range(1, 4):
            self.assertEqual(shapes.get_cells("O", rotation), base)

    def test_i_piece_alternates_between_horizontal_and_vertical(self):
        horizontal = shapes.get_cells("I", 0)
        vertical = shapes.get_cells("I", 1)
        self.assertEqual(len({row for row, _ in horizontal}), 1)
        self.assertEqual(len({col for _, col in vertical}), 1)

    def test_box_size_known_shapes(self):
        self.assertEqual(shapes.box_size("I"), 4)
        self.assertEqual(shapes.box_size("O"), 2)
        self.assertEqual(shapes.box_size("T"), 3)

    def test_get_cells_rejects_unknown_shape(self):
        with self.assertRaises(ValueError):
            shapes.get_cells("X", 0)

    def test_box_size_rejects_unknown_shape(self):
        with self.assertRaises(ValueError):
            shapes.box_size("X")


if __name__ == "__main__":
    unittest.main()
