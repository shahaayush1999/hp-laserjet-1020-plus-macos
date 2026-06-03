#!/bin/zsh
set -euo pipefail

PRINTER_NAME="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
LABEL="${HP1020_LABEL:-com.aayush.hp1020-root-spool-worker}"

printf '%s\n' '--- CUPS queue ---'
lpstat -p "$PRINTER_NAME" -v -l 2>&1 || true
lpstat -W not-completed -o "$PRINTER_NAME" 2>&1 || true

printf '\n%s\n' '--- USB backends ---'
lpinfo -v 2>&1 | rg -n 'usb|LaserJet|Hewlett|hp1020' || true
env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/libexec/cups/backend/usb 2>&1 | sed -n '1,80p' || true

printf '\n%s\n' '--- LaunchDaemon ---'
launchctl print "system/$LABEL" 2>&1 | rg 'state =|runs =|last exit|last terminating|pid =|path =' || true

printf '\n%s\n' '--- Worker log ---'
tail -n 140 /Library/Printers/hp1020/spool-worker.log 2>/dev/null || true

printf '\n%s\n' '--- Processes ---'
ps ax -o pid,user,command | rg 'hp1020|foo2zjs|backend/usb' | rg -v rg || true

if [[ "${1:-}" == "--admin" ]]; then
  printf '\n%s\n' '--- Protected spool state ---'
  osascript \
    -e 'do shell script "echo TMP; ls -l /private/var/spool/cups/tmp/hp1020queue 2>/dev/null || true; echo DONE; ls -lt /Library/Printers/hp1020/done 2>/dev/null | head -n 20 || true; echo FAILED; ls -lt /Library/Printers/hp1020/failed 2>/dev/null | head -n 20 || true" with administrator privileges'
fi
