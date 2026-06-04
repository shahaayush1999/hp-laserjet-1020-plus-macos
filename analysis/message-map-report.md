# HP 1020 Queue/Message Map

This consolidates the internal queue and message-ID evidence from the queue-resolution, message-producer, and dispatch/MMIO passes.

The important rule: the same message number can mean different things on different queues. Treat `(queue, message)` as the meaningful key, not the message number alone.

## Queue Map

| Queue ID | Working name | Consumer | Confidence |
|---:|---|---:|---|
| `0` | `PrintMgrQueue` | `0x1000f324` `hp1020_print_mgr_thread_candidate` | high |
| `1` | `engMsgQ` / engine queue | `0x100163b0` `hp1020_engine_thread_candidate` | high |
| `3` | `Job Mgr Queue` | `0x1000e414` `hp1020_job_mgr_thread_candidate` | high |
| `8` | `Video Queue` | `0x10013c18` `hp1020_video_thread_candidate` | high, but slot write still inferred |
| `10` | `StatusMgrQueue` | `0x10010590` `hp1020_status_mgr_thread_candidate` | high |
| `0x0f` | `DelayMgr Msg Queue` | `0x10010b0c` `hp1020_delay_mgr_receive_thread_candidate` | high |

## Message Highlights

| Queue | Message | Working meaning | Producer/source | Consumer/handler | Confidence |
|---:|---:|---|---|---|---|
| `0` | `0x18` | print-manager startup/initial poll | PrintMgr itself | PrintMgr | high |
| `0` | `0x11` | video reset/high-level continuation | Video reset dispatch | PrintMgr | medium |
| `1` | `0x0b` | main page/engine work | JobMgr / engine continuation | Engine dispatch | high |
| `1` | `0x10` | video finished / engine can advance | Video thread | Engine dispatch | high |
| `1` | `0x17` | engine status/event update / queue wake | Engine status paths / video reset cases | engine dispatch default return block `0x100162aa` | high producer, high default-consumer proof |
| `1` | `0x40` | force/start page path | unresolved | Engine dispatch | medium |
| `3` | `0x21` | job starts engine page work | unresolved | JobMgr | high |
| `3` | `0x25` | job completion/error-looking event | JobMgr | JobMgr | medium |
| `8` | `0x0b` | video/page work item | Video reset dispatch | Video thread | high |
| `8` | `0x0f` | video reset/flush | unresolved | Video thread | medium |
| `10` | `0x30` | status-like event | Job/status path | StatusMgr | medium |
| `10` | `0x31` | status-like event | Job/status path | StatusMgr | medium |
| `0x0f` | `0x44` | delay callback/timer message | delay helpers | DelayMgr | medium |

The complete working table is in `analysis/message-map/queue-message-map.tsv`.

Engine message `0x17` has its own payload map in `analysis/engine-event-report.md` and
`analysis/engine-events/engine-0x17-events.tsv`.

The direct engine-dispatch table maps message `0x17` to the default return/no-op block. It is a
produced and received message, but not a normal consumed engine command in the recovered switch.

## Current Interpretation

The print path is now a set of cooperating queue state machines:

```text
JobMgr queue 3
  -> PrintMgr queue 0
  -> Video Queue 8
  -> Engine queue 1
  -> StatusMgr queue 10
  -> PJL/status response builders
```

The engine side is the highest-risk area. The engine queue receives both page-progress messages and hardware/status events, then drives MMIO-heavy code. The safest next reverse-engineering target is not more broad discovery; it is narrowing the meanings of engine messages `0x0b`, `0x10`, `0x17`, and `0x40`, because those sit closest to actual paper motion, fuser/scanner state, and raster transfer.

## Remaining Gaps

- The queue table write that assigns `Video Queue` to slot `8` still has not been directly found.
- Many PrintMgr active dispatch cases have known table targets but unresolved producers; the queue-send census found no direct static `queue 0, message 0x2d` producer.
- StatusMgr messages are known numerically, but the PJL-visible status semantics still need branch-level naming.
- PJL-visible status strings are now table-mapped, but the physical meaning of each status mask is not fully proven.
- Engine message `0x17` clearly carries status/event detail, but the payload fields are not fully decoded into paper/fuser/toner conditions.
