#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/open-firmware/minimal-idle"
OUT_DIR="$ROOT_DIR/analysis/open-firmware-probes/minimal-idle"

default_prefix="/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf"
prefix="${XTENSA_PREFIX:-$default_prefix}"

as_tool="${prefix}-as"
ld_tool="${prefix}-ld"
readelf_tool="${prefix}-readelf"
objdump_tool="${prefix}-objdump"

for tool in "$as_tool" "$ld_tool" "$readelf_tool" "$objdump_tool"; do
  if [[ ! -x "$tool" ]]; then
    printf 'missing tool: %s\n' "$tool" >&2
    printf 'Run the crosstool-NG build or set XTENSA_PREFIX to /path/bin/xtensa-fsf-elf\n' >&2
    exit 1
  fi
done

mkdir -p "$OUT_DIR"

obj="$OUT_DIR/hp1020-idle-probe.o"
toolchain_elf="$OUT_DIR/hp1020-idle-probe.toolchain-machine.elf"
elf="$OUT_DIR/hp1020-idle-probe.elf"
img="$OUT_DIR/hp1020-idle-probe.img"
dl="$OUT_DIR/hp1020-idle-probe.dl"
readelf_txt="$OUT_DIR/readelf.txt"
disasm_txt="$OUT_DIR/disassembly.txt"
layout_md="$OUT_DIR/layout.md"
layout_json="$OUT_DIR/layout.json"
safety_md="$OUT_DIR/safety-scan.md"
safety_json="$OUT_DIR/safety-scan.json"
summary_md="$OUT_DIR/summary.md"

"$as_tool" -o "$obj" "$SRC_DIR/idle.S"
"$ld_tool" -T "$SRC_DIR/hp1020-idle.ld" -Map "$OUT_DIR/hp1020-idle-probe.map" -o "$toolchain_elf" "$obj"

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
  printf '20260613'
  cat "$elf"
} > "$img"

python3 "$ROOT_DIR/scripts/wrap-firmware-acl.py" "$img" "$dl"
"$readelf_tool" -h -l -S "$elf" > "$readelf_txt"
"$objdump_tool" -d "$elf" > "$disasm_txt"

python3 "$ROOT_DIR/scripts/inspect-firmware-layout.py" \
  --profile boot-probe \
  --markdown-output "$layout_md" \
  --json-output "$layout_json" \
  "$dl" >/tmp/hp1020-idle-layout-status.txt

python3 "$ROOT_DIR/scripts/check-hp1020-safety-boundary.py" \
  "$SRC_DIR" "$disasm_txt" "$readelf_txt" \
  -o "$safety_md" \
  --json "$safety_json"

rm -f "$obj" "$toolchain_elf"

{
  printf '# HP 1020 Minimal Idle Probe Build\n\n'
  printf 'This artifact is offline only. It was not uploaded to the printer.\n\n'
  printf '## Outputs\n\n'
  printf -- '- ELF: `%s`\n' "$elf"
  printf -- '- Date-prefixed image: `%s`\n' "$img"
  printf -- '- PJL/ACL upload wrapper: `%s`\n' "$dl"
  printf -- '- Layout report: `%s`\n' "$layout_md"
  printf -- '- Safety scan: `%s`\n' "$safety_md"
  printf '\n'
  printf '## Key Checks\n\n'
  printf '```text\n'
  cat /tmp/hp1020-idle-layout-status.txt
  printf '```\n\n'
  printf '```text\n'
  file "$elf" "$img" "$dl"
  printf '```\n\n'
  printf '## Meaning\n\n'
  printf 'The build proves we can generate an HP-shaped, old-Xtensa, date-prefixed firmware upload candidate from our own assembly.\n'
  printf 'The system interface table is open-code only: all 75 slots point to the local trap loop, not copied HP routines.\n'
  printf 'It does not prove the printer boot ROM will accept it, and it does not attempt printing.\n'
} > "$summary_md"

chmod 644 "$elf" "$img" "$dl" "$readelf_txt" "$disasm_txt" "$layout_md" "$layout_json" \
  "$safety_md" "$safety_json" "$summary_md" "$OUT_DIR/hp1020-idle-probe.map"

printf '%s\n' "$summary_md"
