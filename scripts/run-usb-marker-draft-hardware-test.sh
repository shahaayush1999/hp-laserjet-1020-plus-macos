#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE_DL="$ROOT_DIR/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.dl"
PROBE_SRC="$ROOT_DIR/open-firmware/usb-marker-draft"
PROBE_DISASM="$ROOT_DIR/analysis/open-firmware-probes/usb-marker-draft/disassembly.txt"
USB_BACKEND="/usr/libexec/cups/backend/usb"

mode="dry-run"
device_uri="${DEVICE_URI:-}"
ack=0
timeout_seconds=25

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/run-usb-marker-draft-hardware-test.sh [--dry-run]
  scripts/run-usb-marker-draft-hardware-test.sh --upload --device-uri 'usb://...' --i-understand-this-uploads-usb-marker-draft

This uploads only the open USB marker draft. It never sends a print job.
The URI must be the direct CUPS USB backend URI, not hp1020queue://localhost.
Actual upload also requires:
  HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD=1

This is a later-stage USB-only write-capable probe. Run stock/idle/read-only
USB checks first.
EOF
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) mode="dry-run"; shift ;;
    --upload) mode="upload"; shift ;;
    --device-uri) [[ $# -ge 2 ]] || usage; device_uri="$2"; shift 2 ;;
    --timeout) [[ $# -ge 2 ]] || usage; timeout_seconds="$2"; shift 2 ;;
    --i-understand-this-uploads-usb-marker-draft) ack=1; shift ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

case "$timeout_seconds" in
  ''|*[!0-9]*) echo "invalid --timeout: $timeout_seconds" >&2; exit 2 ;;
esac

if [[ ! -f "$PROBE_DL" ]]; then
  echo "missing marker draft upload: $PROBE_DL" >&2
  echo "run scripts/build-open-firmware-usb-marker-draft.sh first" >&2
  exit 1
fi

layout_status="$(mktemp /tmp/hp1020-marker-layout.XXXXXX.txt)"
safety_status="$(mktemp /tmp/hp1020-marker-safety.XXXXXX.txt)"
usb_contract_status="$(mktemp /tmp/hp1020-marker-usb-contract.XXXXXX.txt)"
usb_access_status="$(mktemp /tmp/hp1020-marker-usb-access.XXXXXX.txt)"
endpoint0_status="$(mktemp /tmp/hp1020-marker-endpoint0.XXXXXX.txt)"
trap 'rm -f "$layout_status" "$safety_status" "$usb_contract_status" "$usb_access_status" "$endpoint0_status"' EXIT

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" --profile boot-probe "$PROBE_DL" >"$layout_status"
python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" "$PROBE_SRC" "$PROBE_DISASM" >"$safety_status"
python3 "$ROOT_DIR/scripts/check-hp1020-usb-probe-contract.py" "$PROBE_SRC" "$PROBE_DISASM" >"$usb_contract_status"
python3 "$ROOT_DIR/scripts/check-hp1020-usb-mmio-accesses.py" --allow-usb-writes "$PROBE_DISASM" >"$usb_access_status"
python3 "$ROOT_DIR/scripts/check-hp1020-endpoint0-sequence.py" "$PROBE_DISASM" >"$endpoint0_status"

cat <<EOF
HP 1020 USB marker draft hardware test

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

Endpoint-0 sequence check:
$(cat "$endpoint0_status")

This script does not send a PDF, PostScript file, ZjStream print stream, or
engine/video command. It uploads a USB-only custom firmware draft.
EOF

if [[ "$mode" != "upload" ]]; then
  cat <<'EOF'

Dry run only. No printer was contacted.

For a real upload, power-cycle the printer first, run safer stock/idle/read-only
checks first, then run with:
  HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD=1 scripts/run-usb-marker-draft-hardware-test.sh --upload --device-uri 'usb://...' --i-understand-this-uploads-usb-marker-draft
EOF
  exit 0
fi

if [[ "${HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD:-}" != "1" ]]; then
  echo "refusing upload: set HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD=1" >&2
  exit 2
fi
if [[ "$ack" -ne 1 ]]; then
  echo "refusing upload: missing --i-understand-this-uploads-usb-marker-draft" >&2
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
echo "Uploading USB marker draft only. Expect no paper movement. Power-cycle clears the result."
set +e
run_with_timeout "$timeout_seconds" "$USB_BACKEND" 902 "${USER:-hp1020}" "HP1020 open USB marker draft" 1 "" "$PROBE_DL"
status="$?"
set -e
echo "USB backend exit status: $status"
if [[ "$status" -eq 124 ]]; then
  echo "Upload timed out. That may still mean bytes were sent; power-cycle before any normal printing."
fi
exit 0
