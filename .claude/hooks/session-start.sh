#!/bin/bash
# Installs the .NET SDK, Zig and Deno toolchains when missing, and works
# around a couple of environment quirks, so csharp-demo / zig-demo /
# typescript-demo / php-demo work out of the box in a fresh Claude Code on
# the web session. No-ops locally and when already installed.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# --- .NET SDK (needed by csharp-demo) ---------------------------------
DOTNET_VERSION="10.0"

if ! command -v dotnet >/dev/null 2>&1; then
  echo "Installing .NET SDK ${DOTNET_VERSION} via apt..."
  apt-get update -qq > /dev/null
  apt-get install -y -qq "dotnet-sdk-${DOTNET_VERSION}" > /dev/null
fi

# --- Zig ----------------------------------------------------------------
# ziglang.org and GitHub release assets are not reachable from this
# sandbox's network policy, so we install the official prebuilt binary
# distributed as a PyPI wheel (pypi.org is allowlisted) instead. Pinned
# to match the version zig-demo's CI installs (.github/workflows/ci.yml).
ZIG_VERSION="0.15.2"

if [ "$(zig version 2>/dev/null || true)" != "$ZIG_VERSION" ]; then
  echo "Installing Zig ${ZIG_VERSION} via the ziglang PyPI package..."
  python3 -m pip install --quiet --quiet --user "ziglang==${ZIG_VERSION}" > /dev/null

  ZIG_SHIM="$HOME/.local/bin/zig"
  mkdir -p "$(dirname "$ZIG_SHIM")"
  cat > "$ZIG_SHIM" << 'EOF'
#!/bin/bash
exec python3 -m ziglang "$@"
EOF
  chmod +x "$ZIG_SHIM"
fi

# --- Deno (needed by typescript-demo) -----------------------------------
# The official install script (deno.land/install.sh) pulls the binary from
# dl.deno.land / GitHub releases, which this sandbox's network policy
# blocks (403 on CONNECT). registry.npmjs.org is allowlisted instead, and
# the `deno` npm package ships the same prebuilt binary, so install via npm.
if ! command -v deno >/dev/null 2>&1; then
  echo "Installing Deno via npm..."
  npm install -g deno --silent > /dev/null
fi

# --- Composer superuser guard (needed by php-demo) -----------------------
# Composer refuses to run script-defined commands (e.g. `composer test`,
# which invokes `phpunit` as a script) as root unless explicitly allowed.
# This sandbox always runs as root, so allow it once for all shells.
if ! grep -q "^export COMPOSER_ALLOW_SUPERUSER=1$" "$HOME/.bashrc" 2>/dev/null; then
  echo 'export COMPOSER_ALLOW_SUPERUSER=1' >> "$HOME/.bashrc"
fi
export COMPOSER_ALLOW_SUPERUSER=1

echo "dotnet: $(dotnet --version 2>/dev/null || echo 'not available')"
echo "zig: $(zig version 2>/dev/null || echo 'not available')"
echo "deno: $(deno --version 2>/dev/null | head -1 || echo 'not available')"
