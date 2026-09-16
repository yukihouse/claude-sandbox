"""Game state machine: piece spawning, movement, rotation, scoring."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import shapes
from .board import Board

# Simple offsets tried in order when a rotation would otherwise collide.
_WALL_KICKS = [(0, 0), (0, -1), (0, 1), (0, -2), (0, 2)]

# Classic single/double/triple/tetris scoring, multiplied by (level + 1).
_LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}

PIECE_IDS = {name: index + 1 for index, name in enumerate(shapes.SHAPE_NAMES)}


@dataclass
class ActivePiece:
    name: str
    rotation: int = 0
    row: int = 0
    col: int = 0

    @property
    def piece_id(self) -> int:
        return PIECE_IDS[self.name]

    def cells(self) -> list[tuple[int, int]]:
        return shapes.get_cells(self.name, self.rotation)


@dataclass
class Game:
    width: int = 10
    height: int = 20
    rng: random.Random = field(default_factory=random.Random)
    board: Board = field(init=False)
    current: ActivePiece | None = field(init=False, default=None)
    next_name: str = field(init=False, default="")
    score: int = field(init=False, default=0)
    lines_cleared: int = field(init=False, default=0)
    level: int = field(init=False, default=0)
    game_over: bool = field(init=False, default=False)
    _bag: list[str] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.board = Board(self.width, self.height)
        self.next_name = self._draw_from_bag()
        self.spawn_piece()

    def _draw_from_bag(self) -> str:
        if not self._bag:
            self._bag = list(shapes.SHAPE_NAMES)
            self.rng.shuffle(self._bag)
        return self._bag.pop()

    def spawn_piece(self) -> None:
        name = self.next_name
        self.next_name = self._draw_from_bag()
        size = shapes.box_size(name)
        col = (self.width - size) // 2
        piece = ActivePiece(name=name, rotation=0, row=0, col=col)
        if not self.board.can_place(piece.cells(), piece.row, piece.col):
            self.game_over = True
            self.current = piece
            return
        self.current = piece

    def _try_move(self, d_row: int, d_col: int) -> bool:
        if self.game_over or self.current is None:
            return False
        piece = self.current
        new_row, new_col = piece.row + d_row, piece.col + d_col
        if self.board.can_place(piece.cells(), new_row, new_col):
            piece.row, piece.col = new_row, new_col
            return True
        return False

    def move_left(self) -> bool:
        return self._try_move(0, -1)

    def move_right(self) -> bool:
        return self._try_move(0, 1)

    def soft_drop(self) -> bool:
        moved = self._try_move(1, 0)
        if not moved and not self.game_over:
            self._lock_and_advance()
        return moved

    def hard_drop(self) -> int:
        if self.game_over or self.current is None:
            return 0
        distance = 0
        while self._try_move(1, 0):
            distance += 1
        self.score += distance
        self._lock_and_advance()
        return distance

    def rotate(self, clockwise: bool = True) -> bool:
        if self.game_over or self.current is None:
            return False
        piece = self.current
        new_rotation = (piece.rotation + (1 if clockwise else -1)) % 4
        new_cells = shapes.get_cells(piece.name, new_rotation)
        for d_col, d_row in ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0)):
            if self.board.can_place(new_cells, piece.row + d_row, piece.col + d_col):
                piece.rotation = new_rotation
                piece.row += d_row
                piece.col += d_col
                return True
        return False

    def _lock_and_advance(self) -> None:
        piece = self.current
        assert piece is not None
        self.board.lock(piece.cells(), piece.row, piece.col, piece.piece_id)
        full_rows = self.board.full_rows()
        cleared = self.board.clear_rows(full_rows)
        if cleared:
            self.lines_cleared += cleared
            self.score += _LINE_SCORES.get(cleared, 0) * (self.level + 1)
            self.level = self.lines_cleared // 10
        self.spawn_piece()

    def tick(self) -> None:
        """Advance gravity by one row, locking the piece if it can't move."""
        if self.game_over:
            return
        self.soft_drop()
