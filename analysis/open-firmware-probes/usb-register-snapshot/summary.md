# HP 1020 USB Register Snapshot Probe Build

This artifact is offline only. It was not uploaded to the printer.

## Outputs

- ELF: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.elf`
- Date-prefixed image: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.img`
- PJL/ACL upload wrapper: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.dl`
- Layout report: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/layout.md`
- Safety scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/safety-scan.md`
- USB contract scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/usb-contract-scan.md`

## Key Checks

```text
PASS /Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.dl
kind=dl_upload image_bytes=122552 elf_bytes=122544
entry=0x100167a8 machine=0xabc7 phnum=11 shnum=21
```

```text
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.elf: ELF 32-bit MSB executable, Old Xtensa (unofficial), version 1 (SYSV), statically linked, not stripped
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.img: data
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/usb-register-snapshot/hp1020-usb-snapshot-probe.dl:  HP Printer Job Language data
```

## Meaning

This open-code probe reads only the mapped USB 0xb300 registers into local RAM and then idles.
It does not write USB MMIO, engine MMIO, video MMIO, or attempt printing.
It is a candidate for later controlled hardware testing only after review.
