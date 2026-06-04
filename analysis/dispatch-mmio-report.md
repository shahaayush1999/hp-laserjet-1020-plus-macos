# HP 1020 Dispatch/MMIO Pass

This pass turns the previous engine/video findings into a concrete dispatch and register-touch map.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020DispatchAndMmio.java`
- `analysis/dispatch-mmio/dispatch-mmio.md`
- `analysis/dispatch-mmio/decompiled/`

## Main Result

The print/video/engine path now has three useful maps:

1. `PrintMgr` dispatch message IDs `0x0b` through `0x43`
2. video reset/engine-event dispatch cases `0` through `7`
3. direct MMIO use sites for the selected engine/video functions

This does not name every state yet, but it changes the work from "find interesting code" to "explain specific state-machine branches and hardware registers."

## Print Manager Dispatch

`0x1000f324` `hp1020_print_mgr_thread_candidate` dispatches messages through a table at `0x100048f0`.

Resolved range:

- low: `0x0b`
- high: `0x43`

The active-looking table entries are:

| Message | Target block |
|---:|---:|
| `0x0b` | `0x1000f392` |
| `0x0c` | `0x1000f37a` |
| `0x0e` | `0x1000f44c` |
| `0x0f` | `0x1000f399` |
| `0x10` | `0x1000f460` |
| `0x11` | `0x1000f3ca` |
| `0x14` | `0x1000f474` |
| `0x15` | `0x1000f47d` |
| `0x16` | `0x1000f485` |
| `0x17` | `0x1000f4c2` |
| `0x25` | `0x1000f3d3` |
| `0x2d` | `0x1000f497` |
| `0x32` | `0x1000f547` |
| `0x34` | `0x1000f55b` |
| `0x43` | `0x1000f567` |

Most other entries point at `0x1000f358`, which is the shared default/no-op/error-looking block in the current decompile.

## Video Reset Dispatch

`0x10013d4c` `hp1020_video_reset_dispatch_candidate` has an 8-entry switch table at `0x10005710`.

| Case | Target block |
|---:|---:|
| `0` | `0x10013e90` |
| `1` | `0x10013ecd` |
| `2` | `0x10013f14` |
| `3` | `0x10013ee4` |
| `4` | `0x10013ef0` |
| `5` | `0x10013efc` |
| `6` | `0x10013f08` |
| `7` | `0x10013f14` |

The already-observed behavior still stands:

- case `0` can send message `0x11` to queue `0`
- case `0` can send message `0x0b` to queue `8`
- cases `2` through `7` feed encoded constants into engine event message `0x17`

## MMIO Concentration

The selected engine/video path directly touches these MMIO families:

| Family | Functions most visibly touching it | Current interpretation |
|---:|---|---|
| `0xb050....` | `0x10015c68` engine status I/O | engine status/control |
| `0xb100....` | `0x10014910`, `0x10015458` | video/raster setup and reset |
| `0xb200....` | `0x10015214` | video transfer / DMA-like path |
| `0xb204....` | `0x10015214` | video transfer side registers |
| `0xb208....` | `0x10015214` | video transfer side registers |

The generated `analysis/dispatch-mmio/dispatch-mmio.md` lists instruction-level sites such as:

- `0x10015c9f` / `0x10015cad` touching `0xb0500004`
- `0x10014bb8` / `0x10014bc3` touching `0xb1000000`
- `0x10015344` / `0x10015354` touching `0xb2000010`
- `0x10015277` / `0x10015281` touching `0xb2040000`
- `0x100152d9` / `0x100152e3` touching `0xb2080000`

This is enough to start a dedicated register-semantics pass.

## Updated Viability Read

The architecture-level reverse engineering is moving well:

- upload wrapper: known
- queue/thread structure: known
- dispatch tables: mapped
- MMIO use sites: concentrated

The remaining hard part is exact behavior:

- what each engine/video register means
- what values are safe to write and in what order
- whether boot can be reduced to USB-only without initializing the print engine
- whether the boot ROM accepts a small custom ELF with the same ACL/PJL wrapper

The next best step is boot/runtime ABI mapping: reset vector, entry path, data/BSS setup, ThreadX startup, and early hardware init.

