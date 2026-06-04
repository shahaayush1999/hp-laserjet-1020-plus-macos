# HP 1020 Parser To JobMgr Raster Message Flow

This checkpoint connects the host ZjStream parser to the JobMgr raster/page path.

## High-Level Result

The firmware's print stream path is now mapped far enough to explain where the important page/raster
objects come from:

```text
USB bulk receive
  -> ZjStream parser at 0x10009d34
  -> JobMgr queue id 3 messages
  -> active 0x94 video/page work object
  -> work +0x50 raster/chunk list
  -> VideoThread / raw-band hardware feed
```

## Parser Boundary

`0x10009d34` is the ZjStream parser entry. It is wired from the USB2Thread descriptor:

- descriptor `0x10005fc4`
- USB task body `0x10008ff0`
- parser entry `0x10009d34`
- magic string `0x1001bc78` = `JZJZ`
- chunk switch table `0x100036f0`

The parser:

- reads and verifies `JZJZ`
- reads 16-byte ZjStream chunk headers
- checks the `ZZ` signature at header offset `+0x0e`
- dispatches chunk types `0..12` through the table at `0x100036f0`

## Key ZjStream Cases

| ZjStream chunk | Parser target | JobMgr message | Meaning |
|---|---:|---:|---|
| `ZJT_START_DOC` | `0x10009efe` | `1` | creates/parses document object |
| `ZJT_END_DOC` | `0x1000a1b3` | `2` | document end |
| `ZJT_START_PAGE` | `0x10009f86` | `3`, `5` | creates child/page and `0x94` video work objects |
| `ZJT_END_PAGE` | `0x1000a19e` | `6` | page end / page ready marker |
| `ZJT_JBIG_BIH` | `0x1000a006` | `0x29` | sends the 20-byte JBIG BIH payload |
| `ZJT_JBIG_BID` | `0x1000a014` | `0x2a` | wraps compressed raster payload in a list node |
| `ZJT_END_JBIG` | `0x1000a053` | `0x2b` | marks JBIG stream end |
| `ZJT_END_PLANE` | `0x1000a173` | `8` | plane/event marker |

## Resolved Mystery: JobMgr `0x29`

Earlier reports had JobMgr `0x29` as unresolved. The parser pass resolves it.

`ZJT_JBIG_BIH` at `0x1000a006` does:

```text
message[0] = 0x29
message[3] = chunk_payload_pointer
send queue id 3
```

JobMgr case `0x29` then copies that incoming 20-byte payload into runtime block `0x10023e28`.
Those bytes later populate the active work object fields:

| Runtime source | Work object destination |
|---:|---:|
| `0x10023e28 + 0x04` | `work +0x84` |
| `0x10023e28 + 0x08` | `work +0x88` |
| `0x10023e28 + 0x0c` | `work +0x8c` |
| `0x10023e28 + 0x13` | `work +0x90` |

In plain English: the first JBIG image header chunk from the host print file seeds the video
hardware setup fields.

## Raster Data: JobMgr `0x2a`

`ZJT_JBIG_BID` at `0x1000a014` allocates a `0x78`-byte wrapper/list node:

- node `+0x0c` points at an embedded payload object at node `+0x10`
- payload `+0x54` points at the compressed raster chunk bytes
- payload `+0x48` stores the chunk length
- payload `+0x50` is initialized to zero
- payload `+0x4c` gets a copied halfword from payload offset `+0x2c`

It then sends JobMgr message `0x2a`.

JobMgr case `0x2a`:

- copies the already-saved BIH/video hardware fields from `0x10023e28` into the active work object
- falls through into the same append path used by JobMgr case `9`
- appends the raster/list node to the active work object's `+0x50` list

So the core data path is:

```text
BIH chunk -> JobMgr 0x29 -> 0x10023e28 -> work +0x84/+0x88/+0x8c/+0x90
BID chunk -> JobMgr 0x2a -> list node -> work +0x50
```

## Why This Matters

This closes the most important static gap between input parsing and video output:

- we know which firmware function parses the host print stream
- we know which ZjStream chunks create document/page/work objects
- we know where the 20-byte hardware setup block comes from
- we know how compressed raster chunks enter the work object's raster list

The next useful target is the video-side consumer of `work +0x50`: label the list node payload fields
as they are read by `0x10014910`, `0x10015214`, and `0x100140f8`.
