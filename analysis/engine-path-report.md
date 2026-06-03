# HP 1020 Engine And Video Path

This pass maps the firmware area closest to actual printing: print manager dispatch, video/raster handling, engine status polling, and engine queue messages.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020EnginePath.java`
- `analysis/engine/engine-path.md`
- `analysis/engine/engine-decompiled/`

## Main Result

The print path is now anchored to concrete functions:

- `0x1000f324` `hp1020_print_mgr_thread_candidate`
- `0x10013c18` `hp1020_video_thread_candidate`
- `0x10014910` `hp1020_video_prepare_page_candidate`
- `0x10015214` `hp1020_video_render_or_dma_candidate`
- `0x10015438` `hp1020_video_alt_render_candidate`
- `0x10015458` `hp1020_video_reset_or_flush_candidate`
- `0x10015df8` `hp1020_engine_status_poll_candidate`
- `0x10016024` `hp1020_engine_init_step_candidate`
- `0x100160a8` `hp1020_engine_preflight_candidate`
- `0x10016164` `hp1020_engine_message_dispatch_candidate`
- `0x1001635c` `hp1020_engine_delay_thread_candidate`
- `0x100163b0` `hp1020_engine_thread_candidate`
- `0x100165a4` `hp1020_engine_register_handlers_candidate`

The generated map follows those seeds to a `125`-function call neighborhood.

## Hardware Address Families

The engine/video path uses hardware ranges that are separate from the earlier USB `0xb300....` range.

Likely video/raster hardware:

- `0xb1000000`
- `0xb1000100`
- `0xb1000004`
- `0xb1000104`
- `0xb1000008`
- `0xb1000108`
- `0xb100000c`
- `0xb100010c`
- `0xb2000010`
- `0xb2040000`
- `0xb204000c`
- `0xb2080000`
- `0xb208000c`

Likely engine/control hardware:

- `0xb0200000`
- `0xb0200004`
- `0xb0200008`
- `0xb020000c`
- `0xb0500000`
- `0xb0500004`
- `0xb050000c`
- `0xb0501000`

The MMIO scanner is broad, so a few constants may be false positives. The repeated, table-backed address families above are the useful part.

## Engine Dispatch

`hp1020_engine_thread_candidate` initializes engine state, waits for hardware readiness, registers event handlers for IDs `0x0f` through `0x14`, sends an initial message, then loops on an engine queue.

The central dispatch function is:

- `0x10016164` `hp1020_engine_message_dispatch_candidate`

The decompiler shows cases for at least:

- `0x0b`
- `0x0d`
- `0x0f`
- `0x11`
- `0x18`
- `0x19`
- `0x1a`
- `0x40`

Those are likely internal engine/message IDs, not USB or PJL commands.

## Video/Raster Path

`hp1020_video_thread_candidate` waits on the video queue and calls:

- `0x10014910` `hp1020_video_prepare_page_candidate`
- `0x10015214` `hp1020_video_render_or_dma_candidate`
- `0x10015438` `hp1020_video_alt_render_candidate`
- `0x10015458` `hp1020_video_reset_or_flush_candidate`

The video path manipulates page/raster structures, raw-band buffers, and MMIO registers. The string `refreshRawBands, ic.pBidBlock=0x%08x, nBackloggedBands=%u` is a strong hint that this firmware manages raster bands, not a full-page framebuffer.

`hp1020_video_render_or_dma_candidate` writes page dimensions and buffer pointers into hardware registers, waits on register bits, and advances ring/band state. This is exactly the kind of hardware-specific behavior that makes a reliable open replacement hard.

## Practical Viability Update

At this point the reverse-engineering work has moved faster than a normal human-only first pass. The firmware is no longer opaque:

- USB enumeration and control transfer path: mapped.
- Static USB descriptors: mapped.
- Identity/PJL/status: mapped.
- Thread/task layout: mapped.
- Print manager, video, and engine entry points: mapped.
- First engine/video MMIO families: mapped.

What remains hard is not naming more functions. It is proving exact hardware semantics:

- what each `0xb1....`, `0xb2....`, `0xb02....`, and `0xb05....` register does
- which message IDs correspond to safe engine states
- how raster bands are formatted and paced
- how fuser/motor/scanner timing is sequenced
- what hardware failure states must be handled to avoid jams, overheating, or mechanical abuse

So the honest estimate narrows:

- Minimal open firmware that enumerates over USB and answers identity/status: increasingly plausible as a focused prototype.
- Open firmware that prints one controlled page: still a hardware-research project, not just a coding sprint.
- Reliable daily-use replacement firmware: still months-class solo unless hardware docs or prior art are found.

## Next Pass

The next useful technical pass is to label the engine/video message IDs:

- map the `PrintMgr` switch table at `0x100048f0`
- map video switch table around `0x10005710`
- trace queue sends into `hp1020_engine_message_dispatch_candidate`
- name the `0x0b`, `0x0f`, `0x11`, `0x17`, `0x18`, `0x19`, `0x1a`, `0x25`, and `0x40` message IDs
- split likely false-positive MMIO constants from real register addresses
