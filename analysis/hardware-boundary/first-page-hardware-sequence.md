# HP 1020 First-Page Hardware Sequence

This is a generated offline model. It does not contact the printer.

## Purpose

The parser/object path is mapped well enough for the current foo2zjs sample. This report orders the next part: what the stock firmware appears to do when one page crosses from software objects into video and engine hardware.

- source projection case: `a4_default`
- decision: Do not attempt open printing until USB-only open code is proven and video/engine register sequencing is modeled more tightly.

## Modeled Inputs

| Object field | Value | Meaning |
|---:|---|---|
| `work +0x50` | `['raster0']` | raster/list content |
| `work +0x84` | `9600` | BIH-derived horizontal/video field |
| `work +0x88` | `6824` | BIH-derived vertical/video field |
| `work +0x8c` | `128` | BIH L0/band-height-like field |
| `work +0x90` | `92` | BIH options/control source |

- raster payload `+0x48`: `6364`
- raster payload `+0x50`: `0`
- raster payload `+0x54`: `{'byte_count': 6364, 'sha256_hint': 'not stored; payload bytes are kept in the source .zjs', 'source': 'ZJT_JBIG_BID payload', 'zjs_payload_offset': '0x224'}`

## Ordered Sequence

| Step | Stage | Function/path | Hardware registers | Meaning for open firmware | Risk |
|---:|---|---|---|---|---|
| `1` | host stream parsed | `0x10009d34 -> JobMgr queue 3` | none | Software parser state machine. Already mapped well enough for the controlled foo2zjs path. | `medium` |
| `2` | engine accepts page work | `0x10016164 hp1020_engine_message_dispatch_candidate` | `0xb050000c` clear/status wait<br>`0xb0500004` engine command submit | Mechanical gate: paper/fuser/motor state must be correct before video transfer. | `high` |
| `3` | PrintMgr sends work to video | `0x1000f574 -> queue 8 message 0x0b` | none | Scheduling bridge. Pure software, but it coordinates engine and video ownership. | `medium` |
| `4` | VideoThread stores active work | `0x10013c18 hp1020_video_thread_candidate` | none | State bookkeeping before touching video hardware. | `medium` |
| `5` | video page preparation | `0x10014910 hp1020_video_prepare_page_candidate` | `0xb1000000 / 0xb1000100` video block reset/enable<br>`0xb1000004 / 0xb1000104` video block busy/status wait | Programs video block setup/timing. This is not safe to approximate blindly. | `high` |
|  | projected video state `stride_plus_0xb8` | `analysis/hardware-boundary/video-prepare-projection.md` | `1200` | setup projection |  |
|  | projected video state `state_plus_0xbc` | `analysis/hardware-boundary/video-prepare-projection.md` | `1200` | setup projection |  |
|  | projected video state `state_plus_0xc4` | `analysis/hardware-boundary/video-prepare-projection.md` | `1` | setup projection |  |
|  | projected video state `state_plus_0xf4` | `analysis/hardware-boundary/video-prepare-projection.md` | `2` | setup projection |  |
|  | projected video state `state_plus_0xc8_state_200` | `analysis/hardware-boundary/video-prepare-projection.md` | `2` | setup projection |  |
| `6` | video transfer arm | `0x10015214 hp1020_video_render_or_dma_candidate` | `0xb2000008` video descriptor write<br>`0xb200000c` video descriptor write<br>`0xb2000024` video descriptor write<br>`0xb2000000` video transfer control write<br>`0xb2040000 / 0xb2080000` paired channel enable/reset toggles<br>`0xb204000c / 0xb208000c` paired channel status waits | First direct bridge from host-controlled BIH/work fields into video transfer registers. | `high` |
|  | projected `0xb2000008` | work +0x84 from BIH runtime block +0x04 | `9600` | consumer `0x10015214 hp1020_video_render_or_dma_candidate` |  |
|  | projected `0xb200000c` | work +0x88 from BIH runtime block +0x08 | `6824` | consumer `0x10015214 hp1020_video_render_or_dma_candidate` |  |
|  | projected `0xb2000024` | work +0x8c from BIH runtime block +0x0c | `128` | consumer `0x10015214 hp1020_video_render_or_dma_candidate` |  |
|  | projected `0xb2000000` | work +0x90 from BIH runtime block +0x13 | `control derived from work +0x90=0x5c, then OR 0x400` | consumer `0x10015214 hp1020_video_render_or_dma_candidate` |  |
| `7` | video refill / raw-band feed | `normal hypothesis: 0x10014244 -> 0x10013f34 descriptor queue/list path` | `0xb1000008 / 0xb1000108` raw-band pointer/window write<br>`0xb100000c / 0xb100010c` raw-band flags/count write<br>`0xb2080004 / 0xb2080008` channel-B refill descriptor write | Feeds compressed raster bytes to the hardware-side print path; normal/alternate mode selection matters for reproducing timing. | `high` |
|  | projected `normal_refill_state_fields` | analysis/hardware-boundary/video-refill-topology.md | `+0xd0, +0xd8, +0xdc, +0xe0, +0xf0, +0xf8, +0xfc` | consumer `0x10014244 -> 0x10013f34` |  |
|  | projected `normal_refill_unsafe_registers` | analysis/hardware-boundary/video-refill-topology.md | `0xb1000008, 0xb100000c, 0xb1000108, 0xb100010c, 0xb2080004, 0xb2080008` | consumer `0x10014244 -> 0x10013f34` |  |
| `8` | video done wakes PrintMgr | `VideoThread sends PrintMgr queue 1 message 0x10` | none | Completion coordination; needed so engine timing and status do not drift. | `high` |

## Remaining Unknowns

- Exact 0xb100 timing/setup register meanings in video_prepare_page.
- Exact 0xb204/0xb208 channel state machine and timeout/retry behavior.
- Exact 0xb050 engine command set and safe mechanical sequencing.
- Whether the hardware consumes JBIG-compressed BID bytes directly or through an undocumented assist path.

