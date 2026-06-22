# HP 1020 Video Sideband Default Impact

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`

## Field Impact

| Work field | State fields | Risk | Current interpretation |
|---|---|---|---|
| `+0x26` | `+0xd0`, `+0xd4` | `critical` | not safe to assume zero for a printing path |
| `+0x30` | `+0xe8` | `unknown_low_in_current_static_view` | keep tracked, but it is not currently a first blocker compared with +0x26/+0x32 |
| `+0x32` | `+0xec` | `mode_critical` | zero may be correct for generated normal cases, but must be deliberately chosen rather than accidentally defaulted |

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

- The unsourced sideband fields are not all equal: +0x26 is immediately critical for channel-B refill and remaining/final accounting.
- +0x32 is mode-critical: zero may be correct for normal generated cases, but it affects setup tables and B-side raw-band flags.
- +0x30 currently has no selected downstream consumer beyond prepare copying it to +0xe8, so it is tracked but lower priority.
- The next useful static target is still the hidden source or intended default policy for active work +0x26.

## Checks

| Check | Status | Detail |
|---|---|---|
| `unsourced_fields_are_expected_three` | `present` | prepare field model still exposes exactly the three unsourced active work sideband fields |
| `zero_d0_skips_channel_b_refill` | `present` | +0xd0 nonzero gates channel-B pointer/length writes |
| `zero_d4_triggers_final_condition_early` | `present` | +0xd4 participates in final/high-bit logic and is decremented by descriptor units |
| `ec_controls_secondary_paths` | `present` | +0xec controls prepare secondary branches and raw-band B flag behavior |
| `e8_has_no_selected_downstream_consumer` | `present` | +0xe8 is only seen in the prepare assignment within the selected video corpus |
