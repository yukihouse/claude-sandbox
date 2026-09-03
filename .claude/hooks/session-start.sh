#!/bin/bash
# Installs the .NET SDK and Zig toolchain when they are missing, so
# csharp-demo (and any future zig-demo) work out of the box in a fresh
# Claude Code on the web session. No-ops locally and when already installed.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# --- .NET SDK (needed by csharp-demo) ---------------------------------
DOTNET_VERSION="8.0"

if ! command -v dotnet >/dev/null 2>&1; then
  echo "Installing .NET SDK ${DOTNET_VERSION} via apt..."
  apt-get update -qq
  apt-get install -y -qq "dotnet-sdk-${DOTNET_VERSION}"
fi

# --- Zig ----------------------------------------------------------------
# ziglang.org and GitHub release assets are not reachable from this
# sandbox's network policy, so we install the official prebuilt binary
# distributed as a PyPI wheel (pypi.org is allowlisted) instead.
if ! command -v zig >/dev/null 2>&1; then
  echo "Installing Zig via the ziglang PyPI package..."
  python3 -m pip install --quiet --user ziglang

  ZIG_SHIM="$HOME/.local/bin/zig"
  mkdir -p "$(dirname "$ZIG_SHIM")"
  cat > "$ZIG_SHIM" << 'EOF'
#!/bin/bash
exec python3 -m ziglang "$@"
EOF
  chmod +x "$ZIG_SHIM"
fi

echo "dotnet: $(dotnet --version 2>/dev/null || echo 'not available')"
echo "zig: $(zig version 2>/dev/null || echo 'not available')"
