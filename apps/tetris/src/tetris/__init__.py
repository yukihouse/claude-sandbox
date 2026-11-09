from __future__ import annotations

import argparse

from .board import Board
from .game import Game

__all__ = ["Board", "Game", "main", "__version__"]

# Keep in sync with the `version` in pyproject.toml: the build scripts read
# it from there for archive names, while this is what `tetris --version`
# reports (including from the standalone builds), so packaging metadata
# isn't available at runtime for a frozen executable.
__version__ = "0.1.0"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tetris", description="A terminal Tetris game.")
    parser.add_argument("--version", action="version", version=f"tetris {__version__}")
    parser.parse_args(argv)

    from .cli import run

    run()
