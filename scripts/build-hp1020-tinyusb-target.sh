#!/usr/bin/env bash
# Generic USB core plus a synthetic DCD. No actual controller or device access.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCC_PREFIX="${HP1020_GCC_PREFIX:-/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf}"
BIN_PREFIX="${XTENSA_PREFIX:-/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf}"
OUT="$ROOT_DIR/analysis/usb-path/tinyusb-device/target"
SOURCE="$ROOT_DIR/open-firmware/tinyusb-device"
PRINTER="$ROOT_DIR/open-firmware/usb-printer-class"
RECEIVE="$ROOT_DIR/open-firmware/usb-receive-core"
IMAGE="$ROOT_DIR/open-firmware/image-core"
SEMANTIC="$ROOT_DIR/open-firmware/semantic-core"
JBIG="$ROOT_DIR/vendor/jbigkit-2.1/libjbig"
TINYUSB="$ROOT_DIR/vendor/tinyusb-0.21.0/src"
mkdir -p "$OUT"
python3 "$ROOT_DIR/scripts/check-hp1020-c-compiler-profile.py" "${GCC_PREFIX}-gcc"
objects=()
for source in "$SOURCE/fixture.c" "$PRINTER/hp1020_usb_printer.c" \
    "$RECEIVE/hp1020_usb_receive.c" "$RECEIVE/hp1020_usb_document.c" \
    "$IMAGE/hp1020_image.c" "$IMAGE/hp1020_image_page.c" "$IMAGE/hp1020_image_stream.c" \
    "$IMAGE/hp1020_image_ring.c" "$IMAGE/hp1020_image_output.c" "$SEMANTIC/hp1020_semantic.c" \
    "$SEMANTIC/hp1020_page_plan.c" "$IMAGE/target-memory.c" "$SEMANTIC/freestanding/memory.c" \
    "$JBIG/jbig85.c" "$JBIG/jbig_ar.c" "$TINYUSB/tusb.c" "$TINYUSB/device/usbd.c" \
    "$TINYUSB/common/tusb_fifo.c"; do
  obj="$OUT/$(basename "${source%.c}").o"
  "$GCC_PREFIX-gcc" -Os -ffreestanding -fno-builtin -fno-common \
    -fno-tree-loop-distribute-patterns -ffunction-sections -fdata-sections \
    -mtext-section-literals -Wall -Wextra -Werror -fstack-usage -DNDEBUG= \
    -I"$IMAGE/freestanding" -I"$SOURCE" -I"$PRINTER" -I"$RECEIVE" -I"$IMAGE" \
    -I"$SEMANTIC" -I"$JBIG" -I"$TINYUSB" -c "$source" -o "$obj"
  objects+=("$obj")
done
"$GCC_PREFIX-gcc" -nostdlib -Wl,-T,"$SOURCE/target-check.ld" \
  -Wl,-Map,"$OUT/target-check.map" "${objects[@]}" -lgcc -o "$OUT/target-check.elf"
"$BIN_PREFIX-objdump" -d "$OUT/target-check.elf" > "$OUT/disassembly.txt"
"$BIN_PREFIX-nm" -n -S "$OUT/target-check.elf" > "$OUT/symbols.txt"
if [[ -n "$("$BIN_PREFIX-nm" -u "$OUT/target-check.elf")" ]]; then
  echo 'Unexpected undefined target symbol' >&2
  exit 1
fi
rm -f "${objects[@]}"
echo 'Built generic USB protocol core with synthetic DCD; no controller port.'
