#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE_DL="$ROOT_DIR/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl"
PROBE_SRC="$ROOT_DIR/open-firmware/minimal-idle"
PROBE_DISASM="$ROOT_DIR/analysis/open-firmware-probes/minimal-idle/disassembly.txt"
USB_BACKEND="/usr/libexec/cups/backend/usb"

mode="dry-run"
device_uri="${DEVICE_URI:-}"
ack=0

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/run-idle-probe-hardware-test.sh [--dry-run]
  scripts/run-idle-probe-hardware-test.sh --upload --device-uri 'usb://...' --i-understand-this-uploads-custom-firmware

This uploads only the open idle firmware probe. It never sends a print job.
The URI must be the direct CUPS USB backend URI, not hp1020queue://localhost.
Actual upload also requires:
  HP1020_ALLOW_CUSTOM_FIRMWARE_UPLOAD=1
EOF
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) mode="dry-run"; shift ;;
    --upload) mode="upload"; shift ;;
    --device-uri) [[ $# -ge 2 ]] || usage; device_uri="$2"; shift 2 ;;
    --i-understand-this-uploads-custom-firmware) ack=1; shift ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

if [[ ! -f "$PROBE_DL" ]]; then
  echo "missing probe upload: $PROBE_DL" >&2
  echo "run scripts/build-open-firmware-idle-probe.sh first" >&2
  exit 1
fi

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" --profile boot-probe "$PROBE_DL" >/tmp/hp1020-idle-probe-layout.txt
python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" "$PROBE_SRC" "$PROBE_DISASM" >/tmp/hp1020-idle-probe-safety.txt

cat <<EOF
HP 1020 idle-probe hardware test

Mode: $mode
Probe: $PROBE_DL

Layout check:
$(cat /tmp/hp1020-idle-probe-layout.txt)

Safety check:
$(cat /tmp/hp1020-idle-probe-safety.txt)

This script does not send a PDF, PostScript file, or ZjStream print stream.
EOF

if [[ "$mode" != "upload" ]]; then
  cat <<'EOF'

Dry run only. No printer was contacted.

For a real upload, power-cycle the printer first, then run with:
  HP1020_ALLOW_CUSTOM_FIRMWARE_UPLOAD=1 scripts/run-idle-probe-hardware-test.sh --upload --device-uri 'usb://...' --i-understand-this-uploads-custom-firmware
EOF
  exit 0
fi

if [[ "${HP1020_ALLOW_CUSTOM_FIRMWARE_UPLOAD:-}" != "1" ]]; then
  echo "refusing upload: set HP1020_ALLOW_CUSTOM_FIRMWARE_UPLOAD=1" >&2
  exit 2
fi
if [[ "$ack" -ne 1 ]]; then
  echo "refusing upload: missing --i-understand-this-uploads-custom-firmware" >&2
  exit 2
fi
if [[ -z "$device_uri" ]]; then
  echo "refusing upload: missing --device-uri" >&2
  exit 2
fi
case "$device_uri" in
  usb://*) ;;
  hp1020queue://*)
    echo "refusing upload: this is the normal print queue URI, not the direct USB backend URI" >&2
    exit 2
    ;;
  *)
    echo "refusing upload: --device-uri must be a direct usb:// URI" >&2
    exit 2
    ;;
esac
if [[ ! -x "$USB_BACKEND" ]]; then
  echo "missing CUPS USB backend: $USB_BACKEND" >&2
  exit 1
fi

run_with_timeout() {
  local seconds="$1"
  shift
  "$@" &
  local pid="$!"
  local elapsed=0
  while kill -0 "$pid" 2>/dev/null; do
    if (( elapsed >= seconds )); then
      kill -TERM "$pid" 2>/dev/null || true
      sleep 1
      kill -KILL "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      return 124
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  wait "$pid"
}

export DEVICE_URI="$device_uri"
echo
echo "Uploading idle probe only. Expect no paper movement. Power-cycle clears the result."
set +e
run_with_timeout 25 "$USB_BACKEND" 901 "${USER:-hp1020}" "HP1020 open idle probe" 1 "" "$PROBE_DL"
status="$?"
set -e
echo "USB backend exit status: $status"
if [[ "$status" -eq 124 ]]; then
  echo "Upload timed out. That may still mean bytes were sent; power-cycle before any normal printing."
fi
exit 0
