#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCC_PREFIX="${HP1020_GCC_PREFIX:-/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf}"
BIN_PREFIX="${XTENSA_PREFIX:-/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf}"
OUT="$ROOT_DIR/analysis/open-firmware-model/semantic-target"
SOURCE="$ROOT_DIR/open-firmware/semantic-core"
mkdir -p "$OUT"
# Select call0 via the verified compiler default; the old assembler does not
# accept the newer --abi-call0 metadata flag passed by explicit -mabi=call0.
python3 "$ROOT_DIR/scripts/check-hp1020-c-compiler-profile.py" "${GCC_PREFIX}-gcc"
objects=()
for name in hp1020_semantic hp1020_page_plan freestanding/memory freestanding/target-check; do
  obj="$OUT/$(basename "$name").o"
  "$GCC_PREFIX-gcc" -Os -ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns \
    -mtext-section-literals -Wall -Wextra -Werror \
    -I"$SOURCE/freestanding" -I"$SOURCE" -c "$SOURCE/$name.c" -o "$obj"
  objects+=("$obj")
done
"$GCC_PREFIX-gcc" -nostdlib -Wl,-T,"$SOURCE/freestanding/target-check.ld" \
  -Wl,-Map,"$OUT/target-check.map" "${objects[@]}" -lgcc -o "$OUT/target-check.elf"
"$BIN_PREFIX-objdump" -d "$OUT/target-check.elf" > "$OUT/disassembly.txt"
"$BIN_PREFIX-nm" -n "$OUT/target-check.elf" > "$OUT/symbols.txt"
rm -f "${objects[@]}"
echo 'Built synthetic RAM-only target ELF. No boot wrapper, firmware upload image, or hardware output exists.'
