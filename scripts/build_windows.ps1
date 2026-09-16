# Build a standalone Windows executable for the Tetris demo game.
#
# Produces a single-file tetris.exe (no Python install required to run it)
# with version information embedded, plus a zip archive ready for
# distribution. The build fails if version-checker does not confirm the
# version information was embedded correctly.
#
# Requirements: Windows, PowerShell, and uv (https://docs.astral.sh/uv/).
#
# Usage:
#   pwsh scripts/build_windows.ps1

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RootDir

if (-not $IsWindows) {
    Write-Error "error: this script must be run on Windows (PyInstaller builds a native binary for the host OS)."
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "error: uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

$Version = (Select-String -Path "pyproject.toml" -Pattern '^version\s*=\s*"([^"]+)"' | Select-Object -First 1).Matches.Groups[1].Value
$Arch = $env:PROCESSOR_ARCHITECTURE.ToLower()
$DistDir = Join-Path $RootDir "dist\windows"
$WorkDir = Join-Path $RootDir "build\pyinstaller"
$VersionFile = Join-Path $RootDir "scripts\version_info.txt"
$ExePath = Join-Path $DistDir "tetris.exe"
$ArchiveName = "tetris-$Version-windows-$Arch.zip"
$ArchivePath = Join-Path $DistDir $ArchiveName

Remove-Item -Recurse -Force $DistDir, $WorkDir -ErrorAction SilentlyContinue

Write-Host "==> Installing project dependencies"
uv sync --locked

Write-Host "==> Building standalone executable with PyInstaller"
uv run --with pyinstaller pyinstaller `
    --onefile `
    --name tetris `
    --paths "$RootDir\src" `
    --distpath $DistDir `
    --workpath $WorkDir `
    --specpath $WorkDir `
    --version-file $VersionFile `
    --clean `
    --noconfirm `
    "$RootDir\scripts\pyinstaller_entry.py"

Write-Host "==> Verifying embedded version info with version-checker"
uv run --project "$RootDir\version-checker" version-checker $ExePath
if ($LASTEXITCODE -ne 0) {
    Write-Error "error: version-checker did not confirm version info is embedded in $ExePath (exit code $LASTEXITCODE)."
    exit 1
}

Write-Host "==> Verifying --version output"
$ActualVersion = & $ExePath --version
$ExpectedVersion = "tetris $Version"
if ($ActualVersion -ne $ExpectedVersion) {
    Write-Error "error: expected '$ExePath --version' to print '$ExpectedVersion', got '$ActualVersion'."
    exit 1
}

Write-Host "==> Packaging archive for distribution"
Compress-Archive -Path $ExePath -DestinationPath $ArchivePath -Force

Write-Host ""
Write-Host "Build complete:"
Write-Host "  binary:  $ExePath"
Write-Host "  archive: $ArchivePath"
Write-Host ""
Write-Host "Run it with: $ExePath"
