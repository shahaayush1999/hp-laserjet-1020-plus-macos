# HP 1020 PrintMgr Proven Inputs

This report connects the queue-send census to the PrintMgr dispatch table.

## Main Result

The proven constant sends into `PrintMgrQueue` / queue `0` are:

| Message | Producer | Dispatch target | Current meaning |
|---:|---|---:|---|
| `0x18` | PrintMgr startup and `0x10010230` restart helper | `0x1000f358` | receive-loop wake/retry/default path |
| `0x0d` | `0x1000f574` scheduler | `0x1000f358` | receive-loop wake/retry/default path |
| `0x0b` | `0x1000f574` scheduler and engine dispatch `0x10016164` | `0x1000f392` | page/work advance path |
| `0x1a` | `0x100100a8` status auxiliary helper | `0x1000f358` | receive-loop wake/retry/default path |
| `0x4a` | `0x10010230` restart helper | outside range | ignored by dispatch loop; likely wake/retry/no-op |
| `0x11` | video reset dispatch `0x10013d4c` | `0x1000f3ca` | video/high-level continuation; pops work and sends to JobMgr queue |

No direct static `queue 0, message 0x2d` producer has been found.

## Practical Interpretation

For normal print-path reverse engineering, the best PrintMgr messages to follow are no longer
`0x2d`; they are `0x0b` and `0x11`.

`0x0b` is the strongest page/work advance message. It is produced by PrintMgr's own scheduler and
also by the engine dispatch path. Its handler mutates PrintMgr state and can clear pending media
state.

`0x11` is the strongest completion/continuation message from video/reset back into PrintMgr. Its
handler calls `0x1000f814`, which pops active PrintMgr work and sends the message onward to queue
`3` / JobMgr.

`0x18`, `0x0d`, and `0x1a` target the same receive-loop/default block. They look more like
cooperative state-machine wakeups than heavy handlers.

`0x4a` is useful because it is deliberately sent to PrintMgr, but the PrintMgr loop rejects messages
outside `0x0b..0x43`. That makes it a likely wake/retry/no-op trigger rather than a normal switch
case.

## Next Target

The next good static pass is to split the `0x0b` and `0x11` handlers into named blocks and connect
their list operations to the job records created by JobMgr.
