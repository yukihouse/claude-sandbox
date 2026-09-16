from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pe import PEFormatError, has_version_info_resource


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="version-checker",
        description="Check whether a Windows .exe file has version information embedded.",
    )
    parser.add_argument("exe_path", type=Path, help="path to the .exe file to inspect")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        data = args.exe_path.read_bytes()
    except OSError as exc:
        print(f"error: could not read '{args.exe_path}': {exc.strerror}", file=sys.stderr)
        return 2

    try:
        found = has_version_info_resource(data)
    except PEFormatError as exc:
        print(f"error: '{args.exe_path}' is not a valid PE file: {exc}", file=sys.stderr)
        return 2

    if found:
        print("ok")
        return 0

    print("ng")
    return 1
