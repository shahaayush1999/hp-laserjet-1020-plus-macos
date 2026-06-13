# HP 1020 Hardware Boundary Safety Map

This is an offline map of the boundary where reverse engineering stops being just bytes/objects and starts touching physical printer hardware.

No printer is contacted by this model.

## Register Families

| Family | Working name | Risk | Why |
|---|---|---|---|
| `0xb300....` | USB controller | `lower` | Needed for a non-printing boot/USB identity probe. It should not move paper or heat the fuser by itself. |
| `0xb100....` | video/raster block control and raw-band feed | `high` | Controls paired video/raster blocks, raw-band pointers, flags, reset/enable bits, and busy waits. |
| `0xb200....` | video transfer descriptor/control block | `high` | Receives page/raster geometry from the work object and starts/advances transfer. |
| `0xb204....` | video transfer channel A | `high` | Control/status channel toggled by video render before and during raster transfer. |
| `0xb208....` | video transfer channel B | `high` | Second video transfer channel toggled with the same enable/status pattern as channel A. |
| `0xb050....` | engine command/status handshake | `high` | Submits engine commands and polls mechanical/status responses through ready/submit bits. |
| `0xb020....` | engine/control hardware table family | `high` | Appears in engine/control descriptor regions. Exact semantics are weaker than 0xb050, but it sits in the same unsafe hardware area. |
| `0xb080.... / 0xb070.... / 0xb030....` | early boot/timer/diagnostic hardware | `medium` | Not on the normal print-raster path, but still MMIO. A boot probe should not write unknown hardware unless the original init sequence is understood. |

## Critical Functions

| Function | Layer | Risk | Why it matters |
|---|---|---|---|
| `0x10009d34 hp1020_zjs_parser_entry_candidate` | input parser | `offline-safe when modeled only` | Parses JZJZ chunks and sends JobMgr messages. Safe in our host model because it does not run on the printer. |
| `0x10015214 hp1020_video_render_or_dma_candidate` | video transfer | `do-not-call in early custom firmware` | Uses work +0x84/+0x88/+0x8c/+0x90, arms 0xb204/0xb208 channels, writes 0xb200 descriptors, and starts transfer. |
| `0x100140f8 hp1020_video_refresh_raw_bands_candidate` | raw-band feed | `do-not-call in early custom firmware` | Walks video_state +0x9c raster nodes and writes payload pointers/flags to 0xb100 raw-band registers. |
| `0x10014910 hp1020_video_prepare_page_candidate` | video preparation | `do-not-call in early custom firmware` | Programs many 0xb100 control, timing, and setup registers before render. |
| `0x10015458 hp1020_video_reset_or_flush_candidate` | video reset/flush | `do-not-call until semantics are clearer` | Clears/sets 0x100 enable/reset bits and waits on 0x200 busy bits in 0xb100 pairs. |
| `0x10015c68 hp1020_engine_status_io_candidate` | engine command/status | `do-not-call in early custom firmware` | Writes 16-bit engine commands into 0xb0500004 and uses 0x00010000 submit/ready handshake. |
| `0x10015df8 hp1020_engine_status_poll_candidate` | engine status poll | `do-not-call in early custom firmware` | Chains multiple engine command/status reads and can trigger video reset dispatch. |
| `0x100160a8 hp1020_engine_preflight_candidate` | engine preflight | `do-not-call in early custom firmware` | Sets an engine command-register bit and waits for hardware state before publishing status. |
| `0x10016164 hp1020_engine_message_dispatch_candidate` | engine dispatcher | `do-not-feed page work in early custom firmware` | Engine message 0x0b/0x40 path stores work pointer and calls engine status I/O. |

## Concrete Register Actions

| Register | Action | Function | Evidence | Risk |
|---|---|---:|---|---|
| `0xb050000c` | clear/status wait | `0x10015c68` | clears with 0xfeffffff, waits for bit 0x00010000 | engine handshake |
| `0xb0500004` | engine command submit | `0x10015c68` | writes requested 16-bit command, then sets bit 0x00010000 | engine handshake |
| `0xb2000008` | video descriptor write | `0x10015214` | receives work +0x84, BIH-derived horizontal field | video transfer |
| `0xb200000c` | video descriptor write | `0x10015214` | receives work +0x88, BIH-derived vertical field | video transfer |
| `0xb2000024` | video descriptor write | `0x10015214` | receives work +0x8c, BIH L0/band-height-like field | video transfer |
| `0xb2000000` | video transfer control write | `0x10015214` | writes computed control word from work +0x90 flags, OR 0x400 | video transfer start/control |
| `0xb2040000 / 0xb2080000` | paired channel enable/reset toggles | `0x10015214` | toggles bits 1 and 2 before descriptor writes | video transfer channel control |
| `0xb204000c / 0xb208000c` | paired channel status waits | `0x10015214` | waits for bit 2 after channel toggles | video transfer channel status |
| `0xb1000008 / 0xb1000108` | raw-band pointer/window write | `0x100140f8` | writes raster payload +0x54 pointer and pointer plus video_state +0xbc | raw-band feed |
| `0xb100000c / 0xb100010c` | raw-band flags/count write | `0x100140f8` | writes count from payload +0x20 and flags from payload +0x4c/+0x50 | raw-band feed |
| `0xb1000000 / 0xb1000100` | video block reset/enable | `0x10014910 / 0x10015458` | clears and sets bit 0x100 | video block control |
| `0xb1000004 / 0xb1000104` | video block busy/status wait | `0x10014910 / 0x10015458` | waits while bit 0x200 remains set; tests bit 0x100 in raw-band loop | video block status |

## Safe Custom-Firmware Rule

- A first custom firmware upload, if ever attempted, should initialize only the minimum CPU/runtime/USB path.
- It must not call video prepare/render/raw-band functions.
- It must not feed engine queue message 0x0b or 0x40.
- It must not write 0xb100, 0xb200, 0xb204, 0xb208, 0xb050, or 0xb020 registers.

## Practical Readout

The safe early target is not printing. It is a non-printing boot/USB identity probe that avoids engine and video MMIO entirely.

The unsafe line is now concrete: do not touch the `0xb100`, `0xb200`, `0xb204`, `0xb208`, `0xb050`, or `0xb020` families until the exact register semantics are understood.

The previous print-path model hands off at `work +0x50`. This map explains why that is the correct stop point: the next firmware functions program raw raster buffers, transfer channels, and engine handshakes.

For the narrow custom-firmware target, see `analysis/non-printing-usb-probe-spec.md`.

