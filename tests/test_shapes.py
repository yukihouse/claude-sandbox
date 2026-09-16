import pytest

from tetris import shapes


def test_shape_names_cover_all_seven_tetrominoes():
    assert set(shapes.SHAPE_NAMES) == {"I", "O", "T", "S", "Z", "J", "L"}


@pytest.mark.parametrize("name", shapes.SHAPE_NAMES)
def test_every_rotation_has_four_cells(name):
    for rotation in range(4):
        assert len(shapes.get_cells(name, rotation)) == 4


@pytest.mark.parametrize("name", shapes.SHAPE_NAMES)
def test_rotation_wraps_around(name):
    assert shapes.get_cells(name, 0) == shapes.get_cells(name, 4)
    assert shapes.get_cells(name, -1) == shapes.get_cells(name, 3)


def test_o_piece_is_identical_in_every_rotation():
    base = shapes.get_cells("O", 0)
    for rotation in range(1, 4):
        assert shapes.get_cells("O", rotation) == base


def test_i_piece_alternates_between_horizontal_and_vertical():
    horizontal = shapes.get_cells("I", 0)
    vertical = shapes.get_cells("I", 1)
    assert len({row for row, _ in horizontal}) == 1
    assert len({col for _, col in vertical}) == 1


def test_box_size_known_shapes():
    assert shapes.box_size("I") == 4
    assert shapes.box_size("O") == 2
    assert shapes.box_size("T") == 3


def test_get_cells_rejects_unknown_shape():
    with pytest.raises(ValueError):
        shapes.get_cells("X", 0)


def test_box_size_rejects_unknown_shape():
    with pytest.raises(ValueError):
        shapes.box_size("X")
