# HP 1020 Video Remaining Units

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: direct source for video state `+0xd0/+0xd4` remaining-unit counters

## Source Chain

| Stage | Field | Status | Evidence |
|---|---|---|---|
| `START_PAGE` | `allocated 0x94 work` | `ELF-byte verified` | 0x10009faf call8 allocate; a7 retains result |
| `direct_builder` | `work +0x26 = low16(ZJI_VIDEO_Y)` | `ELF-byte verified` | 0x10009fe0 a10=a7; 0x10009fed call8 0x10009b4c; item 0x12 store at 0x10009c35 |
| `prepare` | `video +0xd0/+0xd4 = work +0x26` | `static consumer verified` | 0x10014910 consumer |

## Initial Refill Projection

| Case | ZJI_VIDEO_Y | +0xcc max chunk units | Stride +0xb8 | First refill units | First channel-B length |
|---|---:|---:|---:|---:|---:|
| `base` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_2400x600` | `6824` | `0` | `2384` | `0` | `0` |
| `a4_600x600` | `6824` | `12` | `608` | `12` | `7296` |
| `a4_cardstock_media` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_default` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_draft` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_logical_clip` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_manual_feed` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_two_copies` | `6824` | `4` | `1200` | `4` | `4800` |
| `legal_default` | `8208` | `4` | `1232` | `4` | `4928` |
| `letter_default` | `6408` | `4` | `1232` | `4` | `4928` |

## Explicit `+0x26` Write Hits

| Source | Line | Text |
|---|---:|---|
| `page_param_builder` | `102` | `*(undefined2 *)(param_1 + 0x26) = *(undefined2 *)((int)param_2 + 10);` |
| `prepare` | `196` | `*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26);` |
| `prepare` | `197` | `*(uint *)(puVar15 + 0xd4) = (uint)*(ushort *)(param_1 + 0x26);` |

## Current Conclusion

- ZJI_VIDEO_Y directly initializes active work +0x26; prepare copies it into both remaining counters.
- The alternate 0x100104c8 constructor is not used by the normal START_PAGE handler; its missing copy is irrelevant here.
- The source is resolved. Hardware must still establish the physical meaning and safe completion behavior of the counters.

## Checks

| Check | Status | Detail |
|---|---|---|
| `page_param_builder_maps_zji_video_y_to_0x26` | `present` | page parameter builder stores item id 0x12, ZJI_VIDEO_Y, into page-param +0x26 |
| `prepare_reads_work_0x26_to_remaining_counters` | `present` | video prepare copies active parameter +0x26 into video state +0xd0/+0xd4 |
| `simple_work_populate_does_not_copy_0x26` | `present` | 0x100104c8 does not visibly copy page-param +0x26 into work +0x26 |
| `work_common_init_clears_early_body` | `present` | common initializer clears the early work-object body, including +0x26 unless later populated |
| `direct_start_page_builder_verified` | `present` | ELF bytes prove the builder destination is the same active work pointer |
| `queue_payload_identity` | `present` | queue payload preserves the directly populated active work object |
| `candidate_values_match_generated_cases` | `present` | candidate remaining-unit values follow generated page heights |
