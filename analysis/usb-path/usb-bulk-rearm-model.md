# HP 1020 USB Bulk Re-Arm Model

This is an offline static model. It does not contact the printer.

## Key Result

- Stock receive re-arm writes a receive target pointer into descriptor bytes `+0x08..+0x0b`.
- It submits descriptor pool pointer `0x90021370` through MMIO register `0xb3000234`.
- It sets the visible bulk-done byte and clears the bulk RX done flag after descriptor setup.

## Constants

| Name | Value |
|---|---:|
| `descriptor_pool_pointer_word` | `0x1001bc48` |
| `bulk_buffer_base_word` | `0x1001bc40` |
| `next_aligned_pointer_word` | `0x1001bc44` |
| `descriptor_mode_flag_byte` | `0x1001bc6e` |
| `descriptor_submit_register` | `0xb3000234` |
| `descriptor_busy_flag_byte` | `0x1001bc6c` |
| `bulk_done_byte` | `0x1001bc70` |
| `bulk_rx_done_flag` | `0x1001bc72` |
| `descriptor_pool` | `0x90021370` |
| `bulk_buffer_base` | `0x900216f0` |

## Descriptor Layout

| Field | Meaning |
|---|---|
| `+0x08..+0x0b` | big-endian receive target pointer |
| `+0x0c..+0x0f` | zeroed tail/control bytes |
| `sram[0]` | opcode/value 8 written through descriptor SRAM pointer |
| `sram[1..3]` | zeroed after submit |

## Branch Model

| Condition | Target pointer | Mode flag |
|---|---|---:|
| next pointer is zero or not 16-byte aligned | bulk buffer base + caller offset | `0` |
| next pointer is non-zero and 16-byte aligned | next aligned pointer | `1` |

## Open-Firmware Meaning

- Bulk receive is descriptor-based, not just a raw write to the USB data FIFO.
- The open shim needs to write the receive target pointer into descriptor bytes +0x08..+0x0b, submit descriptor 0x90021370 through 0xb3000234, and reset the visible done flags.
- The stock path uses a 16-byte alignment decision for the next receive pointer; an open implementation should preserve that alignment rule until hardware behavior is proven otherwise.

## Evidence Checks

- status: `pass`

| Status | Name | Evidence | Needle |
|---|---|---|---|
| `present` | `reads_next_aligned_pointer_candidate` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `uVar7 = *(uint *)PTR_DAT_10005e54` |
| `present` | `falls_back_when_next_pointer_absent_or_unaligned` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `(uVar7 == 0) \|\| ((uVar7 & 0xf) != 0)` |
| `present` | `falls_back_to_buffer_base_plus_offset` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `param_1 = *(int *)PTR_DAT_10005e44 + param_1` |
| `present` | `writes_descriptor_address_bytes` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*(char *)(iVar6 + 8)` |
| `present` | `writes_descriptor_mode_flag` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*PTR_DAT_10005e28 = uVar5` |
| `present` | `submits_descriptor_pointer_to_mmio` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*piVar2 = iVar6` |
| `present` | `zeros_descriptor_tail_bytes` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*(undefined1 *)(iVar6 + 0xc) = 0` |
| `present` | `writes_sram_descriptor_opcode` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*puVar4 = 8` |
| `present` | `sets_bulk_done_byte` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*puVar1 = 1` |
| `present` | `clears_bulk_rx_done_flag` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `*puVar3 = 0` |

