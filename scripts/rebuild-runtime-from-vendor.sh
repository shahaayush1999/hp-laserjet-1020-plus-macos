#!/bin/zsh
# Maintainer-only, offline build. Installation uses the bundled binaries.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/build-macos-runtime.py" "$@"
