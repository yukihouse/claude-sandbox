"""Entry point used by PyInstaller to build a standalone tetris executable.

PyInstaller needs a plain script (not an installed package) to analyze, so
this wraps the ``tetris.main`` console-script entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tetris import main

if __name__ == "__main__":
    main()
