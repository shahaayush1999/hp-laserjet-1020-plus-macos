#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/analysis/toolchain-probe/binutils-smoke"

default_prefix="/tmp/hp1020-ctng-mnt/x-tools/xtensa-fsf-elf/bin/xtensa-fsf-elf"
prefix="${XTENSA_PREFIX:-$default_prefix}"

as_tool="${prefix}-as"
ld_tool="${prefix}-ld"
readelf_tool="${prefix}-readelf"
objdump_tool="${prefix}-objdump"
objcopy_tool="${prefix}-objcopy"

for tool in "$as_tool" "$ld_tool" "$readelf_tool" "$objdump_tool" "$objcopy_tool"; do
  if [[ ! -x "$tool" ]]; then
    printf 'missing tool: %s\n' "$tool" >&2
    printf 'Set XTENSA_PREFIX to the tool prefix, for example /path/bin/xtensa-fsf-elf\n' >&2
    exit 1
  fi
done

mkdir -p "$OUT_DIR"

asm="$OUT_DIR/tiny-boot.S"
obj="$OUT_DIR/tiny-boot.o"
elf="$OUT_DIR/tiny-boot.elf"
bin="$OUT_DIR/tiny-boot.bin"
report="$OUT_DIR/report.md"

cat > "$asm" <<'ASM'
    .section .text.start, "ax", @progbits
    .global _start
_start:
    entry a1, 16
    movi a2, 0
    retw
ASM

"$as_tool" -o "$obj" "$asm"
"$ld_tool" -Ttext=0x10000000 -e _start -o "$elf" "$obj"
"$objcopy_tool" -O binary "$elf" "$bin"

{
  printf '# Xtensa Binutils Smoke Test\n\n'
  printf 'Tool prefix: `%s`\n\n' "$prefix"
  printf '## File Types\n\n'
  printf '```text\n'
  file "$obj" "$elf" "$bin"
  printf '```\n\n'
  printf '## ELF Header\n\n'
  printf '```text\n'
  "$readelf_tool" -h "$elf"
  printf '```\n\n'
  printf '## Sections\n\n'
  printf '```text\n'
  "$readelf_tool" -S "$elf"
  printf '```\n\n'
  printf '## Disassembly\n\n'
  printf '```text\n'
  "$objdump_tool" -d "$elf"
  printf '```\n\n'
  printf '## Raw Binary\n\n'
  printf -- '- `%s`\n' "$bin"
  printf -- '- Size: `%s bytes`\n' "$(wc -c < "$bin" | tr -d ' ')"
} > "$report"

printf '%s\n' "$report"
