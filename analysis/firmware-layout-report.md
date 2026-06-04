# Firmware Layout Report

This is an offline structural check for HP LaserJet 1020/1020 Plus firmware blobs.
It does not upload anything to the printer.

## Result

- Input: `assets/runtime/sihp1020.dl`
- Source kind: `dl_upload`
- Validation: `PASS`
- Source bytes: `128431`
- Date-prefixed image bytes: `128380`
- Raw ELF bytes: `128372`
- Date prefix: `20050309`

## Upload Envelope

- PJL/ACL prefix bytes: `34`
- ACL magic: `00acc0de`
- ACL ELF length: `128372`
- Embedded image offset: `42`
- Embedded image length: `128380`
- UEL trailer: `1b252d313233343558`

## ELF Header

- Class/data: `ELF32` / `big-endian`
- Type: `0x2`
- Machine: `0xabc7`
- Entry point: `0x100167a8`
- Program headers: `11`
- Section headers: `39`
- LOAD segment file bytes: `109820`
- LOAD segment memory bytes: `207004`
- Allocated section bytes: `207003`
- Executable section bytes: `91295`

## Critical Sections

| Section | Address | Size | Flags |
| --- | ---: | ---: | --- |
| `.WindowVectors.text` | `0x10000000` | `0x180` | `AX` |
| `.sys_interface_table` | `0x10000370` | `0x12c` | `WA` |
| `.rodata` | `0x10003000` | `0x2c80` | `A` |
| `.text` | `0x10005c80` | `0x15f0f` | `AX` |
| `.data` | `0x1001bb90` | `0x1ab0` | `WA` |
| `.bss` | `0x1001d640` | `0x17ba0` | `WA` |
| `.ResetVector.text` | `0x10100020` | `0x2e0` | `AX` |

## Anchor Addresses

| Name | Address | Section |
| --- | ---: | --- |
| `elf_entry` | `0x100167a8` | `.text` |
| `reset_vector` | `0x10100020` | `.ResetVector.text` |
| `sys_interface_table` | `0x10000370` | `.sys_interface_table` |
| `threadx_queue_create_wrapper_candidate` | `0x10017f18` | `.text` |
| `threadx_queue_receive_wrapper_candidate` | `0x1001809c` | `.text` |
| `threadx_queue_send_wrapper_candidate` | `0x100180dc` | `.text` |
| `threadx_thread_create_wrapper_candidate` | `0x10018274` | `.text` |
| `queue_send_by_id_candidate` | `0x10013668` | `.text` |
| `engine_thread_candidate` | `0x100163b0` | `.text` |
| `video_thread_candidate` | `0x10013c18` | `.text` |
| `print_mgr_thread_candidate` | `0x1000f324` | `.text` |

## Program Headers

| # | Type | Offset | VAddr | File Size | Mem Size | Flags | Align |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `LOAD` | `0x194` | `0x10000000` | `0x180` | `0x180` | `0x5` | `0x1` |
| 1 | `LOAD` | `0x314` | `0x10000180` | `0x4` | `0x4` | `0x5` | `0x1` |
| 2 | `LOAD` | `0x318` | `0x10000200` | `0x1c` | `0x1c` | `0x5` | `0x1` |
| 3 | `LOAD` | `0x334` | `0x1000021c` | `0x4` | `0x4` | `0x5` | `0x1` |
| 4 | `LOAD` | `0x338` | `0x10000220` | `0x1c` | `0x1c` | `0x5` | `0x1` |
| 5 | `LOAD` | `0x354` | `0x10000270` | `0xe0` | `0xe0` | `0x5` | `0x1` |
| 6 | `LOAD` | `0x434` | `0x10000370` | `0x12c` | `0x12c` | `0x6` | `0x1` |
| 7 | `LOAD` | `0x560` | `0x10003000` | `0x1a640` | `0x321e0` | `0x7` | `0x1` |
| 8 | `LOAD` | `0x1aba0` | `0x10100020` | `0x2e0` | `0x2e0` | `0x5` | `0x1` |
| 9 | `LOAD` | `0x1ae80` | `0x10100300` | `0x4` | `0x4` | `0x5` | `0x1` |
| 10 | `LOAD` | `0x1ae84` | `0x10100320` | `0xc` | `0xc` | `0x5` | `0x1` |

## Practical Meaning

A replacement/prototype image has to preserve the upload envelope, date-prefixed image convention,
ELF class/endianness/machine identity, entry/reset-vector placement, and the memory layout expected
by the printer boot path. Passing this check would not prove a firmware is safe or useful, but failing
it means the blob is structurally wrong before hardware testing even begins.
