# HP 1020 Job Object Flow

This pass connects the JobMgr queue, PrintMgr queue, and shared linked-list helpers.

## Main Result

The normal print path is now best understood as a small work-object pipeline:

```text
host/PJL/job setup
  -> JobMgr creates job/work records
  -> JobMgr sends engine/page work
  -> PrintMgr moves a pending list node to an active list
  -> Video/engine process the page
  -> PrintMgr message 0x11 returns active work to JobMgr queue 3
```

This is still a static map, but it is no longer just loose function names.

## Shared List Helpers

| Function | Meaning |
|---:|---|
| `0x10013000` | append node to list tail |
| `0x10013050` | pop node from list head |
| `0x100130bc` | peek list head |
| `0x10013140` | allocate memory with retry; sends JobMgr `0x21` if allocation stalls |

The list object appears to be two words: head pointer and tail pointer. List nodes use word `+0x00`
as the next pointer.

## PrintMgr Lists

| Pointer word | Points to | Working name | Evidence |
|---:|---:|---|---|
| `0x10006324` | `0x1002874c` | PrintMgr pending/work-ready list | scheduler peeks/pops this list before sending video or self messages |
| `0x10006328` | `0x10024684` | PrintMgr active/in-flight list | scheduler pushes here before queue-0 `0x0b`; `0x11` helper pops here |
| `0x1000633c` | `0x1001bf08` | current media/page descriptor candidate | media selection reads fields at `+0x08`, `+0x0c`, and `+0x10` |

## JobMgr Creation Points

`0x10010338` allocates a `0x78`-byte job/work record, initializes fields, and sends message `1`
to JobMgr queue `3`.

Important fields currently visible:

| Offset | Evidence |
|---:|---|
| `+0x48` | copied from setup argument `param_1[2]`; later used in status/job progress |
| `+0x58` | copied from setup argument `param_1[0]`; later status payload |
| `+0x5c` | copied from setup argument `param_1[1]`; job/status mode |
| `+0x60` | copied from setup argument `param_1[3]`; controls downstream queue forwarding |
| `+0x64` | copied from setup argument `param_1[4]`; queue id used by JobMgr dynamic sends |
| `+0x6c` | per-job/page completion counter |
| `+0x70`/`+0x74` | list heads or page chains used by JobMgr |

`0x10010398` allocates a `0x50`-byte child/page-ish record, sends JobMgr message `3`, links it
into the current job via `0x100104c8`, then sends JobMgr message `5`.

## PrintMgr State Movement

The strongest PrintMgr scheduler path is in `0x1000f574`:

- peeks active list `0x10006328`
- peeks pending list `0x10006324`
- when a pending node reaches state `4`, it pops from `0x10006324`
- pushes that node into active list `0x10006328`
- marks the node state as `5`
- sends `queue 0, message 0x0b`

That makes queue-0 `0x0b` a real page/work advance message.

## Completion Back To JobMgr

PrintMgr message `0x11` calls `0x1000f814`.

`0x1000f814`:

- increments PrintMgr active counter byte when needed
- pops one node from active list `0x10006328`
- clears fields at node `+0x00` and `+0x0c`
- frees or releases an associated object through `0x10013408`
- sends the original message payload onward to queue `3` / JobMgr

That makes queue-0 `0x11` the clearest currently proven PrintMgr-to-JobMgr completion or continuation handoff.

## Practical Next Target

The next useful static step is to name the fields in the `0x78`-byte job record and the `0x50`-byte
child/page record by following offsets `+0x48`, `+0x4c`, `+0x50`, `+0x54`, `+0x58`, `+0x5c`,
`+0x60`, `+0x64`, `+0x70`, and `+0x74` through JobMgr cases `0x11`, `0x21`, and `0x25`.
