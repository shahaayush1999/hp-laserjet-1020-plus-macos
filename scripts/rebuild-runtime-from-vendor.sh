#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/vendor/foo2zjs-source"
OUT="$ROOT/assets/runtime"

for cmd in brew make cc gs gsed; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    print "Missing required command: $cmd" >&2
    print "Install build/runtime dependencies with: brew install ghostscript gnu-sed jbigkit" >&2
    exit 1
  fi
done

if ! brew list jbigkit >/dev/null 2>&1; then
  print "jbigkit is not installed. Install with: brew install jbigkit" >&2
  exit 1
fi

work="$(mktemp -d -t hp1020-foo2zjs-build.XXXXXX)"
trap 'rm -rf "$work"' EXIT

rsync -a --exclude='.git/' "$SRC/" "$work/foo2zjs/"
cd "$work/foo2zjs"

make clean >/dev/null 2>&1 || true
make

install -m 755 foo2zjs "$OUT/foo2zjs"
install -m 755 foo2zjs-wrapper "$OUT/foo2zjs-wrapper"
install -m 755 foo2zjs-pstops "$OUT/foo2zjs-pstops"

if [[ -f "$ROOT/assets/firmware-source/sihp1020.dl" ]]; then
  install -m 644 "$ROOT/assets/firmware-source/sihp1020.dl" "$OUT/sihp1020.dl"
fi

print "Rebuilt runtime into $OUT"
