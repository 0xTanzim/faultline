#!/usr/bin/env bash
# Faultline Universal Installer Wrapper (POSIX)
# Supports both local repository execution and remote streamed one-liner execution:
#   curl -fsSL https://raw.githubusercontent.com/0xTanzim/faultline/main/install.sh | bash -s -- /path/to/project
set -euo pipefail

PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1 && command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: Python 3 (python3 or python) is required to run the Faultline installer." >&2
  exit 1
fi

LOCAL_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  LOCAL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
fi

if [ -n "$LOCAL_DIR" ] && [ -f "$LOCAL_DIR/install.py" ]; then
  exec "$PYTHON_BIN" "$LOCAL_DIR/install.py" "$@"
fi

# Streamed remote execution via curl/pipe
TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'faultline')"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

REPO_TARBALL="https://github.com/0xTanzim/faultline/archive/refs/heads/main.tar.gz"
echo "Fetching latest Faultline release from GitHub..." >&2

if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$REPO_TARBALL" | tar -xz -C "$TMP_DIR" --strip-components=1
elif command -v wget >/dev/null 2>&1; then
  wget -qO- "$REPO_TARBALL" | tar -xz -C "$TMP_DIR" --strip-components=1
else
  echo "ERROR: Neither curl nor wget was found to download Faultline." >&2
  exit 1
fi

# Default to current directory if no arguments passed
if [ $# -eq 0 ]; then
  set -- "."
fi

"$PYTHON_BIN" "$TMP_DIR/install.py" "$@"
