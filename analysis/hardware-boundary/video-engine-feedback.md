# HP 1020 Video-to-Engine Feedback Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: VideoThread completion, reset dispatch, and engine/status feedback messages

## Key Literal Values

| Name | Value |
|---|---:|
| `video_reset_event_case_3` | `0xe6e01201` |
| `video_reset_event_case_4` | `0xe6e01202` |
| `video_reset_event_case_5` | `0xeee01b02` |
| `video_reset_event_case_6` | `0xeee01b04` |
| `video_reset_event_case_2_or_7` | `0xeee01b01` |
| `video_transfer_status_control` | `0xb2000010` |
| `video_channel_b_control` | `0xb2080000` |
| `video_channel_a_control` | `0xb2040000` |
| `video_channel_a_status` | `0xb204000c` |
| `video_channel_b_status` | `0xb208000c` |
| `video_channel_status_clear_mask` | `0x7fffffff` |
| `video_block_a_status` | `0xb1000004` |
| `video_block_b_status` | `0xb1000104` |
| `video_block_a_control` | `0xb1000000` |
| `video_block_b_control` | `0xb1000100` |

## Feedback Sequences

### `normal_video_done`

- source: `0x10013c18 hp1020_video_thread_candidate`
- trigger: video queue message 0x0b with page work pointer
- meaning: After prepare/render, VideoThread tells PrintMgr (queue 1) that video work reached the post-render checkpoint.

| Target | Message | Payload | Case |
|---|---:|---:|---|
| `queue 1` | `0x10` | `original video queue payload` | `-` |

State slots:
- video_state +0x60 active work
- video_state +0x64 deferred work

### `video_reset_or_flush`

- source: `0x10013c18 -> 0x10015458 -> 0x10013d4c`
- trigger: video queue message 0x0f
- meaning: Flush/reset clears active/deferred video work and reports reset completion to PrintMgr (queue 1).

| Target | Message | Payload | Case |
|---|---:|---:|---|
| `queue 1 via wrapper` | `0x25` | `no event word in word 1` | `-` |

State slots:
- clear video_state +0x60
- clear video_state +0x64

### `reset_dispatch_complete_active`

- source: `0x10013d4c hp1020_video_reset_dispatch_candidate(param=0)`
- trigger: engine poll/reset path calls video reset dispatch with param 0
- meaning: This is the strongest current video-to-engine work-advance bridge.

| Target | Message | Payload | Case |
|---|---:|---:|---|
| `wrapper target 0` | `0x11` | `completion/advance` | `-` |
| `wrapper target 8` | `0x0b` | `deferred video work when present` | `-` |

State slots:
- clear video_state +0x60 active work
- if video_state +0x64 deferred work exists, requeue it as video queue message 0x0b then clear +0x64

### `reset_dispatch_event_words`

- source: `0x10013d4c hp1020_video_reset_dispatch_candidate(param=2..7)`
- trigger: video reset dispatch error/status cases
- meaning: Video reset/error states and mechanical status polling both send event words to PrintMgr queue 1.

| Target | Message | Payload | Case |
|---|---:|---:|---|
| `queue 1 via wrapper` | `0x17` | `0xeee01b01` | `2 or 7` |
| `queue 1 via wrapper` | `0x17` | `0xe6e01201` | `3` |
| `queue 1 via wrapper` | `0x17` | `0xe6e01202` | `4` |
| `queue 1 via wrapper` | `0x17` | `0xeee01b02` | `5` |
| `queue 1 via wrapper` | `0x17` | `0xeee01b04` | `6` |

State slots:
- clear video_state +0x68
- clear video_state +0x6c

## Video State Fields

| Offset | Field | Meaning |
|---:|---|---|
| `+0x60` | active video work pointer | work currently being prepared/rendered by VideoThread |
| `+0x64` | deferred video work pointer | second work item held while active slot is occupied |
| `+0x68` | reset/dispatch scratch slot | cleared at the end of video reset dispatch |
| `+0x6c` | video state/mode flag | set to 2 after render reaches transfer-running state; cleared at reset dispatch end |
| `+0x94` | video ring read/consumer index candidate | compared with +0x98 before descriptor handoff |
| `+0x98` | video ring write/producer index candidate | advanced modulo 4 in render path |
| `+0x9c` | active raster list pointer | set from work +0x50 before render |
| `+0xa0` | raster/reset walk list | walked and drained during reset dispatch |
| `+0xa4` | saved raster pointer | set when render captures the current raster list |
| `+0xfc` | reset dispatch sign/latch field | gates a decompiler-broken reset-dispatch branch; exact meaning unresolved |

## Hardware Reset Registers

| Register | Role |
|---:|---|
| `0xb2000010` | transfer status/control bit 0 cleared during reset dispatch |
| `0xb2080000` | channel B reset/enable toggled with bit 0x2 |
| `0xb2040000` | channel A reset/enable toggled with bit 0x2 |
| `0xb204000c` | channel A status bit 0 waited clear and masked with 0x7fffffff |
| `0xb208000c` | channel B status bit 0 waited clear and masked with 0x7fffffff |
| `0xb1000000` | video block A control bit 0x100 cleared/set in reset flush |
| `0xb1000100` | video block B control bit 0x100 cleared/set in reset flush |
| `0xb1000004` | video block A busy bit 0x200 wait in reset flush |
| `0xb1000104` | video block B busy bit 0x200 wait in reset flush |

## Evidence Checks

| Check | Status | Source | Needle |
|---|---|---|---|
| `video_queue_receive` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `threadx_queue_receive_wait_candidate` |
| `video_queue_message_0x0b` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `if (aiStack_30[0] == 0xb) break` |
| `video_queue_message_0x0f` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `if (aiStack_30[0] == 0xf)` |
| `video_active_slot_0x60` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `*(undefined4 *)(puVar1 + 0x60) = uStack_24` |
| `video_deferred_slot_0x64` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `*(undefined4 *)(puVar1 + 100) = uStack_24` |
| `video_normal_prepare` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `hp1020_video_prepare_page_candidate(piVar3)` |
| `video_normal_render` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `hp1020_video_render_or_dma_candidate(piVar3)` |
| `video_alt_render` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `hp1020_video_alt_render_candidate(piVar3)` |
| `video_done_engine_0x10` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `aiStack_30[0] = 0x10` |
| `video_done_send_engine_queue` | `present` | `analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c` | `hp1020_queue_send_candidate(1,aiStack_30)` |
| `reset_dispatch_case_0_engine_0x11` | `present` | `analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c` | `local_30 = 0x11` |
| `reset_dispatch_requeue_0x0b` | `present` | `analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c` | `hp1020_send_or_raise_engine_msg_candidate(8,&local_30)` |
| `reset_dispatch_case_1_0x25` | `present` | `analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c` | `local_30 = 0x25` |
| `reset_dispatch_event_0x17` | `present` | `analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c` | `local_30 = 0x17` |
| `reset_dispatch_clears_0x68` | `present` | `analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c` | `*(undefined4 *)(hp1020_video_state_ptr_word + 0x68) = 0` |
| `reset_flush_calls_dispatch_1` | `present` | `analysis/dispatch-mmio/decompiled/10015458_hp1020_video_reset_or_flush_candidate.c` | `hp1020_video_reset_dispatch_candidate(1)` |
| `render_sets_state_0x6c_2` | `present` | `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c` | `*(undefined4 *)(hp1020_video_state_ptr_word + 0x6c) = 2` |
| `engine_case_0x11_receives_video_done` | `present` | `analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c` | `case 0x11:` |

## Open Firmware Meaning

- Printing firmware needs this feedback loop, not only parser and video register writes.
- The normal render path reports message 0x10 to PrintMgr queue 1 after prepare/render.
- Video reset/error cases produce engine event 0x17 words that share the status pipeline with mechanical engine polling.
- The next missing offline model is exact timing/ownership around the video transfer ring and interrupts, especially how +0x94/+0x98/+0x9c/+0xa0 advance.

