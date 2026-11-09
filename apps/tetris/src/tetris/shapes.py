"""Tetromino shape definitions and rotation helpers."""

from __future__ import annotations

Cell = tuple[int, int]

# Each shape is defined by its cells (row, col) within a square bounding box
# and the size of that box, following the classic Tetris Guideline layouts.
_BASE_SHAPES: dict[str, list[Cell]] = {
    "I": [(1, 0), (1, 1), (1, 2), (1, 3)],
    "O": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "T": [(0, 1), (1, 0), (1, 1), (1, 2)],
    "S": [(0, 1), (0, 2), (1, 0), (1, 1)],
    "Z": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "J": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "L": [(0, 2), (1, 0), (1, 1), (1, 2)],
}

_BOX_SIZE: dict[str, int] = {
    "I": 4,
    "O": 2,
    "T": 3,
    "S": 3,
    "Z": 3,
    "J": 3,
    "L": 3,
}

SHAPE_NAMES: tuple[str, ...] = tuple(_BASE_SHAPES.keys())


def _rotate_cw(cells: list[Cell], size: int) -> list[Cell]:
    """Rotate cells 90 degrees clockwise within a size x size box."""
    return [(col, size - 1 - row) for row, col in cells]


def _build_rotations(name: str) -> list[list[Cell]]:
    size = _BOX_SIZE[name]
    rotations = [sorted(_BASE_SHAPES[name])]
    for _ in range(3):
        rotations.append(sorted(_rotate_cw(rotations[-1], size)))
    return rotations


ROTATIONS: dict[str, list[list[Cell]]] = {name: _build_rotations(name) for name in _BASE_SHAPES}


def get_cells(name: str, rotation: int) -> list[Cell]:
    """Return the (row, col) offsets for a shape at a given rotation index."""
    if name not in ROTATIONS:
        raise ValueError(f"Unknown tetromino shape: {name!r}")
    return ROTATIONS[name][rotation % 4]


def box_size(name: str) -> int:
    if name not in _BOX_SIZE:
        raise ValueError(f"Unknown tetromino shape: {name!r}")
    return _BOX_SIZE[name]
