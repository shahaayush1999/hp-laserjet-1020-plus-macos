# HP 1020 PrintMgr 0x2d Fallout

This pass checks whether data-store queue subscriber notifications land in the PrintMgr queue.

## Key Result

- Data-store writes notify queue subscribers with message `0x2d` and payload words: entry id, new value, type class.
- PrintMgr registers queue subscribers for data-store entries `0x18` and `0x01`, with subscriber queue id `1`.
- Stock constructor registration proves queue id `1` is `PrintMgrQueue`; the older engine/no-op interpretation was a mapping error. See `analysis/queue-routing/registration.md`.
- PrintMgr dispatch includes message `0x2d`, target `0x1000f497`. The datastore subscriber path supplies its producer through queue id `1`.
- The downstream scheduler function `0x1000f574` calls `0x1000fcb0`, and `0x1000fcb0` explicitly handles `message == 0x2d` and `entry == 1` in its state machine.

## Important Functions

| Address | Working label | Role |
|---:|---|---|
| `0x1000f324` | `hp1020_print_mgr_thread_candidate` | receives PrintMgrQueue messages and dispatches table `0x100048f0` |
| `0x1000f574` | `hp1020_print_mgr_schedule_or_advance_candidate` | advances queued page/media work and calls notification state helper |
| `0x1000fcb0` | `hp1020_print_mgr_datastore_notify_state_candidate` | handles `0x2d` datastore notifications and completion-style messages `0x2c`/`0x32` |
| `0x1000f84c` | `hp1020_print_mgr_media_select_candidate` | locks data-store entries `0x1d` and `0x01`, chooses/updates media fields, and may emit status |
| `0x10010170` | `hp1020_print_mgr_emit_media_status_candidate` | writes back data-store entry `0x1f` and sends StatusMgrQueue message `0x2c` |
| `0x10010218` | `hp1020_queue_send_message4_candidate` | small wrapper that sends a 4-word message to a queue |

## Data-Store Notification Path

```text
data-store entry write
  -> 0x10010fd0 write/notify helper
  -> queue subscriber message 0x2d
  -> known subscriber queue id 1
  -> PrintMgrQueue, object 0x10028a74
  -> PrintMgr 0x2d handler at 0x1000f497
```

The same notification continues through the PrintMgr handler:

```text
PrintMgrQueue message 0x2d
  -> PrintMgr dispatch table target 0x1000f497
  -> print scheduling/state helper 0x1000f574
  -> notification state helper 0x1000fcb0
  -> possible media/status writeback and StatusMgrQueue message 0x2c
```

## Current Interpretation

- Known data-store queue subscriptions target PrintMgr through queue id `1`.
- The producer-to-handler route is resolved statically; execution still depends on successful initialization and RTOS delivery.
- Next, execute selected PrintMgr dispatch and cancellation transitions with explicit queue and hardware-completion boundaries.
