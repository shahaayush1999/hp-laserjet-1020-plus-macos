# HP 1020 USB Marker Draft Build

This artifact is offline only. It was not uploaded to the printer.

## Outputs

- ELF: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.elf`
- Date-prefixed image: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.img`
- PJL/ACL upload wrapper: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.dl`
- Layout report: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/layout.md`
- Safety scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/safety-scan.md`
- USB contract scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.md`
- USB MMIO access scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/usb-mmio-access-scan.md`
- Endpoint-0 sequence scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.md`
- Memory boundary scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.md`
- Marker descriptor check: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.md`
- Marker length-flow check: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.md`
- Behavior model: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/behavior-model.md`

## Key Checks

```text
PASS /Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.dl
kind=dl_upload image_bytes=123496 elf_bytes=123488
entry=0x100167a8 machine=0xabc7 phnum=11 shnum=22
```

```text
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.elf: ELF 32-bit MSB executable, Old Xtensa (unofficial), version 1 (SYSV), statically linked, not stripped
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.img: data
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.dl:  HP Printer Job Language data
```

```text
scenarios=6 marker=3 no_match=3
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/behavior-model.md
```

## Meaning

This open-code draft recognizes a USB product-string GET_DESCRIPTOR setup shape and tries to expose the marker string `HP1020 OPEN MARKER` through endpoint-0.
It writes only USB-controller MMIO registers that match the extracted stock endpoint-0 sequence contract.
It also writes the stock USB response-state RAM slots used by that contract; the memory boundary scan makes those non-MMIO writes explicit.
The marker descriptor check verifies the embedded `HP1020 OPEN MARKER` USB string descriptor, its length constant, and its 0x90000000 hardware alias pointer.
The marker length-flow check verifies the clipped USB request length is preserved into the endpoint-0 response-state write.
It does not touch engine, fuser, motor, paper-feed, video, or raster MMIO.
It is not hardware-ready; the missing proof is whether the setup buffer and stock response state are valid after custom upload.
