from .board import Board
from .game import Game

__all__ = ["Board", "Game", "main"]


def main() -> None:
    from .cli import run

    run()
