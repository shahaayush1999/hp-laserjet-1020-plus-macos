#!/bin/zsh
set -euo pipefail

PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
tmp_ps="$(mktemp -t hp1020-test.XXXXXX.ps)"
trap 'rm -f "$tmp_ps"' EXIT

cat > "$tmp_ps" <<'PS'
%!PS-Adobe-3.0
%%Pages: 1
%%BoundingBox: 0 0 595 842
/Helvetica findfont 22 scalefont setfont
72 760 moveto
(HP LaserJet 1020 macOS queue test) show
/Helvetica findfont 12 scalefont setfont
72 730 moveto
(If you can read this, the custom CUPS queue, worker, firmware preload, and USB send path worked.) show
showpage
PS

lp -d "$PRINTER_NAME" "$tmp_ps"
sleep 5
lpstat -p "$PRINTER_NAME" -l
lpstat -W not-completed -o "$PRINTER_NAME" 2>&1 || true
