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
kind=dl_upload image_bytes=124792 elf_bytes=124784
entry=0x100167a8 machine=0xabc7 phnum=11 shnum=23
```

```text
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.elf: ELF 32-bit MSB executable, Old Xtensa (unofficial), version 1 (SYSV), statically linked, not stripped
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.img: data
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/hp1020-usb-marker-draft.dl:  HP Printer Job Language data
```

```text
scenarios=9 marker=7 poll_continue=2
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-marker-draft/behavior-model.md
```

## Meaning

This open-code draft polls for standard USB GET_DESCRIPTOR setup shapes and tries to answer device, configuration, language, manufacturer, and product-string requests through endpoint-0.
The product string is intentionally changed to `HP1020 OPEN MARKER` so a direct host descriptor read can prove open code controlled USB response data.
Non-matching setup packets or inactive USB gates now continue polling instead of parking after a one-shot miss.
It writes only USB-controller MMIO registers that match the extracted stock endpoint-0 sequence contract.
It also writes the stock USB response-state RAM slots used by that contract; the memory boundary scan makes those non-MMIO writes explicit.
For a matching request, it clips the host `wLength`, copies the selected descriptor into the stock control-IN staging buffer `0x90022bd0`, builds one four-word transfer descriptor at `0x900226f0`, submits that descriptor through `0xb3000014`, and kicks `0xb3000000 |= 0x108`.
The marker descriptor check verifies the embedded `HP1020 OPEN MARKER` USB string descriptor, its length constant, and its 0x90000000 hardware alias pointer.
The marker length-flow check verifies the clipped USB request length is preserved into the endpoint-0 response-state write and transfer descriptor word.
It does not touch engine, fuser, motor, paper-feed, video, or raster MMIO.
It is still not the first thing to upload; the missing proof is whether the setup buffer, staging buffer, descriptor ring, and controller completion path are valid after custom upload without the full stock USB runtime.
