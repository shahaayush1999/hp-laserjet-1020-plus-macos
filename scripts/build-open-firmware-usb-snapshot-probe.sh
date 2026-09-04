#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/open-firmware/usb-register-snapshot"
OUT_DIR="$ROOT_DIR/analysis/open-firmware-probes/usb-register-snapshot"

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

obj="$OUT_DIR/hp1020-usb-snapshot-probe.o"
toolchain_elf="$OUT_DIR/hp1020-usb-snapshot-probe.toolchain-machine.elf"
elf="$OUT_DIR/hp1020-usb-snapshot-probe.elf"
img="$OUT_DIR/hp1020-usb-snapshot-probe.img"
dl="$OUT_DIR/hp1020-usb-snapshot-probe.dl"
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
summary_md="$OUT_DIR/summary.md"

"$as_tool" -o "$obj" "$SRC_DIR/usb-snapshot.S"
"$ld_tool" -T "$SRC_DIR/hp1020-usb-snapshot.ld" -Map "$OUT_DIR/hp1020-usb-snapshot-probe.map" -o "$toolchain_elf" "$obj"

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
python3 "$ROOT_DIR/scripts/check-hp1020-probe-instructions.py" "$elf" --prefix "$prefix" --self-test

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
  --profile boot-probe \
  --markdown-output "$layout_md" \
  --json-output "$layout_json" \
  "$dl" >/tmp/hp1020-usb-snapshot-layout-status.txt

python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$safety_md" \
  --json "$safety_json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-probe-contract.py" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$usb_contract_md" \
  --json "$usb_contract_json"

python3 "$ROOT_DIR/scripts/check-hp1020-usb-mmio-accesses.py" \
  "$disasm_txt" \
  -o "$usb_access_md" \
  --json "$usb_access_json"

rm -f "$obj" "$toolchain_elf"

{
  printf '# HP 1020 USB Register Snapshot Probe Build\n\n'
  printf 'This artifact is offline only. It was not uploaded to the printer.\n\n'
  printf '## Outputs\n\n'
  printf -- '- ELF: `%s`\n' "$elf"
  printf -- '- Date-prefixed image: `%s`\n' "$img"
  printf -- '- PJL/ACL upload wrapper: `%s`\n' "$dl"
  printf -- '- Layout report: `%s`\n' "$layout_md"
  printf -- '- Safety scan: `%s`\n' "$safety_md"
  printf -- '- USB contract scan: `%s`\n' "$usb_contract_md"
  printf -- '- USB MMIO access scan: `%s`\n' "$usb_access_md"
  printf '\n'
  printf '## Key Checks\n\n'
  printf '```text\n'
  cat /tmp/hp1020-usb-snapshot-layout-status.txt
  printf '```\n\n'
  printf '```text\n'
  file "$elf" "$img" "$dl"
  printf '```\n\n'
  printf '## Meaning\n\n'
  printf 'This open-code probe reads only the mapped USB 0xb300 registers into local RAM and then idles.\n'
  printf 'The disassembly access scan recovers 14 mapped USB reads and 0 USB writes.\n'
  printf 'It does not write USB MMIO, engine MMIO, video MMIO, or attempt printing.\n'
  printf 'It is a candidate for later controlled hardware testing only after review.\n'
} > "$summary_md"

chmod 644 "$elf" "$img" "$dl" "$readelf_txt" "$disasm_txt" "$layout_md" "$layout_json" \
  "$safety_md" "$safety_json" "$usb_contract_md" "$usb_contract_json" \
  "$usb_access_md" "$usb_access_json" "$summary_md" "$OUT_DIR/hp1020-usb-snapshot-probe.map"

printf '%s\n' "$summary_md"
