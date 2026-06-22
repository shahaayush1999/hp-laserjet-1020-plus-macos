# HP 1020 USB Interrupt Event Model

This is an offline model of the interrupt-side producer for USB event flags. It does not contact the printer.

## Key Result

- USB interrupt task `0x10008208` scans two groups of 16 event lanes.
- Each lane uses a `0x20`-byte hardware/status stride.
- Per-lane status bit `0x400` is the strongest static completion signal feeding `0x10021318` event flags.
- This narrows a future open polling loop to a concrete register/lane map, but live transition order still needs hardware evidence.

## Resolved Constants

| Name | Value |
|---|---:|
| `irq_status` | `0xb300040c` |
| `irq_pending_lanes` | `0xb3000414` |
| `usb_global_status` | `0xb3010004` |
| `control_setup_gate` | `0xb3000400` |
| `masked_lane_word` | `0xb3000418` |
| `lane_bank0_base` | `0xb3000004` |
| `lane_bank1_base` | `0xb3000204` |
| `pending_transfer_list` | `0x10022740` |
| `transfer_state` | `0x100212d4` |
| `completion_event_flags` | `0x10021318` |
| `event_ack_register` | `0xb3000200` |
| `event_signature_mask` | `0xc0000000` |
| `event_signature_value` | `0x80000000` |
| `bulk_available_size_word` | `0x1001bc50` |
| `bulk_source_offset_word` | `0x1001bc4c` |
| `bulk_next_offset_word` | `0x100216c0` |
| `bulk_buffer_base_word` | `0x1001bc40` |
| `bulk_suppress_copy_byte` | `0x1001bc6f` |
| `bulk_remaining_request_word` | `0x1001bc54` |
| `bulk_threshold_word` | `0x10021590` |
| `bulk_next_pointer_word` | `0x1001bc44` |
| `bulk_destination_offset_word` | `0x10021594` |

## Event Scan

- pending word: `0xb3000414`
- mask word: `0xb3000418`
- lane stride: `0x20`
- per-lane status bits: `0x200`, `0x80`, `0x40`, `0x30`, `0x400`
- completion status bit: `0x400`

| Bank | Lane Base | Event Bits |
|---:|---:|---|
| `0` | `0xb3000004` | `0x00000001..0x00008000` |
| `1` | `0xb3000204` | `0x00010000..0x80000000` |

## Bulk Receive Lane

- bank/lane: `1` / `1`
- event bit: `0x00020000`
- lane status register: `0xb3000224`
- lane ack register: `0xb3000220`
- ack bits: `0x80`, `0x400`
- guard: bank 1 lane 1 and bulk_done_byte != 0

Bulk buffer fields updated by this branch:

| Field | Address |
|---|---:|
| `available_size_word` | `0x1001bc50` |
| `source_offset_word` | `0x1001bc4c` |
| `next_offset_word` | `0x100216c0` |
| `buffer_base_word` | `0x1001bc40` |
| `suppress_copy_byte` | `0x1001bc6f` |
| `remaining_request_word` | `0x1001bc54` |
| `threshold_word` | `0x10021590` |
| `next_pointer_word` | `0x1001bc44` |
| `destination_offset_word` | `0x10021594` |

## Event Flag Outputs

| Condition | Call | Meaning |
|---|---|---|
| per-lane status bit 0x400 and event bit != 0x2 | `event_flags_set(0x10021318, event_bit, 0)` | normal completion wake for endpoint/control transfer lanes |
| bank 1 transfer-service branch | `event_flags_set(0x10021318, event_bit, 0)` | main USB2Thread/service wake after transfer-buffer processing |

## Special Cases

- event bit 0x2 has a pending-transfer-list path instead of the direct completion event set
- bank 1 lane 1 processes 0x90022bc0-style descriptor/event records before setting its event bit
- bank 1 lane 1 is the bulk receive lane: event bit 0x00020000, lane status 0xb3000224, lane ack 0xb3000220
- USB2Thread separately waits on event bit 0x00010000
- control-IN data stage waits on event bit 0x00000001

## Open-Firmware Meaning

- A future bulk receive loop should watch bank 1 lane 1: status register 0xb3000224, ack register 0xb3000220, and event bit 0x00020000.
- The interrupt task updates the stock receive counters before waking the waiting read callback, then calls the descriptor re-arm function.
- This still needs live hardware proof before open code should rely on the exact transition order.

## Evidence Checks

- status: `pass`

| Status | Needle |
|---|---|
| `present` | `uVar7 = *DAT_10005de4` |
| `present` | `uVar12 = *DAT_10005de8` |
| `present` | `uVar13 = *DAT_10005e00` |
| `present` | `puVar10 = (uint *)(uVar8 * 0x20 + iVar11)` |
| `present` | `if ((uVar9 & 0x400) != 0)` |
| `present` | `FUN_10017dac(PTR_DAT_10005e18,iVar11,0)` |
| `present` | `if ((uVar8 == 1) && (*PTR_DAT_10005e20 != '\0'))` |
| `present` | `*(uint *)(DAT_10005e24 + 0x20) = *(uint *)(DAT_10005e24 + 0x20) \| 0x80` |
| `present` | `*(uint *)PTR_DAT_10005e38 = *(int *)PTR_DAT_10005e38 + uVar9` |
| `present` | `FUN_100086f4(*(undefined4 *)PTR_DAT_10005e40)` |
| `present` | `FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0)` |

