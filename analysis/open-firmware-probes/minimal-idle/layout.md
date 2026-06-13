# Firmware Layout Report

This is an offline structural check for HP LaserJet 1020/1020 Plus firmware blobs.
It does not upload anything to the printer.

## Result

- Input: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl`
- Profile: `boot-probe`
- Source kind: `dl_upload`
- Validation: `PASS`
- Source bytes: `121931`
- Date-prefixed image bytes: `121880`
- Raw ELF bytes: `121872`
- Date prefix: `20260613`

## Upload Envelope

- PJL/ACL prefix bytes: `34`
- ACL magic: `00acc0de`
- ACL ELF length: `121872`
- Embedded image offset: `42`
- Embedded image length: `121880`
- UEL trailer: `1b252d313233343558`

## ELF Header

- Class/data: `ELF32` / `big-endian`
- Type: `0x2`
- Machine: `0xabc7`
- Entry point: `0x100167a8`
- Program headers: `11`
- Section headers: `21`
- LOAD segment file bytes: `109544`
- LOAD segment memory bytes: `109544`
- Allocated section bytes: `1963`
- Executable section bytes: `1451`

## Critical Sections

| Section | Address | Size | Flags |
| --- | ---: | ---: | --- |
| `.WindowVectors.text` | `0x10000000` | `0x180` | `AX` |
| `.sys_interface_table` | `0x10000370` | `0x12c` | `WA` |
| `.rodata` | `0x10003000` | `0x20` | `A` |
| `.text` | `0x10005c80` | `0xd` | `AX` |
| `.ResetVector.text` | `0x10100020` | `0x2e0` | `AX` |

## Anchor Addresses

| Name | Address | Section |
| --- | ---: | --- |
| `elf_entry` | `0x100167a8` | `.text.entry` |
| `reset_vector` | `0x10100020` | `.ResetVector.text` |
| `sys_interface_table` | `0x10000370` | `.sys_interface_table` |

## Program Headers

| # | Type | Offset | VAddr | File Size | Mem Size | Flags | Align |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `LOAD` | `0x1000` | `0x10000000` | `0x180` | `0x180` | `0x5` | `0x1000` |
| 1 | `LOAD` | `0x1180` | `0x10000180` | `0x4` | `0x4` | `0x5` | `0x1000` |
| 2 | `LOAD` | `0x1200` | `0x10000200` | `0x1c` | `0x1c` | `0x5` | `0x1000` |
| 3 | `LOAD` | `0x121c` | `0x1000021c` | `0x4` | `0x4` | `0x5` | `0x1000` |
| 4 | `LOAD` | `0x1220` | `0x10000220` | `0x1c` | `0x1c` | `0x5` | `0x1000` |
| 5 | `LOAD` | `0x1270` | `0x10000270` | `0xe0` | `0xe0` | `0x5` | `0x1000` |
| 6 | `LOAD` | `0x1370` | `0x10000370` | `0x12c` | `0x12c` | `0x6` | `0x1000` |
| 7 | `LOAD` | `0x2000` | `0x10003000` | `0x1a52c` | `0x1a52c` | `0x7` | `0x1000` |
| 8 | `LOAD` | `0x1d020` | `0x10100020` | `0x2e0` | `0x2e0` | `0x5` | `0x1000` |
| 9 | `LOAD` | `0x1d300` | `0x10100300` | `0x4` | `0x4` | `0x5` | `0x1000` |
| 10 | `LOAD` | `0x1d320` | `0x10100320` | `0xc` | `0xc` | `0x5` | `0x1000` |

## Practical Meaning

A replacement/prototype image has to preserve the upload envelope, date-prefixed image convention,
ELF class/endianness/machine identity, entry/reset-vector placement, and the memory layout expected
by the printer boot path. Passing this check would not prove a firmware is safe or useful, but failing
it means the blob is structurally wrong before hardware testing even begins.
