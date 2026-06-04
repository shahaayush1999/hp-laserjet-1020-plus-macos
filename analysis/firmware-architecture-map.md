# HP 1020 Firmware Architecture Map

This is the current working map of the HP LaserJet 1020/1020 Plus firmware after the first reverse-engineering passes.

It is intentionally practical: what subsystem exists, what evidence anchors it, and what remains unresolved.

## Upload Layer

The downloadable firmware file is not just a raw blob. It is:

```text
PJL prefix -> ACL header -> date-prefixed Xtensa ELF -> PJL reset trailer
```

Known structure:

| Offset | Length | Meaning |
|---:|---:|---|
| `0x00000000` | `34` | `ESC %-12345X@PJL ENTER LANGUAGE=ACL\r\n` |
| `0x00000022` | `8` | ACL header: magic `00 ac c0 de`, ELF payload length `0x0001f574` |
| `0x0000002a` | `128380` | exact `sihp1020.img` |
| `0x0001f613` | `9` | `ESC %-12345X` |

The `.img` file starts with ASCII date `20050309`; the real ELF begins after those 8 bytes.

`scripts/wrap-firmware-acl.py` now reproduces `assets/runtime/sihp1020.dl` byte-for-byte from `assets/firmware-source/sihp1020.img`.

## CPU And Program Shape

Firmware payload:

- architecture: 32-bit big-endian Xtensa, old/unofficial machine ID `0xabc7`
- entry point: `0x100167a8`
- stripped static executable
- `.text`: `0x10005c80`, size `0x15f0f`
- reset vector section around `0x10100020`

Ghidra can analyze and decompile this when forced to:

```text
Xtensa:BE:32:default / default compiler spec
```

The decompiler is good enough for useful structure, but some indirect jumps and Xtensa instructions still produce warnings.

## Runtime Model

The firmware appears to use ThreadX-style queues, tasks, and synchronization.

Startup now appears layered:

```text
ELF entry 0x100167a8
  -> pointer at 0x10006a14
  -> 0x10006cd0 CPU/TLB init candidate
  -> interrupt/scheduler/runtime region
  -> task descriptors
  -> queue-driven printer subsystems
```

Key queue primitive labels:

| Address | Label |
|---:|---|
| `0x10013658` | `hp1020_queue_send_candidate` |
| `0x10013620` | `hp1020_send_or_raise_engine_msg_candidate` |
| `0x10013668` | lower queue table send wrapper |
| `0x1001809c` | `threadx_queue_receive_wait_candidate` |
| `0x100180dc` | lower ThreadX queue send candidate |

RTOS object signatures now confirmed:

| Magic | Meaning |
|---|---|
| `SEMA` | semaphore |
| `MUTE` | mutex |
| `QUEU` | queue |
| `BLOC` | block pool / block object |
| `BYTE` | byte pool |
| `THRD` | thread |

The lower wrapper at `0x10013668` computes queue control blocks like this:

```text
queue_control_block = *(0x1002c918 + queue_id * 4)
```

That means queue IDs in send calls are meaningful firmware-level routing numbers.

## Main Threads

| Subsystem | Thread entry | Queue / object evidence | Current confidence |
|---|---:|---|---|
| USB2 | `0x10008ff0` | `USB2Thread` | high |
| USB idle | `0x10009934` | `USB2IdleThread` | high |
| Job manager | `0x1000e414` | `Job Mgr Queue` | high |
| Print manager | `0x1000f324` | `PrintMgrQueue` | high |
| Status manager | `0x10010590` | `StatusMgrQueue` | high |
| Delay manager | `0x10010b0c` | `DelayMgr Msg Queue` | high |
| Data store | `0x1001146c` | data-store descriptor region | medium |
| Control panel | `0x100139e4` | control-panel descriptor region | medium |
| Video/raster | `0x10013c18` | `Video Queue` / `tVideo` | high |
| Engine delay | `0x1001635c` | `engDelayMsgQ` | high |
| Engine | `0x100163b0` | `engMsgQ` / `tEngine` | high |
| System timer | `0x1001788c` | timer descriptor region | medium |

## Queue Map

| Queue ID | Likely owner | Consumer | Known produced messages |
|---:|---|---:|---|
| `0` | Print manager | `0x1000f324` | `0x18`, `0x11` |
| `1` | Engine | `0x100163b0` | `0x0b`, `0x0d`, `0x10`, `0x11`, `0x16`, `0x17`, `0x18`, `0x19`, `0x1a`, `0x25` |
| `3` | Job manager | `0x1000e414` | `1`, `2`, `3`, `5`, `6`, `0x21`, `0x25` |
| `8` | Video/deferred engine path | likely `0x10013c18` or adjacent video worker | `0x0b` |
| `10` | Status manager | `0x10010590` | `0x2c`, `0x2e`, `0x30`, `0x31` |
| `0x0f` | Delay manager | `0x10010b0c` | `0x44` |

Queue `8` remains the least resolved active print-path queue.

The consolidated `(queue, message)` dictionary is in `analysis/message-map-report.md` and
`analysis/message-map/queue-message-map.tsv`.

Engine queue message `0x17` is a status/event family with a second-word payload. The current
event-code map is in `analysis/engine-event-report.md`. The exact engine dispatch table maps
`0x17` to the default return/no-op block, so it is not a normal consumed engine command.
The branch conditions that select the poller event words are in `analysis/engine-status-poll-report.md`.

The PJL-visible status/fault vocabulary is separate from engine dispatch. Strings such as
`PAPERLESS`, `FUSER`, `TONEREXP`, and `JAMRECOVERY` are rows in a status command table at
`0x10003c8c`, reached through the PJL/status parser and response builders.

## Indexed Data Store

Several PJL/status, USB, video, and job paths read state through a shared indexed data-store API:

| Address | Label | Role |
|---:|---|---|
| `0x10010f54` | `hp1020_datastore_read_locked_candidate` | copies indexed entry values into caller buffers after locking |
| `0x10010fd0` | `hp1020_datastore_write_notify_unlock_candidate` | writes indexed entry values, notifies subscribers, then unlocks |
| `0x10011178` | `hp1020_datastore_get_value_candidate` | reads byte/halfword/word values by entry index |
| `0x100111b4` | `hp1020_datastore_lock_entry_candidate` | locks the indexed entry and returns its value pointer |
| `0x100111d8` | `hp1020_datastore_unlock_entry_candidate` | unlocks the indexed entry |
| `0x10011258` | `hp1020_datastore_register_callback_subscriber_candidate` | registers callback subscribers for data-store entry changes |
| `0x1001135c` | `hp1020_datastore_register_queue_subscriber_candidate` | registers queue subscribers for data-store entry changes |
| `0x10013764` | `hp1020_control_panel_datastore_callback_candidate` | callback for entries `0x18`/`0x19`; updates control-panel/LED-ish state bytes |
| `0x100162cc` | `hp1020_engine_datastore_media_callback_candidate` | callback for entries `0x10..0x14`; maps them to internal ids `0x200..0x204` |
| `0x10016318` | `hp1020_engine_event_0x0f_config_callback_candidate` | callback for entry `0x0f`; maps DENSITY into engine state |

The data descriptor table is reached through `0x1000647c -> 0x1001ce14`, with `0x18`-byte entries.
The matching lock table is reached through `0x10006464 -> 0x1002c0b0`, with `0x1c`-byte entries.
The subscriber table is reached through `0x10006490 -> 0x1002c56c`; queue subscribers receive
message `0x2d`, while callback subscribers are called as `callback(entry_id, new_value)`.

Important status-facing slots:

| Index | Current meaning |
|---:|---|
| `0x18` | `ONLINE=` boolean used by USTATUS DEVICE |
| `0x1a` | `DISPLAY="..."` string pointer used by USTATUS DEVICE |
| `0x1b` | StatusMgr USTATUS timing/enable slot |
| `0x1f` | status-code lookup state object pointer |
| `0x24` | JAMRECOVERY/status alternate backing slot |
| `0x25` | PAPERLESS/status variable backing slot |

## High-Level Data Flow

```text
USB/PJL/ZjStream input
  -> JobMgr
  -> PrintMgr
  -> Video thread
  -> Engine thread
  -> MMIO hardware registers
  -> StatusMgr
  -> PJL/status responses
```

This is not one monolithic parser. It is a set of cooperating state machines connected through queues.

`analysis/job-object-flow-report.md` now maps the first work-object flow: JobMgr allocates a
`0x78`-byte job/work record and `0x50`-byte child/page-ish records; PrintMgr moves list nodes from
pending list `0x10006324` to active list `0x10006328`; PrintMgr `0x11` returns active work to
JobMgr queue `3`.

`analysis/job-record-fields-report.md` maps the first useful fields in those records. The important
ones for print flow are job `+0x70`/`+0x74` child-list head/tail and child/page `+0x48`/`+0x4c`
active work slots.

`analysis/video-handoff-report.md` maps the next bridge: PrintMgr sends `queue 8, message 0x0b`
with the video work pointer in payload word 3; VideoThread stores that pointer in video state
`+0x60` or `+0x64`, then calls prepare/render and sends engine queue `0x10` when done.

## Status/PJL Fault Path

The status path now has a concrete bridge from hardware-ish engine words to user-visible PJL text:

```text
engine status polling / preflight
  -> internal status/event word
  -> 0x10010838 status-state update
  -> StatusMgrQueue / status event storage
  -> USTATUS DEVICE builders
  -> PJL CODE= / DISPLAY= response text
```

Important status functions:

| Address | Label | Role |
|---:|---|---|
| `0x1000a2a4` | `hp1020_status_word_to_pjl_code_candidate` | converts an internal status word into a numeric PJL `CODE=` value |
| `0x1000b870` | `hp1020_pjl_status_table_get_candidate` | reads values by PJL/status table row |
| `0x1000c8fc` | `hp1020_pjl_status_table_set_candidate` | parses string names and updates stored status/config values |
| `0x10010590` | `hp1020_status_mgr_thread_candidate` | consumes `StatusMgrQueue` messages |
| `0x10010838` | `hp1020_status_state_update_candidate` | normalizes status words and triggers notification paths |

The status-state object is reached through `0x100063d8 -> 0x1002adb4`.
Useful offsets:

| Offset | Working field |
|---:|---|
| `0x04` | phase/state (`2`, `3`, `4`) |
| `0x08` | current status word |
| `0x0c` | pending/highest category status word |
| `0x10` | transition status word |
| `0x14` | source/reason parameter |
| `0x18` | pending/subscriber depth |

The status table lives at `0x10003c8c` through pointer word `0x10006148`, with `0x24`-byte entries.
Important rows include `JAMRECOVERY`, `TONEREXP`, `SETERROR`, `PAPERLESS`, and `FUSER`.

The PJL `CODE=` path has a second table at `0x1001be40` through pointer word `0x10006014`.
It contains 20 halfword-pair entries that map an internal input/status index to an offset added to
base `0xa028`, producing codes such as `41000`, `41002`, `41009`, and `41034`.
HP's PJL reference defines `41xyy` as foreground paper loading, so these generated `410xx` codes
are currently best interpreted as paper/media loading state.

Key constants currently worth naming:

| Address | Value | Current note |
|---:|---:|---|
| `0x10005f74` | `0xff00` | low/mid status field mask |
| `0x10006418` | `0x1600` | status subfamily value |
| `0x1000641c` | `0x160a` | status subfamily equality value |
| `0x10005e34` | `0x80000000` | generic high-bit/error/fallback status word |
| `0x10006378` | `0x7c000000` | high-bit severity/category mask |
| `0x10006018` | `0x2711` | default PJL code base/value |
| `0x1000601c` | `0xa028` | PJL code base for mapped fault/status values |
| `0x10006014` | `0x1001be40` | pointer to PJL status-code offset table |
| `0x100063d8` | `0x1002adb4` | pointer to status-state object |

## Print Path

### Print Manager

Entry:

- `0x1000f324` `hp1020_print_mgr_thread_candidate`

Behavior:

- marks itself ready
- initializes or registers message IDs `0x18` and `1`
- sends startup message `0x18` to queue `0`
- receives from `PrintMgrQueue`
- dispatches message IDs `0x0b` through `0x43`
- has a real `0x2d` dispatch case, but the queue-send census found no direct static `queue 0, message 0x2d` producer
- proven queue-0 inputs include `0x18`, `0x0d`, `0x0b`, `0x1a`, `0x4a`, and `0x11`
- among those, `0x0b` and `0x11` are the strongest normal print-path messages; `0x4a` is sent to queue 0 but is outside the dispatch range
- calls `0x1000f574` to advance page/media work; that path can call `0x1000fcb0`, which handles `0x2d`/entry `1`

Switch table:

- table address: `0x100048f0`
- first useful entries map `0x0b` through `0x11` to non-default blocks
- `0x2d` maps to target `0x1000f497`, a notification-looking handler inside PrintMgr
- many later IDs currently point at a default/no-op/error block

### Video/Raster

Entry:

- `0x10013c18` `hp1020_video_thread_candidate`

Known message cases:

- `0x0b`: page/video work item
- `0x0f`: reset/flush

Important callees:

| Address | Label |
|---:|---|
| `0x10014910` | `hp1020_video_prepare_page_candidate` |
| `0x10015214` | `hp1020_video_render_or_dma_candidate` |
| `0x10015438` | `hp1020_video_alt_render_candidate` |
| `0x10015458` | `hp1020_video_reset_or_flush_candidate` |

After page/video processing, the video thread sends message `0x10` to queue `1`, feeding the engine.

The string `refreshRawBands, ic.pBidBlock=0x%08x, nBackloggedBands=%u` strongly suggests this firmware processes raster bands, not a single full-page framebuffer.

The work pointer carried by Engine/PrintMgr/Video `0x0b` is now mapped as a `0x94`-byte
video/page work object:

- created by `0x1000f228` `hp1020_video_work_create_candidate`
- populated by `0x100104c8` `hp1020_work_populate_from_page_params_candidate`
- linked from the `0x50` child/page container through active slot `+0x48`
- carries raster/chunk list nodes at `+0x50`
- carries late video hardware fields at `+0x84`, `+0x88`, `+0x8c`, and `+0x90`

Those late hardware fields are copied from runtime block `0x10023e28`, which JobMgr case `0x29`
fills from a 20-byte incoming payload. The producer of JobMgr `0x29` is not yet proven.

### Engine

Entry:

- `0x100163b0` `hp1020_engine_thread_candidate`

Central dispatch:

- `0x10016164` `hp1020_engine_message_dispatch_candidate`

Known engine dispatch cases:

| Message | Observed behavior |
|---:|---|
| `0x0b` | main page/engine work path |
| `0x0d` | rewritten to `0x0e` and sent to engine queue |
| `0x0f` | reset/clear path; sends `0x25`; resets state fields |
| `0x11` | polls status; drains deferred engine/page work |
| `0x18` | status poll |
| `0x19` | sends `0x16` |
| `0x1a` | preflight/status update path |
| `0x40` | sets state then falls through into `0x0b` |

The engine thread registers handlers for event IDs `0x0f` through `0x14`, then loops on the engine queue.

## Hardware Register Families

Current likely MMIO families:

| Family | Likely role | Evidence |
|---:|---|---|
| `0xb100....` | video/raster engine setup | heavily used in `0x10014910` |
| `0xb200....` | video/DMA or band transfer | used in `0x10015214` |
| `0xb204....` | video/DMA side registers | used in `0x10015214` |
| `0xb208....` | video/DMA side registers | used in `0x10015214` |
| `0xb020....` | engine/control hardware | engine descriptor table region |
| `0xb050....` | engine status/control | engine status/preflight path |
| `0xb300....` | USB hardware | USB path pass |

Register names are not known yet. The family grouping is useful; exact semantics still require focused analysis or hardware observation.

First behavioral names:

- `0xb050000c`: engine status/ready register candidate
- `0xb0500004`: engine command/control register candidate
- `0xb1000000` / `0xb1000004`: video reset/control-status pair A
- `0xb1000100` / `0xb1000104`: video reset/control-status pair B
- `0xb200....`: video transfer control/descriptors
- `0xb204....` and `0xb208....`: paired video transfer channels

## What Is Actually Known Now

Known with high confidence:

- how to package firmware upload bytes
- CPU/endian/load shape
- USB descriptor/control path exists and has static descriptors
- thread/task boundaries
- main queue IDs for print/job/status/video/engine
- major print/video/engine entry points
- broad MMIO address families

Known with medium confidence:

- queue `8` is video/deferred engine-related
- message `0x0b` is page/work in video and engine contexts
- message `0x0f` is reset/flush-ish in video/engine contexts
- message `0x17` is engine status-change/event
- message `0x25` is reset/clear/completion-ish notification

Still unknown:

- exact boot ROM validation rules for the ELF/interface table
- exact transition from low-level CPU init into scheduler start
- exact hardware meaning of each engine/video register
- exact raster band format expected by video hardware
- exact event semantics for engine handler IDs `0x0f` through `0x14`
- whether the boot ROM accepts any sane Xtensa ELF with the same wrapper or expects HP-specific ABI/interface details
- whether a minimal non-printing firmware can enumerate without initializing engine hardware

## Practical Next Targets

Best next reverse-engineering steps:

1. Label RTOS primitives around `0x100175c0` through `0x1001a590`.
2. Resolve the scheduler/task creation path from startup into the named task descriptors.
3. Resolve queue `8` by finding the queue table initialization path or all consumers of `0x1002ee38`.
4. Build a register-semantics table for `0xb100`, `0xb200`, `0xb204`, `0xb208`, `0xb020`, and `0xb050`.
5. Only after those: consider a minimal firmware experiment that packages a harmless ELF and validates boot/upload behavior.
