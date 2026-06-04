# HP 1020 Job Record Field Map

This is the first field map for the job/work records used by JobMgr and PrintMgr.

## Record Types

Two record sizes are now visible:

| Size | Creator | Working type |
|---:|---:|---|
| `0x78` | `0x10010338` | job/work record |
| `0x50` | `0x10010398` | child/page record |

JobMgr stores these records inside small linked-list nodes. The list node payload is at node
offset `+0x0c`.

## `0x78` Job/Work Record

| Offset | Working meaning | Evidence |
|---:|---|---|
| `+0x48` | status/user payload word | copied from creator `param_1[2]`; forwarded to StatusMgr messages `0x30`/`0x31`; mirrored into PJL/status helper payloads |
| `+0x58` | status/job id payload word | copied from creator `param_1[0]`; forwarded to StatusMgr messages `0x30`/`0x31`; written to data-store entry `0x1c` by PrintMgr helper |
| `+0x5c` | job mode/status mode | copied from creator `param_1[1]`; if `1`, JobMgr emits StatusMgr `0x31`; if not `6`, JobMgr increments data-store entry `6` on completion |
| `+0x60` | downstream forwarding mode | copied from creator `param_1[3]`; if `1`, JobMgr forwards the current message to queue id at `+0x64` |
| `+0x64` | dynamic queue id | copied from creator `param_1[4]`; used as the queue id in JobMgr dynamic sends |
| `+0x68` | pending/resume flag | toggled in JobMgr cases `2`, `0x11`, and cleanup paths |
| `+0x69` | active/inhibit flag | set when job enters JobMgr case `1`; later used to decide cleanup and pause behavior |
| `+0x6a` | coarse job state byte | copied into status helper output; values `1` and `2` appear in JobMgr cleanup paths |
| `+0x6b` | PrintMgr/status helper flag | cleared during JobMgr case `1`; set by PrintMgr message helper after status data-store writes |
| `+0x6c` | completion/page counter | incremented in JobMgr case `0x11`; forwarded in StatusMgr `0x31` payload |
| `+0x70` | child/page list head | initialized to `0`; JobMgr appends child records here |
| `+0x74` | child/page list tail | initialized to `0`; compared with `+0x70` to detect one-item/list-tail conditions |

## `0x50` Child/Page Record

| Offset | Working meaning | Evidence |
|---:|---|---|
| `+0x48` | active work slot A | JobMgr case `0x11` searches for the completed work pointer here; case `0x21` sets it to active |
| `+0x4a` | slot A option/duplex-ish flag | initialized to `1` by creator; JobMgr checks it before choosing status/queue behavior |
| `+0x4c` | active work slot B | JobMgr case `0x11` searches for the completed work pointer here; cleanup mirrors slot A behavior |
| `+0x50` | sub-list head | JobMgr appends list nodes here in case `9`; cleanup walks/removes it |
| `+0x54` | sub-list tail or owned allocation pointer | freed/released in JobMgr cleanup paths when state is not `2` |

The related work object is now mapped separately in `analysis/video-work-object-report.md`. It is a
`0x94`-byte video/page work object created by `0x1000f228`; its `+0x76` byte is initialized by
`0x10010398` and read by PrintMgr media selection.

## Message Case Anchors

| JobMgr case | Field behavior |
|---:|---|
| `1` | receives new `0x78` job record, sets flags, appends it to JobMgr queue/list |
| `3` | allocates a list node and appends child/page work to current job `+0x70` |
| `5` | initializes page/work counters and links active work into a child/page record |
| `0x11` | completion path; increments job `+0x6c`, forwards status, clears child slots `+0x48`/`+0x4c` |
| `0x21` | engine/page start path; sets child slot `+0x48`, marks work active, sends engine queue `0x0b` |
| `0x25` | cleanup/error/finish path; walks child/page list and clears slots |

## Practical Interpretation

For a future runtime trace, these offsets are the ones to watch first. If a print job is active,
changes around job `+0x70`/`+0x74` and child `+0x48`/`+0x4c` should correspond to page work being
queued, started, completed, or cleaned up.

The PrintMgr-to-video queue handoff is now mapped in `analysis/video-handoff-report.md`, and the
work pointer object itself is mapped in `analysis/video-work-object-report.md`.

The next useful static target is the producer side of JobMgr messages `0x29` and `9`, which appear
to populate the late hardware setup block and raster/chunk list nodes before Video Queue message
`0x0b`.
