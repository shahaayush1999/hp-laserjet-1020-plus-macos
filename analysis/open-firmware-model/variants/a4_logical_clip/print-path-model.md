# HP 1020 Offline Print-Path Model

This is an executable offline model of the normal HP LaserJet 1020/1020 Plus print path mapped from the firmware.
It parses host-side ZjStream bytes and builds firmware-shaped document, page, work, and raster-list objects.

It does not send data to the printer and it stops before any hardware register writes.

## Input

- source: `analysis/samples/generated/matrix-a4_logical_clip.zjs`
- file bytes: `7011`
- ZjStream magic offset: `0x10c`
- parser entry modeled: `0x10009d34`
- JobMgr queue id: `3`
- trailing bytes after parsed stream: `27`

## Object Graph

- document objects: `1`
- page objects: `1`
- `0x94` video work objects: `1`
- raster/list nodes under work `+0x50`: `1`

### Document Items

| Item | Value |
|---|---:|
| `ZJI_DMCOLLATE` | `0` |
| `ZJI_DMDUPLEX` | `1` |
| `ZJI_PAGECOUNT` | `0` |

### Page Items

| Item | Value |
|---|---:|
| `ZJI_ECONOMODE` | `0` |
| `ZJI_VIDEO_X` | `4768` |
| `ZJI_VIDEO_Y` | `6824` |
| `ZJI_VIDEO_BPP` | `2` |
| `ZJI_RASTER_X` | `9536` |
| `ZJI_RASTER_Y` | `6824` |
| `ZJI_OFFSET_X` | `192` |
| `ZJI_OFFSET_Y` | `96` |
| `ZJI_NBIE` | `1` |
| `ZJI_RESOLUTION_X` | `600` |
| `ZJI_RESOLUTION_Y` | `600` |
| `ZJI_DMDEFAULTSOURCE` | `7` |
| `ZJI_DMCOPIES` | `1` |
| `ZJI_DMPAPER` | `9` |
| `ZJI_DMMEDIATYPE` | `1` |

### BIH Runtime Block

Firmware case `ZJT_JBIG_BIH -> JobMgr 0x29` copies the 20-byte BIH into runtime block `0x10023e28`.

| Runtime field | Modeled value | Later work field |
|---:|---:|---:|
| `+0x04` | `9600` | `work +0x84` |
| `+0x08` | `6824` | `work +0x88` |
| `+0x0c` | `128` | `work +0x8c` |
| `+0x13` | `0x5c` | `work +0x90` |

- decoded BIH: `XD=9600`, `YD=6824`, `L0=128`, `MX=16`, `MY=0`, `options=0x5c`
- raw BIH: `00 00 01 00 00 00 25 80 00 00 1a a8 00 00 00 80 10 00 03 5c`

### Video Work Object

- object id: `work0`
- size: `0x94`
- owner page: `page0`

| Work offset | Modeled value | Meaning |
|---:|---|---|
| `+0x0c` | `1` | copy/reference count candidate |
| `+0x22` | `1` | plane/count-like page field |
| `+0x50` | `raster0` | raster list head/list content |
| `+0x84` | `9600` | BIH-derived video setup field |
| `+0x88` | `6824` | BIH-derived video setup field |
| `+0x8c` | `128` | BIH-derived video setup field |
| `+0x90` | `0x5c` | BIH options/mode byte |

### Raster Nodes

| Node | Compressed bytes | Source offset | Owner work |
|---|---:|---:|---|
| `raster0` | `6364` | `0x23c` | `work0` |

Each modeled raster node uses the firmware shape identified from parser and video consumers:

- node `+0x00`: next pointer
- node `+0x0c`: payload pointer
- payload `+0x48`: compressed raster byte count
- payload `+0x4e`: retain/release counter
- payload `+0x50`: source/retention mode
- payload `+0x54`: compressed raster buffer pointer

## Message Trace

| Chunk | Type | Parser target | JobMgr messages | Object/model effects |
|---:|---|---:|---|---|
| `0` | `ZJT_START_DOC` | `0x10009efe` | q3:`1` | created document object doc0 from 3 ZjStream items |
| `1` | `ZJT_START_PAGE` | `0x10009f86` | q3:`3`, q3:`5` | created page object page0 and work object work0 |
| `2` | `ZJT_JBIG_BIH` | `0x1000a006` | q3:`0x29` | copied 20-byte BIH into runtime block 0x10023e28<br>seeded late video fields on work0 at +0x84/+0x88/+0x8c/+0x90 |
| `3` | `ZJT_JBIG_BID` | `0x1000a014` | q3:`0x2a` | created raster list node raster0 for 6364 compressed bytes<br>appended raster0 to work0 field +0x50 |
| `4` | `ZJT_END_JBIG` | `0x1000a053` | q3:`0x2b` | closed current JBIG stream |
| `5` | `ZJT_END_PAGE` | `0x1000a19e` | q3:`6` | marked active page complete |
| `6` | `ZJT_END_DOC` | `0x1000a1b3` | q3:`2` | closed active document |

## Safe Stop Boundary

- boundary: VideoThread consumes work +0x50 and writes video/engine MMIO registers
- model status: offline model stops before MMIO
- why stop here: From this point the original firmware touches motor/fuser/video hardware registers.

Next firmware functions after this boundary:

- `0x10015214 hp1020_video_render_or_dma_candidate`
- `0x100140f8 hp1020_video_refresh_raw_bands_candidate`
- `0x10015c68 hp1020_engine_status_io_candidate`

## What This Proves

- The normal host print stream has been reduced to a concrete, replayable object/message model.
- The model reaches the exact point where the original firmware would hand raster data to video/engine code.
- The remaining replacement-firmware risk is no longer finding the print input path; it is safely reproducing the video/engine hardware side.

