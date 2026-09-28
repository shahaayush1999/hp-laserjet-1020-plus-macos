#!/bin/zsh
# Build native CUPS components, preserving upstream/research sources unchanged.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ $# == 1 ]] || { print -u2 -- "Usage: $0 OUTPUT_DIRECTORY"; exit 2; }
OUT="$1"
SRC="$ROOT/vendor/foo2zjs-source"
mkdir -p "$OUT"
work="$(mktemp -d -t hp1020-build.XXXXXXXX)"
trap 'rm -rf "$work"' EXIT
/usr/bin/clang -O2 -arch arm64 -I "$SRC" -Dmain=foo2zjs_main -c "$SRC/foo2zjs.c" -o "$work/encoder.o"
/usr/bin/clang -O2 -arch arm64 -I "$SRC" -c "$SRC/jbig.c" -o "$work/jbig.o"
/usr/bin/clang -O2 -arch arm64 -I "$SRC" -c "$SRC/jbig_ar.c" -o "$work/jbig_ar.o"
flags=(-O2 -arch arm64 -Wall -Wextra -Werror -Wno-deprecated-declarations -Wno-unused-function)
/usr/bin/clang "${flags[@]}" "$ROOT/files/macos/rastertohp1020.c" "$work/encoder.o" "$work/jbig.o" "$work/jbig_ar.o" -lcups -o "$OUT/rastertohp1020"
/usr/bin/clang "${flags[@]}" "$ROOT/files/macos/hp1020-backend.c" -lcups -o "$OUT/hp1020"
for binary in "$OUT/rastertohp1020" "$OUT/hp1020"; do
  /usr/bin/codesign --force --sign - "$binary"
done
cp "$ROOT/assets/runtime/sihp1020.dl" "$OUT/sihp1020.dl"
