"""The Tetris playing field."""

from __future__ import annotations

EMPTY = 0

Cell = tuple[int, int]


class Board:
    """A grid of locked cells. 0 means empty, any other value is a piece id."""

    def __init__(self, width: int = 10, height: int = 20) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = width
        self.height = height
        self.grid: list[list[int]] = [[EMPTY] * width for _ in range(height)]

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def is_free(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and self.grid[row][col] == EMPTY

    def can_place(self, cells: list[Cell], row_offset: int, col_offset: int) -> bool:
        """Return True if every cell fits on the board without colliding."""
        for r, c in cells:
            row, col = r + row_offset, c + col_offset
            if not self.in_bounds(row, col):
                return False
            if self.grid[row][col] != EMPTY:
                return False
        return True

    def lock(self, cells: list[Cell], row_offset: int, col_offset: int, piece_id: int) -> None:
        for r, c in cells:
            row, col = r + row_offset, c + col_offset
            if not self.in_bounds(row, col):
                raise ValueError(f"Cell ({row}, {col}) is out of bounds")
            self.grid[row][col] = piece_id

    def full_rows(self) -> list[int]:
        return [r for r in range(self.height) if all(cell != EMPTY for cell in self.grid[r])]

    def clear_rows(self, rows: list[int]) -> int:
        """Remove the given rows and insert empty rows at the top. Returns count cleared."""
        if not rows:
            return 0
        rows_set = set(rows)
        remaining = [row for i, row in enumerate(self.grid) if i not in rows_set]
        cleared = len(self.grid) - len(remaining)
        new_rows = [[EMPTY] * self.width for _ in range(cleared)]
        self.grid = new_rows + remaining
        return cleared

    def is_row_empty(self, row: int) -> bool:
        return all(cell == EMPTY for cell in self.grid[row])

    def top_is_blocked(self, rows: int = 1) -> bool:
        """Return True if any cell in the topmost `rows` rows is occupied."""
        return any(not self.is_row_empty(r) for r in range(min(rows, self.height)))

    def __str__(self) -> str:
        lines = []
        for row in self.grid:
            lines.append("".join("." if cell == EMPTY else "#" for cell in row))
        return "\n".join(lines)
