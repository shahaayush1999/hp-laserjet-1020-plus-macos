#!/usr/bin/env bash
# Build the recording-acquisition RAM fixture; no controller/upload.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCC_PREFIX="${HP1020_GCC_PREFIX:-/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf}"
BIN_PREFIX="${XTENSA_PREFIX:-/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf}"
SOURCE="$ROOT_DIR/open-firmware/udc-acquire-test"
PUBLISH="$ROOT_DIR/open-firmware/udc-publish"
PROGRAM="$ROOT_DIR/open-firmware/udc-program"
EP0="$ROOT_DIR/open-firmware/udc-ep0"
USB_OUT="$ROOT_DIR/open-firmware/udc-out"
SETUP="$ROOT_DIR/open-firmware/udc-setup"
OUT="$ROOT_DIR/analysis/usb-path/udc-acquire/target"
ADAPTER="$ROOT_DIR/open-firmware/tinyusb-printer-adapter"
PROTOCOL="$ROOT_DIR/open-firmware/tinyusb-device"
PRINTER="$ROOT_DIR/open-firmware/usb-printer-class"
RECEIVE="$ROOT_DIR/open-firmware/usb-receive-core"
IMAGE="$ROOT_DIR/open-firmware/image-core"
SEMANTIC="$ROOT_DIR/open-firmware/semantic-core"
JBIG="$ROOT_DIR/vendor/jbigkit-2.1/libjbig"
mkdir -p "$OUT"
effective_source="$(mktemp -d "${TMPDIR:-/tmp}/hp1020-udc-acquire-source.XXXXXX")"
python3 "$ROOT_DIR/scripts/prepare-hp1020-tinyusb.py" --output "$effective_source" --patched
cp "$effective_source/effective-source.json" "$OUT/effective-source.json"
TINYUSB="$effective_source/src"
python3 "$ROOT_DIR/scripts/check-hp1020-c-compiler-profile.py" "${GCC_PREFIX}-gcc"
objects=()
for source in "$SOURCE/fixture.c" "$PUBLISH/hp1020_udc_publish.c" "$PROGRAM/hp1020_udc_program.c" \
    "$EP0/hp1020_udc_ep0.c" "$USB_OUT/hp1020_udc_out.c" \
    "$SETUP/hp1020_udc_setup.c" "$ADAPTER/hp1020_tusb_adapter.c" \
    "$PRINTER/hp1020_usb_printer.c" "$RECEIVE/hp1020_usb_receive.c" "$RECEIVE/hp1020_usb_document.c" \
    "$IMAGE/hp1020_image.c" "$IMAGE/hp1020_image_page.c" "$IMAGE/hp1020_image_stream.c" \
    "$IMAGE/hp1020_image_ring.c" "$IMAGE/hp1020_image_output.c" "$ROOT_DIR/open-firmware/image-pump/hp1020_image_pump.c" "$SEMANTIC/hp1020_semantic.c" \
    "$SEMANTIC/hp1020_page_plan.c" "$IMAGE/target-memory.c" "$SEMANTIC/freestanding/memory.c" \
    "$JBIG/jbig85.c" "$JBIG/jbig_ar.c" "$TINYUSB/tusb.c" "$TINYUSB/device/usbd.c" \
    "$TINYUSB/common/tusb_fifo.c"; do
  obj="$OUT/$(basename "${source%.c}").o"
  upstream_warning=()
  if [[ "$source" == "$TINYUSB/device/usbd.c" ]]; then upstream_warning=(-Wno-type-limits); fi
  "$GCC_PREFIX-gcc" -Os -ffreestanding -fno-builtin -fno-common \
    -fno-tree-loop-distribute-patterns -ffunction-sections -fdata-sections \
    -mtext-section-literals -Wall -Wextra -Werror "${upstream_warning[@]}" -fstack-usage -DNDEBUG= \
    -I"$PROTOCOL/freestanding" -I"$IMAGE/freestanding" -I"$SOURCE" -I"$PUBLISH" -I"$PROGRAM" -I"$EP0" -I"$USB_OUT" -I"$SETUP" \
    -I"$ROOT_DIR/open-firmware" -I"$ADAPTER" -I"$PROTOCOL" -I"$PRINTER" -I"$RECEIVE" \
    -I"$IMAGE" -I"$SEMANTIC" -I"$JBIG" -I"$TINYUSB" -c "$source" -o "$obj"
  objects+=("$obj")
done
"$GCC_PREFIX-gcc" -nostdlib -Wl,-T,"$SOURCE/target-check.ld" \
  -Wl,-Map,"$OUT/target-check.map" "${objects[@]}" -lgcc -o "$OUT/target-check.elf"
"$BIN_PREFIX-objdump" -d "$OUT/target-check.elf" > "$OUT/disassembly.txt"
"$BIN_PREFIX-nm" -n -S "$OUT/target-check.elf" > "$OUT/symbols.txt"
if [[ -n "$("$BIN_PREFIX-nm" -u "$OUT/target-check.elf")" ]]; then
  echo 'Unexpected undefined target symbol' >&2; exit 1
fi
# The independent Python validator must additionally call the existing
# validate-hp1020-image-core.py audit_target() before any QEMU execution.
rm -f "${objects[@]}"
echo "Built acquisition RAM-only fixture in $OUT; no physical register/cache backend."
