#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
stamp="$(date +%Y%m%d-%H%M%S)"
output_dir="$ROOT_DIR/analysis/usb-identity-captures/$stamp"

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/capture-hp1020-usb-identity.sh [--output-dir DIR]

Captures host-side macOS USB/printer identity evidence for HP LaserJet 1020
open-firmware tests. If libusb is available, it also sends standard USB
control-IN GET_DESCRIPTOR reads. It never sends print data.
EOF
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir) [[ $# -ge 2 ]] || usage; output_dir="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

mkdir -p "$output_dir"

lpinfo_out="$output_dir/lpinfo-v.txt"
spusb_json="$output_dir/system-profiler-spusb.json"
spusb_text="$output_dir/system-profiler-spusb.txt"
ioreg_out="$output_dir/ioreg-iousb.txt"
direct_json="$output_dir/direct-descriptors.json"
direct_md="$output_dir/direct-descriptors.md"
matches_json="$output_dir/matches.json"
summary="$output_dir/summary.md"

if command -v lpinfo >/dev/null 2>&1; then
  lpinfo -v >"$lpinfo_out" 2>&1 || true
else
  printf 'lpinfo not found\n' >"$lpinfo_out"
fi

if command -v system_profiler >/dev/null 2>&1; then
  system_profiler SPUSBDataType -json >"$spusb_json" 2>"$output_dir/system-profiler-spusb-json.stderr" || true
  system_profiler SPUSBDataType >"$spusb_text" 2>"$output_dir/system-profiler-spusb-text.stderr" || true
else
  printf '{}\n' >"$spusb_json"
  printf 'system_profiler not found\n' >"$spusb_text"
fi

if command -v ioreg >/dev/null 2>&1; then
  ioreg -p IOUSB -l -w0 >"$ioreg_out" 2>&1 || true
else
  printf 'ioreg not found\n' >"$ioreg_out"
fi

python3 "$ROOT_DIR/scripts/read-hp1020-usb-descriptors.py" \
  --json "$direct_json" \
  --output "$direct_md" \
  >"$output_dir/direct-descriptors.stdout" \
  2>"$output_dir/direct-descriptors.stderr" || true

python3 - "$spusb_json" "$lpinfo_out" "$ioreg_out" "$direct_json" "$matches_json" "$summary" <<'PY'
import json
import re
import sys
from pathlib import Path

spusb_path, lpinfo_path, ioreg_path, direct_path, matches_path, summary_path = map(Path, sys.argv[1:])

def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def walk_usb_items(value):
    if isinstance(value, dict):
        if "_name" in value:
            yield value
        for key in ("_items", "items"):
            for child in value.get(key, []) or []:
                yield from walk_usb_items(child)
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from walk_usb_items(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_usb_items(child)

def stringify(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)

def interesting_item(item):
    text = stringify(item).lower()
    needles = [
        "laserjet 1020",
        "hewlett-packard",
        "hp1020 open marker",
        "0x03f0",
        "0x2b17",
    ]
    return any(needle in text for needle in needles)

spusb = load_json(spusb_path)
direct = load_json(direct_path)
usb_matches = []
for item in walk_usb_items(spusb):
    if interesting_item(item):
        usb_matches.append(
            {
                "name": item.get("_name") or item.get("name"),
                "manufacturer": item.get("manufacturer"),
                "vendor_id": item.get("vendor_id"),
                "product_id": item.get("product_id"),
                "serial_num": item.get("serial_num"),
                "raw": item,
            }
        )

lpinfo_text = lpinfo_path.read_text(errors="replace")
ioreg_text = ioreg_path.read_text(errors="replace")
lpinfo_matches = [line for line in lpinfo_text.splitlines() if re.search(r"LaserJet|Hewlett|HP%20LaserJet|2b17|03f0|HP1020", line, re.I)]
ioreg_matches = [line.strip() for line in ioreg_text.splitlines() if re.search(r"LaserJet|Hewlett|HP1020 OPEN MARKER|idVendor|idProduct|USB Product Name", line, re.I)]

out = {
    "direct_descriptor_report": direct,
    "system_profiler_matches": usb_matches,
    "lpinfo_matches": lpinfo_matches,
    "ioreg_matching_lines": ioreg_matches[:200],
}
matches_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

lines = [
    "# HP 1020 USB Identity Capture",
    "",
    "This is host-side evidence plus standard USB descriptor reads. No print data, PJL, engine commands, or video/raster data were sent.",
    "",
    f"- system_profiler matches: `{len(usb_matches)}`",
    f"- lpinfo matches: `{len(lpinfo_matches)}`",
    f"- ioreg matching lines: `{len(ioreg_matches)}`",
    f"- direct descriptor status: `{direct.get('status', 'not_run')}`",
    "",
    "## Direct Descriptor Read",
    "",
    f"- report: `{direct_path.with_suffix('.md')}`",
    f"- status: `{direct.get('status', 'not_run')}`",
    f"- matching devices: `{len(direct.get('devices', []))}`",
    "",
    "## lpinfo Matches",
    "",
]
if lpinfo_matches:
    lines.extend(f"- `{line}`" for line in lpinfo_matches)
else:
    lines.append("- none")

lines.extend(["", "## system_profiler Matches", ""])
if usb_matches:
    for match in usb_matches:
        lines.append(
            f"- name=`{match.get('name')}` manufacturer=`{match.get('manufacturer')}` "
            f"vendor=`{match.get('vendor_id')}` product=`{match.get('product_id')}` "
            f"serial=`{match.get('serial_num')}`"
        )
else:
    lines.append("- none")

lines.extend(["", "## ioreg Matching Lines", ""])
if ioreg_matches:
    lines.extend(f"- `{line}`" for line in ioreg_matches[:40])
else:
    lines.append("- none")

summary_path.write_text("\n".join(lines) + "\n")
print(summary_path)
PY

printf '%s\n' "$summary"
