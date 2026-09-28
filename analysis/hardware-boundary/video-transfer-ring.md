# HP 1020 Video Transfer Ring Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: video transfer ring indices, descriptor ownership, and band-done refill path

## Key Literal Values

| Name | Value |
|---|---:|
| `video_state_base` | `0x1002efc0` |
| `ring_descriptor_base` | `0x1002efe0` |
| `channel_b_pointer` | `0xb2080004` |
| `channel_b_length` | `0xb2080008` |
| `channel_a_pointer` | `0xb2040004` |
| `channel_a_progress` | `0xb2040008` |
| `transfer_status_control` | `0xb2000010` |
| `channel_a_control` | `0xb2040000` |
| `channel_a_status` | `0xb204000c` |
| `channel_b_control` | `0xb2080000` |
| `channel_b_status` | `0xb208000c` |
| `video_error_busy` | `0x00001003` |
| `scratch_control_word` | `0x1002ee34` |
| `descriptor_width` | `0xb2000008` |
| `descriptor_height` | `0xb200000c` |
| `descriptor_band_height` | `0xb2000024` |
| `clear_0x2000_mask` | `0xffffdfff` |
| `transfer_start_control` | `0xb2000000` |
| `block_a_status` | `0xb1000004` |
| `block_b_status` | `0xb1000104` |

## State Fields

| Offset | Field | Meaning |
|---:|---|---|
| `+0x20 + slot*0x0c` | output descriptor owned flag | 0x10014283 claims it before pixels are filled; 0x10014569 releases it after supplied completion; it is not a ready-pixels flag |
| `+0x24 + slot*0x0c` | final output band flag | 0x1001427e..0x10014281 sets it when remaining +0xd0 reaches zero; 0x10013f6f..0x10013f72 permits the otherwise-withheld final slot |
| `+0x28 + slot*0x0c` | output band row/unit count | 0x1001426e stores min(+0xcc,+0xd0); 0x100140cc reads it for output accounting |
| `+0x94` | consumer/read index candidate | render treats equality with next producer index as ring full |
| `+0x98` | producer/write index candidate | render advances `(value + 1) & 3` after descriptor setup |
| `+0x9c` | active raster-list pointer | set from work +0x50 and walked by raw-band refresh |
| `+0xa0` | pending/active raster node pointer | cleared by render, walked by reset/IRQ paths when +0xfc is negative |
| `+0xa4` | saved raster pointer for current transfer | set when render snapshots channel-A pointer/progress |
| `+0xb8` | stride bytes candidate | used by band helper as transfer length multiplier |
| `+0xcc` | maximum chunk lines/units | caps helper chunk size |
| `+0xd0` | remaining transfer units | helper decrements this by the chosen chunk |
| `+0xd4` | remaining output units | 0x100140c9..0x100140d7 subtracts the selected descriptor count after the output-write boundary |
| `+0xd8` | IRQ done index candidate | advanced `(value + 1) & 3` when band-done bit 0x20 arrives |
| `+0xdc` | next output-selection index | 0x10013f60 selects it; 0x100140e2 advances it modulo four after output accounting; recovery also clears it |
| `+0xe0` | next fill/publication index | chooses `descriptor_base + slot*0x0c` and buffer at state + slot*4; 0x10014468 advances it modulo four at the fill-completion RAM tail |
| `+0xf0` | band-done happened flag | set by IRQ path after handling block status |
| `+0xf8` | band-done counter | incremented when block status bit 0x20 is seen |
| `+0xfc` | raw-band/reset mode sign field | negative path drains +0xa0 and refreshes raw bands; nonnegative path advances descriptor ring |

## Ownership Sequences

### `prepare_initializes_ring`

- function: `0x10014910 hp1020_video_prepare_page_candidate`
- registers: -

1. clear five saved pointer slots beginning at video_state +0xa4
2. clear input producer index +0x98, input consumer index +0x94, output done index +0xd8, and output-selection index +0xdc
3. clear four 0x0c-byte ring records beginning at video_state +0x20
4. derive stride +0xb8 from work +0x84 and derive maximum chunk +0xcc

### `render_claims_next_slot`

- function: `0x10015214 hp1020_video_render_or_dma_candidate`
- registers: `0xb2000008`, `0xb200000c`, `0xb2000024`, `0xb2000000`

1. compute next producer slot as `(video_state +0x98 + 1) & 3`
2. store work +0x50 raster list at +0x9c and clear +0xa0 before checking busy; rejection therefore changes these pointers
3. return busy/error 0x1003 if state +0x6c is outside the accepted range or next slot equals +0x94
4. arm channel A/B if not already in running state +0x6c == 2
5. write work +0x84/+0x88/+0x8c/+0x90 into 0xb200 descriptor/control registers
6. advance +0x98 to the claimed next slot

### `render_starts_first_transfer`

- function: `0x10015214 hp1020_video_render_or_dma_candidate`
- registers: `0xb2040004`, `0xb2040008`, `0xb2080004`, `0xb2080008`, `0xb2000010`

1. when producer and consumer indices are equal, snapshot raster pointer/length into channel-A registers
2. call 0x10014244 helper to fill channel-B descriptor from remaining units
3. wait until `raster_end - 0xb2040008 >= 8` before setting transfer status/control bit 0
4. raise internal event 0x13 and set video state +0x6c to 2

### `band_helper_refills_channel_b`

- function: `0x10014244 hp1020_video_band_done_or_irq_helper_candidate`
- registers: `0xb2080004`, `0xb2080008`

1. select descriptor record at `0x1002efe0 + (video_state +0xe0) * 0x0c`
2. if the descriptor record is free and +0xd0 remaining is nonzero, choose `min(+0xcc, +0xd0)` units
3. decrement +0xd0, mark whether this was the final chunk, and mark the descriptor busy
4. write source pointer to 0xb2080004 and transfer length `chunk * stride(+0xb8)` to 0xb2080008

### `irq_band_done_advances_or_refills`

- function: `0x100144d0 hp1020_video_irq_or_band_done_candidate`
- registers: `0xb1000004`, `0xb1000104`

1. status bit 0x20 on either video block is acknowledged and increments +0xf8
2. if +0xfc is negative, walk +0xa0, decrement child/page counters, advance +0xa0, then refresh raw bands
3. otherwise clear ring record at `+0x20 + (+0xd8 * 0x0c)`, advance +0xd8 modulo 4, refill helper, and queue/list the next band
4. set +0xf0 after handling the band-done status

## Ring Scenarios

| Scenario | Producer before | Consumer | Next slot | Result | Producer after | Meaning |
|---|---:|---:|---:|---|---:|---|
| `producer_0_consumer_0` | `0` | `0` | `1` | `slot_claimed` | `1` | render may claim the next modulo-4 slot |
| `producer_0_consumer_1` | `0` | `1` | `1` | `busy_error_0x1003` | `0` | render refuses to overrun consumer |
| `producer_1_consumer_2` | `1` | `2` | `2` | `busy_error_0x1003` | `1` | render refuses to overrun consumer |
| `producer_2_consumer_3` | `2` | `3` | `3` | `busy_error_0x1003` | `2` | render refuses to overrun consumer |
| `producer_3_consumer_0` | `3` | `0` | `0` | `busy_error_0x1003` | `3` | render refuses to overrun consumer |

## Evidence Checks

| Check | Status | Source | Needle |
|---|---|---|---|
| `prepare_clears_ring_slots` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `*(undefined4 *)(puVar15 + iVar8 * 4 + 0xa4) = 0` |
| `prepare_clears_transfer_indices` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `*(undefined4 *)(puVar9 + 0x98) = 0` |
| `prepare_clears_consumer_index` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `*(undefined4 *)(puVar9 + 0x94) = 0` |
| `prepare_clears_done_index` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `*(undefined4 *)(puVar9 + 0xd8) = 0` |
| `prepare_initializes_ring_records` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `*(undefined4 *)(puVar9 + *puVar1 * 0xc + 0x20) = 0` |
| `render_next_index_mod4` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `uVar7 = *(int *)(hp1020_video_state_ptr_word + 0x98) + 1U & 3` |
| `render_stores_raster_list` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*(int *)(puVar1 + 0x9c) = iVar8` |
| `render_clears_a0` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*(undefined4 *)(puVar1 + 0xa0) = 0` |
| `render_rejects_full_ring` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `if (*(uint *)(puVar1 + 0x94) == uVar7)` |
| `render_descriptor_width` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*puVar5 = uVar11` |
| `render_descriptor_height` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*DAT_100068f4 = *(undefined4 *)(param_1 + 0x88)` |
| `render_descriptor_band_height` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `uVar11 = *(undefined4 *)(param_1 + 0x8c)` |
| `render_start_bit_0x400` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*puVar2 = uVar10 \| 0x400` |
| `render_channel_a_pointer` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*DAT_100067f4 = uVar9` |
| `render_channel_a_progress` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*piVar4 = iVar8` |
| `render_saves_raster_pointer` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*(undefined4 *)(puVar1 + 0xa4) = uVar9` |
| `render_advances_producer_index` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*(uint *)(puVar1 + 0x98) = uVar7` |
| `render_calls_band_helper` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `FUN_10014244()` |
| `render_waits_channel_a_progress` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `} while ((uint)(iVar8 - *DAT_100067f8) < 8);` |
| `render_sets_transfer_go` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*DAT_10006790 = *DAT_10006790 \| 1` |
| `render_sets_state_running` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*(undefined4 *)(hp1020_video_state_ptr_word + 0x6c) = 2` |
| `band_helper_uses_e0_slot` | `present` | `analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c` | `*(int *)(PTR_DAT_10006770 + 0xe0) * 0xc` |
| `band_helper_caps_chunk` | `present` | `analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c` | `if (*(uint *)(PTR_DAT_10006770 + 0xcc) < uVar3)` |
| `band_helper_decrements_remaining` | `present` | `analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c` | `*(uint *)(puVar1 + 0xd0) = iVar4 - uVar3` |
| `band_helper_marks_descriptor_busy` | `present` | `analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c` | `*piVar6 = 1` |
| `band_helper_writes_channel_b_pointer` | `present` | `analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c` | `*DAT_100067e4 = uVar7` |
| `band_helper_writes_channel_b_length` | `present` | `analysis/zjs-parser-boundary/decompiled/10014244_hp1020_video_band_done_or_irq_helper_candidate.c` | `*piVar2 = iVar4 * iVar5` |
| `irq_ack_0x20` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `*puVar2 = 0xffffffdf` |
| `irq_counts_band_done` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `*(int *)(PTR_DAT_10006770 + 0xf8) = *(int *)(PTR_DAT_10006770 + 0xf8) + 1` |
| `irq_clears_ring_record` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `*(undefined4 *)(puVar1 + *(int *)(puVar1 + 0xd8) * 0xc + 0x20) = 0` |
| `irq_advances_done_index` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `*(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3` |
| `irq_refills_band_helper` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `hp1020_video_band_done_or_irq_helper_candidate()` |
| `irq_refreshes_raw_bands` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `hp1020_video_refresh_raw_bands_candidate()` |
| `irq_reset_case_7` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `FUN_10013d4c(7)` |

## Open Firmware Meaning

- A printing replacement needs the ring ownership rules, not just the 0xb200 descriptor writes.
- The normal render path protects the input ring at +0x94/+0x98 and returns 0x1003 when the next slot would collide with the consumer index. This differs from the four output descriptors controlled by +0xe0/+0xdc/+0xd8.
- Output ownership, completed fill publication, output acceptance and completed consumption are separate stages. The RAM cuts and exact byte comparisons are owned by analysis/hardware-boundary/software-ring.json; they omit physical readiness and transfer operations.
- The interrupt/band-done path is responsible for clearing completed ring records and refilling channel-B descriptors.
- The remaining hard unknown is the exact interrupt/event timing that advances the consumer side under live hardware.

