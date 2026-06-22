# HP 1020 Video Refill Topology

This is a generated synthesis from lower-level offline models. It does not contact the printer.

## Result

- status: `pass`
- scope: video band-done refill path after parser/render handoff

## Source Reports

- `analysis/hardware-boundary/video-mode-flag.json`
- `analysis/hardware-boundary/video-irq-decisions.json`
- `analysis/hardware-boundary/video-transfer-ring.json`
- `analysis/hardware-boundary/video-band-queue.json`

## Topology

### `normal_descriptor_queue_refill`

- entry condition: work object +0x74 == 0, so video state +0xfc is nonnegative
- state fields: `+0xd0`, `+0xd8`, `+0xdc`, `+0xe0`, `+0xf0`, `+0xf8`, `+0xfc`
- unsafe registers: `0xb1000008`, `0xb100000c`, `0xb1000108`, `0xb100010c`, `0xb2080004`, `0xb2080008`

Evidence:
- mode flag model selects descriptor_queue_mode
- IRQ bit 0x20 branch clears +0xd8 ring record and advances +0xd8
- 0x10014244 fills a channel-B descriptor from remaining +0xd0 units
- 0x10013f34 advances +0xdc and writes raw-band A/B pointer/flag registers

### `alternate_raw_linked_list_refill`

- entry condition: work object +0x74 != 0, so video state +0xfc is negative
- state fields: `+0x9c`, `+0xa0`, `+0xf0`, `+0xf8`, `+0xfc`
- unsafe registers: `0xb1000008`, `0xb100000c`, `0xb1000108`, `0xb100010c`

Evidence:
- mode flag model selects raw_linked_list_mode
- IRQ bit 0x20 branch walks video state +0xa0 linked-list nodes
- the branch may adjust child/page counters and send JobMgr queue message 8
- 0x100140f8 refreshes raw-band registers from video state +0x9c raster nodes

## Current Conclusion

- For the currently mapped normal print path, +0x74 is initialized to zero and the descriptor-queue refill path is the stronger default hypothesis.
- The raw linked-list refresh path is real firmware behavior, but its normal print-path producer is not yet proven.
- Both paths remain inside unsafe video/raw-band hardware, so this is planning evidence, not a reason to run custom mechanical firmware yet.

## Checks

| Check | Status | Detail |
|---|---|---|
| `video_mode_flag_status_pass` | `present` | video_mode_flag status is 'pass' |
| `video_irq_decisions_status_pass` | `present` | video_irq_decisions status is 'pass' |
| `video_transfer_ring_status_pass` | `present` | video_transfer_ring status is 'pass' |
| `video_band_queue_status_pass` | `present` | video_band_queue status is 'pass' |
| `descriptor_queue_mode_present` | `present` | mode-flag model has descriptor_queue_mode |
| `raw_linked_list_mode_present` | `present` | mode-flag model has raw_linked_list_mode |
| `irq_has_ring_and_raw_band_done_scenarios` | `present` | IRQ model keeps both 0x20 band-done branches |
| `ring_has_helper_refill_sequence` | `present` | transfer-ring model includes channel-B helper refill |
| `queue_has_loop_gate_and_raw_band_writes` | `present` | band-queue model includes loop gate and raw-band writes |
