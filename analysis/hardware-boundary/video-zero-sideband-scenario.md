# HP 1020 Zero Sideband Scenario

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`

## Scenario

| Step | Function | If work +0x26 is zero | Effect |
|---|---|---|---|
| `prepare_defaults` | `0x10014910` | video state +0xd0 and +0xd4 are seeded to zero | remaining-unit counters start empty |
| `initial_channel_a_still_arms` | `0x10015214` | no direct gate before channel-A pointer/length setup | render can still write channel-A pointer and length from the raster payload |
| `channel_b_refill_skipped` | `0x10014244` | helper condition `+0xd0 != 0` is false | no channel-B pointer/length descriptor is written by the helper |
| `raw_band_final_logic_becomes_ambiguous` | `0x10013f34` | +0xd4 starts at zero while descriptor units can still be consumed later | final/high-bit and remaining decrement logic no longer has a proven sane seed |

## Practical Conclusion

- Zero active work +0x26 is not an immediate proof that render setup cannot start.
- It is a refill/descriptor-path blocker: channel A can be armed, but channel B is not seeded by 0x10014244.
- For a narrow print-only replacement, this means a trivial first-transfer probe might appear alive while still being far from a complete page-printing implementation.
- The direct builder now proves +0x26=VIDEO_Y, +0x30=RET, +0x32=ECONOMODE. This zero-height scenario is a counterfactual, not the default host page.

## Checks

| Check | Status | Detail |
|---|---|---|
| `sideband_census_passes` | `present` | sideband census identifies three direct active-work stores; this report analyzes zero values counterfactually |
| `prepare_seeds_d0_d4_from_work_0x26` | `present` | prepare copies active argument +0x26 into both remaining counters |
| `render_channel_a_does_not_depend_on_d0` | `present` | render sets channel-A pointer/length and then calls the channel-B helper |
| `helper_requires_nonzero_d0` | `present` | channel-B helper writes pointer/length only when remaining +0xd0 is nonzero |
| `band_queue_uses_d4_for_final_and_decrement` | `present` | raw-band queue logic uses +0xd4 for final/high-bit decisions and decrements it by descriptor units |
| `a4_channel_a_payload_is_modeled` | `present` | a4_default channel-A payload length remains concretely modeled |
