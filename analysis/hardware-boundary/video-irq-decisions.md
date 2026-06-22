# HP 1020 Video IRQ Decision Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- function: `0x100144d0 hp1020_video_irq_or_band_done_candidate`
- scenarios: `11`
- scenario failures: `0`

## Branch Priority

1. 0x20 band done/refill
2. 0x02 reset dispatch case 0
3. 0x04 recovery or reset dispatch case 0
4. 0x01 latch or reset dispatch case 7
5. 0x08 reset dispatch case 3
6. 0x10 reset dispatch case 4

## Scenario Table

| Scenario | Status | Block A | Block B | State +0x70 | State +0x6c | State +0xf0 | +0xfc negative | Category | Reset dispatch | Actions | Trace |
|---|---|---:|---:|---|---:|---|---|---|---:|---|---|
| `band_done_ring_refill` | `pass` | `0x20` | `0x00` | `False` | `0` | `False` | `False` | `band_done` | `-` | `increment video_state +0xf8`<br>`set video_state +0xf0`<br>`clear ring record at +0x20 + (+0xd8 * 0x0c)`<br>`advance +0xd8 modulo 4`<br>`refill channel-B descriptor`<br>`queue/list next band` | `bit_0x20_band_done_priority`<br>`ring_record_complete_and_refill` |
| `band_done_raw_band_refresh` | `pass` | `0x00` | `0x20` | `False` | `0` | `False` | `True` | `band_done` | `-` | `increment video_state +0xf8`<br>`set video_state +0xf0`<br>`advance video_state +0xa0 list`<br>`refresh raw bands` | `bit_0x20_band_done_priority`<br>`fc_negative_raw_band_refresh` |
| `bit_0x02_reset_case_0` | `pass` | `0x02` | `0x00` | `False` | `0` | `False` | `False` | `reset_dispatch` | `0` | - | `block_a_bit_0x02_reset_case_0` |
| `bit_0x04_rearm_without_reset` | `pass` | `0x04` | `0x00` | `True` | `2` | `False` | `False` | `recover_or_reset` | `-` | `clear video_state +0x70`<br>`clear video_state +0xdc`<br>`toggle block control bit 0x100 after busy waits`<br>`queue/list next band` | `block_a_bit_0x04_recovery`<br>`rearm_video_blocks_without_reset_dispatch` |
| `bit_0x04_dispatch_case_0_after_done` | `pass` | `0x04` | `0x00` | `True` | `2` | `True` | `False` | `recover_or_reset` | `0` | `clear video_state +0x70` | `block_a_bit_0x04_recovery`<br>`state_f0_already_seen_dispatch_case_0` |
| `bit_0x01_dispatch_case_7_when_idle` | `pass` | `0x01` | `0x00` | `False` | `0` | `False` | `False` | `latch_or_reset_case_7` | `7` | `set video_state +0x70`<br>`signal video event object` | `bit_0x01_latch_or_case_7` |
| `bit_0x01_latch_when_running` | `pass` | `0x00` | `0x01` | `False` | `2` | `False` | `False` | `latch_or_reset_case_7` | `-` | `set video_state +0x70` | `bit_0x01_latch_or_case_7` |
| `bit_0x08_reset_case_3` | `pass` | `0x08` | `0x00` | `False` | `0` | `False` | `False` | `reset_dispatch` | `3` | - | `bit_0x08_reset_case_3` |
| `bit_0x10_reset_case_4` | `pass` | `0x00` | `0x10` | `False` | `0` | `False` | `False` | `reset_dispatch` | `4` | - | `bit_0x10_reset_case_4` |
| `bit_0x10_ignored_without_dual_block` | `pass` | `0x00` | `0x10` | `False` | `0` | `False` | `False` | `no_action` | `-` | - | `no_modeled_status_bit` |
| `priority_0x20_over_0x02` | `pass` | `0x22` | `0x00` | `False` | `0` | `False` | `False` | `band_done` | `-` | `increment video_state +0xf8`<br>`set video_state +0xf0`<br>`clear ring record at +0x20 + (+0xd8 * 0x0c)`<br>`advance +0xd8 modulo 4`<br>`refill channel-B descriptor`<br>`queue/list next band` | `bit_0x20_band_done_priority`<br>`ring_record_complete_and_refill` |

## Evidence Checks

| Check | Status | Needle |
|---|---|---|
| `bit_0x20_priority` | `present` | `(*DAT_100067c0 & 0x20) != 0` |
| `bit_0x20_ack_a` | `present` | `*puVar2 = 0xffffffdf` |
| `bit_0x20_ack_b` | `present` | `*DAT_100067d8 = 0xffffffdf` |
| `fc_negative_raw_band_path` | `present` | `if (*(int *)(puVar1 + 0xfc) < 0)` |
| `ring_done_index_advance` | `present` | `*(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3` |
| `bit_0x02_reset_case_0` | `present` | `uVar6 = 0` |
| `bit_0x04_recovery_branch` | `present` | `if ((*DAT_100067c0 & 4) != 0)` |
| `bit_0x04_ack` | `present` | `*DAT_100067c0 = 0xfffffffb` |
| `bit_0x04_done_case_0` | `present` | `FUN_10013d4c(0)` |
| `bit_0x01_case_7` | `present` | `FUN_10013d4c(7)` |
| `bit_0x08_case_3` | `present` | `uVar6 = 3` |
| `bit_0x10_case_4` | `present` | `uVar6 = 4` |
| `bit_0x10_ack` | `present` | `uVar4 = 0xffffffef` |
| `dispatch_param` | `present` | `FUN_10013d4c(uVar6)` |
| `event_10_ack` | `present` | `FUN_100171e0(10)` |
| `event_0x0b_ack` | `present` | `FUN_100171e0(0xb)` |

## Open Firmware Meaning

- The video IRQ path is not a single done bit; multiple block-status bits have different reset/recovery meanings.
- Bit 0x20 is the continue/refill path and has priority over reset bits.
- Reset dispatch cases 3, 4, and 7 become video reset event words through the video-to-engine feedback model.
- Hardware calibration is still needed to attach physical labels to these video block status bits.

