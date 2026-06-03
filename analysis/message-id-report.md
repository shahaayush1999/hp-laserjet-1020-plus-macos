# HP 1020 Firmware Message IDs

This notes the first stable internal message IDs found in the print manager, video, and engine paths.

This is not a final protocol spec. It is a map of queue/message numbers visible from the decompiled functions in `analysis/engine/engine-decompiled/`.

## Queue Send Helpers

Two helper functions are important:

- `0x10013658` `hp1020_queue_send_candidate`
- `0x10013620` `hp1020_send_or_raise_engine_msg_candidate`

`hp1020_send_or_raise_engine_msg_candidate` wraps the same lower queue-send function but logs `tx_queue_send() failed, MSG LOST !!` if the send fails.

## Print Manager Message Range

`0x1000f324` `hp1020_print_mgr_thread_candidate` waits on `PrintMgrQueue`, then dispatches:

```c
while (0x38 < aiStack_50[0] - 0xbU) { ... }
(switch_table + (aiStack_50[0] - 0xbU) * 4)(...);
```

So `PrintMgr` accepts message IDs from:

- low: `0x0b`
- high: `0x43`

It sends an initial message:

- `0x18`

The switch table starts at `0x100048f0`. First known entries:

- `0x0b` -> internal block `0x1000f392`
- `0x0c` -> internal block `0x1000f37a`
- `0x0d` -> default-ish/internal block `0x1000f358`
- `0x0e` -> internal block `0x1000f44c`
- `0x0f` -> internal block `0x1000f399`
- `0x10` -> internal block `0x1000f460`
- `0x11` -> internal block `0x1000f3ca`
- many later IDs initially point to `0x1000f358`, likely a default/no-op/error path

## Engine Message Dispatch

`0x10016164` `hp1020_engine_message_dispatch_candidate` handles at least:

- `0x0b`
- `0x0d`
- `0x0f`
- `0x11`
- `0x18`
- `0x19`
- `0x1a`
- `0x40`

Observed behavior:

- `0x0d`: converted to `0x0e` and sent onward.
- `0x0f`: sends `0x25`, clears/sets engine state fields, and calls `FUN_10016098`.
- `0x11`: checks engine status; may send/defer another `0x11`; may send `0x0b`.
- `0x18`: polls engine status.
- `0x19`: sends `0x16`.
- `0x1a`: updates status/preflight path.
- `0x40`: sets state and falls through to `0x0b`.
- `0x0b`: main page/engine work path; stores current work pointer, computes state through `FUN_100162b0`, and calls lower engine status functions.

Other IDs sent by engine/video/status functions:

- `0x10`: video thread sends this after processing a page/video message.
- `0x11`: video reset path sends this back to engine.
- `0x16`: engine thread sends this during startup and `0x19` handling.
- `0x17`: engine status poll sends this when status changes.
- `0x25`: engine/video reset path sends this as a reset/clear-style notification.

## Video Dispatch

`0x10013c18` `hp1020_video_thread_candidate` waits on the video queue.

Observed cases:

- `0x0b`: page/video work item.
- `0x0f`: reset/flush path.
- sends `0x10` after processing.

`0x10013d4c` has a separate small switch table around `0x10005710`. Known case mapping from the table:

- `0` -> `0x10013e90`
- `1` -> `0x10013ecd`
- `2` -> `0x10013f14`
- `3` -> `0x10013ee4`
- `4` -> `0x10013ef0`
- `5` -> `0x10013efc`
- `6` -> `0x10013f08`
- `7` -> `0x10013f14`

Cases `2` through `7` choose encoded constants like `0xe6e01201`, `0xe6e01202`, `0xeee01b02`, `0xeee01b04`, and `0xeee01b01`, then send message `0x17`.

## Current Interpretation

The queue/message layer is real and now partially mapped. It looks like this:

- `PrintMgr` owns high-level print-job messages.
- `Video` owns raster/page-band work and reset/flush messages.
- `Engine` owns mechanical/engine state messages.
- `StatusMgr` emits PJL-visible status as engine state changes.

This is the bridge from software parsing into hardware behavior. It is also the point where replacement firmware stops being mostly "copy descriptors and parse commands" and becomes "model an embedded real-time print engine."

## Next Step

The next useful mapping step is to trace producers for each message ID:

- find every assignment of `0x0b`, `0x0f`, `0x10`, `0x11`, `0x16`, `0x17`, `0x18`, `0x19`, `0x1a`, `0x25`, and `0x40`
- identify which queue each send targets
- split message IDs by queue, because the same numeric ID may mean different things on different queues
