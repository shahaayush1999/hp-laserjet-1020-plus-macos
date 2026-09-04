# HP 1020 Video Sideband Default Impact

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`

## Field Impact

| Work field | State fields | Risk | Current interpretation |
|---|---|---|---|
| `+0x26` | `+0xd0`, `+0xd4` | `critical` | not safe to assume zero for a printing path |
| `+0x30` | `+0xe8` | `unknown_low_in_current_static_view` | keep tracked, but it is not currently a first blocker compared with +0x26/+0x32 |
| `+0x32` | `+0xec` | `mode_critical` | ECONOMODE determines the value: normal fixtures use zero, draft uses one |

### `+0x26` If Zero

- 0x10014244 band helper sees +0xd0 == 0 and skips channel-B pointer/length writes
- 0x10013f34 sees +0xd4 <= descriptor_units<<2 immediately, setting the final/high-bit condition early
- after queue/list consumption, +0xd4 subtracts descriptor units and can underflow as an unsigned-looking counter

### `+0x30` If Zero

- prepare copies zero into +0xe8
- no downstream +0xe8 consumer was recovered in the selected video prepare/render/refill corpus

### `+0x32` If Zero

- prepare takes non-secondary timing/table branches when +0xec == 0
- 0x10013f34 does not OR secondary-output bit 0x19 into B raw-band flags
- 0x100140f8 reads +0xec in the alternate raw-refresh path

## Current Conclusion

- The sourced sideband fields have different zero-value consequences: +0x26 is immediately critical for channel-B refill and remaining/final accounting.
- +0x32 is mode-critical: ECONOMODE supplies zero normally and one for draft, affecting setup tables and B-side raw-band flags.
- +0x30 currently has no selected downstream consumer beyond prepare copying it to +0xe8, so it is tracked but lower priority.
- The direct START_PAGE builder resolves the source: VIDEO_Y initializes +0x26; physical counter behavior remains uncalibrated.

## Ghidra Exact State Access Scan

- path: `analysis/ghidra-probes/video-state-sideband-access-scan.md`
- language: `Xtensa:BE:32:default`
- access hits: `19`

| Address | Function | Access | Offset | Role | Classification | Instruction |
|---|---|---|---:|---|---|---|
| `10013fbb` | `10013f34 FUN_10013f34` | `load` | `0xd4` | `descriptor_final_accounting` | descriptor queue final/high-bit accounting | `l32i a9,a7,0xd4` |
| `10014088` | `10013f34 FUN_10013f34` | `load` | `0xec` | `descriptor_b_flag` | B-side raw-band flag bit source | `l32i a8,a7,0xec` |
| `100140c9` | `10013f34 FUN_10013f34` | `load` | `0xd4` | `descriptor_final_accounting` | descriptor queue final/high-bit accounting | `l32i a9,a7,0xd4` |
| `100140d7` | `10013f34 FUN_10013f34` | `store` | `0xd4` | `descriptor_final_accounting` | descriptor queue final/high-bit accounting | `s32i a9,a7,0xd4` |
| `100141b3` | `100140f8 FUN_100140f8` | `load` | `0xec` | `raw_refresh_b_flag` | alternate raw-refresh B-side flag source | `l32i a9,a4,0xec` |
| `1001425f` | `10014244 FUN_10014244` | `load` | `0xd0` | `channel_b_refill_counter` | channel-B refill amount and decrement path | `l32i a2,a7,0xd0` |
| `10014270` | `10014244 FUN_10014244` | `load` | `0xd0` | `channel_b_refill_counter` | channel-B refill amount and decrement path | `l32i a2,a7,0xd0` |
| `10014279` | `10014244 FUN_10014244` | `store` | `0xd0` | `channel_b_refill_counter` | channel-B refill amount and decrement path | `s32i a2,a7,0xd0` |
| `10014b7d` | `10014910 FUN_10014910` | `store` | `0xd0` | `prepare_seed` | video state seed from active work argument | `s32i a8,a5,0xd0` |
| `10014b83` | `10014910 FUN_10014910` | `store` | `0xd4` | `prepare_seed` | video state seed from active work argument | `s32i a8,a5,0xd4` |
| `10014b89` | `10014910 FUN_10014910` | `store` | `0xec` | `prepare_seed` | video state seed from active work argument | `s32i a8,a5,0xec` |
| `10014b8f` | `10014910 FUN_10014910` | `store` | `0xe8` | `prepare_seed` | video state seed from active work argument | `s32i a8,a5,0xe8` |
| `10014ea6` | `10014910 FUN_10014910` | `load` | `0xec` | `prepare_mode_consumer` | prepare setup branch/table consumer | `l32i a8,a8,0xec` |
| `10014ed0` | `10014910 FUN_10014910` | `load` | `0xec` | `prepare_mode_consumer` | prepare setup branch/table consumer | `l32i a8,a8,0xec` |
| `10014fc9` | `10014910 FUN_10014910` | `load` | `0xec` | `prepare_mode_consumer` | prepare setup branch/table consumer | `l32i a8,a8,0xec` |
| `100165e6` | `100165a4 FUN_100165a4` | `store` | `0xd0` | `stack_local_false_positive` | same numeric stack offset, not video state | `s32i a2,a1,0xd0` |
| `1001663a` | `100165a4 FUN_100165a4` | `load` | `0xd0` | `stack_local_false_positive` | same numeric stack offset, not video state | `l32i a2,a1,0xd0` |
| `10016675` | `100165a4 FUN_100165a4` | `load` | `0xd0` | `stack_local_false_positive` | same numeric stack offset, not video state | `l32i a2,a1,0xd0` |
| `1001667e` | `100165a4 FUN_100165a4` | `store` | `0xd0` | `stack_local_false_positive` | same numeric stack offset, not video state | `s32i a2,a1,0xd0` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `field_sources_are_resolved` | `present` | direct START_PAGE resolves sidebands; default-zero impact below is a counterfactual |
| `zero_d0_skips_channel_b_refill` | `present` | +0xd0 nonzero gates channel-B pointer/length writes |
| `zero_d4_triggers_final_condition_early` | `present` | +0xd4 participates in final/high-bit logic and is decremented by descriptor units |
| `ec_controls_secondary_paths` | `present` | +0xec controls prepare secondary branches and raw-band B flag behavior |
| `e8_has_no_selected_downstream_consumer` | `present` | +0xe8 is only seen in the prepare assignment within the selected video corpus |
| `ghidra_state_access_scan_classified` | `present` | Ghidra exact-offset state access scan is forced to Xtensa BE and every hit is classified |
| `ghidra_state_access_scan_covers_critical_consumers` | `present` | Ghidra exact-offset scan independently sees the critical +0xd0/+0xd4/+0xec consumers |
| `ghidra_e8_has_prepare_store_only` | `present` | Ghidra exact-offset scan finds +0xe8 only as the prepare-side seed store |
| `ghidra_stack_local_false_positive_is_not_video_state` | `present` | scan records and classifies numeric +0xd0 stack-local false positives separately from video-state accesses |
