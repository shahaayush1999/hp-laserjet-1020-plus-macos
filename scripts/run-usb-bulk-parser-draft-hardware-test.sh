#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_SCRIPT="$ROOT_DIR/scripts/build-open-firmware-usb-bulk-parser-draft.sh"
PROBE_DL="$ROOT_DIR/analysis/open-firmware-probes/usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.dl"
RESULTS_JSON="$ROOT_DIR/analysis/open-firmware-probes/usb-bulk-parser-draft/deterministic-test-results.json"
DESCRIPTOR_READER="$ROOT_DIR/scripts/read-hp1020-usb-descriptors.py"
USB_BACKEND="/usr/libexec/cups/backend/usb"

EXPECTED_BEFORE="HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000"
EXPECTED_AFTER="HP1020 B=00000024 D=00000001 C=00000002 E=00000000 U=00000000"
PAYLOAD_SHA256="935c947d40c020007ecf88534956defbd9e1764bde63708e025a2897a597978d"

mode="dry-run"
mode_seen=""
send_probe_data=0
device_uri=""
timeout_seconds=25
settle_seconds=2
output_dir=""

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/run-usb-bulk-parser-draft-hardware-test.sh [--dry-run] [--send-probe-data]
  scripts/run-usb-bulk-parser-draft-hardware-test.sh --upload --device-uri 'usb://...' [--send-probe-data]

Default mode rebuilds and validates the draft and the inert payload offline. It
does not enumerate USB, read descriptors, invoke a USB backend, upload firmware,
or send data.

Upload mode sends only the custom bulk/parser draft .dl and then reads its
product descriptor. It requires both --upload and exactly:
  HP1020_ALLOW_USB_BULK_PARSER_UPLOAD=1

The optional 36-byte START_DOC/END_DOC-only data step additionally requires
both --send-probe-data and exactly:
  HP1020_ALLOW_USB_BULK_PARSER_DATA=1

Options:
  --dry-run              Offline build, validation, and payload check only.
  --upload               Enable the guarded custom firmware upload path.
  --send-probe-data      Request the separately guarded inert data step.
  --device-uri URI       Explicit direct usb:// CUPS backend URI.
  --timeout SECONDS      USB backend timeout per send; default 25.
  --settle-seconds N     Delay before each descriptor read; default 2.
  --output-dir DIR       Preserve logs and descriptor captures in DIR.
  -h, --help             Show this help.

The hp1020queue://localhost working queue is never accepted or selected.
Recovery after any upload attempt is a printer power cycle.
EOF
}

die() {
  printf '%s\n' "$*" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      [[ "$mode_seen" != "upload" ]] || die "--dry-run and --upload are mutually exclusive"
      mode="dry-run"
      mode_seen="dry-run"
      shift
      ;;
    --upload)
      [[ "$mode_seen" != "dry-run" ]] || die "--dry-run and --upload are mutually exclusive"
      mode="upload"
      mode_seen="upload"
      shift
      ;;
    --send-probe-data)
      send_probe_data=1
      shift
      ;;
    --device-uri)
      [[ $# -ge 2 ]] || die "--device-uri requires a value"
      device_uri="$2"
      shift 2
      ;;
    --timeout)
      [[ $# -ge 2 ]] || die "--timeout requires a value"
      timeout_seconds="$2"
      shift 2
      ;;
    --settle-seconds)
      [[ $# -ge 2 ]] || die "--settle-seconds requires a value"
      settle_seconds="$2"
      shift 2
      ;;
    --output-dir)
      [[ $# -ge 2 && -n "$2" ]] || die "--output-dir requires a non-empty value"
      output_dir="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      die "unknown option: $1"
      ;;
  esac
done

case "$timeout_seconds" in
  ''|*[!0-9]*) die "invalid --timeout: $timeout_seconds" ;;
esac
[[ "$timeout_seconds" -gt 0 ]] || die "--timeout must be greater than zero"
case "$settle_seconds" in
  ''|*[!0-9]*) die "invalid --settle-seconds: $settle_seconds" ;;
esac

if [[ -n "$device_uri" ]]; then
  case "$device_uri" in
    usb://?*) ;;
    hp1020queue://*) die "refusing URI: hp1020queue is the working print queue, not a direct USB backend URI" ;;
    *) die "refusing URI: --device-uri must use the direct usb:// scheme" ;;
  esac
fi

# All dangerous-mode guards are resolved before the offline build. A rejected
# invocation therefore cannot reach either USB-facing command below.
if [[ "$mode" == "upload" ]]; then
  [[ "${HP1020_ALLOW_USB_BULK_PARSER_UPLOAD:-}" == "1" ]] || \
    die "refusing upload: set HP1020_ALLOW_USB_BULK_PARSER_UPLOAD=1 exactly"
  [[ -n "$device_uri" ]] || die "refusing upload: pass an explicit direct --device-uri 'usb://...'"
  if [[ "$send_probe_data" -eq 1 ]]; then
    [[ "${HP1020_ALLOW_USB_BULK_PARSER_DATA:-}" == "1" ]] || \
      die "refusing probe data: set HP1020_ALLOW_USB_BULK_PARSER_DATA=1 exactly"
  fi
fi

tmp_dir="$(mktemp -d /tmp/hp1020-usb-bulk-parser-harness.XXXXXX)"
recovery_required=0
cleanup() {
  rm -rf "$tmp_dir"
  if [[ "$recovery_required" -eq 1 ]]; then
    printf '\nPower-cycle the printer before normal printing or another firmware test.\n' >&2
    printf 'The custom firmware is volatile; no proprietary runtime or working queue was changed.\n' >&2
  fi
}
trap cleanup EXIT

if [[ -n "$output_dir" ]]; then
  run_dir="$output_dir"
elif [[ "$mode" == "upload" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  run_dir="$ROOT_DIR/analysis/open-firmware-probes/usb-bulk-parser-draft/hardware-test-runs/$stamp"
else
  run_dir="$tmp_dir"
fi
mkdir -p "$run_dir"

build_log="$run_dir/offline-build.log"
printf 'Running offline bulk/parser build and validation first.\n'
if ! "$BUILD_SCRIPT" >"$build_log" 2>&1; then
  printf 'offline build or validation failed; no USB command was run\n' >&2
  tail -40 "$build_log" >&2
  exit 1
fi

[[ -f "$PROBE_DL" ]] || {
  printf 'missing custom upload after build: %s\n' "$PROBE_DL" >&2
  exit 1
}
[[ -f "$RESULTS_JSON" ]] || {
  printf 'missing deterministic results after build: %s\n' "$RESULTS_JSON" >&2
  exit 1
}

offline_gate="$run_dir/offline-gate.txt"
python3 - "$RESULTS_JSON" "$PROBE_DL" >"$offline_gate" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
probe = Path(sys.argv[2])
data = json.loads(path.read_text())
if data.get("status") != "pass":
    raise SystemExit("deterministic test result is not pass")
if data.get("hardware_contact") is not False:
    raise SystemExit("offline build did not record hardware_contact=false")
reports = data.get("reports", {})
if not reports:
    raise SystemExit("deterministic result contains no generated report statuses")
failed = sorted(name for name, status in reports.items() if status != "pass")
if failed:
    raise SystemExit("failed generated reports: " + ", ".join(failed))
expected_digest = data.get("artifacts", {}).get("dl", {}).get("sha256")
actual_digest = hashlib.sha256(probe.read_bytes()).hexdigest()
if actual_digest != expected_digest:
    raise SystemExit("custom .dl does not match the validated deterministic result")
print(f"status=pass reports={len(reports)} hardware_contact=false")
print(f"dl_sha256={actual_digest}")
PY

probe_payload="$run_dir/inert-start-end-doc.zjs"
payload_check="$run_dir/inert-start-end-doc-check.txt"
python3 - "$probe_payload" "$PAYLOAD_SHA256" >"$payload_check" <<'PY'
import hashlib
import struct
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_sha256 = sys.argv[2]
header = struct.Struct(">IIIHH")
payload = b"JZJZ" + header.pack(16, 0, 0, 0, 0x5A5A) + header.pack(16, 1, 0, 0, 0x5A5A)
path.write_bytes(payload)

chunks = [header.unpack_from(payload, 4), header.unpack_from(payload, 20)]
expected = [(16, 0, 0, 0, 0x5A5A), (16, 1, 0, 0, 0x5A5A)]
digest = hashlib.sha256(payload).hexdigest()
if len(payload) != 36 or payload[:4] != b"JZJZ" or chunks != expected:
    raise SystemExit("inert payload structure check failed")
if digest != expected_sha256:
    raise SystemExit(f"inert payload digest mismatch: {digest}")

print("status=pass bytes=36 magic=JZJZ")
print("chunk_1=START_DOC total_size=16 items=0 reserved=0 signature=0x5a5a")
print("chunk_2=END_DOC total_size=16 items=0 reserved=0 signature=0x5a5a")
print("page_chunks=0 raster_bytes=0 engine_or_video_commands=0")
print(f"sha256={digest}")
print(f"hex={payload.hex()}")
PY

cat <<EOF
HP 1020 USB bulk/parser draft hardware harness

Mode: $mode
Custom upload: $PROBE_DL
Probe data requested: $send_probe_data

Offline gate:
$(cat "$offline_gate")

Inert payload gate:
$(cat "$payload_check")

Expected product string before data:
$EXPECTED_BEFORE

Expected product string after the one-descriptor 36-byte data step:
$EXPECTED_AFTER

B=bytes, D=completed bulk receive descriptors, C=recognized chunks,
E=parser errors, and U=unknown chunks. No START_PAGE, END_PAGE, image,
raster, engine, video, motor, fuser, laser, or paper-feed command is present.
EOF

if [[ "$mode" != "upload" ]]; then
  cat <<'EOF'

Dry run complete. No USB device was enumerated, no descriptor was read, the
CUPS USB backend was not invoked, and no firmware or probe data was sent.
Environment opt-ins do not change dry-run mode without --upload.
EOF
  exit 0
fi

[[ -x "$USB_BACKEND" ]] || {
  printf 'missing CUPS USB backend: %s\n' "$USB_BACKEND" >&2
  exit 1
}
[[ -f "$DESCRIPTOR_READER" ]] || {
  printf 'missing direct descriptor reader: %s\n' "$DESCRIPTOR_READER" >&2
  exit 1
}

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

send_backend_file() {
  local file_prefix="$1"
  local job_id="$2"
  local title="$3"
  local input_file="$4"
  run_with_timeout "$timeout_seconds" \
    env DEVICE_URI="$device_uri" \
    "$USB_BACKEND" "$job_id" "${USER:-hp1020}" "$title" 1 "" "$input_file" \
    >"$run_dir/$file_prefix.stdout" \
    2>"$run_dir/$file_prefix.stderr" \
    3>"$run_dir/$file_prefix.backchannel.bin"
}

capture_counter_marker() {
  local label="$1"
  local json_path="$run_dir/$label-descriptors.json"
  local markdown_path="$run_dir/$label-descriptors.md"
  local product_path="$run_dir/$label-product.txt"

  python3 "$DESCRIPTOR_READER" \
    --json "$json_path" \
    --output "$markdown_path" \
    >"$run_dir/$label-descriptors.stdout" \
    2>"$run_dir/$label-descriptors.stderr"

  python3 - "$json_path" >"$product_path" <<'PY'
import json
import re
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
pattern = re.compile(
    r"^HP1020 B=[0-9A-F]{8} D=[0-9A-F]{8} C=[0-9A-F]{8} "
    r"E=[0-9A-F]{8} U=[0-9A-F]{8}$"
)
device_markers = []
for device in data.get("devices", []):
    matches = []
    for item in device.get("control_reads", []):
        text = item.get("text")
        if item.get("name") in {"product_first", "product"} and isinstance(text, str) and pattern.fullmatch(text):
            matches.append(text)
    unique = list(dict.fromkeys(matches))
    if len(unique) > 1:
        raise SystemExit(f"one device returned changing bulk counter strings: {unique!r}")
    if unique:
        device_markers.append(unique[0])
if len(device_markers) != 1:
    raise SystemExit(f"expected one HP device with a stable bulk counter string, found {device_markers!r}")
print(device_markers[0])
PY
}

summary="$run_dir/summary.md"
cat >"$summary" <<EOF
# HP 1020 USB Bulk Parser Hardware Run

- mode: \`upload\`
- custom firmware: \`$PROBE_DL\`
- optional inert data requested: \`$send_probe_data\`
- expected before data: \`$EXPECTED_BEFORE\`
- expected after data: \`$EXPECTED_AFTER\`
- working queue used: \`no\`
- proprietary firmware sent or changed: \`no\`

The only possible data payload is the validated 36-byte START_DOC/END_DOC-only
stream recorded as \`inert-start-end-doc.zjs\`. Recovery is a printer power cycle.
EOF

printf '\nUploading only the custom USB bulk/parser draft .dl. Expect no mechanical activity.\n'
recovery_required=1
set +e
send_backend_file "custom-upload" 905 "HP1020 open USB bulk parser draft" "$PROBE_DL"
upload_status="$?"
set -e
printf '%s\n' "$upload_status" >"$run_dir/custom-upload-exit-status.txt"
printf 'Custom upload backend exit status: %s\n' "$upload_status"
if [[ "$upload_status" -eq 124 ]]; then
  printf 'Upload timed out; bytes may still have been sent. Descriptor evidence decides execution.\n'
fi

if [[ "$settle_seconds" -gt 0 ]]; then
  sleep "$settle_seconds"
fi

printf 'Reading the product descriptor counter marker before any probe data.\n'
set +e
capture_counter_marker "before-data"
before_capture_status="$?"
set -e
before_marker="not observed"
if [[ "$before_capture_status" -eq 0 && -s "$run_dir/before-data-product.txt" ]]; then
  before_marker="$(cat "$run_dir/before-data-product.txt")"
fi
printf 'Observed before data: %s\n' "$before_marker"

cat >>"$summary" <<EOF

## Upload And Initial Descriptor

- USB backend exit status: \`$upload_status\`
- descriptor capture status: \`$before_capture_status\`
- observed before data: \`$before_marker\`
EOF

if [[ "$before_marker" != "$EXPECTED_BEFORE" ]]; then
  cat >>"$summary" <<'EOF'

The exact zero-counter marker was not observed. No probe data was sent, so bulk
receive and parser execution remain unproven.
EOF
  printf 'initial marker mismatch: no probe data was sent\n' >&2
  printf 'Run evidence: %s\n' "$summary" >&2
  exit 1
fi

if [[ "$send_probe_data" -ne 1 ]]; then
  cat >>"$summary" <<'EOF'

The zero-counter product marker proves the custom endpoint-0 response path ran.
No bulk probe data was requested or sent; bulk receive/parser execution remains
untested.
EOF
  printf 'Zero-counter marker matched. No probe data was requested or sent.\n'
  printf 'Run evidence: %s\n' "$summary"
  exit 0
fi

printf 'Sending exactly 36 inert bytes: JZJZ, START_DOC, END_DOC. No page chunk exists.\n'
set +e
send_backend_file "probe-data" 906 "HP1020 inert START_DOC END_DOC parser probe" "$probe_payload"
data_status="$?"
set -e
printf '%s\n' "$data_status" >"$run_dir/probe-data-exit-status.txt"
printf 'Probe data backend exit status: %s\n' "$data_status"

if [[ "$settle_seconds" -gt 0 ]]; then
  sleep "$settle_seconds"
fi

printf 'Reading the product descriptor counter marker after probe data.\n'
set +e
capture_counter_marker "after-data"
after_capture_status="$?"
set -e
after_marker="not observed"
if [[ "$after_capture_status" -eq 0 && -s "$run_dir/after-data-product.txt" ]]; then
  after_marker="$(cat "$run_dir/after-data-product.txt")"
fi
printf 'Observed after data: %s\n' "$after_marker"

cat >>"$summary" <<EOF

## Inert Data And Final Descriptor

- probe data backend exit status: \`$data_status\`
- descriptor capture status: \`$after_capture_status\`
- observed after data: \`$after_marker\`
EOF

if [[ "$after_marker" == "$EXPECTED_AFTER" ]]; then
  cat >>"$summary" <<'EOF'

The exact final marker proves one bulk descriptor delivered all 36 bytes and
the inert parser recognized START_DOC and END_DOC with no parser error or
unknown chunk. It does not prove or exercise printing.
EOF
  printf 'Exact post-data counter marker matched. Bulk receive and inert framing are proven.\n'
  printf 'Run evidence: %s\n' "$summary"
  exit 0
fi

cat >>"$summary" <<'EOF'

The exact final marker did not match. Preserve these captures as useful USB or
parser evidence, but do not claim the expected one-descriptor framing path was
proven.
EOF
printf 'post-data marker mismatch; expected: %s\n' "$EXPECTED_AFTER" >&2
printf 'Run evidence: %s\n' "$summary" >&2
exit 1
