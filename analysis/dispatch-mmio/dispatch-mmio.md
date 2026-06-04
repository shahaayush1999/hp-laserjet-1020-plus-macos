# HP 1020 Dispatch And MMIO Map

This pass extracts the concrete switch table entries and MMIO use sites around the print/video/engine path.

## Print Manager Dispatch Table

- table: `0x100048f0`
- message range: `0x0b` through `0x43`

| Message | Target | Description |
|---:|---:|---|
| `0x0b` | `0x1000f392` | inside `hp1020_print_mgr_thread_candidate` + `0x6e` |
| `0x0c` | `0x1000f37a` | inside `hp1020_print_mgr_thread_candidate` + `0x56` |
| `0x0d` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x0e` | `0x1000f44c` | inside `hp1020_print_mgr_thread_candidate` + `0x128` |
| `0x0f` | `0x1000f399` | inside `hp1020_print_mgr_thread_candidate` + `0x75` |
| `0x10` | `0x1000f460` | inside `hp1020_print_mgr_thread_candidate` + `0x13c` |
| `0x11` | `0x1000f3ca` | inside `hp1020_print_mgr_thread_candidate` + `0xa6` |
| `0x12` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x13` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x14` | `0x1000f474` | inside `hp1020_print_mgr_thread_candidate` + `0x150` |
| `0x15` | `0x1000f47d` | inside `hp1020_print_mgr_thread_candidate` + `0x159` |
| `0x16` | `0x1000f485` | inside `hp1020_print_mgr_thread_candidate` + `0x161` |
| `0x17` | `0x1000f4c2` | inside `hp1020_print_mgr_thread_candidate` + `0x19e` |
| `0x18` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x19` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x1a` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x1b` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x1c` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x1d` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x1e` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x1f` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x20` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x21` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x22` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x23` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x24` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x25` | `0x1000f3d3` | inside `hp1020_print_mgr_thread_candidate` + `0xaf` |
| `0x26` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x27` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x28` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x29` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x2a` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x2b` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x2c` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x2d` | `0x1000f497` | inside `hp1020_print_mgr_thread_candidate` + `0x173` |
| `0x2e` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x2f` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x30` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x31` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x32` | `0x1000f547` | inside `hp1020_print_mgr_thread_candidate` + `0x223` |
| `0x33` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x34` | `0x1000f55b` | inside `hp1020_print_mgr_thread_candidate` + `0x237` |
| `0x35` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x36` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x37` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x38` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x39` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x3a` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x3b` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x3c` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x3d` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x3e` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x3f` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x40` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x41` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x42` | `0x1000f358` | inside `hp1020_print_mgr_thread_candidate` + `0x34` |
| `0x43` | `0x1000f567` | inside `hp1020_print_mgr_thread_candidate` + `0x243` |

## Video Reset Dispatch Table

- table: `0x10005710`

| Case | Target | Description |
|---:|---:|---|
| `0` | `0x10013e90` | inside `hp1020_video_reset_dispatch_candidate` + `0x144` |
| `1` | `0x10013ecd` | inside `hp1020_video_reset_dispatch_candidate` + `0x181` |
| `2` | `0x10013f14` | inside `hp1020_video_reset_dispatch_candidate` + `0x1c8` |
| `3` | `0x10013ee4` | inside `hp1020_video_reset_dispatch_candidate` + `0x198` |
| `4` | `0x10013ef0` | inside `hp1020_video_reset_dispatch_candidate` + `0x1a4` |
| `5` | `0x10013efc` | inside `hp1020_video_reset_dispatch_candidate` + `0x1b0` |
| `6` | `0x10013f08` | inside `hp1020_video_reset_dispatch_candidate` + `0x1bc` |
| `7` | `0x10013f14` | inside `hp1020_video_reset_dispatch_candidate` + `0x1c8` |

## Engine Dispatch Cases

The engine dispatch at `0x10016164` decompiles cleanly enough to identify these cases:

| Message | Working name | Evidence |
|---:|---|---|
| `0x0b` | page/engine work | stores current work pointer, computes state, calls engine status I/O |
| `0x0d` | convert-to-0x0e | rewrites first word to `0x0e` and resends queue `1` |
| `0x0f` | engine reset/clear | sends `0x25`, clears deferred work fields, calls reset helper |
| `0x11` | drain deferred work | polls status, sends delayed `0x11` or pending page `0x0b` |
| `0x18` | status poll | calls engine status poll with flag `1` |
| `0x19` | startup/ready event | sends `0x16` to queue `1` |
| `0x1a` | preflight/status refresh | calls preflight and status poll |
| `0x40` | force/start page path | sets state and falls through to `0x0b` |

## Engine/Video MMIO Use Sites

These are direct literal/register references visible in selected engine/video functions. They are not final register names.

| MMIO address | Family | Sites |
|---:|---|---|
| `0xb0500004` | `0xb050....` | `10015c9f` `hp1020_engine_status_io_candidate` `l32i.n a8,a6,0x0`<br>`10015cad` `hp1020_engine_status_io_candidate` `s32i a8,a6,0x0`<br>`10015cb3` `hp1020_engine_status_io_candidate` `l32i.n a8,a6,0x0`<br>`10015cbd` `... |
| `0xb050000c` | `0xb050....` | `10015c85` `hp1020_engine_status_io_candidate` `l32i.n a8,a11,0x0`<br>`10015c8f` `hp1020_engine_status_io_candidate` `s32i.n a8,a11,0x0`<br>`10015c97` `hp1020_engine_status_io_candidate` `l32i.n a8,a8,0x0`<br>`10015cc... |
| `0xb1000000` | `0xb100....` | `10014bb8` `hp1020_video_prepare_page_candidate` `l32i.n a8,a9,0x0`<br>`10014bc3` `hp1020_video_prepare_page_candidate` `s32i.n a8,a9,0x0`<br>`10014c01` `hp1020_video_prepare_page_candidate` `l32i.n a8,a9,0x0`<br>`100... |
| `0xb1000004` | `0xb100....` | `10014bd8` `hp1020_video_prepare_page_candidate` `l32i a8,a10,0x0`<br>`10014be4` `hp1020_video_prepare_page_candidate` `l32i a8,a10,0x0`<br>`10014d0e` `hp1020_video_prepare_page_candidate` `s32i a9,a8,0x0`<br>`1001547... |
| `0xb1000010` | `0xb100....` | `1001517f` `hp1020_video_prepare_page_candidate` `l32i a10,a9,0x0`<br>`1001518b` `hp1020_video_prepare_page_candidate` `s32i a8,a9,0x0` |
| `0xb1000014` | `0xb100....` | `100151a8` `hp1020_video_prepare_page_candidate` `l32i.n a8,a12,0x0`<br>`100151c1` `hp1020_video_prepare_page_candidate` `s32i a8,a12,0x0`<br>`1001520a` `hp1020_video_prepare_page_candidate` `call8 0x10017184` |
| `0xb100001c` | `0xb100....` | `10014d22` `hp1020_video_prepare_page_candidate` `l32i.n a8,a10,0x0`<br>`10014d30` `hp1020_video_prepare_page_candidate` `s32i.n a8,a10,0x0`<br>`10014d77` `hp1020_video_prepare_page_candidate` `l32i.n a8,a12,0x0`<br>`... |
| `0xb1000020` | `0xb100....` | `10014c6c` `hp1020_video_prepare_page_candidate` `s32i a8,a9,0x0`<br>`10014ca4` `hp1020_video_prepare_page_candidate` `s32i a8,a9,0x0`<br>`10014cc9` `hp1020_video_prepare_page_candidate` `s32i a8,a9,0x0` |
| `0xb1000024` | `0xb100....` | `10014c7e` `hp1020_video_prepare_page_candidate` `s32i a8,a10,0x0`<br>`10014ced` `hp1020_video_prepare_page_candidate` `s32i a8,a11,0x0` |
| `0xb1000100` | `0xb100....` | `10014bc8` `hp1020_video_prepare_page_candidate` `l32i.n a8,a11,0x0`<br>`10014bd3` `hp1020_video_prepare_page_candidate` `s32i.n a8,a11,0x0`<br>`10014c11` `hp1020_video_prepare_page_candidate` `l32i.n a8,a10,0x0`<br>`... |
| `0xb1000104` | `0xb100....` | `10014bf3` `hp1020_video_prepare_page_candidate` `l32i.n a8,a10,0x0`<br>`10014d1a` `hp1020_video_prepare_page_candidate` `s32i.n a9,a8,0x0`<br>`100154b5` `hp1020_video_reset_or_flush_candidate` `l32i.n a8,a10,0x0`<br>... |
| `0xb1000110` | `0xb100....` | `10015197` `hp1020_video_prepare_page_candidate` `l32i a10,a9,0x0`<br>`100151a3` `hp1020_video_prepare_page_candidate` `s32i.n a8,a9,0x0` |
| `0xb1000114` | `0xb100....` | `100151c7` `hp1020_video_prepare_page_candidate` `l32i a8,a10,0x0`<br>`100151d6` `hp1020_video_prepare_page_candidate` `s32i.n a8,a10,0x0` |
| `0xb100011c` | `0xb100....` | `10014d35` `hp1020_video_prepare_page_candidate` `l32i a9,a13,0x0`<br>`10014d4f` `hp1020_video_prepare_page_candidate` `s32i.n a9,a13,0x0`<br>`10014d8a` `hp1020_video_prepare_page_candidate` `l32i.n a8,a11,0x0`<br>`10... |
| `0xb1000120` | `0xb100....` | `10014cda` `hp1020_video_prepare_page_candidate` `s32i.n a8,a10,0x0` |
| `0xb1000124` | `0xb100....` | `10014cf9` `hp1020_video_prepare_page_candidate` `s32i a9,a8,0x0` |
| `0xb1000400` | `0xb100....` | `10014ee5` `hp1020_video_prepare_page_candidate` `s32i.n a10,a12,0x0`<br>`10014f1c` `hp1020_video_prepare_page_candidate` `s32i.n a10,a12,0x0`<br>`10014f48` `hp1020_video_prepare_page_candidate` `s32i a9,a11,0x0`<br>`... |
| `0xb1000410` | `0xb100....` | `10014eea` `hp1020_video_prepare_page_candidate` `s32i.n a9,a11,0x0`<br>`10014f21` `hp1020_video_prepare_page_candidate` `s32i.n a9,a11,0x0`<br>`10014f4e` `hp1020_video_prepare_page_candidate` `s32i a8,a10,0x0`<br>`10... |
| `0xb1000420` | `0xb100....` | `10014f48` `hp1020_video_prepare_page_candidate` `s32i a9,a11,0x0`<br>`10015001` `hp1020_video_prepare_page_candidate` `s32i.n a8,a9,0x0` |
| `0xb1000430` | `0xb100....` | `10014f4e` `hp1020_video_prepare_page_candidate` `s32i a8,a10,0x0`<br>`10015001` `hp1020_video_prepare_page_candidate` `s32i.n a8,a9,0x0` |
| `0xb2000000` | `0xb200....` | `100153b5` `hp1020_video_render_or_dma_candidate` `s32i a8,a9,0x0` |
| `0xb2000008` | `0xb200....` | `10015359` `hp1020_video_render_or_dma_candidate` `s32i.n a8,a10,0x0` |
| `0xb200000c` | `0xb200....` | `1001536a` `hp1020_video_render_or_dma_candidate` `s32i.n a9,a11,0x0` |
| `0xb2000010` | `0xb200....` | `10015344` `hp1020_video_render_or_dma_candidate` `l32i.n a9,a11,0x0`<br>`10015354` `hp1020_video_render_or_dma_candidate` `s32i.n a9,a11,0x0`<br>`1001540f` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a11,0x0`<b... |
| `0xb2000024` | `0xb200....` | `1001536f` `hp1020_video_render_or_dma_candidate` `s32i.n a8,a10,0x0` |
| `0xb2040000` | `0xb204....` | `10015277` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a10,0x0`<br>`10015281` `hp1020_video_render_or_dma_candidate` `s32i.n a8,a10,0x0`<br>`10015286` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a10,0x0`<b... |
| `0xb2040004` | `0xb204....` | `100153da` `hp1020_video_render_or_dma_candidate` `s32i.n a8,a9,0x0` |
| `0xb2040008` | `0xb204....` | `100153e4` `hp1020_video_render_or_dma_candidate` `s32i a8,a10,0x0`<br>`100153f3` `hp1020_video_render_or_dma_candidate` `call8 0x10014244`<br>`100153ff` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a9,0x0` |
| `0xb204000c` | `0xb204....` | `10015298` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a9,0x0`<br>`100152a4` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a10,0x0` |
| `0xb2080000` | `0xb208....` | `100152d9` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a10,0x0`<br>`100152e3` `hp1020_video_render_or_dma_candidate` `s32i.n a8,a10,0x0`<br>`100152e8` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a10,0x0`<b... |
| `0xb208000c` | `0xb208....` | `100152fa` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a9,0x0`<br>`10015307` `hp1020_video_render_or_dma_candidate` `l32i.n a8,a10,0x0` |

## Queue 8 Evidence

Queue `8` remains the least-resolved active queue in the print path.

Current evidence:

- `hp1020_video_reset_dispatch_candidate` can send message `0x0b` to queue `8`.
- `hp1020_video_thread_candidate` receives from pointer `PTR_DAT_1000676c`; the descriptor region around `0x10006784` contains `tVideo` and video MMIO constants.
- The direct queue ID -> queue object table lives in runtime BSS at `0x1002c918`, so the static file does not directly expose every queue slot value.

The next proof step is to identify the init path that populates `0x1002c918`, or to find every receive wrapper call and match queue object pointers to descriptor names.

## Interpretation

This pass reinforces the current model:

- `PrintMgr` is the high-level message dispatcher, but most entries beyond the early active range still need handler-level names.
- `Video` owns page/raster-band preparation and hardware transfer.
- `Engine` owns mechanical state gating and status-driven advancement.
- The MMIO families are now concentrated enough to support a dedicated register-semantics pass.

A minimal non-printing firmware experiment should wait until the boot/runtime ABI is mapped. A printing experiment should wait until at least the `0xb100`, `0xb200`, `0xb020`, and `0xb050` register families have behavioral names.
