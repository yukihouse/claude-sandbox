#!/usr/bin/env bash
# Build a standalone macOS executable for the Tetris demo game.
#
# Produces a single-file binary (no Python install required to run it) plus
# a zip archive ready for distribution.
#
# Requirements: macOS, and uv (https://docs.astral.sh/uv/).
#
# Usage:
#   scripts/build_macos.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: this script must be run on macOS (PyInstaller builds a native binary for the host OS)." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

VERSION="$(grep -m1 '^version' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')"
ARCH="$(uname -m)"
DIST_DIR="$ROOT_DIR/dist/macos"
WORK_DIR="$ROOT_DIR/build/pyinstaller"
ARCHIVE_NAME="tetris-${VERSION}-macos-${ARCH}.zip"

rm -rf "$DIST_DIR" "$WORK_DIR"

echo "==> Installing project dependencies"
uv sync --locked

echo "==> Building standalone executable with PyInstaller"
uv run --with pyinstaller pyinstaller \
  --onefile \
  --name tetris \
  --paths "$ROOT_DIR/src" \
  --distpath "$DIST_DIR" \
  --workpath "$WORK_DIR" \
  --specpath "$WORK_DIR" \
  --clean \
  --noconfirm \
  "$ROOT_DIR/scripts/pyinstaller_entry.py"

echo "==> Verifying --version output"
ACTUAL_VERSION="$("$DIST_DIR/tetris" --version)"
EXPECTED_VERSION="tetris ${VERSION}"
if [[ "$ACTUAL_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "error: expected '$DIST_DIR/tetris --version' to print '$EXPECTED_VERSION', got '$ACTUAL_VERSION'" >&2
  exit 1
fi

echo "==> Packaging archive for distribution"
(cd "$DIST_DIR" && zip -q "$ARCHIVE_NAME" tetris)

echo
echo "Build complete:"
echo "  binary:  $DIST_DIR/tetris"
echo "  archive: $DIST_DIR/$ARCHIVE_NAME"
echo
echo "Run it with: $DIST_DIR/tetris"
