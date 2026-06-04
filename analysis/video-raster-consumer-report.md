# HP 1020 Video Raster Consumer Flow

This checkpoint maps how the video side consumes the raster list populated by the ZjStream parser and
JobMgr.

## Main Result

The compressed raster data path now has a continuous static chain:

```text
ZJT_JBIG_BID chunk
  -> parser message 0x2a
  -> JobMgr appends raster/list node to work +0x50
  -> Video render stores work +0x50 in video state +0x9c
  -> raw-band refresh walks video state +0x9c
  -> video hardware registers receive raster buffer pointer/size/flags
```

## List Shape

The active video/page work object is the `0x94`-byte object created by `0x1000f228`.

Its raster list lives at:

```text
work +0x50
```

Each list node has the usual firmware list shape:

| Node offset | Meaning |
|---:|---|
| `+0x00` | next node pointer |
| `+0x0c` | payload pointer |

For parser-produced JBIG data, the payload is embedded at `node +0x10`.

## Payload Fields

Current high-confidence payload fields:

| Payload offset | Meaning | Evidence |
|---:|---|---|
| `+0x48` | raster byte count / transfer length candidate | parser stores chunk length; `0x10015214` passes it to hardware/transfer path |
| `+0x4c` | nonzero marker/ref flag candidate | copied from payload `+0x2c`; raw-band path turns nonzero into a hardware flag bit |
| `+0x4e` | retain/release counter | JobMgr sets from active work `+0x0c`; list cleanup decrements/tests it |
| `+0x50` | source/retention mode candidate | initialized to zero; cleanup frees `+0x54` unless this equals `2` |
| `+0x54` | raster byte buffer pointer | parser stores chunk payload pointer; video render/raw-band code writes it to hardware path |

Lower-confidence but useful field:

| Payload offset | Meaning | Evidence |
|---:|---|---|
| `+0x20` | band height / unit count candidate | raw-band refresh feeds it into `FUN_1001b668(..., video_state +0xc4)` before writing a hardware word |

## Video Consumers

### `0x10015214` `hp1020_video_render_or_dma_candidate`

This is the first direct consumer of the work object's raster list:

```text
list_head = work +0x50
video_state +0x9c = list_head
payload = list_head->payload
raster_ptr = payload +0x54
raster_len = payload +0x48
```

It also programs video hardware fields from the work object:

| Work offset | Use |
|---:|---|
| `+0x84` | written to video hardware width/stride-looking register |
| `+0x88` | written to video hardware register |
| `+0x8c` | written to video hardware register |
| `+0x90` | bit flags that select hardware mode bits |

Those fields came from `ZJT_JBIG_BIH -> JobMgr 0x29 -> 0x10023e28`.

### `0x100140f8` `hp1020_video_refresh_raw_bands_candidate`

This function walks the active raster list in `video_state +0x9c`.

For each node:

```text
payload = node +0x0c
raster_ptr = payload +0x54
mode_or_source = payload +0x50
band_units = payload +0x20
marker_flag = payload +0x4c
```

It writes the raster pointer and derived flags/counts into MMIO-looking registers around
`DAT_100067cc`, `DAT_100067d0`, `DAT_100067d4`, `DAT_100067d8`, and `DAT_100067dc`.

## Cleanup / Lifetime

`0x1000f0a8` walks the same `work +0x50` list for cleanup/marking:

- mode `1`: release all nodes
- mode `2`: decrement payload `+0x4e`
- mode `3`: force payload `+0x4e = 1`

When a node is released, it frees `payload +0x54` unless payload `+0x50 == 2`, then frees the node
itself.

## Interpretation

We now have enough static understanding to say the normal HP 1020 print path is:

```text
host foo2zjs output
  -> firmware ZjStream parser
  -> JobMgr page/work/raster messages
  -> work +0x50 raster list
  -> VideoThread DMA/raw-band setup
```

The next useful reverse-engineering target is not “find the print path” anymore. It is field
semantics: correlate the JBIG BIH bytes and ZjStream item fields to the exact meanings of work
`+0x84/+0x88/+0x8c/+0x90` and payload `+0x20/+0x48/+0x4c/+0x50/+0x54`.
