#!/bin/zsh
# Software-only diagnostics. Never enumerates or queries USB devices.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
print -- 'Printer queue and waiting jobs:'
lpstat -p "$PRINTER_NAME" -l 2>&1 || true
lpstat -W not-completed -o "$PRINTER_NAME" 2>&1 || true
print -- 'Native driver:'
for binary in /Library/Printers/hp1020/runtime/rastertohp1020 /usr/libexec/cups/backend/hp1020; do
  "$binary" --version 2>&1 || true
  codesign --verify --strict "$binary" 2>&1 || true
done
if [[ "${1:-}" == --admin ]]; then
  osascript -e 'do shell script "tail -n 80 /private/var/log/cups/error_log 2>/dev/null; exit 0" with administrator privileges'
else
  print -- 'For protected system printing logs, run: zsh scripts/diagnose.sh --admin'
fi
