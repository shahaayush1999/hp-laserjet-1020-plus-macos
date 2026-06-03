# HP 1020 Message Producer Trace

This pass traces where internal message IDs are assigned and sent through queue helpers in the print/job/status/video/engine neighborhood.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020MessageProducers.java`
- `analysis/message-producers/message-producers.md`
- `analysis/message-producers/producer-decompiled/`

## Main Result

The firmware's print path is visibly queue-driven. The same numeric message can appear on multiple queues, so IDs must be read with the queue context.

Important queue send helpers:

- `0x10013658` `hp1020_queue_send_candidate`
- `0x10013620` `hp1020_send_or_raise_engine_msg_candidate`
- lower wrapper: `0x10013668`

Important queue receive helper:

- `0x1001809c` `threadx_queue_receive_wait_candidate`

## Confirmed Message Producers

### Print Manager

`0x1000f324` `hp1020_print_mgr_thread_candidate`:

- sends initial message `0x18` to queue `0`
- receives from `PrintMgrQueue`
- dispatch range remains `0x0b` through `0x43`

### Job Manager

`0x1000e414` `hp1020_job_mgr_thread_candidate`:

- handles cases `1`, `2`, `3`, `5`, `6`, `8`, `9`, `0x0f`, `0x11`, `0x21`, `0x25`, `0x29`, `0x2a`, `0x2b`, `0x33`
- sends `0x0f` in case `0x0f`
- sends `0x25` to queue `3` when a counter/state reaches zero
- sends `0x0b` to queue `1` in case `0x21`
- sends status-like `0x30`/`0x31` messages to queue `10`

This looks like high-level job lifecycle coordination feeding print/status/engine queues.

### Status Manager

`0x10010590` `hp1020_status_mgr_thread_candidate`:

- handles cases `0x0f`, `0x2c`, `0x2e`, `0x2f`, `0x30`, `0x31`, `0x32`, `0x43`
- receives from `StatusMgrQueue`
- sends onward through `hp1020_queue_send_candidate(uVar5, &message)`
- calls PJL/status response builders in completion/error cases

### Video Thread

`0x10013c18` `hp1020_video_thread_candidate`:

- receives video queue messages
- recognizes `0x0b` as a page/video work item
- recognizes `0x0f` as reset/flush
- sends `0x10` to queue `1` after processing

### Video Reset/Dispatch

`0x10013d4c` `hp1020_video_reset_dispatch_candidate`:

- case `0`: sends `0x11` to queue `0`
- case `0`: may also send `0x0b` to queue `8`
- case `1`: prepares `0x25`
- cases `2` through `7`: prepare encoded hardware/status constants and send `0x17` to queue `1`

This function is a bridge from video/raster state back into engine/status messaging.

### Engine Status

`0x10015df8` `hp1020_engine_status_poll_candidate`:

- emits `0x17` to queue `1` when engine status changes
- reacts to status bit patterns and updates state fields before sending

`0x10015c68` `hp1020_engine_read_or_write_status_candidate` also emits `0x17` to queue `1` in one timeout/failure path.

### Engine Dispatch

`0x10016164` `hp1020_engine_message_dispatch_candidate`:

- handles `0x0b`, `0x0d`, `0x0f`, `0x11`, `0x18`, `0x19`, `0x1a`, `0x40`
- `0x0d` becomes `0x0e`
- `0x0f` sends `0x25`
- `0x11` may resend `0x11` or send `0x0b`
- `0x19` sends `0x16`
- `0x40` falls through into the `0x0b` page/engine path

### Engine Thread

`0x100163b0` `hp1020_engine_thread_candidate`:

- sends startup message `0x16`
- registers event handlers for `0x0f` through `0x14`
- loops on engine queue and dispatches through `0x10016164`

## Working Queue Interpretation

The queue numbers are still candidate labels, but this is the working map:

- queue `0`: print manager or high-level control path
- queue `1`: engine/video/status event path
- queue `3`: job manager path
- queue `8`: secondary/deferred video or engine path
- queue `10`: status manager path
- queue `0x0f`: delay manager queue path

The exact queue-to-subsystem mapping should be validated by resolving the queue descriptor pointer table and every call into `0x10013668`.

## Why This Matters

The firmware now looks less like a blob and more like a set of cooperating state machines:

- Job manager starts and advances job records.
- Print manager dispatches print-stage messages.
- Video thread prepares/renders raster bands.
- Engine thread drives mechanical state.
- Status manager converts engine/job events into PJL-visible status.

That is the right structure to keep reverse-engineering. The next useful pass is not broad discovery; it is queue resolution.

## Next Pass

Trace `0x10013668` and its queue argument:

- map queue number to queue control block
- map queue control block to descriptor name where possible
- split each message ID by queue
- produce a table like `queue name -> message ID -> producer -> consumer`
