# HP 1020 Video Remaining Units

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: candidate source for video state `+0xd0/+0xd4` remaining-unit counters

## Candidate Chain

| Stage | Field | Status | Evidence |
|---|---|---|---|
| `host_page_item` | `ZJI_VIDEO_Y / item id 0x12` | `candidate source` | generated ZjStream page item values and page-parameter builder switch case 0x12 |
| `page_parameter_builder` | `page-param +0x26` | `proven for page-parameter object` | 0x10009b4c writes item value at param_2 + 10 into param_1 +0x26 |
| `active_video_parameter` | `prepare param_1 +0x26` | `proven consumer` | 0x10014910 reads param_1 +0x26 into video state +0xd0/+0xd4 |
| `copy_or_alias_gap` | `page-param +0x26 -> active work/prepare +0x26` | `unresolved` | 0x100104c8 simple copier does not visibly copy +0x26; current explicit-source scan finds no direct work-object writer |

## Projection If Alias Holds

| Case | ZJI_VIDEO_Y candidate | +0xcc max chunk units | Stride +0xb8 | First refill units | First channel-B length |
|---|---:|---:|---:|---:|---:|
| `base` | `6824` | `4` | `1200` | `4` | `4800` |
| `a4_2400x600` | `6824` | `4` | `2384` | `4` | `9536` |
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

- The best static source candidate for +0xd0/+0xd4 is ZJI_VIDEO_Y through page-param +0x26.
- The direct copy or alias from page-param +0x26 into the active video prepare argument is not proven in current decompilation.
- Open firmware planning may use the generated candidate values, but implementation should keep this as a calibrated field until the copy/alias gap is closed.

## Checks

| Check | Status | Detail |
|---|---|---|
| `page_param_builder_maps_zji_video_y_to_0x26` | `present` | page parameter builder stores item id 0x12, ZJI_VIDEO_Y, into page-param +0x26 |
| `prepare_reads_work_0x26_to_remaining_counters` | `present` | video prepare copies active parameter +0x26 into video state +0xd0/+0xd4 |
| `simple_work_populate_does_not_copy_0x26` | `present` | 0x100104c8 does not visibly copy page-param +0x26 into work +0x26 |
| `work_common_init_clears_early_body` | `present` | common initializer clears the early work-object body, including +0x26 unless later populated |
| `current_search_keeps_gap_explicit` | `present` | explicit +0x26 hits are builder and prepare paths; no direct work-populate copy is currently visible |
| `candidate_values_match_generated_cases` | `present` | candidate remaining-unit values follow generated page heights |
