#!/bin/zsh
# Build the small encoder for this Mac; preserve the original research runtime.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ $# == 1 ]] || { print -u2 -- "Usage: $0 OUTPUT_DIRECTORY"; exit 2; }
OUT="$1"
SRC="$ROOT/vendor/foo2zjs-source"
mkdir -p "$OUT"
/usr/bin/clang -O2 -arch arm64 -I "$SRC" -o "$OUT/foo2zjs" \
  "$SRC/foo2zjs.c" "$SRC/jbig.c" "$SRC/jbig_ar.c"
/usr/bin/codesign --force --sign - "$OUT/foo2zjs"
# Quote filenames and propagate renderer failures through the original pipeline.
awk '
  NR == 1 { print "#!/bin/bash"; print "set -o pipefail"; next }
  /exec < \$1/ { sub(/exec < \$1/, "exec < \"$1\""); quoted++ }
  $0 == "if [ -x /usr/bin/logger ]; then" {
    print "pipeline_status=$?"
    print "[ \"$pipeline_status\" -eq 0 ] || exit \"$pipeline_status\""
    guarded++
  }
  { print }
  END { if (quoted != 1 || guarded != 1) exit 1 }
' "$ROOT/assets/runtime/foo2zjs-wrapper" > "$OUT/foo2zjs-wrapper"
cp "$ROOT/assets/runtime/foo2zjs-pstops" "$OUT/foo2zjs-pstops"
cp "$ROOT/assets/runtime/sihp1020.dl" "$OUT/sihp1020.dl"
chmod 755 "$OUT/foo2zjs" "$OUT/foo2zjs-wrapper" "$OUT/foo2zjs-pstops"
