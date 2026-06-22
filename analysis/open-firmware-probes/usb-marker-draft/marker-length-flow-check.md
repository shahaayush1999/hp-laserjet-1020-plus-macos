# HP 1020 Marker Length Flow Check

- fail hits: `0`

| Severity | Check | Detail |
|---|---|---|
| `watch` | `clipped_length_saved` | clipped host wLength must be saved in local probe state at +0x20 |
| `watch` | `response_length_uses_a6` | endpoint-0 response length must be programmed from the clipped-length register |
| `watch` | `descriptor_word_uses_clipped_length` | transfer descriptor word must OR the final flag with the clipped-length register before descriptor submission |
| `watch` | `a6_not_clobbered_before_sequence` | no writes to a6 are allowed between clipped-length calculation and sequence dispatch |
| `watch` | `response_store_in_kick_path` | the response length write must live in hp1020_usb_marker_kick_control_in |
