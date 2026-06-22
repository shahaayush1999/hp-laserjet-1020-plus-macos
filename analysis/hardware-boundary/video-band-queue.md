# HP 1020 Video Band Queue/List Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: `0x10013f34` descriptor queue/list helper and raw-band register feed

## Key Literal Values

| Name | Value |
|---|---:|
| `high_bit` | `0x80000000` |
| `high_bit_clear_mask` | `0x7fffffff` |
| `video_state_base` | `0x1002efc0` |
| `ring_descriptor_base` | `0x1002efe0` |
| `callback_ptr_cell` | `0x1002efb0` |
| `dual_block_mode_ptr` | `0x1001cdac` |
| `raw_band_a_pointer` | `0xb1000008` |
| `raw_band_b_pointer` | `0xb1000108` |
| `raw_band_a_flags` | `0xb100000c` |
| `block_a_status` | `0xb1000004` |
| `block_b_status` | `0xb1000104` |
| `raw_band_b_flags` | `0xb100010c` |

## Descriptor Fields

| Offset | Field | Meaning |
|---:|---|---|
| `+0x00` | descriptor busy/owned flag | set by 0x10014244 helper; cleared by IRQ band-done path |
| `+0x04` | final/secondary flag | allows one more queue iteration when next +0xdc would meet +0xe0; contributes raw-band flag bit 0x18 |
| `+0x08` | band units/count | fed to callback, raw-band flag encoding, remaining +0xd4 decrement, and dual-block half-count |

## Queue Sequences

### `queue_loop_gate`

- registers: `0xb1000004`

1. select descriptor at `0x1002efe0 + (video_state +0xdc) * 0x0c`
2. continue only while block A status bit 0x100 is set
3. stop when the next +0xdc slot would equal +0xe0 unless the current descriptor final flag is nonzero

### `optional_callback_and_padding`

- registers: -

1. when state +0xc0 and callback pointer are nonzero, optionally zero padding after the descriptor band
2. if remaining +0xd4 is within the current descriptor size, set high bit 0x80000000 on the per-slot control word
3. call the callback with adjusted pointer, per-slot control word, and descriptor units masked to a multiple of four
4. after callback, use the per-slot control word as the raw-band pointer/control source

### `raw_band_single_block_write`

- registers: `0xb1000008`, `0xb100000c`

1. write descriptor pointer/control to 0xb1000008
2. encode descriptor units using the firmware helper and state +0xc4
3. OR descriptor final flag into bit 0x18 and write 0xb100000c

### `raw_band_dual_block_write`

- registers: `0xb1000008`, `0xb1000108`, `0xb100000c`, `0xb100010c`

1. write A pointer/control to 0xb1000008
2. write B pointer/control as A plus state +0xbc to 0xb1000108
3. encode half descriptor units for both blocks
4. wait for A and B status bit 0x100 before writing flags
5. OR descriptor final flag into A bit 0x18 and state +0xec into B bit 0x19

### `advance_queue_side`

- registers: `0xb1000004`

1. subtract descriptor units from state +0xd4
2. advance state +0xdc modulo 4
3. load the next 0x0c-byte descriptor record and re-read block A status

## Loop Scenarios

| Scenario | +0xdc | +0xe0 | Final flag | Next slot | Decision | +0xdc after |
|---|---:|---:|---:|---:|---|---:|
| `dc_0_e0_2_final_0` | `0` | `2` | `0` | `1` | `queue_descriptor` | `1` |
| `dc_0_e0_1_final_0` | `0` | `1` | `0` | `1` | `stop_before_e0_collision` | `0` |
| `dc_0_e0_1_final_1` | `0` | `1` | `1` | `1` | `queue_descriptor` | `1` |
| `dc_3_e0_0_final_0` | `3` | `0` | `0` | `0` | `stop_before_e0_collision` | `3` |

## Evidence Checks

| Check | Status | Needle |
|---|---|---|
| `descriptor_base_dc` | `present` | `PTR_DAT_100067bc + *(int *)(PTR_DAT_10006770 + 0xdc) * 0xc` |
| `loop_requires_ready_0x100` | `present` | `while (((uVar8 & 0x100) != 0` |
| `loop_stops_at_e0_unless_final` | `present` | `(*(int *)(puVar2 + 0xdc) + 1U & 3) != *(uint *)(puVar2 + 0xe0)` |
| `source_pointer_from_slot` | `present` | `iVar7 = *(int *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4)` |
| `callback_enabled_by_c0` | `present` | `if (*(int *)(puVar2 + 0xc0) != 0)` |
| `callback_pointer_present` | `present` | `if (*(int *)puVar4 != 0)` |
| `final_padding_zero` | `present` | `if (*(int *)(puVar6 + 4) != 0)` |
| `high_bit_set_on_last_units` | `present` | `*(uint *)(puVar2 + *(int *)(puVar2 + 0xdc) * 4 + 0x10) + DAT_10005e34` |
| `callback_call` | `present` | `(**(code **)puVar4)` |
| `dual_block_branch` | `present` | `if (*(int *)PTR_DAT_100067c8 == 1)` |
| `raw_band_a_pointer_write` | `present` | `*DAT_100067cc = iVar7` |
| `raw_band_b_pointer_write` | `present` | `*piVar5 = iVar7 + *(int *)(puVar2 + 0xbc)` |
| `raw_band_a_ready_wait` | `present` | `while ((uVar8 & 0x100) == 0)` |
| `raw_band_a_flags_write` | `present` | `*DAT_100067d4 = uVar9` |
| `raw_band_b_flags_write` | `present` | `*DAT_100067dc = uVar9 \| (uint)(*(int *)(puVar2 + 0xec) != 0) << 0x19` |
| `single_block_flags_write` | `present` | `*DAT_100067d4 = uVar8 \| (uint)(*(int *)(puVar6 + 4) != 0) << 0x18` |
| `remaining_d4_decrement` | `present` | `*(int *)(puVar2 + 0xd4) = *(int *)(puVar2 + 0xd4) - *(int *)(puVar6 + 8)` |
| `dc_advance_mod4` | `present` | `uVar9 = *(int *)(puVar2 + 0xdc) + 1U & 3` |

## Open Firmware Meaning

- This helper is the queue/list side paired with IRQ band-done refill; it explains how +0xdc advances.
- The helper will not blindly overrun +0xe0 unless the current descriptor carries its final/secondary flag.
- It is also a raw-band MMIO writer, so it remains unsafe for early custom firmware until live video timing is proven.

