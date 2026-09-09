# HP 1020 MMIO Semantics Pass

> Routing correction (2026-09-08): [stock registration](queue-routing/registration.md) proves queue 0 is engine and queue 1 is PrintMgr. Older routing interpretations below are historical; event 0x17 and datastore notification 0x2d reach PrintMgr, so their former missing-consumer conclusions are superseded.


This pass starts naming engine/video hardware registers by behavior rather than just address family.

It uses:

- `analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c`
- `analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c`
- `analysis/dispatch-mmio/decompiled/10015458_hp1020_video_reset_or_flush_candidate.c`
- literal tables around `0x10006790` and `0x100068e0`

## Main Result

The engine/video hardware path now has a first behavioral split:

| Address family | Working role |
|---:|---|
| `0xb050....` | engine command/status handshake |
| `0xb100....` | video/raster block reset/control |
| `0xb200....` | video transfer control / descriptors |
| `0xb204....` | video transfer channel A |
| `0xb208....` | video transfer channel B |

These names are still working names, not final register names.

## Engine Status I/O

Function:

- `0x10015c68` `hp1020_engine_status_io_candidate`

Literal table:

| Table address | Value | Working meaning |
|---:|---:|---|
| `0x1000691c` | `0xb050000c` | engine status/ready register candidate |
| `0x10006924` | `0xfeffffff` | clear-mask candidate |
| `0x10006928` | `0xb0500004` | engine command/control register candidate |
| `0x1000692c` | `0xfe001401` | failure/status event constant |

Observed behavior:

1. Stores the requested 16-bit engine command into firmware state at offset `0x5a`.
2. Clears a bit in `0xb050000c` using mask `0xfeffffff`.
3. Waits until `0xb050000c & 0x00010000` is nonzero.
4. Writes the command into `0xb0500004`.
5. Sets bit `0x00010000` in `0xb0500004`.
6. Waits for a queue/event response through `FUN_10017d28(...)`.
7. On timeout/failure, sends engine event message `0x17` to queue `1`.
8. On success, returns a 16-bit status value from firmware state offset `0x5c`.

Current interpretation:

- `0xb050000c` is a status/ready/handshake register.
- `0xb0500004` is a command/control register.
- bit `0x00010000` is part of the command-ready or command-submit handshake.

## Video Transfer / DMA Path

Function:

- `0x10015214` `hp1020_video_render_or_dma_candidate`

Literal table:

| Table address | Value | Working meaning |
|---:|---:|---|
| `0x10006790` | `0xb2000010` | transfer status/control candidate |
| `0x10006794` | `0xb2080000` | channel B control candidate |
| `0x10006798` | `0xb2040000` | channel A control candidate |
| `0x1000679c` | `0xb204000c` | channel A status candidate |
| `0x100067a0` | `0xb208000c` | channel B status candidate |
| `0x100068f0` | `0xb2000008` | transfer pointer/descriptor candidate |
| `0x100068f4` | `0xb200000c` | transfer pointer/descriptor candidate |
| `0x100068f8` | `0xb2000024` | transfer pointer/descriptor candidate |
| `0x10006900` | `0xb2000000` | transfer start/control candidate |

Observed behavior:

- toggles bit `2` and bit `1` in `0xb2040000`
- waits for bit `2` in `0xb204000c`
- toggles bit `2` and bit `1` in `0xb2080000`
- waits for bit `2` in `0xb208000c`
- writes page/raster descriptor values from the page object into `0xb2000008`, `0xb200000c`, and `0xb2000024`
- updates mode bits in a firmware-side control word
- writes that control word to `0xb2000000`
- writes buffer/page positions through `0xb2040004`, `0xb2040008`, `0xb2080010`, and related addresses
- waits for a transfer pointer delta before setting bit `1` in `0xb2000010`

Current interpretation:

- `0xb204....` and `0xb208....` are paired transfer channels or paired video hardware lanes.
- `0xb200....` is the higher-level video transfer/DMA control block.
- the function programs raster/page buffer descriptors and then starts or advances transfer.

## Video Reset / Flush

Function:

- `0x10015458` `hp1020_video_reset_or_flush_candidate`

Literal table:

| Table address | Value | Working meaning |
|---:|---:|---|
| `0x100067c0` | `0xb1000004` | video reset/status register A |
| `0x100067d8` | `0xb1000104` | video reset/status register B |
| `0x10006808` | `0xb1000000` | video control register A |
| `0x1000680c` | `0xb1000100` | video control register B |

Observed behavior:

- clears bit `0x100` in `0xb1000000`
- waits while bit `0x200` remains set in `0xb1000004`
- sets bit `0x100` in `0xb1000000`
- clears bit `0x100` in `0xb1000100`
- waits while bit `0x200` remains set in `0xb1000104`
- conditionally sets bit `0x100` in `0xb1000100`
- calls video reset dispatch with case `1`

Current interpretation:

- `0xb1000000`/`0xb1000004` and `0xb1000100`/`0xb1000104` are paired video block control/status registers.
- bit `0x100` looks like reset/enable/flush control.
- bit `0x200` looks like busy/reset-in-progress status.

## Practical Meaning

This is the first point where a printing firmware replacement becomes truly hardware-sensitive:

- engine command submission is a handshake with status bits and queue response timing
- video transfer programming uses multiple MMIO blocks and waits on hardware status
- reset/flush order matters

For a minimal non-printing prototype, these registers should be avoided if possible.

For a printing prototype, the next step would be:

1. label every `0xb100`, `0xb200`, `0xb204`, `0xb208`, `0xb050`, and `0xb020` use site
2. group reads versus writes
3. extract constants written to each register
4. correlate those with state-machine message IDs (`0x0b`, `0x0f`, `0x10`, `0x17`, `0x25`)

