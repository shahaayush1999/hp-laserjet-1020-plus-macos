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

Switch table:

- table address: `0x100048f0`
- first useful entries map `0x0b` through `0x11` to non-default blocks
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
