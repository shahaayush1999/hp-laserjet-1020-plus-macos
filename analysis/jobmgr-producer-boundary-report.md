# HP 1020 JobMgr Producer Boundary

This report records the current static boundary around JobMgr message producers, especially the
unresolved messages `9` and `0x29`.

## Main Result

The current scans do not prove a normal static producer for JobMgr message `0x29`.

This matters because JobMgr case `0x29` copies a 20-byte incoming payload into runtime block
`0x10023e28`; later JobMgr copies that block into the `0x94` video/page work object fields
`+0x84`, `+0x88`, `+0x8c`, and `+0x90`.

## Proven JobMgr Producers

The normal queue-id wrapper sends to queue id `3` for these messages:

| Message | Known producer |
|---:|---|
| `1` | `0x10010338` job record creator |
| `2` | `0x1001040c` small JobMgr control helper |
| `3` | `0x10010398` child/page record creator |
| `5` | `0x10010398` child/page record creator |
| `6` | `0x100103f8` small JobMgr control helper |
| `0x0f` | `0x10010838` status/state path |
| `0x21` | `0x10013140` allocation-stall path |
| `0x25` | JobMgr self-send completion/error-looking path |

`0x1000f814` also sends to queue id `3`, but it forwards an existing payload from PrintMgr rather
than constructing a new message.

## Direct Queue-Object Sends

Some JobMgr messages bypass the queue-id wrapper and call the ThreadX-style scalar send helper with
the JobMgr queue object directly.

Current direct JobMgr scalar-send functions:

| Function | Meaning |
|---:|---|
| `0x10013d4c` | video reset dispatch path |
| `0x100144d0` | video interrupt/band-done-looking path |

Both point at message `8`, not `9` or `0x29`.

## Message `9`

Message `9` remains semantically tied to the raster/chunk list because JobMgr case `9` appends an
incoming list node to the active `0x94` work object's `+0x50` list.

The producer is not proven yet. Most `9` constants found in broad scans are PJL/data-store row
numbers, not JobMgr queue messages. They should not be treated as raster producers without queue
evidence.

## Message `0x29`

JobMgr case `0x29` is the late hardware setup block copy:

```text
memcpy(0x10023e28, incoming_payload_pointer, 0x14)
```

No static producer was found by:

- the queue-send census
- the JobMgr producer-boundary scan
- direct JobMgr queue-object send search

The likely explanation is that the producer sits behind a parser-side callback or indirect queue
path that the current wrapper scanner does not classify yet.

## Generated Evidence

Detailed generated output:

- `analysis/jobmgr-producer-boundary/jobmgr-producer-boundary.md`
- `analysis/jobmgr-producer-boundary/jobmgr-producer-hits.tsv`
- `analysis/ghidra-scripts/MapHp1020JobMgrProducerBoundary.java`

## Next Target

The next useful pass is parser-side tracing around the host raster/ZjStream path, not more PrintMgr
work:

- identify the function that parses the `JZJZ`/raster command stream
- find indirect callbacks that enqueue JobMgr payloads
- search for construction of the 20-byte block eventually copied into `0x10023e28`
- search for list-node creation that reaches JobMgr case `9`
