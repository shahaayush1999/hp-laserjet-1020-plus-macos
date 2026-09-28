#!/bin/zsh
# Software-only diagnostics. Does not enumerate or query USB devices.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
LABEL="${HP1020_LABEL:-com.aayush.hp1020-root-spool-worker}"

print -- 'Printer queue and waiting jobs:'
lpstat -p "$PRINTER_NAME" -l 2>&1 || true
lpstat -W not-completed -o "$PRINTER_NAME" 2>&1 || true
print -- 'Printer worker:'
launchctl print "system/$LABEL" 2>&1 | grep -E 'state =|runs =|last exit|last terminating|pid =|path =' || true
print -- 'Required software:'
/opt/homebrew/bin/gs --version 2>&1 || true
/opt/homebrew/bin/gsed --version 2>&1 | head -n 1 || true
/opt/homebrew/opt/python@3.14/bin/python3.14 --version 2>&1 || true

if [[ "${1:-}" == --admin ]]; then
  osascript \
    -e 'do shell script "tail -n 80 /Library/Printers/hp1020/state/spool-worker.log 2>/dev/null; tail -n 20 /Library/Printers/hp1020/state/launchd.err.log 2>/dev/null; exit 0" with administrator privileges'
else
  print -- 'For protected worker logs, run: zsh scripts/diagnose.sh --admin'
fi
