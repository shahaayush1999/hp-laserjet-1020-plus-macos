# ZjStream Inspection: analysis/samples/generated/minimal-page-a4.zjs

- file bytes: `6987`
- magic offset: `0x10c`
- prefix bytes before magic: `268`
- magic: `JZJZ`

## Chunks

| # | Offset | Type | Name | Size | Items | Reserved | Signature | Notes |
|---:|---:|---:|---|---:|---:|---:|---:|---|
| `0` | `0x110` | `0x00` | `ZJT_START_DOC` | `52` | `3` | `0x0024` | `0x5a5a` |  |
| `1` | `0x144` | `0x02` | `ZJT_START_PAGE` | `172` | `13` | `0x009c` | `0x5a5a` |  |
| `2` | `0x1f0` | `0x04` | `ZJT_JBIG_BIH` | `36` | `0` | `0x0000` | `0x5a5a` | BIH XD=9600 YD=6824 |
| `3` | `0x214` | `0x05` | `ZJT_JBIG_BID` | `6380` | `0` | `0x0000` | `0x5a5a` | BID bytes=6364 |
| `4` | `0x1b00` | `0x06` | `ZJT_END_JBIG` | `16` | `0` | `0x0000` | `0x5a5a` |  |
| `5` | `0x1b10` | `0x03` | `ZJT_END_PAGE` | `16` | `0` | `0x0000` | `0x5a5a` |  |
| `6` | `0x1b20` | `0x01` | `ZJT_END_DOC` | `16` | `0` | `0x0000` | `0x5a5a` |  |

## Summary

- parsed chunks: `7`
- trailing bytes after parsed stream: `27`
- JBIG_BID chunks: `1`
- total JBIG_BID payload bytes: `6364`

## Decoded Details

### Chunk 0 `ZJT_START_DOC` Items

| Offset | Item | Type | Value |
|---:|---|---|---|
| `0x0` | `ZJI_DMCOLLATE` (`0x0001`) | `UINT32` | `0` |
| `0xc` | `ZJI_DMDUPLEX` (`0x0002`) | `UINT32` | `1` |
| `0x18` | `ZJI_PAGECOUNT` (`0x0000`) | `UINT32` | `0` |

### Chunk 1 `ZJT_START_PAGE` Items

| Offset | Item | Type | Value |
|---:|---|---|---|
| `0x0` | `ZJI_ECONOMODE` (`0x0017`) | `UINT32` | `0` |
| `0xc` | `ZJI_VIDEO_X` (`0x0011`) | `UINT32` | `4768` |
| `0x18` | `ZJI_VIDEO_Y` (`0x0012`) | `UINT32` | `6824` |
| `0x24` | `ZJI_VIDEO_BPP` (`0x0010`) | `UINT32` | `2` |
| `0x30` | `ZJI_RASTER_X` (`0x000c`) | `UINT32` | `9536` |
| `0x3c` | `ZJI_RASTER_Y` (`0x000d`) | `UINT32` | `6824` |
| `0x48` | `ZJI_NBIE` (`0x0007`) | `UINT32` | `1` |
| `0x54` | `ZJI_RESOLUTION_X` (`0x0008`) | `UINT32` | `600` |
| `0x60` | `ZJI_RESOLUTION_Y` (`0x0009`) | `UINT32` | `600` |
| `0x6c` | `ZJI_DMDEFAULTSOURCE` (`0x0005`) | `UINT32` | `7` |
| `0x78` | `ZJI_DMCOPIES` (`0x0004`) | `UINT32` | `1` |
| `0x84` | `ZJI_DMPAPER` (`0x0003`) | `UINT32` | `9` |
| `0x90` | `ZJI_DMMEDIATYPE` (`0x0006`) | `UINT32` | `1` |

### Chunk 2 JBIG BIH

- raw: `00 00 01 00 00 00 25 80 00 00 1a a8 00 00 00 80 10 00 03 5c`
- dl/d/p/unknown3: `0` / `0` / `1` / `0`
- XD/YD: `9600` x `6824`
- L0: `128`
- MX/MY: `16` / `0`
- Order: `0x03`
- Options: `0x5c`
- stripes/layers/planes: `54` / `0` / `1`

