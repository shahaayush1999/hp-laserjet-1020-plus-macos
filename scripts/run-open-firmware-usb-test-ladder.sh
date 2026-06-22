#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mode="dry-run"
stage=""
device_uri="${DEVICE_URI:-}"
ack=0
stamp="$(date +%Y%m%d-%H%M%S)"
run_dir="$ROOT_DIR/analysis/open-firmware-probes/hardware-test-runs/$stamp"

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/run-open-firmware-usb-test-ladder.sh [--dry-run]
  scripts/run-open-firmware-usb-test-ladder.sh --upload --stage idle|snapshot|marker --device-uri 'usb://...' --i-understand-this-uploads-open-firmware

Default dry-run validates the offline probes and sends nothing to the printer.

Upload mode runs exactly one selected non-printing open-firmware probe stage and
captures host-side USB identity before and after. It does not print.

Actual upload also requires:
  HP1020_ALLOW_OPEN_FIRMWARE_LADDER_UPLOAD=1

Power-cycle the printer before each real stage. Use direct usb:// backend URIs,
not hp1020queue://localhost.
EOF
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) mode="dry-run"; shift ;;
    --upload) mode="upload"; shift ;;
    --stage) [[ $# -ge 2 ]] || usage; stage="$2"; shift 2 ;;
    --device-uri) [[ $# -ge 2 ]] || usage; device_uri="$2"; shift 2 ;;
    --output-dir) [[ $# -ge 2 ]] || usage; run_dir="$2"; shift 2 ;;
    --i-understand-this-uploads-open-firmware) ack=1; shift ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

case "$stage" in
  ""|idle|snapshot|marker) ;;
  *) echo "invalid --stage: $stage" >&2; usage ;;
esac

run_and_log() {
  local label="$1"
  local logfile="$2"
  shift 2
  echo "==> $label"
  "$@" >"$logfile" 2>&1
  tail -40 "$logfile"
}

identity_marker_count() {
  local matches_json="$1"
  if [[ ! -f "$matches_json" ]]; then
    printf '0\n'
    return 0
  fi
  python3 - "$matches_json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(errors="replace"))
except Exception:
    print(0)
    raise SystemExit(0)

def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)
    else:
        yield str(value)

count = sum(text.count("HP1020 OPEN MARKER") for text in walk(data))
print(count)
PY
}

write_summary() {
  local summary="$run_dir/summary.md"
  local marker_before="0"
  local marker_after="0"
  marker_before="$(identity_marker_count "$run_dir/identity-before/matches.json")"
  marker_after="$(identity_marker_count "$run_dir/identity-after/matches.json")"
  {
    printf '# HP 1020 Open Firmware USB Test Ladder Run\n\n'
    printf -- '- mode: `%s`\n' "$mode"
    printf -- '- stage: `%s`\n' "${stage:-dry-run-all}"
    printf -- '- run directory: `%s`\n' "$run_dir"
    if [[ "$mode" == "upload" ]]; then
      printf -- '- marker string before upload: `%s`\n' "$marker_before"
      printf -- '- marker string after upload: `%s`\n' "$marker_after"
    fi
    printf '\n'
    printf '## Files\n\n'
    find "$run_dir" -maxdepth 2 -type f | sort | sed "s#^$run_dir/#- #"
    printf '\n'
    printf '## Meaning\n\n'
    if [[ "$mode" == "upload" ]]; then
      printf 'One non-printing open-firmware stage was attempted. Check `identity-before/summary.md`, the stage log, and `identity-after/summary.md`.\n'
      if [[ "$stage" == "marker" ]]; then
        if [[ "$marker_after" != "0" ]]; then
          printf 'Marker result: macOS observed `HP1020 OPEN MARKER` after upload. That is the first useful proof that open code controlled USB descriptor response data.\n'
        else
          printf 'Marker result: macOS did not observe `HP1020 OPEN MARKER` after upload. That means descriptor control is still unproven; inspect logs before changing the firmware again.\n'
        fi
      fi
      printf 'Power-cycle the printer before normal printing or before another custom firmware stage.\n'
    else
      printf 'Dry-run only. No printer bytes were sent.\n'
    fi
  } >"$summary"
  printf '%s\n' "$summary"
}

mkdir -p "$run_dir"

if [[ "$mode" != "upload" ]]; then
  run_and_log "offline open-firmware validation" "$run_dir/offline-validation.log" \
    "$ROOT_DIR/scripts/validate-open-firmware-probes.sh"
  write_summary
  exit 0
fi

if [[ "${HP1020_ALLOW_OPEN_FIRMWARE_LADDER_UPLOAD:-}" != "1" ]]; then
  echo "refusing upload: set HP1020_ALLOW_OPEN_FIRMWARE_LADDER_UPLOAD=1" >&2
  exit 2
fi
if [[ "$ack" -ne 1 ]]; then
  echo "refusing upload: missing --i-understand-this-uploads-open-firmware" >&2
  exit 2
fi
if [[ -z "$stage" ]]; then
  echo "refusing upload: choose --stage idle, snapshot, or marker" >&2
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

run_and_log "identity before upload" "$run_dir/identity-before.log" \
  "$ROOT_DIR/scripts/capture-hp1020-usb-identity.sh" --output-dir "$run_dir/identity-before"

case "$stage" in
  idle)
    run_and_log "idle probe upload" "$run_dir/idle-upload.log" \
      env HP1020_ALLOW_CUSTOM_FIRMWARE_UPLOAD=1 \
      "$ROOT_DIR/scripts/run-idle-probe-hardware-test.sh" \
      --upload --device-uri "$device_uri" --i-understand-this-uploads-custom-firmware
    ;;
  snapshot)
    run_and_log "USB snapshot probe upload" "$run_dir/snapshot-upload.log" \
      env HP1020_ALLOW_USB_SNAPSHOT_UPLOAD=1 \
      "$ROOT_DIR/scripts/run-usb-snapshot-probe-hardware-test.sh" \
      --upload --device-uri "$device_uri" --i-understand-this-uploads-usb-snapshot-probe
    ;;
  marker)
    run_and_log "USB marker draft upload" "$run_dir/marker-upload.log" \
      env HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD=1 \
      "$ROOT_DIR/scripts/run-usb-marker-draft-hardware-test.sh" \
      --upload --device-uri "$device_uri" --i-understand-this-uploads-usb-marker-draft
    ;;
esac

run_and_log "identity after upload" "$run_dir/identity-after.log" \
  "$ROOT_DIR/scripts/capture-hp1020-usb-identity.sh" --output-dir "$run_dir/identity-after"

write_summary
