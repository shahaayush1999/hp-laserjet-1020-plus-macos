# HP 1020 Video Dataflow Contract

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- source case: `a4_default`
- scope: normal first-page path from host raster fields through video render/refill hardware boundary

## Source Reports

- `raster_fields`: `analysis/open-firmware-model/raster-field-semantics.json`
- `prepare_projection`: `analysis/hardware-boundary/video-prepare-projection.json`
- `transfer_ring`: `analysis/hardware-boundary/video-transfer-ring.json`
- `band_queue`: `analysis/hardware-boundary/video-band-queue.json`
- `refill_topology`: `analysis/hardware-boundary/video-refill-topology.json`
- `chunk_sizing`: `analysis/hardware-boundary/video-chunk-sizing.json`
- `remaining_units`: `analysis/hardware-boundary/video-remaining-units.json`

## Contract Stages

### `host_raster_fields`

- function: `ZjStream parser + JobMgr`
- meaning: Host BIH/BID data is already enough to define page geometry and the first compressed raster payload.
- remaining unknown: exact physical meaning of every BIH option bit

| Field/Register | Value/Formula |
|---|---|
| `work +0x84` | `9600` |
| `work +0x88` | `6824` |
| `work +0x8c` | `128` |
| `work +0x90` | `0x5c` |
| `payload +0x48` | `6364` |
| `payload +0x54` | `pointer to the same compressed BID bytes` |

### `video_prepare_geometry`

- function: `0x10014910 hp1020_video_prepare_page_candidate`
- meaning: The current host cases land in the normal 600dpi setup family.
- remaining unknown: hardware-calibrated meaning of datastore 0x20 and less common prepare branches

| Field/Register | Value/Formula |
|---|---|
| `video state +0xb8 stride` | `1200` |
| `video state +0xbc dual-output window` | `2400` |
| `video state +0xc4` | `1` |
| `video state +0xf4` | `2` |
| `video state +0xc8 / 200` | `2` |

### `render_initial_transfer`

- function: `0x10015214 hp1020_video_render_or_dma_candidate`
- meaning: Render arms the first transfer using the host-derived geometry and first compressed raster buffer.
- remaining unknown: live completion timing for channel A progress

| Field/Register | Value/Formula |
|---|---|
| `0xb2000008` | `9600` |
| `0xb200000c` | `6824` |
| `0xb2000024` | `128` |
| `0xb2000000` | `derived from work +0x90, then OR 0x400` |
| `0xb2040004` | `payload +0x54 compressed raster pointer` |
| `0xb2040008` | `6364` |

### `helper_channel_b_refill`

- function: `0x10014244 hp1020_video_band_done_or_irq_helper_candidate`
- meaning: The helper keeps channel B fed from the modulo-4 descriptor side.
- remaining unknown: active work +0x26 remains unsourced; ZJI_VIDEO_Y reaches page-param +0x26 upstream, but the queue payload chain weakens that alias/copy theory

| Field/Register | Value/Formula |
|---|---|
| `video state +0xcc max chunk units` | `4` |
| `video state +0xd0 candidate if alias holds` | `6824` |
| `chunk_units` | `min(4, video state +0xd0)` |
| `0xb2080004` | `slot pointer from video state + slot*4` |
| `0xb2080008` | `min(4, +0xd0) * stride(1200)` |
| `0xb2080008 candidate if alias holds` | `4800` |
| `final_flag` | `set when remaining units become zero` |

### `raw_band_queue_feed`

- function: `0x10013f34 hp1020_video_band_queue_or_list_candidate`
- meaning: This is the normal raw-band/channel feed boundary after render and refill helper setup.
- remaining unknown: exact encoding performed by 0x1001b668

| Field/Register | Value/Formula |
|---|---|
| `0xb1000008` | `descriptor pointer/control source` |
| `0xb1000108` | `A pointer plus dual-output window(2400) when dual-block mode is active` |
| `0xb100000c` | `encoded descriptor units plus final flag bit 0x18` |
| `0xb100010c` | `encoded descriptor units plus secondary output bit 0x19` |
| `queue index +0xdc` | `advances modulo 4 unless it would collide with +0xe0 without final flag` |

### `irq_refill_loop`

- function: `0x100144d0 hp1020_video_irq_or_band_done_candidate`
- meaning: Actual printing depends on the video IRQ/band-done loop continuing this refill safely.
- remaining unknown: live interrupt cadence and exact stop/completion condition

| Field/Register | Value/Formula |
|---|---|
| `band_done_bit` | `0x20` |
| `normal_path` | `clear ring record, advance +0xd8, call helper, then queue/list next band` |
| `alternate_path` | `raw linked-list refresh when video state +0xfc is negative` |

## Current Conclusion

- The host-to-render dataflow is now concrete for the generated a4_default case.
- The remaining unknowns are not parser fields; they are the active work +0x26 source, raw-band helper divide confirmation, video timing, and live IRQ completion behavior.
- This report is still not a reason to upload custom printing firmware; it is the static contract a future implementation must satisfy.

## Checks

| Check | Status | Detail |
|---|---|---|
| `raster_fields_status_pass` | `present` | raster field model is pass |
| `prepare_projection_status_pass` | `present` | prepare projection model is pass |
| `transfer_ring_status_pass` | `present` | transfer ring model is pass |
| `band_queue_status_pass` | `present` | band queue model is pass |
| `refill_topology_status_pass` | `present` | refill topology model is pass |
| `chunk_sizing_status_pass` | `present` | chunk sizing model is pass |
| `remaining_units_status_pass` | `present` | remaining-units model is pass |
| `a4_default_values_projected` | `present` | a4_default work/raster/prepare/chunk values match the current generated model |
| `normal_refill_path_preserved` | `present` | normal descriptor refill still connects channel-B helper and raw-band queue writes |
