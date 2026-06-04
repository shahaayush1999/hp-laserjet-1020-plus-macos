# HP 1020 Video Work Object

This report maps the object that moves from JobMgr/Engine/PrintMgr into VideoThread.

## Main Result

The video work item is a `0x94`-byte object created by `0x1000f228`
`hp1020_video_work_create_candidate`.

The high-level path is now:

```text
0x10010398 creates:
  - a 0x50 child/page container
  - a 0x94 video/page work object

JobMgr stores the 0x94 object in child/page slot +0x48
JobMgr sends queue 1 / engMsgQ message 0x0b with payload word 3 = work_ptr
Engine stores work_ptr in engine state +0x68
PrintMgr later sends queue 8 / Video Queue message 0x0b with payload word 3 = same work_ptr
VideoThread stores work_ptr in video state +0x60/+0x64
Video prepare/render consumes the object and its raster list at +0x50
```

This ties the earlier job/page records to the actual object consumed by video hardware setup.

## Creator

`0x1000f228` allocates `0x94` bytes, initializes embedded lists, clears late hardware fields,
then calls the common work initializer.

| Work offset | Initialization |
|---:|---|
| `+0x50` | embedded raster/chunk list init |
| `+0x58` | embedded list init |
| `+0x60` | embedded list init |
| `+0x68` | embedded list init |
| `+0x70` | cleared halfword |
| `+0x74` | cleared flag byte |
| `+0x77` | cleared flag byte |
| `+0x84` | cleared word |
| `+0x88` | cleared word |
| `+0x8c` | cleared word |
| `+0x90` | cleared byte |

The common initializer `0x1000f204` clears the early object body and sets:

| Work offset | Value |
|---:|---:|
| `+0x0a` | `0` |
| `+0x0c` | `1` |
| `+0x0e` | `3` |
| `+0x10` | `0` |

## Page Parameter Copier

`0x100104c8` copies selected page parameters into the work object.

| Source offset | Work offset | Notes |
|---:|---:|---|
| `+0x00` | `+0x00` | first word copied directly |
| `+0x06` | `+0x10` | media/page parameter |
| `+0x0a` | `+0x0a` | media/page parameter |
| `+0x0e` | `+0x0e` | media/page parameter |
| `+0x12` | `+0x22` | plane/count-like value consumed by video prepare |
| `+0x16` | `+0x1e` | page dimension/config field |
| `+0x1a` | `+0x14` | resolution field consumed by video prepare |
| `+0x1e` | `+0x16` | page dimension/config field |
| `+0x22` | `+0x0c` | count/state field |

This function is called by both the top-level `0x78` job creator and the child/page creator.
For the normal page path, `0x10010398` creates the `0x94` object and populates it from the
incoming page parameter block.

## JobMgr Fields On The `0x94` Work Object

JobMgr adds runtime state after creation:

| Work offset | Working meaning | Evidence |
|---:|---|---|
| `+0x48` | submitted/rendered count | JobMgr increments when queueing engine `0x0b`; completion decrements/compares it |
| `+0x4a` | slot/duplex-ish option flag | initialized to `1`; finalize path checks it before releasing raster list |
| `+0x4c` | completed count | JobMgr increments on completion and compares against `+0x0c` |
| `+0x4e` | raster/list reference count | copied from child/page state; `+0x50` list cleanup decrements it |
| `+0x50` | raster/chunk list head | JobMgr appends incoming raster nodes; video render reads first node payload |
| `+0x72` | active/in-engine flag | set before engine `0x0b`; cleared on completion paths |
| `+0x75` | option copied from data-store entry `0x24` | affects completion/list handling |
| `+0x76` | media-selection flag | read by PrintMgr media select |
| `+0x78` | ready-for-start flag | JobMgr checks before sending repeated engine `0x0b` |
| `+0x7a` | page sequence number | JobMgr assigns from a counter |
| `+0x7c/+0x7e/+0x80` | selected media/output fields | PrintMgr media select writes these; engine reads `+0x80` |

## Late Hardware Fields

The video hardware setup fields are filled later, not at object creation.

JobMgr case `0x29` does:

```text
memcpy(0x10023e28, incoming_payload_pointer, 0x14)
```

Later, JobMgr copies that runtime block into the active `0x94` work object:

| Runtime block | Work offset | Video use |
|---:|---:|---|
| `0x10023e28 + 0x04` | `+0x84` | width/byte-count source; video prepare rounds it and computes stride |
| `0x10023e28 + 0x08` | `+0x88` | written to video/MMIO register path |
| `0x10023e28 + 0x0c` | `+0x8c` | written to video/MMIO register path |
| `0x10023e28 + 0x13` | `+0x90` | bit flags used by video hardware setup |

The queue-send census and `analysis/jobmgr-producer-boundary-report.md` do not currently prove who
emits JobMgr message `0x29`. That is now a parser-side boundary, not a PrintMgr boundary.

## Raster List At `+0x50`

JobMgr case `9` appends incoming list nodes to work `+0x50`. Video render then reads:

```text
work +0x50 -> first list node
first node +0x0c -> raster/chunk payload
payload +0x48 -> buffer/address-like value
payload +0x54 -> size/count-like value
```

Helpers around this list:

| Function | Working meaning |
|---:|---|
| `0x1000f0a8` | walks `+0x50`, decrements/refcounts, pops nodes, releases payload buffers |
| `0x1000f128` | marks one page/chunk done and updates list counts |
| `0x1000f030` | finalizes or releases raster list depending on active flags |
| `0x1000efbc` | force-releases the raster list and the work object |

## Practical Meaning

The normal print path is now narrowed to a concrete object:

- create/populate `0x94` work object
- attach raster/chunk nodes under `+0x50`
- copy late hardware fields from runtime block `0x10023e28`
- send engine `0x0b`
- send video `0x0b`
- video consumes dimensions, raster list, and MMIO payload fields

The next useful static target is the host raster/ZjStream parser side, because JobMgr messages
`0x29` and `9` appear to carry the rendered raster chunks and the late hardware setup block but are
not produced by the normal queue-id wrapper paths.
