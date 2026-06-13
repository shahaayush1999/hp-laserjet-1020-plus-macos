# HP 1020 Boot/Upload Handoff Analysis

This is an offline analysis. It does not contact the printer.

## Plain Result

The open idle probe now matches the outer firmware shape well enough for a controlled boot experiment:

- HP-style PJL/ACL wrapper
- 8-byte date prefix
- big-endian old-Xtensa ELF machine id `0xabc7`
- HP entry address `0x100167a8`
- HP vector/interface/reset anchor addresses

The remaining unknown is not packaging anymore. It is whether the printer's resident boot/ACL code expects the uploaded firmware to provide more of HP's runtime ABI than our idle probe currently provides.

## Stock vs Idle Probe

| Item | Stock HP firmware | Open idle probe |
| --- | ---: | ---: |
| Source bytes | `128431` | `121931` |
| Image bytes | `128380` | `121880` |
| Date prefix | `20050309` | `20260613` |
| ELF machine | `0x0000abc7` | `0x0000abc7` |
| ELF entry | `0x100167a8` | `0x100167a8` |
| Program headers | `11` | `11` |
| Section headers | `39` | `21` |
| System-interface unique targets | `75` | `1` |

## Entry/Runtime Vector Words

These words are important in the stock firmware because the ELF entry jumps into low-level CPU/runtime setup through them.

| Address | Stock value | Stock label/section | Probe value | Probe label/section |
| ---: | ---: | --- | ---: | --- |
| `0x10006a14` | `0x10006cd0` | hp1020_cpu_tlb_init_candidate | `0x10005c88` | .text |
| `0x10006a18` | `0x1001d498` | .data | `0x1001d498` | .runtime_state |
| `0x10006a1c` | `0x10016c5c` | .text | `0x10005c88` | .text |
| `0x10006a58` | `0x1001861c` | hp1020_interrupt_context_save_dispatch_candidate | `0x10005c88` | .text |
| `0x10006a60` | `0x1001d4ac` | .data | `0x1001d4ac` | .interrupt_table |
| `0x10006a64` | `0x100187e0` | .text | `0x10005c88` | .text |

## ACL Module Descriptor

The stock firmware has a descriptor-like table at `0x1001be90`. The first word points at `0x10000350`, which is exactly the boundary after `.DoubleExceptionVector.text`; the next word is ASCII `ACL`.

| # | Address | Value | Decoded text / target |
| ---: | ---: | ---: | --- |
| `0` | `0x1001be90` | `0x10000350` |  |
| `1` | `0x1001be94` | `0x41434c00` | ACL |
| `2` | `0x1001be98` | `0x100040c4` | ID |
| `3` | `0x1001be9c` | `0x100040bc` | CONFIG |
| `4` | `0x1001bea0` | `0x100040b4` | MEMORY |
| `5` | `0x1001bea4` | `0x100040ac` | STATUS |
| `6` | `0x1001bea8` | `0x100040a0` | VARIABLES |
| `7` | `0x1001beac` | `0x10004098` | USTATUS |
| `8` | `0x1001beb0` | `0x1000408c` | DENSITYLUT |
| `9` | `0x1001beb4` | `0x10004080` | PAGECOUNT |
| `10` | `0x1001beb8` | `0x10004048` | SERVICEID |
| `11` | `0x1001bebc` | `0x10004070` | COLORMETRICS |
| `12` | `0x1001bec0` | `0x00000000` |  |
| `13` | `0x1001bec4` | `0x40504a4c` | @PJL |
| `14` | `0x1001bec8` | `0x00000000` |  |
| `15` | `0x1001becc` | `0x1b252d31` |  |
| `16` | `0x1001bed0` | `0x32333435` | 2345 |
| `17` | `0x1001bed4` | `0x58000000` | X |
| `18` | `0x1001bed8` | `0x504a4c00` | PJL |
| `19` | `0x1001bedc` | `0x100044c0` | @PJL USTATUS DEVICE
CODE=35031
DISPLAY=INVALID PERSONALITY
 |

## System Interface Strategy

The stock table has 75 mostly distinct runtime-service function pointers. The idle probe intentionally does not copy those HP routines. Instead, every interface slot points to one local trap loop.

| Firmware | Table behavior | Practical meaning |
| --- | --- | --- |
| Stock | `75` unique targets | full HP/ThreadX runtime services |
| Idle probe | `1` unique target: `0x10005c88` | unexpected interface call hangs in our code instead of jumping through null or touching hardware |

## Hardware-Test Readiness

A first hardware test is now technically defined, but still optional:

1. Power-cycle printer.
2. Upload only `analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl`.
3. Send no document and no ZjStream data.
4. Watch whether the USB device disappears, re-enumerates, or hangs until power-cycle.

This would answer one narrow question: does the printer accept and branch into our uploaded code at all?

## Remaining Offline Unknowns

- Whether the resident boot/ACL code validates the exact HP section table or only the loadable program headers.
- Whether `0x10000350` is patched or treated specially by resident boot code during ACL module handling.
- Whether the ELF entry is reached directly after upload, or whether the boot path expects the HP CPU/TLB init sequence first.
- Whether an idle-only payload leaves USB in a recoverable-but-non-enumerating state until power-cycle.

## Recommendation

There is still offline value in tightening the upload harness and documenting expected observations, but the core packaging/shape question is now mostly answered. The next truly decisive question requires a hardware upload of the idle probe.
