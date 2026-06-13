# HP 1020 Minimal Idle Probe Build

This artifact is offline only. It was not uploaded to the printer.

## Outputs

- ELF: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.elf`
- Date-prefixed image: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.img`
- PJL/ACL upload wrapper: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl`
- Layout report: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/layout.md`
- Safety scan: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/safety-scan.md`

## Key Checks

```text
PASS /Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl
kind=dl_upload image_bytes=121880 elf_bytes=121872
entry=0x100167a8 machine=0xabc7 phnum=11 shnum=21
```

```text
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.elf: ELF 32-bit MSB executable, Old Xtensa (unofficial), version 1 (SYSV), statically linked, not stripped
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.img: data
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl:  HP Printer Job Language data
```

## Meaning

The build proves we can generate an HP-shaped, old-Xtensa, date-prefixed firmware upload candidate from our own assembly.
The system interface table is open-code only: all 75 slots point to the local trap loop, not copied HP routines.
The early runtime-vector placeholders at 0x10006a14 and 0x10006a58 also point only to local trap/state placeholders.
It does not prove the printer boot ROM will accept it, and it does not attempt printing.
