#!/bin/zsh
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
printer_name="${HP1020_PRINTER_NAME:-HP_LaserJet_1020_Plus}"
sample_ps="$repo_root/analysis/samples/minimal-page.ps"
print_script="${HP1020_PRINT_SCRIPT:-/Users/aayush/bin/hp1020-print}"
log_path="/Library/Printers/hp1020/spool-worker.log"

usage() {
  print "Usage: run-printer-readiness-test.sh [--send]" >&2
  print "" >&2
  print "Without --send, this only generates/parses the offline ZjStream sample and checks queue state." >&2
  print "With --send, it sends the known sample page through the installed HP1020 print path." >&2
  exit 2
}

send=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --send) send=1; shift ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

"$repo_root/scripts/generate-zjs-sample.sh"

print ""
print "Queue state:"
lpstat -p "$printer_name" -l 2>&1 || true
lpstat -W not-completed -o "$printer_name" 2>&1 || true

if [[ "$send" -eq 0 ]]; then
  print ""
  print "Dry run complete. Connect/power on the printer, then run:"
  print "  $repo_root/scripts/run-printer-readiness-test.sh --send"
  exit 0
fi

if [[ ! -x "$print_script" ]]; then
  print "Missing executable print script: $print_script" >&2
  exit 1
fi

print ""
print "Sending known sample page through $print_script"
"$print_script" -p a4 "$sample_ps"

print ""
print "Recent worker log:"
tail -80 "$log_path" 2>/dev/null || true
