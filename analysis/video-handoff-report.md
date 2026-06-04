# HP 1020 Video Handoff

This report connects PrintMgr work scheduling to the video/raster thread.

## Main Result

The PrintMgr-to-video handoff is:

```text
PrintMgr scheduler 0x1000f574
  -> hp1020_queue_send_message4_candidate(8, 0x0b, 0, 0, work_ptr)
  -> Video Queue message 0x0b
  -> Video thread stores work_ptr in video state
  -> video prepare/render functions consume work_ptr
  -> Video thread sends engine queue message 0x10 when done
```

The small queue wrapper at `0x10010218` builds payload words like this:

| Payload word | Source |
|---:|---|
| word 0 | message id |
| word 1 | wrapper argument 3 |
| word 2 | wrapper argument 4 |
| word 3 | wrapper argument 5 |

So `hp1020_queue_send_message4_candidate(8, 0x0b, 0, 0, uVar10)` means:

```text
queue id 8 / Video Queue
message 0x0b
payload word 3 = uVar10 work pointer
```

## Producers

| Producer | Send | Meaning |
|---:|---|---|
| `0x1000f574` PrintMgr scheduler | `queue 8, message 0x0b, word3 = work_ptr` | normal video work start |
| `0x10013d4c` video reset dispatch | `queue 8, message 0x0b` | requeue deferred video work after reset |

## Video State Object

The video state pointer word is `0x10006770 -> 0x1002efc0`.

Important state offsets currently visible:

| Offset | Working meaning | Evidence |
|---:|---|---|
| `+0x60` | primary/current video work pointer | `VideoThread` stores payload word 3 here on first `0x0b` |
| `+0x64` | secondary/deferred video work pointer | `VideoThread` stores payload word 3 here if primary slot is busy |
| `+0x68` | event/status scratch | reset dispatch and prepare path clear/read it |
| `+0x6c` | video render state | prepare sets `1`, render sets `2`, reset clears it |
| `+0x98`/`+0x94` | ring/buffer index pair | render advances `+0x98` modulo 4 and compares with `+0x94` |
| `+0xa0` | list of pending rendered chunks or DMA descriptors | reset dispatch walks this list and decrements child work counters |
| `+0xb8`/`+0xbc` | raster stride/size values | prepare computes these from work pointer fields |
| `+0xc8` | plane/count-like value | prepare copies from work pointer `+0x22` |
| `+0xfc` | high-bit status/control word | reset and prepare inspect/update high bit |

## Work Pointer Fields Used By Video

The video work pointer passed in payload word 3 is read by video prepare/render code at these
offsets:

| Work offset | Current meaning |
|---:|---|
| `+0x14` | resolution value; compared with `300`, `600`, and `0x4b0` |
| `+0x22` | plane/count-like halfword copied into video state `+0xc8` |
| `+0x26` | dimension/line count copied into video state `+0xd0`/`+0xd4` |
| `+0x30` | copied into video state `+0xe8` |
| `+0x32` | copied into video state `+0xec` |
| `+0x36` | mode flag used with data-store entry `0x20` to decide state `+0xc0` |
| `+0x50` | list head used by render; node payload provides buffer pointers |
| `+0x74` | flag that toggles high-bit video state at `+0xfc` |
| `+0x84` | width/byte-count source; rounded and shifted to compute raster stride |
| `+0x88`/`+0x8c` | hardware/DMA register payloads |
| `+0x90` | bit flags for video hardware setup |

This work pointer is now mapped in `analysis/video-work-object-report.md` as a `0x94`-byte
video/page work object. It is created by `0x1000f228`, populated by `0x100104c8`, stored in the
child/page container, and later passed through Engine/PrintMgr into VideoThread.

## Why This Matters

This is the first clear bridge from high-level print scheduling into raster/video hardware setup.
For reverse engineering the actual page path, `queue 8, message 0x0b` is now more important than
the earlier `0x2d` notification path.

## Next Target

The next static pass should map the producer side of JobMgr messages `0x29` and `9`, because those
appear to carry the late hardware setup block and raster/chunk list nodes used by the video work
object.
