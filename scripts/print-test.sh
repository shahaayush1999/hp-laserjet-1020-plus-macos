#!/bin/zsh
# Explicit user-run physical print test, through the normal Mac queue.
set -euo pipefail
PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
test_text="$(mktemp -t hp1020-test.XXXXXXXX.txt)"
trap 'rm -f "$test_text"' EXIT
cat > "$test_text" <<'TEXT'
HP LaserJet 1020 Plus - Mac printing test

If you can read this page, the Mac queue and printer printed successfully.
TEXT
lp -d "$PRINTER_NAME" -o PageSize=A4 "$test_text"
lpstat -p "$PRINTER_NAME" -l
