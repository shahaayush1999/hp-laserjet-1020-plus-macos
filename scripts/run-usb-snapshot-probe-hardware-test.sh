#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE_DL="$ROOT_DIR/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.dl"
PROBE_SRC="$ROOT_DIR/open-firmware/usb-register-snapshot"
PROBE_DISASM="$ROOT_DIR/analysis/open-firmware-probes/usb-register-snapshot/disassembly.txt"
USB_BACKEND="/usr/libexec/cups/backend/usb"

mode="dry-run"
device_uri="${DEVICE_URI:-}"
ack=0
timeout_seconds=25

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/run-usb-snapshot-probe-hardware-test.sh [--dry-run]
  scripts/run-usb-snapshot-probe-hardware-test.sh --upload --device-uri 'usb://...' --i-understand-this-uploads-usb-snapshot-probe

This uploads only the open USB register snapshot probe. It never sends a print job.
The URI must be the direct CUPS USB backend URI, not hp1020queue://localhost.
Actual upload also requires:
  HP1020_ALLOW_USB_SNAPSHOT_UPLOAD=1

This is the read-only USB-register step between the idle probe and the
write-capable USB marker draft.
EOF
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) mode="dry-run"; shift ;;
    --upload) mode="upload"; shift ;;
    --device-uri) [[ $# -ge 2 ]] || usage; device_uri="$2"; shift 2 ;;
    --timeout) [[ $# -ge 2 ]] || usage; timeout_seconds="$2"; shift 2 ;;
    --i-understand-this-uploads-usb-snapshot-probe) ack=1; shift ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

case "$timeout_seconds" in
  ''|*[!0-9]*) echo "invalid --timeout: $timeout_seconds" >&2; exit 2 ;;
esac

if [[ ! -f "$PROBE_DL" ]]; then
  echo "missing USB snapshot upload: $PROBE_DL" >&2
  echo "run scripts/build-open-firmware-usb-snapshot-probe.sh first" >&2
  exit 1
fi

layout_status="$(mktemp /tmp/hp1020-snapshot-layout.XXXXXX.txt)"
safety_status="$(mktemp /tmp/hp1020-snapshot-safety.XXXXXX.txt)"
usb_contract_status="$(mktemp /tmp/hp1020-snapshot-usb-contract.XXXXXX.txt)"
usb_access_status="$(mktemp /tmp/hp1020-snapshot-usb-access.XXXXXX.txt)"
trap 'rm -f "$layout_status" "$safety_status" "$usb_contract_status" "$usb_access_status"' EXIT

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" --profile boot-probe "$PROBE_DL" >"$layout_status"
python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" "$PROBE_SRC" "$PROBE_DISASM" >"$safety_status"
python3 "$ROOT_DIR/scripts/check-hp1020-usb-probe-contract.py" "$PROBE_SRC" "$PROBE_DISASM" >"$usb_contract_status"
python3 "$ROOT_DIR/scripts/check-hp1020-usb-mmio-accesses.py" "$PROBE_DISASM" >"$usb_access_status"

cat <<EOF
HP 1020 USB register snapshot hardware test

Mode: $mode
Probe: $PROBE_DL

Layout check:
$(cat "$layout_status")

Safety check:
$(cat "$safety_status")

USB contract check:
$(cat "$usb_contract_status")

USB access check:
$(cat "$usb_access_status")

This script does not send a PDF, PostScript file, ZjStream print stream, or
engine/video command. It uploads a custom firmware probe that reads mapped USB
registers into RAM and then idles.
EOF

if [[ "$mode" != "upload" ]]; then
  cat <<'EOF'

Dry run only. No printer was contacted.

For a real upload, power-cycle the printer first, run the idle probe first, then run with:
  HP1020_ALLOW_USB_SNAPSHOT_UPLOAD=1 scripts/run-usb-snapshot-probe-hardware-test.sh --upload --device-uri 'usb://...' --i-understand-this-uploads-usb-snapshot-probe
EOF
  exit 0
fi

if [[ "${HP1020_ALLOW_USB_SNAPSHOT_UPLOAD:-}" != "1" ]]; then
  echo "refusing upload: set HP1020_ALLOW_USB_SNAPSHOT_UPLOAD=1" >&2
  exit 2
fi
if [[ "$ack" -ne 1 ]]; then
  echo "refusing upload: missing --i-understand-this-uploads-usb-snapshot-probe" >&2
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
echo "Uploading USB snapshot probe only. Expect no paper movement. Power-cycle clears the result."
set +e
run_with_timeout "$timeout_seconds" "$USB_BACKEND" 903 "${USER:-hp1020}" "HP1020 open USB snapshot probe" 1 "" "$PROBE_DL"
status="$?"
set -e
echo "USB backend exit status: $status"
if [[ "$status" -eq 124 ]]; then
  echo "Upload timed out. That may still mean bytes were sent; power-cycle before any normal printing."
fi
exit 0
