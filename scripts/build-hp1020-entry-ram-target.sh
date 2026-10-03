#!/usr/bin/env bash
# UNEXECUTED draft. ELF-only entry-to-C experiment; never an upload image.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCC_PREFIX="${HP1020_GCC_PREFIX:-/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf}"
BIN_PREFIX="${XTENSA_PREFIX:-/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf}"
OUT="$ROOT_DIR/analysis/boot-handoff/entry-ram/target"
SOURCE="$ROOT_DIR/open-firmware/entry-ram-test"
RX="$ROOT_DIR/open-firmware/usb-receive-core"
IMAGE="$ROOT_DIR/open-firmware/image-core"
SEMANTIC="$ROOT_DIR/open-firmware/semantic-core"
JBIG="$ROOT_DIR/vendor/jbigkit-2.1/libjbig"
INPUT="$ROOT_DIR/analysis/boot-handoff/entry-ram/fixtures/small-black.zjs"
mkdir -p "$OUT"
python3 "$ROOT_DIR/scripts/check-hp1020-c-compiler-profile.py" "${GCC_PREFIX}-gcc"
python3 - "$INPUT" "$OUT/hp1020_entry_input.h" <<'PY'
from pathlib import Path
import sys
raw=Path(sys.argv[1]).read_bytes()
assert 0<len(raw)<=1024 and raw[:4]==b'JZJZ','expected bounded frozen ZjStream fixture'
rows=[', '.join(f'0x{v:02x}' for v in raw[i:i+16]) for i in range(0,len(raw),16)]
Path(sys.argv[2]).write_text('/* Generated from the exact saved RAM input; do not hand-edit. */\n'
    '#ifndef HP1020_ENTRY_INPUT_H\n#define HP1020_ENTRY_INPUT_H\n#include <stdint.h>\n'
    f'#define HP1020_ENTRY_INPUT_BYTES {len(raw)}u\n'
    'static const uint8_t hp1020_entry_input[HP1020_ENTRY_INPUT_BYTES] = {\n    '+
    ',\n    '.join(rows)+'\n};\n#endif\n')
PY
objects=()
for source in "$SOURCE/hp1020_entry_workload.c" "$SOURCE/hp1020_entry_layout.c" \
    "$RX/hp1020_usb_receive.c" "$RX/hp1020_usb_document.c" \
    "$IMAGE/hp1020_image.c" "$IMAGE/hp1020_image_page.c" "$IMAGE/hp1020_image_stream.c" \
    "$IMAGE/hp1020_image_ring.c" "$IMAGE/hp1020_image_output.c" "$SEMANTIC/hp1020_semantic.c" \
    "$SEMANTIC/hp1020_page_plan.c" "$IMAGE/target-memory.c" "$SEMANTIC/freestanding/memory.c" \
    "$JBIG/jbig85.c" "$JBIG/jbig_ar.c"; do
  obj="$OUT/$(basename "${source%.c}").o"
  "$GCC_PREFIX-gcc" -Os -ffreestanding -fno-builtin -fno-common \
    -fno-tree-loop-distribute-patterns -ffunction-sections -fdata-sections \
    -mtext-section-literals -Wall -Wextra -Werror -fstack-usage -DNDEBUG= \
    -I"$OUT" -I"$SOURCE" -I"$IMAGE/freestanding" -I"$RX" -I"$IMAGE" -I"$SEMANTIC" -I"$JBIG" \
    -MD -MF "${obj%.o}.d" -c "$source" -o "$obj"
  objects+=("$obj")
done
"$BIN_PREFIX-as" --text-section-literals "$SOURCE/startup.S" -o "$OUT/startup.o"
objects+=("$OUT/startup.o")
# Preserve instruction/literal annotations and all exact linked artifacts.
"$GCC_PREFIX-gcc" -nostdlib -Wl,-T,"$SOURCE/entry.ld" \
  -Wl,-Map,"$OUT/entry-ram.map" "${objects[@]}" -lgcc -o "$OUT/entry-ram.elf"
"$BIN_PREFIX-objdump" -d "$OUT/entry-ram.elf" > "$OUT/disassembly.txt"
"$BIN_PREFIX-nm" -n -S "$OUT/entry-ram.elf" > "$OUT/symbols.txt"
"$BIN_PREFIX-readelf" -W -h -l -S "$OUT/entry-ram.elf" > "$OUT/layout.txt"
if [[ -n "$("$BIN_PREFIX-nm" -u "$OUT/entry-ram.elf")" ]]; then
  echo 'Unexpected undefined entry target symbol' >&2
  exit 1
fi
rm -f "${objects[@]}"
echo 'Built ELF-only entry RAM experiment; linked footprint/instruction audit and execution still required.'
