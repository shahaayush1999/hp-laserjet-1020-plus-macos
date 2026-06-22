# HP 1020 Video/Engine Register Semantics

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: first-page print hardware boundary after ZjStream parsing

## Engine Handshake Constants

| Name | Literal cell | Value/register | Source |
|---|---:|---:|---|
| `engine_status_reg` | `0x1000691c` | `0xb050000c` | `analysis/status-masks/status-mask-map.md` |
| `engine_command_reg` | `0x10006928` | `0xb0500004` | `analysis/status-masks/status-mask-map.md` |
| `engine_clear_mask` | `0x10006924` | `0xfeffffff` | `analysis/status-masks/status-mask-map.md` |
| `engine_command_preserve_mask` | `0x10005d04` | `0xffff0000` | `analysis/status-masks/status-mask-map.md` |
| `engine_ready_submit_bit` | `0x10005f20` | `0x00010000` | `analysis/status-masks/status-mask-map.md` |
| `engine_failure_event` | `0x1000692c` | `0xfe001401` | `analysis/status-masks/status-mask-map.md` |

## MMIO Literal Map

| Source | Literal cell | Register | Role |
|---|---:|---:|---|
| `raw_band` | `0x100067c0` | `0xb1000004` | video block A status/busy/readiness register |
| `raw_band` | `0x100067cc` | `0xb1000008` | raw-band A raster pointer register |
| `raw_band` | `0x100067d4` | `0xb100000c` | raw-band A count/flag register |
| `raw_band` | `0x100067d8` | `0xb1000104` | video block B status/busy/readiness register |
| `raw_band` | `0x100067d0` | `0xb1000108` | raw-band B raster window/pointer register |
| `raw_band` | `0x100067dc` | `0xb100010c` | raw-band B count/flag register |
| `video_prepare` | `0x10006808` | `0xb1000000` | video block A control/reset/enable register |
| `video_prepare` | `0x100067c0` | `0xb1000004` | video block A status/busy/readiness register |
| `video_prepare` | `0x100068d8` | `0xb1000010` | video setup A vertical/offset packed register |
| `video_prepare` | `0x100068e0` | `0xb1000014` | video setup A stride/window mask register |
| `video_prepare` | `0x10006884` | `0xb100001c` | video setup A mode/timing register |
| `video_prepare` | `0x10006854` | `0xb1000020` | video timing/setup A table register |
| `video_prepare` | `0x10006868` | `0xb1000024` | video timing/setup A constant register |
| `video_prepare` | `0x1000680c` | `0xb1000100` | video block B control/reset/enable register |
| `video_prepare` | `0x100067d8` | `0xb1000104` | video block B status/busy/readiness register |
| `video_prepare` | `0x100068dc` | `0xb1000110` | video setup B vertical/offset packed register |
| `video_prepare` | `0x100068e8` | `0xb1000114` | video setup B stride/window mask register |
| `video_prepare` | `0x1000688c` | `0xb100011c` | video setup B mode/timing register |
| `video_prepare` | `0x10006874` | `0xb1000120` | video timing/setup B table register |
| `video_prepare` | `0x10006880` | `0xb1000124` | video timing/setup B constant register |
| `video_prepare` | `0x10006894` | `0xb1000400` | video timing table register 0 |
| `video_prepare` | `0x100068a4` | `0xb1000410` | video timing table register 1 |
| `video_prepare` | `0x100068b0` | `0xb1000420` | video timing table register 2 |
| `video_prepare` | `0x100068b4` | `0xb1000430` | video timing table register 3 |
| `video_render` | `0x10006900` | `0xb2000000` | video transfer start/control register |
| `video_render` | `0x100068f0` | `0xb2000008` | video transfer descriptor field from work +0x84 |
| `video_render` | `0x100068f4` | `0xb200000c` | video transfer descriptor field from work +0x88 |
| `video_render` | `0x10006790` | `0xb2000010` | video transfer status/control register |
| `video_render` | `0x100068f8` | `0xb2000024` | video transfer descriptor field from work +0x8c |
| `video_render` | `0x10006798` | `0xb2040000` | video transfer channel A control register |
| `video_render` | `0x100067f4` | `0xb2040004` | video channel A raster pointer register |
| `video_render` | `0x100067f8` | `0xb2040008` | video channel A transfer length/progress register |
| `video_render` | `0x1000679c` | `0xb204000c` | video transfer channel A status register |
| `video_render` | `0x10006794` | `0xb2080000` | video transfer channel B control register |
| `video_render` | `0x100067a0` | `0xb208000c` | video transfer channel B status register |
| `video_reset` | `0x10006808` | `0xb1000000` | video block A control/reset/enable register |
| `video_reset` | `0x100067c0` | `0xb1000004` | video block A status/busy/readiness register |
| `video_reset` | `0x1000680c` | `0xb1000100` | video block B control/reset/enable register |
| `video_reset` | `0x100067d8` | `0xb1000104` | video block B status/busy/readiness register |

## Semantic Sequences

### `engine_command_status_handshake`

- function: `0x10015c68 hp1020_engine_status_io_candidate`
- registers: `0xb050000c`, `0xb0500004`
- meaning: This is the mechanical engine command door. An open printer path cannot safely fake it without knowing command meanings and response timing.

1. store requested 16-bit engine command in firmware state +0x5a
2. clear status register with mask 0xfeffffff
3. wait until status register bit 0x00010000 is set
4. write command into low 16 bits of command register while preserving upper 16 bits
5. set command register bit 0x00010000 to submit
6. wait for event response; timeout sends engine queue message 0x17 with event 0xfe001401

### `video_block_prepare_and_enable`

- function: `0x10014910 hp1020_video_prepare_page_candidate`
- registers: `0xb1000000`, `0xb1000004`, `0xb1000100`, `0xb1000104`
- meaning: This is video hardware setup before transfer. It is register-heavy and timing-sensitive.

1. clear block control bit 0x100 on both video blocks
2. wait while status bit 0x200 remains set
3. program mode/timing registers from resolution, planes, and work fields
4. set block control bit 0x100 to enable/release the prepared block

### `video_transfer_channel_arm`

- function: `0x10015214 hp1020_video_render_or_dma_candidate`
- registers: `0xb2040000`, `0xb204000c`, `0xb2080000`, `0xb208000c`
- meaning: The two transfer channels have a handshake before descriptor registers are started.

1. toggle channel A control bit 0x2 and wait for channel A status bit 0x2
2. set channel A control bit 0x1 and high/control bit 0x80000000
3. repeat the same arm/wait pattern for channel B

### `video_descriptor_start`

- function: `0x10015214 hp1020_video_render_or_dma_candidate`
- registers: `0xb2000008`, `0xb200000c`, `0xb2000024`, `0xb2000000`, `0xb2000010`
- meaning: This is the first direct path from host-controlled BIH fields into video transfer hardware.

1. clear transfer-control bit 0 in 0xb2000010
2. write work +0x84 to 0xb2000008
3. write work +0x88 to 0xb200000c
4. write work +0x8c to 0xb2000024
5. derive a control word from work +0x90, then set bit 0x400 and write 0xb2000000
6. later set bit 0 in 0xb2000010 after transfer-progress checks

### `raw_band_feed`

- function: `0x100140f8 hp1020_video_refresh_raw_bands_candidate`
- registers: `0xb1000008`, `0xb100000c`, `0xb1000108`, `0xb100010c`
- meaning: This path feeds compressed raster payload pointers and flags into the raw-band side of the video block.

1. walk video_state +0x9c raster-list nodes
2. write payload +0x54 raster pointer to 0xb1000008
3. in two-lane mode write pointer + video_state +0xbc to 0xb1000108
4. derive count from payload +0x20 and video_state +0xc4
5. OR flag bits from payload +0x4c, payload +0x50, and video_state +0xec
6. write count/flags to 0xb100000c and 0xb100010c

## Evidence Checks

| Check | Status | Detail | Source |
|---|---|---|---|
| `engine_status_clear` | `present` | engine status register is cleared with the clear mask before command submission | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` |
| `engine_wait_ready_bit` | `present` | engine status register is polled for the ready/submit bit | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` |
| `engine_command_write_preserve_upper` | `present` | engine command register preserves upper bits and inserts the 16-bit command | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` |
| `engine_command_submit_bit` | `present` | engine command register sets the ready/submit bit after command write | `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c` |
| `video_prepare_block_a_enable` | `present` | video prepare enables or releases video block A with bit 0x100 | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` |
| `video_prepare_block_busy_wait` | `present` | video prepare waits while the block busy bit 0x200 remains set | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` |
| `video_render_channel_a_wait` | `present` | video render waits for channel status bit 0x2 | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` |
| `video_render_descriptor_width` | `present` | video render writes work-derived descriptor words | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` |
| `video_render_start_control` | `present` | video render writes the start/control word with bit 0x400 set | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` |
| `raw_band_pointer_write` | `present` | raw-band feed writes the raster payload pointer | `analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c` |
| `raw_band_flags_write` | `present` | raw-band feed writes count and flag bits | `analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c` |
| `engine_poll_can_reset_video` | `present` | engine status polling can trigger video reset dispatch | `analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c` |

## Open Firmware Meaning

- USB-only probes remain the correct next hardware tests.
- A printing firmware cannot jump straight from the parsed raster list to these registers without reproducing engine and video state-machine ordering.
- The most useful next offline target is extracting exact bit semantics and timing for the 0xb100 setup path and the 0xb050 engine command set.

