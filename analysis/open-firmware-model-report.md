# HP 1020 Open Firmware Model Checkpoint

This checkpoint adds an executable offline model for the already-mapped normal print path.

## What Changed

New script:

- `scripts/model-hp1020-print-path.py`

Generated model outputs:

- `analysis/open-firmware-model/print-path-model.md`
- `analysis/open-firmware-model/print-path-model.json`

The script parses a host-side HP 1020 ZjStream file and builds firmware-shaped objects/messages:

```text
JZJZ ZjStream input
  -> parser entry 0x10009d34
  -> JobMgr queue 3 messages
  -> document/page objects
  -> 0x94 video work object
  -> work +0x50 raster/list nodes
  -> stop before VideoThread/Engine MMIO
```

## Controlled Sample Result

Input:

- `analysis/samples/generated/minimal-page-a4.zjs`
- file bytes: `6987`
- `JZJZ` offset: `0x10c`

Modeled object graph:

| Object kind | Count | Notes |
|---|---:|---|
| document object | `1` | from `ZJT_START_DOC` |
| page object | `1` | from `ZJT_START_PAGE` |
| `0x94` video work object | `1` | firmware-shaped work item consumed by video path |
| raster/list node | `1` | from `ZJT_JBIG_BID`, attached to work `+0x50` |

Modeled message trace:

| ZjStream chunk | Parser target | JobMgr message |
|---|---:|---:|
| `ZJT_START_DOC` | `0x10009efe` | `1` |
| `ZJT_START_PAGE` | `0x10009f86` | `3`, `5` |
| `ZJT_JBIG_BIH` | `0x1000a006` | `0x29` |
| `ZJT_JBIG_BID` | `0x1000a014` | `0x2a` |
| `ZJT_END_JBIG` | `0x1000a053` | `0x2b` |
| `ZJT_END_PAGE` | `0x1000a19e` | `6` |
| `ZJT_END_DOC` | `0x1000a1b3` | `2` |

## Important Field Correlation

The model reproduces the BIH-to-work-object handoff:

```text
ZJT_JBIG_BIH payload
  -> runtime block 0x10023e28
  -> work +0x84/+0x88/+0x8c/+0x90
```

For the controlled A4 sample:

| Runtime field | Value | Work field |
|---:|---:|---:|
| `0x10023e28 + 0x04` | `9600` | `work +0x84` |
| `0x10023e28 + 0x08` | `6824` | `work +0x88` |
| `0x10023e28 + 0x0c` | `128` | `work +0x8c` |
| `0x10023e28 + 0x13` | `0x5c` | `work +0x90` |

It also reproduces the raster node shape:

```text
ZJT_JBIG_BID payload, 6364 bytes
  -> parser-created 0x78 node
  -> payload +0x48 byte count
  -> payload +0x54 compressed raster pointer
  -> active work +0x50 list
```

## Safe Boundary

This model deliberately stops at the point where the original firmware would enter:

- `0x10015214` `hp1020_video_render_or_dma_candidate`
- `0x100140f8` `hp1020_video_refresh_raw_bands_candidate`
- `0x10015c68` `hp1020_engine_status_io_candidate`

That is the hardware-sensitive boundary. Beyond that point the firmware writes video/engine MMIO
registers that can drive paper motion, laser/scanner timing, and fuser-related state.

## Practical Meaning

The input side of the printing path is no longer just notes from Ghidra. It is now a replayable
host-side model that can be run against any generated HP 1020 ZjStream file.

The remaining open-firmware work is concentrated on the hardware side:

1. label the video/engine register writes enough to name the safe and unsafe paths
2. identify a non-printing custom firmware boot/USB probe path that avoids those registers
3. only then consider any printer-connected custom firmware upload
