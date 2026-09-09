# HP 1020 Video Work Object Static Pass

This pass exports the functions around the `0x94` video work object and records direct xrefs to the important helpers.

## Target Helpers

| Address | Label | Incoming refs |
|---:|---|---:|
| `0x1000f228` | `hp1020_video_work_create_candidate` | `2` |
| `0x100104c8` | `hp1020_work_populate_from_page_params_candidate` | `2` |
| `0x1000f0a8` | `hp1020_work_list_mark_or_send_candidate` | `6` |
| `0x1000f128` | `hp1020_work_mark_page_done_candidate` | `2` |
| `0x1000efbc` | `hp1020_work_release_raster_list_candidate` | `4` |

## Decompiled Targets

- `0x1000e414` `hp1020_job_mgr_thread_candidate`
- `0x1000ed90` `hp1020_job_try_start_or_continue_candidate`
- `0x1000eeb8` `hp1020_job_resume_or_enqueue_candidate`
- `0x1000efbc` `hp1020_work_release_raster_list_candidate`
- `0x1000f030` `hp1020_work_finalize_raster_list_candidate`
- `0x1000f0a8` `hp1020_work_list_mark_or_send_candidate`
- `0x1000f128` `hp1020_work_mark_page_done_candidate`
- `0x1000f204` `hp1020_work_common_init_candidate`
- `0x1000f228` `hp1020_video_work_create_candidate`
- `0x1000f280` `hp1020_work_mode_normalize_candidate`
- `0x1000f574` `hp1020_print_mgr_schedule_or_advance_candidate`
- `0x1000f84c` `hp1020_print_mgr_media_select_candidate`
- `0x10010338` `hp1020_job_record_create_and_enqueue_candidate`
- `0x10010398` `hp1020_child_page_record_create_candidate`
- `0x100104c8` `hp1020_work_populate_from_page_params_candidate`
- `0x10013c18` `hp1020_video_thread_candidate`
- `0x10014910` `hp1020_video_prepare_page_candidate`
- `0x10015214` `hp1020_video_render_or_dma_candidate`
- `0x10015438` `hp1020_video_alt_render_candidate`
- `0x10016164` `hp1020_engine_message_dispatch_candidate`

## Working Interpretation

- `0x1000f228` allocates a `0x94`-byte work object, initializes four embedded lists at `+0x50`, `+0x58`, `+0x60`, and `+0x68`, clears video DMA fields at `+0x84/+0x88/+0x8c/+0x90`, then calls common work initialization.
- `0x10010398` creates both a `0x50` child/page container and this `0x94` work object, then sends JobMgr messages `3` and `5`.
- JobMgr later stores this `0x94` object into child/page slot `+0x48`, sends it to PrintMgr queue `1` as message `0x0b`, and PrintMgr eventually sends it to video queue `8` as message `0x0b`.
- `0x100104c8` copies selected page-parameter halfwords into the work object: source `+0x22 -> +0x0c`, `+0x0a -> +0x0a`, `+0x06 -> +0x10`, `+0x12 -> +0x22`, `+0x16 -> +0x1e`, `+0x1a -> +0x14`, `+0x1e -> +0x16`, `+0x0e -> +0x0e`, and source word `+0x00 -> +0x00`.
- JobMgr case `0x29` copies a 20-byte incoming payload into runtime block `0x10023e28`; later JobMgr copies that block into work offsets `+0x84/+0x88/+0x8c/+0x90` before video starts.
- No producer for JobMgr message `0x29` is currently proven by the queue-send census, so the parser-side origin of that 20-byte runtime block remains the next unresolved boundary.
