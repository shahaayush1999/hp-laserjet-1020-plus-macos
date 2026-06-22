# HP 1020 Video Mode Flag Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: work object `+0x74`, video state `+0xfc`, and the video IRQ refill fork

## Key Values

| Name | Value |
|---|---:|
| `high_bit` | `0x80000000` |
| `high_bit_clear_mask` | `0x7fffffff` |
| `video_state_base` | `0x1002efc0` |
| `work_object_mode_flag_offset` | `+0x74` |
| `video_state_mode_flag_offset` | `+0xfc` |

## Mode Cases

| Work +0x74 | State +0xfc after prepare | Sign bit | Mode | IRQ band-done path |
|---:|---:|---|---|---|
| `0` | `0x00000000` | `False` | `descriptor_queue_mode` | clear descriptor done slot at video_state +0x20 + (+0xd8 * 0x0c)<br>advance +0xd8 modulo 4<br>call hp1020_video_band_done_or_irq_helper_candidate<br>call hp1020_video_band_queue_or_list_candidate |
| `1` | `0x80000000` | `True` | `raw_linked_list_mode` | use video_state +0xa0 linked-list entry<br>optionally decrement work/raster counters and send JobMgr queue message 8<br>advance +0xa0 to next linked-list node<br>call hp1020_video_refresh_raw_bands_candidate |

## Branch Sequences

### `prepare_copies_work_flag_to_state_sign`

- function: `0x10014910 hp1020_video_prepare_page_candidate`

1. read work object byte +0x74
2. when zero, clear high bit in video state +0xfc with 0x7fffffff
3. when nonzero, set high bit in video state +0xfc with 0x80000000

### `irq_band_done_selects_refill_family`

- function: `0x100144d0 hp1020_video_irq_or_band_done_candidate`

1. on video status bit 0x20, acknowledge block status and increment state +0xf8
2. if state +0xfc is negative, follow +0xa0 linked-list/raw-band refresh path
3. if state +0xfc is nonnegative, follow descriptor ring +0xd8 and band queue/list path

### `reset_dispatch_depends_on_same_sign_bit`

- function: `0x10013d4c hp1020_video_reset_dispatch_candidate`

1. reset/flush path also tests the sign of video state +0xfc
2. Ghidra truncates the nonnegative branch as bad data, so this report records only the proven gate, not a full reset model

## Evidence Checks

| Check | Status | Source | Needle |
|---|---|---|---|
| `work_flag_initialized_zero` | `present` | `analysis/video-work-object/decompiled/1000f228_hp1020_video_work_create_candidate.c` | `*(undefined1 *)(iVar1 + 0x74) = 0` |
| `work_flag_documented` | `present` | `analysis/video-work-object-report.md` | `\| `+0x74` \| cleared flag byte \|` |
| `prepare_reads_work_flag` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `if (*(char *)(param_1 + 0x74) == '\0')` |
| `prepare_clears_state_high_bit` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `uVar7 = *(uint *)(puVar15 + 0xfc) & DAT_1000628c` |
| `prepare_sets_state_high_bit` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `uVar7 = *(uint *)(puVar15 + 0xfc) \| DAT_10005e34` |
| `prepare_stores_state_flag` | `present` | `analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c` | `*(uint *)(puVar15 + 0xfc) = uVar7` |
| `irq_tests_state_flag_negative` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `if (*(int *)(puVar1 + 0xfc) < 0)` |
| `irq_negative_calls_raw_refresh` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `hp1020_video_refresh_raw_bands_candidate();` |
| `irq_nonnegative_calls_band_done` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `hp1020_video_band_done_or_irq_helper_candidate();` |
| `irq_nonnegative_calls_band_queue` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `hp1020_video_band_queue_or_list_candidate();` |
| `irq_nonnegative_clears_descriptor_done_slot` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `*(undefined4 *)(puVar1 + *(int *)(puVar1 + 0xd8) * 0xc + 0x20) = 0` |
| `irq_nonnegative_advances_d8` | `present` | `analysis/zjs-parser-boundary/decompiled/100144d0_hp1020_video_irq_or_band_done_candidate.c` | `*(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3` |
| `reset_dispatch_has_state_flag_gate` | `present` | `analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c` | `-(*(int *)(hp1020_video_state_ptr_word + 0xfc) >> 0x1f)` |

## Open Firmware Meaning

- The normal created video work object initializes +0x74 to zero in currently mapped evidence.
- A zero +0x74 selects the descriptor queue/list path, which matches the transfer-ring and band-queue models.
- The nonzero +0x74 raw linked-list path remains mapped enough to recognize, but no normal print-path producer has been proven yet.
