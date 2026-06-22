#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USB_BACKEND="/usr/libexec/cups/backend/usb"
STOCK_FIRMWARE="$ROOT_DIR/assets/runtime/sihp1020.dl"

mode="dry-run"
device_uri="${DEVICE_URI:-}"
query="echo"
timeout_seconds=15
post_preload_sleep=2
preload_stock=0
output_dir=""

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/query-hp1020-pjl-status.sh [--dry-run] [--query echo|info-status|info-id|ustatus-device]
  scripts/query-hp1020-pjl-status.sh --send --device-uri 'usb://...' [--preload-stock-firmware]

This sends a tiny non-printing PJL/status payload through the direct CUPS USB
backend and captures back-channel bytes from CUPS fd 3.

It never sends a PDF, PostScript file, or ZjStream print stream.
The URI must be the direct CUPS USB URI, not hp1020queue://localhost.

Actual USB send requires:
  HP1020_ALLOW_NONPRINTING_USB_QUERY=1

Options:
  --dry-run                  Build payload and report only; default.
  --send                     Send the selected payload to the printer.
  --device-uri URI           Direct usb:// CUPS backend URI.
  --query NAME               echo, info-status, info-id, or ustatus-device.
  --preload-stock-firmware   Send bundled HP firmware first, then query PJL.
  --post-preload-sleep N     Seconds to wait after firmware preload; default 2.
  --timeout SECONDS          Backend timeout per send; default 15.
  --output-dir DIR           Run output directory.
EOF
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) mode="dry-run"; shift ;;
    --send) mode="send"; shift ;;
    --device-uri) [[ $# -ge 2 ]] || usage; device_uri="$2"; shift 2 ;;
    --query) [[ $# -ge 2 ]] || usage; query="$2"; shift 2 ;;
    --preload-stock-firmware) preload_stock=1; shift ;;
    --post-preload-sleep) [[ $# -ge 2 ]] || usage; post_preload_sleep="$2"; shift 2 ;;
    --timeout) [[ $# -ge 2 ]] || usage; timeout_seconds="$2"; shift 2 ;;
    --output-dir) [[ $# -ge 2 ]] || usage; output_dir="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

case "$query" in
  echo|info-status|info-id|ustatus-device) ;;
  *) echo "unsupported query: $query" >&2; usage ;;
esac

case "$timeout_seconds" in
  ''|*[!0-9]*) echo "invalid --timeout: $timeout_seconds" >&2; exit 2 ;;
esac
case "$post_preload_sleep" in
  ''|*[!0-9]*) echo "invalid --post-preload-sleep: $post_preload_sleep" >&2; exit 2 ;;
esac

if [[ -z "$output_dir" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  output_dir="$ROOT_DIR/analysis/non-printing-status-probe/runs/$stamp-$query"
fi
mkdir -p "$output_dir"

payload="$output_dir/payload.bin"
payload_hex="$output_dir/payload.hex"
payload_text="$output_dir/payload-printable.txt"
run_summary="$output_dir/summary.md"

python3 "$ROOT_DIR/scripts/model-hp1020-pjl-status-contract.py" \
  --write-payload "$query" \
  --payload-output "$payload" \
  --text-output "$payload_text" >/tmp/hp1020-pjl-payload-status.txt

if command -v xxd >/dev/null 2>&1; then
  xxd -g 1 "$payload" > "$payload_hex"
else
  od -An -tx1 -v "$payload" > "$payload_hex"
fi

payload_bytes="$(wc -c < "$payload" | tr -d ' ')"

cat > "$run_summary" <<EOF
# HP 1020 Non-Printing PJL Status Query

- Mode: \`$mode\`
- Query: \`$query\`
- Payload bytes: \`$payload_bytes\`
- Preload stock firmware first: \`$preload_stock\`
- Post-preload sleep: \`$post_preload_sleep\`
- Device URI: \`${device_uri:-not set}\`
- Payload: \`$payload\`
- Back-channel capture: \`backchannel.bin\`

This probe sends only PJL/status text. It does not send PDF, PostScript,
ZjStream raster data, or engine/video commands.

## Payload

\`\`\`text
$(cat "$payload_text")
\`\`\`
EOF

echo "HP 1020 non-printing PJL/status query"
echo "Mode: $mode"
echo "Query: $query"
echo "Payload bytes: $payload_bytes"
echo "Output: $output_dir"

if [[ "$mode" != "send" ]]; then
  cat <<'EOF'

Dry run only. No printer was contacted.

For hardware use, connect the printer and pass the direct usb:// URI:
  HP1020_ALLOW_NONPRINTING_USB_QUERY=1 scripts/query-hp1020-pjl-status.sh --send --device-uri 'usb://...' --preload-stock-firmware
EOF
  exit 0
fi

if [[ "${HP1020_ALLOW_NONPRINTING_USB_QUERY:-}" != "1" ]]; then
  echo "refusing send: set HP1020_ALLOW_NONPRINTING_USB_QUERY=1" >&2
  exit 2
fi
if [[ -z "$device_uri" ]]; then
  echo "refusing send: missing --device-uri" >&2
  exit 2
fi
case "$device_uri" in
  usb://*) ;;
  hp1020queue://*)
    echo "refusing send: this is the normal print queue URI, not the direct USB backend URI" >&2
    exit 2
    ;;
  *)
    echo "refusing send: --device-uri must be a direct usb:// URI" >&2
    exit 2
    ;;
esac
if [[ ! -x "$USB_BACKEND" ]]; then
  echo "missing CUPS USB backend: $USB_BACKEND" >&2
  exit 1
fi
if [[ "$preload_stock" -eq 1 && ! -f "$STOCK_FIRMWARE" ]]; then
  echo "missing stock firmware: $STOCK_FIRMWARE" >&2
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

send_file() {
  local label="$1"
  local file="$2"
  local stdout_path="$3"
  local stderr_path="$4"
  local backchannel_path="$5"

  export DEVICE_URI="$device_uri"
  set +e
  run_with_timeout "$timeout_seconds" "$USB_BACKEND" 904 "${USER:-hp1020}" "$label" 1 "" "$file" \
    >"$stdout_path" 2>"$stderr_path" 3>"$backchannel_path"
  local status="$?"
  set -e
  return "$status"
}

if [[ "$preload_stock" -eq 1 ]]; then
  echo "Preloading stock HP firmware only; no print data."
  set +e
  send_file "HP1020 stock firmware preload for PJL query" "$STOCK_FIRMWARE" \
    "$output_dir/preload-stdout.txt" "$output_dir/preload-stderr.txt" "$output_dir/preload-backchannel.bin"
  preload_status="$?"
  set -e
  echo "$preload_status" > "$output_dir/preload-exit-status.txt"
  if [[ "$post_preload_sleep" -gt 0 ]]; then
    echo "Waiting $post_preload_sleep seconds for firmware startup."
    sleep "$post_preload_sleep"
  fi
else
  preload_status="not-run"
fi

echo "Sending PJL/status payload only."
set +e
send_file "HP1020 PJL status query $query" "$payload" \
  "$output_dir/query-stdout.txt" "$output_dir/query-stderr.txt" "$output_dir/backchannel.bin"
query_status="$?"
set -e
echo "$query_status" > "$output_dir/query-exit-status.txt"

backchannel_bytes="$(wc -c < "$output_dir/backchannel.bin" | tr -d ' ')"

cat >> "$run_summary" <<EOF

## Result

- Preload exit status: \`$preload_status\`
- Query exit status: \`$query_status\`
- Captured query back-channel bytes: \`$backchannel_bytes\`

Relevant files:

- \`query-stdout.txt\`
- \`query-stderr.txt\`
- \`backchannel.bin\`
- \`backchannel-analysis.md\`
- \`preload-stderr.txt\` if stock firmware preload was used
EOF

if [[ "$backchannel_bytes" -gt 0 ]]; then
  if command -v xxd >/dev/null 2>&1; then
    xxd -g 1 "$output_dir/backchannel.bin" > "$output_dir/backchannel.hex"
  else
    od -An -tx1 -v "$output_dir/backchannel.bin" > "$output_dir/backchannel.hex"
  fi
  python3 - "$output_dir/backchannel.bin" "$output_dir/backchannel-printable.txt" <<'PY'
import sys
from pathlib import Path
data = Path(sys.argv[1]).read_bytes()
printable = "".join(chr(b) if 32 <= b <= 126 or b in (10, 13, 9) else "." for b in data)
Path(sys.argv[2]).write_text(printable, encoding="ascii", errors="replace")
PY
fi

python3 "$ROOT_DIR/scripts/analyze-hp1020-pjl-status-capture.py" \
  --query "$query" \
  --capture "$output_dir/backchannel.bin" \
  --stderr "$output_dir/query-stderr.txt" \
  --json-output "$output_dir/backchannel-analysis.json" \
  --markdown-output "$output_dir/backchannel-analysis.md"

echo "Query exit status: $query_status"
echo "Back-channel bytes captured: $backchannel_bytes"
echo "Run summary: $run_summary"

exit 0
