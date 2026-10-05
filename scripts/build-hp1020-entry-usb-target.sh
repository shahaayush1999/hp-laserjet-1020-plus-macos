#!/usr/bin/env bash
# Authored as an unexecuted draft. ELF-only RAM USB lifetime; never an upload.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCC_PREFIX="${HP1020_GCC_PREFIX:-/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf}"
BIN_PREFIX="${XTENSA_PREFIX:-/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf}"
SOURCE="$ROOT_DIR/open-firmware/entry-usb-test"
OUT="$ROOT_DIR/analysis/boot-handoff/entry-usb/target"
INPUT="$ROOT_DIR/analysis/boot-handoff/entry-ram/fixtures/small-black.zjs"
PUBLISH="$ROOT_DIR/open-firmware/udc-publish"
PROGRAM="$ROOT_DIR/open-firmware/udc-program"
EP0="$ROOT_DIR/open-firmware/udc-ep0"
USB_OUT="$ROOT_DIR/open-firmware/udc-out"
SETUP="$ROOT_DIR/open-firmware/udc-setup"
ADAPTER="$ROOT_DIR/open-firmware/tinyusb-printer-adapter"
PROTOCOL="$ROOT_DIR/open-firmware/tinyusb-device"
PRINTER="$ROOT_DIR/open-firmware/usb-printer-class"
RECEIVE="$ROOT_DIR/open-firmware/usb-receive-core"
IMAGE="$ROOT_DIR/open-firmware/image-core"
SEMANTIC="$ROOT_DIR/open-firmware/semantic-core"
JBIG="$ROOT_DIR/vendor/jbigkit-2.1/libjbig"
mkdir -p "$OUT"
effective_source="$(mktemp -d "${TMPDIR:-/tmp}/hp1020-entry-usb-source.XXXXXX")"
python3 "$ROOT_DIR/scripts/prepare-hp1020-tinyusb.py" --output "$effective_source" --patched
cp "$effective_source/effective-source.json" "$OUT/effective-source.json"
TINYUSB="$effective_source/src"
python3 "$ROOT_DIR/scripts/check-hp1020-c-compiler-profile.py" "${GCC_PREFIX}-gcc"
python3 - "$INPUT" "$OUT/hp1020_usb_runtime_input.h" <<'PY'
from pathlib import Path
import hashlib,sys
raw=Path(sys.argv[1]).read_bytes()
assert len(raw)==352 and hashlib.sha256(raw).hexdigest()=='ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d'
rows=[', '.join(f'0x{v:02x}' for v in raw[i:i+16]) for i in range(0,len(raw),16)]
Path(sys.argv[2]).write_text('/* Generated from the exact independently specified352-byte stream. */\n'
    '#ifndef HP1020_USB_RUNTIME_INPUT_H\n#define HP1020_USB_RUNTIME_INPUT_H\n#include <stdint.h>\n'
    '#define HP1020_USB_RUNTIME_INPUT_BYTES 352u\n'
    'const uint8_t hp1020_usb_runtime_input[HP1020_USB_RUNTIME_INPUT_BYTES] = {\n    '+
    ',\n    '.join(rows)+'\n};\n#endif\n')
PY
objects=()
for source in "$SOURCE/hp1020_usb_runtime.c" "$SOURCE/hp1020_usb_runtime_ram.c" \
    "$SOURCE/hp1020_usb_runtime_layout.c" \
    "$PUBLISH/hp1020_udc_publish.c" "$PROGRAM/hp1020_udc_program.c" \
    "$EP0/hp1020_udc_ep0.c" "$USB_OUT/hp1020_udc_out.c" "$SETUP/hp1020_udc_setup.c" \
    "$ADAPTER/hp1020_tusb_adapter.c" "$PRINTER/hp1020_usb_printer.c" \
    "$RECEIVE/hp1020_usb_receive.c" "$RECEIVE/hp1020_usb_document.c" \
    "$IMAGE/hp1020_image.c" "$IMAGE/hp1020_image_page.c" "$IMAGE/hp1020_image_stream.c" \
    "$IMAGE/hp1020_image_ring.c" "$IMAGE/hp1020_image_output.c" "$ROOT_DIR/open-firmware/image-pump/hp1020_image_pump.c" \
    "$SEMANTIC/hp1020_semantic.c" "$SEMANTIC/hp1020_page_plan.c" \
    "$IMAGE/target-memory.c" "$SEMANTIC/freestanding/memory.c" \
    "$JBIG/jbig85.c" "$JBIG/jbig_ar.c" "$TINYUSB/tusb.c" \
    "$TINYUSB/device/usbd.c" "$TINYUSB/common/tusb_fifo.c"; do
  obj="$OUT/$(basename "${source%.c}").o"
  upstream_warning=()
  if [[ "$source" == "$TINYUSB/device/usbd.c" ]]; then upstream_warning=(-Wno-type-limits); fi
  "$GCC_PREFIX-gcc" -Os -ffreestanding -fno-builtin -fno-common \
    -fno-tree-loop-distribute-patterns -ffunction-sections -fdata-sections \
    -mtext-section-literals -Wall -Wextra -Werror "${upstream_warning[@]}" -fstack-usage -DNDEBUG= \
    -I"$OUT" -I"$SOURCE" -I"$PROTOCOL/freestanding" -I"$IMAGE/freestanding" \
    -I"$PUBLISH" -I"$PROGRAM" -I"$EP0" -I"$USB_OUT" -I"$SETUP" \
    -I"$ADAPTER" -I"$PROTOCOL" -I"$PRINTER" -I"$RECEIVE" -I"$IMAGE" \
    -I"$SEMANTIC" -I"$JBIG" -I"$TINYUSB" \
    -MD -MF "${obj%.o}.d" -c "$source" -o "$obj"
  objects+=("$obj")
done
"$BIN_PREFIX-as" --text-section-literals "$SOURCE/startup.S" -o "$OUT/startup.o"
objects+=("$OUT/startup.o")
# Preserve the actual compiler-selected archive before linking. The audit and
# separate raw-capture gate independently verify the link map selected these
# exact two members; extraction does not by itself establish link membership.
python3 - "$ROOT_DIR/scripts" "$GCC_PREFIX-gcc" "$OUT/libgcc" <<'PY'
from pathlib import Path
import json,subprocess,sys
sys.path.insert(0,sys.argv[1])
from hp1020_entry_usb_audit import selected_archive_members,LIBGCC_MEMBERS,digest
original=Path(subprocess.check_output([sys.argv[2],'-print-libgcc-file-name'],text=True).strip()).resolve()
archive=original.read_bytes();members=selected_archive_members(archive)
out=Path(sys.argv[3]);out.mkdir(exist_ok=False)
(out/'libgcc.a').write_bytes(archive)
for name,raw in members.items():
    size,expected=LIBGCC_MEMBERS[name]
    if len(raw)!=size or digest(raw)!=expected:raise ValueError('original libgcc member differs: '+name)
    (out/name).write_bytes(raw)
manifest=dict(schema='hp1020-entry-usb-libgcc-v1',
    archive=dict(file='libgcc.a',original_path=str(original),sha256=digest(archive),bytes=len(archive)),
    members={name:dict(file=name,sha256=digest(raw),bytes=len(raw)) for name,raw in members.items()})
(out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
PY
"$GCC_PREFIX-gcc" -nostdlib -Wl,--gc-sections,--print-gc-sections -Wl,-T,"$SOURCE/runtime.ld" \
  -Wl,-Map,"$OUT/entry-usb.map" "${objects[@]}" -lgcc -o "$OUT/entry-usb.elf"
"$BIN_PREFIX-objdump" -d "$OUT/entry-usb.elf" > "$OUT/disassembly.txt"
"$BIN_PREFIX-nm" -n -S "$OUT/entry-usb.elf" > "$OUT/symbols.txt"
"$BIN_PREFIX-readelf" -W -h -l -S "$OUT/entry-usb.elf" > "$OUT/layout.txt"
if [[ -n "$("$BIN_PREFIX-nm" -u "$OUT/entry-usb.elf")" ]]; then
  echo 'Unexpected undefined continuous USB target symbol' >&2
  exit 1
fi
# Preserve input objects as well as the final ELF. The audit must establish
# that a custom NOLOAD allocation did not discard any nonzero initializer.
# The capture owns their exact bytes even if scratch source paths disappear.
echo 'Built ELF-only RAM USB lifetime; whole-linked audit and continuous execution still required.'
