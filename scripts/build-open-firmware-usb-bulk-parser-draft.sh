#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/open-firmware/usb-bulk-parser-draft"
OUT_DIR="$ROOT_DIR/analysis/open-firmware-probes/usb-bulk-parser-draft"
NAME="hp1020-usb-bulk-parser-draft"
DATE_PREFIX="20260712"

manual_prefix="/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf"
ctng_prefix="/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf"
prefix="${XTENSA_PREFIX:-}"
if [[ -z "$prefix" ]]; then
  if [[ -x "${manual_prefix}-as" ]]; then
    prefix="$manual_prefix"
  else
    prefix="$ctng_prefix"
  fi
fi

python3 "$ROOT_DIR/scripts/check-xtensa-instruction-encoding.py" --prefix "$prefix"

as_tool="${prefix}-as"
ld_tool="${prefix}-ld"
readelf_tool="${prefix}-readelf"
objdump_tool="${prefix}-objdump"
for tool in "$as_tool" "$ld_tool" "$readelf_tool" "$objdump_tool"; do
  if [[ ! -x "$tool" ]] || ! "$tool" --version >/dev/null 2>&1; then
    printf 'missing or unusable tool: %s\n' "$tool" >&2
    printf 'Run scripts/build-xtensa-binutils-manual.sh or set XTENSA_PREFIX.\n' >&2
    exit 1
  fi
done

mkdir -p "$OUT_DIR"

obj="$OUT_DIR/$NAME.o"
toolchain_elf="$OUT_DIR/$NAME.toolchain-machine.elf"
elf="$OUT_DIR/$NAME.elf"
img="$OUT_DIR/$NAME.img"
dl="$OUT_DIR/$NAME.dl"
map="$OUT_DIR/$NAME.map"
readelf_txt="$OUT_DIR/readelf.txt"
disasm_txt="$OUT_DIR/disassembly.txt"

cleanup() {
  rm -f "$obj" "$toolchain_elf"
}
trap cleanup EXIT

"$as_tool" -o "$obj" "$SRC_DIR/usb-bulk-parser.S"
"$ld_tool" -T "$SRC_DIR/hp1020-usb-bulk-parser.ld" -Map "$map" -o "$toolchain_elf" "$obj"
cp "$toolchain_elf" "$elf"
python3 - "$elf" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = bytearray(path.read_bytes())
if data[:4] != b"\x7fELF" or data[4:6] != b"\x01\x02":
    raise SystemExit("expected ELF32 big-endian")
data[18:20] = (0xABC7).to_bytes(2, "big")
path.write_bytes(data)
PY

python3 - "$elf" "$img" "$DATE_PREFIX" <<'PY'
import sys
from pathlib import Path

elf, img, prefix = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].encode("ascii")
if len(prefix) != 8 or not prefix.isdigit():
    raise SystemExit("date prefix must be eight ASCII digits")
img.write_bytes(prefix + elf.read_bytes())
PY

python3 "$ROOT_DIR/scripts/wrap-firmware-acl.py" "$img" "$dl"
"$readelf_tool" -h -l -S "$elf" > "$readelf_txt"
"$objdump_tool" -d "$elf" > "$disasm_txt"

python3 "$ROOT_DIR/scripts/model-hp1020-usb-bulk-probe-contract.py"
python3 "$ROOT_DIR/scripts/model-hp1020-usb-bulk-parser-draft.py"
XTENSA_PREFIX="$prefix" python3 "$ROOT_DIR/scripts/check-hp1020-assembled-parser.py"

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
  --profile boot-probe \
  --markdown-output "$OUT_DIR/layout.md" \
  --json-output "$OUT_DIR/layout.json" \
  "$dl"

python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$OUT_DIR/safety-scan.md" \
  --json "$OUT_DIR/safety-scan.json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-probe-contract.py" \
  --mmio-map "$ROOT_DIR/analysis/usb-path/usb-bulk-probe-contract.json" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$OUT_DIR/usb-contract-scan.md" \
  --json "$OUT_DIR/usb-contract-scan.json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-mmio-accesses.py" \
  --allow-usb-writes \
  --mmio-map "$ROOT_DIR/analysis/usb-path/usb-bulk-probe-contract.json" \
  "$disasm_txt" \
  -o "$OUT_DIR/usb-mmio-access-scan.md" \
  --json "$OUT_DIR/usb-mmio-access-scan.json"

python3 "$ROOT_DIR/scripts/check-hp1020-endpoint0-sequence.py" \
  --additional-mmio-map "$ROOT_DIR/analysis/usb-path/usb-bulk-probe-contract.json" \
  "$disasm_txt" \
  -o "$OUT_DIR/endpoint0-sequence-scan.md" \
  --json "$OUT_DIR/endpoint0-sequence-scan.json"

python3 "$ROOT_DIR/scripts/check-hp1020-memory-boundary.py" \
  "$disasm_txt" \
  -o "$OUT_DIR/memory-boundary-scan.md" \
  --json "$OUT_DIR/memory-boundary-scan.json"

python3 "$ROOT_DIR/scripts/check-hp1020-marker-length-flow.py" \
  "$SRC_DIR/usb-bulk-parser.S" \
  -o "$OUT_DIR/endpoint0-length-flow-check.md" \
  --json "$OUT_DIR/endpoint0-length-flow-check.json"

python3 "$ROOT_DIR/scripts/check-hp1020-marker-rearm-flow.py" \
  "$SRC_DIR/usb-bulk-parser.S" \
  -o "$OUT_DIR/endpoint0-rearm-flow-check.md" \
  --json "$OUT_DIR/endpoint0-rearm-flow-check.json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-bulk-parser-source.py" \
  "$SRC_DIR/usb-bulk-parser.S" \
  -o "$OUT_DIR/source-contract-check.md" \
  --json "$OUT_DIR/source-contract-check.json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-bulk-status-descriptor.py" \
  "$elf" \
  --source "$SRC_DIR/usb-bulk-parser.S" \
  -o "$OUT_DIR/status-descriptor-check.md" \
  --json "$OUT_DIR/status-descriptor-check.json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-bulk-config-descriptors.py" \
  "$elf" \
  --source "$SRC_DIR/usb-bulk-parser.S" \
  -o "$OUT_DIR/config-descriptor-check.md" \
  --json "$OUT_DIR/config-descriptor-check.json"

python3 - "$ROOT_DIR" "$OUT_DIR" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
reports = {
    "layout": "layout.json",
    "safety": "safety-scan.json",
    "usb_contract": "usb-contract-scan.json",
    "usb_mmio": "usb-mmio-access-scan.json",
    "endpoint0_sequence": "endpoint0-sequence-scan.json",
    "memory_boundary": "memory-boundary-scan.json",
    "endpoint0_length": "endpoint0-length-flow-check.json",
    "endpoint0_rearm": "endpoint0-rearm-flow-check.json",
    "source_contract": "source-contract-check.json",
    "status_descriptor": "status-descriptor-check.json",
    "config_descriptors": "config-descriptor-check.json",
    "parser_model": "parser-model.json",
}

def report_status(data):
    if isinstance(data, dict) and data.get("status") in {"pass", "fail"}:
        return data["status"]
    items = data.get("checks", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return "pass"
    for item in items:
        if item.get("severity") == "fail" or item.get("status") == "fail":
            return "fail"
    return "pass"

loaded = {name: json.loads((out / rel).read_text()) for name, rel in reports.items()}
statuses = {name: report_status(data) for name, data in loaded.items()}
artifacts = {}
for suffix in ("elf", "img", "dl", "map"):
    path = out / f"hp1020-usb-bulk-parser-draft.{suffix}"
    artifacts[suffix] = {
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }

parser = loaded["parser_model"]
result = {
    "status": "pass" if all(value == "pass" for value in statuses.values()) else "fail",
    "reports": statuses,
    "parser_coverage": parser["coverage"],
    "artifacts": artifacts,
    "hardware_contact": False,
}
(out / "deterministic-test-results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

lines = [
    "# HP 1020 USB Bulk Parser Deterministic Test Results",
    "",
    f"- status: `{result['status']}`",
    "- printer or USB contacted: `no`",
    f"- generated samples: `{parser['coverage']['generated_samples_passed']}/{parser['coverage']['generated_samples_discovered']}` passed",
    f"- synthetic cases: `{parser['coverage']['synthetic_cases_passed']}/{parser['coverage']['synthetic_cases']}` passed",
    f"- assertions: `{parser['coverage']['assertions_passed']}/{parser['coverage']['assertions']}` passed",
    "",
    "## Validation Reports",
    "",
]
lines.extend(f"- `{name}`: `{status}`" for name, status in statuses.items())
lines.extend(["", "## Firmware Artifacts", "", "| Artifact | Bytes | SHA-256 |", "|---|---:|---|"])
for name, info in artifacts.items():
    lines.append(f"| `{name}` | `{info['bytes']}` | `{info['sha256']}` |")
lines.append("")
(out / "deterministic-test-results.md").write_text("\n".join(lines))
if result["status"] != "pass":
    raise SystemExit("one or more generated validation reports failed")
PY

python3 - "$OUT_DIR" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
results = json.loads((out / "deterministic-test-results.json").read_text())
parser = json.loads((out / "parser-model.json").read_text())
lines = [
    "# HP 1020 USB Bulk Receive And Parser Probe",
    "",
    "This is a buildable, mechanically inert open-firmware probe. It was generated and validated offline and was not uploaded to a printer.",
    "",
    "## Proven Offline",
    "",
    "- The Old-Xtensa source assembles and links into ELF, date-prefixed IMG, and wrapped DL artifacts.",
    "- Endpoint 0 exposes a writable product string with bytes, descriptor, recognized-chunk, parser-error, and unknown-chunk counters.",
    "- Bulk OUT uses only the statically mapped bank-1/lane-1 descriptor, buffer, status, acknowledgement, and submit contract; it polls lane status directly instead of recreating the stock ThreadX event bit.",
    "- Completed receive data is bounded to 0x400 bytes, parsed incrementally across transfers, and never reaches engine, video, laser, fuser, motor, or paper-feed code.",
    f"- Host model: {parser['coverage']['generated_samples_passed']}/{parser['coverage']['generated_samples_discovered']} generated samples and {parser['coverage']['synthetic_cases_passed']}/{parser['coverage']['synthetic_cases']} boundary cases passed.",
    "- Every generated safety, USB, memory, source, descriptor, and parser report passes.",
    "",
    "## Unproven Until Hardware",
    "",
    "- Whether custom code actually executes after upload on this printer.",
    "- Whether the mapped USB controller retains enough boot-ROM initialization for endpoint 0 and bulk OUT to operate under this standalone probe.",
    "- Whether a real bulk completion reports the expected descriptor status/length encoding and continues after repeated re-arms.",
    "",
    "The next meaningful step is the guarded test in `hardware-test-plan.md`: upload after a fresh power cycle, read the product descriptor marker, send one START_DOC/END_DOC-only stream, then read the counters again. No print or mechanical command is involved.",
    "",
    "## Artifacts",
    "",
]
for suffix, info in results["artifacts"].items():
    lines.append(f"- `{out.name}/hp1020-usb-bulk-parser-draft.{suffix}`: `{info['sha256']}`")
lines.append("")
(out / "summary.md").write_text("\n".join(lines))
PY

chmod 644 "$elf" "$img" "$dl" "$map" "$readelf_txt" "$disasm_txt" "$OUT_DIR"/*.md "$OUT_DIR"/*.json
printf '%s\n' "$OUT_DIR/summary.md"
