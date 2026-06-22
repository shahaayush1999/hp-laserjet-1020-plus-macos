#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/open-firmware/usb-marker-draft"
OUT_DIR="$ROOT_DIR/analysis/open-firmware-probes/usb-marker-draft"

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

as_tool="${prefix}-as"
ld_tool="${prefix}-ld"
readelf_tool="${prefix}-readelf"
objdump_tool="${prefix}-objdump"

for tool in "$as_tool" "$ld_tool" "$readelf_tool" "$objdump_tool"; do
  if [[ ! -x "$tool" ]]; then
    printf 'missing tool: %s\n' "$tool" >&2
    printf 'Run scripts/build-xtensa-binutils-manual.sh or set XTENSA_PREFIX to /path/bin/xtensa-fsf-elf\n' >&2
    exit 1
  fi
  if ! "$tool" --version >/dev/null 2>&1; then
    printf 'tool exists but cannot run: %s\n' "$tool" >&2
    file "$tool" >&2 || true
    printf 'Set XTENSA_PREFIX to a runnable macOS xtensa-fsf-elf tool prefix.\n' >&2
    exit 1
  fi
done

mkdir -p "$OUT_DIR"

obj="$OUT_DIR/hp1020-usb-marker-draft.o"
toolchain_elf="$OUT_DIR/hp1020-usb-marker-draft.toolchain-machine.elf"
elf="$OUT_DIR/hp1020-usb-marker-draft.elf"
img="$OUT_DIR/hp1020-usb-marker-draft.img"
dl="$OUT_DIR/hp1020-usb-marker-draft.dl"
readelf_txt="$OUT_DIR/readelf.txt"
disasm_txt="$OUT_DIR/disassembly.txt"
layout_md="$OUT_DIR/layout.md"
layout_json="$OUT_DIR/layout.json"
safety_md="$OUT_DIR/safety-scan.md"
safety_json="$OUT_DIR/safety-scan.json"
usb_contract_md="$OUT_DIR/usb-contract-scan.md"
usb_contract_json="$OUT_DIR/usb-contract-scan.json"
usb_access_md="$OUT_DIR/usb-mmio-access-scan.md"
usb_access_json="$OUT_DIR/usb-mmio-access-scan.json"
endpoint0_sequence_md="$OUT_DIR/endpoint0-sequence-scan.md"
endpoint0_sequence_json="$OUT_DIR/endpoint0-sequence-scan.json"
summary_md="$OUT_DIR/summary.md"

"$as_tool" -o "$obj" "$SRC_DIR/usb-marker.S"
"$ld_tool" -T "$SRC_DIR/hp1020-usb-marker.ld" -Map "$OUT_DIR/hp1020-usb-marker-draft.map" -o "$toolchain_elf" "$obj"

cp "$toolchain_elf" "$elf"
python3 - "$elf" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = bytearray(path.read_bytes())
if data[:4] != b"\x7fELF":
    raise SystemExit("not an ELF file")
if data[4] != 1 or data[5] != 2:
    raise SystemExit("expected ELF32 big-endian")
data[18:20] = (0xABC7).to_bytes(2, "big")
path.write_bytes(data)
PY

{
  printf '20260622'
  cat "$elf"
} > "$img"

python3 "$ROOT_DIR/scripts/wrap-firmware-acl.py" "$img" "$dl"
"$readelf_tool" -h -l -S "$elf" > "$readelf_txt"
"$objdump_tool" -d "$elf" > "$disasm_txt"

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
  --profile boot-probe \
  --markdown-output "$layout_md" \
  --json-output "$layout_json" \
  "$dl" >/tmp/hp1020-usb-marker-layout-status.txt

python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$safety_md" \
  --json "$safety_json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-probe-contract.py" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$usb_contract_md" \
  --json "$usb_contract_json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-mmio-accesses.py" \
  --allow-usb-writes \
  "$disasm_txt" \
  -o "$usb_access_md" \
  --json "$usb_access_json"

python3 "$ROOT_DIR/scripts/check-hp1020-endpoint0-sequence.py" \
  "$disasm_txt" \
  -o "$endpoint0_sequence_md" \
  --json "$endpoint0_sequence_json"

rm -f "$obj" "$toolchain_elf"

{
  printf '# HP 1020 USB Marker Draft Build\n\n'
  printf 'This artifact is offline only. It was not uploaded to the printer.\n\n'
  printf '## Outputs\n\n'
  printf -- '- ELF: `%s`\n' "$elf"
  printf -- '- Date-prefixed image: `%s`\n' "$img"
  printf -- '- PJL/ACL upload wrapper: `%s`\n' "$dl"
  printf -- '- Layout report: `%s`\n' "$layout_md"
  printf -- '- Safety scan: `%s`\n' "$safety_md"
  printf -- '- USB contract scan: `%s`\n' "$usb_contract_md"
  printf -- '- USB MMIO access scan: `%s`\n' "$usb_access_md"
  printf -- '- Endpoint-0 sequence scan: `%s`\n' "$endpoint0_sequence_md"
  printf '\n'
  printf '## Key Checks\n\n'
  printf '```text\n'
  cat /tmp/hp1020-usb-marker-layout-status.txt
  printf '```\n\n'
  printf '```text\n'
  file "$elf" "$img" "$dl"
  printf '```\n\n'
  printf '## Meaning\n\n'
  printf 'This open-code draft recognizes a USB product-string GET_DESCRIPTOR setup shape and tries to expose the marker string `HP1020 OPEN MARKER` through endpoint-0.\n'
  printf 'It writes only USB-controller MMIO registers that match the extracted stock endpoint-0 sequence contract.\n'
  printf 'It does not touch engine, fuser, motor, paper-feed, video, or raster MMIO.\n'
  printf 'It is not hardware-ready; the missing proof is whether the setup buffer and stock response state are valid after custom upload.\n'
} > "$summary_md"

chmod 644 "$elf" "$img" "$dl" "$readelf_txt" "$disasm_txt" "$layout_md" "$layout_json" \
  "$safety_md" "$safety_json" "$usb_contract_md" "$usb_contract_json" \
  "$usb_access_md" "$usb_access_json" "$endpoint0_sequence_md" "$endpoint0_sequence_json" \
  "$summary_md" "$OUT_DIR/hp1020-usb-marker-draft.map"

printf '%s\n' "$summary_md"
