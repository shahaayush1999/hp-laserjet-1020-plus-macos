# HP 1020 Firmware Task Map

This pass maps ThreadX-style task, queue, semaphore, and engine descriptor tables from readable names embedded in the firmware.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020TaskDescriptors.java`
- `analysis/tasks/task-descriptors.md`
- `analysis/tasks/task-decompiled/`

## Main Result

The firmware has now been split into named task-level subsystems. This is a major step beyond generic function clustering because it identifies the likely thread entry functions for the parts that actually run the printer.

Resolved task/thread candidates:

- `0x10008ff0` `hp1020_usb2_thread`
- `0x10009934` `hp1020_usb2_idle_thread`
- `0x1000e414` `hp1020_job_mgr_thread_candidate`
- `0x1000f324` `hp1020_print_mgr_thread_candidate`
- `0x10010590` `hp1020_status_mgr_thread_candidate`
- `0x10010b0c` `hp1020_delay_mgr_receive_thread_candidate`
- `0x1001146c` `hp1020_data_store_thread_candidate`
- `0x100139e4` `hp1020_control_panel_thread_candidate`
- `0x10013c18` `hp1020_video_thread_candidate`
- `0x1001635c` `hp1020_engine_delay_thread_candidate`
- `0x100163b0` `hp1020_engine_thread_candidate`
- `0x1001788c` `hp1020_system_timer_thread_candidate`

Important queue/semaphore anchors:

- `Job Mgr Queue`
- `PrintMgrQueue`
- `StatusMgrQueue`
- `DelayMgr Semaphore`
- `DelayMgr Msg Queue`
- `engDelayMsgQ`
- `?Video Queue`

## What The Task Entries Show

### Print Manager

`hp1020_print_mgr_thread_candidate` waits on `PrintMgrQueue`, checks message IDs, then dispatches through a jump table. This is probably the high-level print-job state machine.

The decompiler shows message IDs around `0x0b` through `0x43`, with a switch table at the `0x100048f0` region.

### Job Manager

`hp1020_job_mgr_thread_candidate` is larger and handles job lifecycle state. It receives queue messages, allocates or links job records, handles start/stop/cancel-like states, and calls into the print manager path.

### Status Manager

`hp1020_status_mgr_thread_candidate` handles status events and builds PJL-style status responses through the functions already mapped in the identity/status pass. It calls the `USTATUS` response builders for page/result/device status cases.

### Video Thread

`hp1020_video_thread_candidate` touches memory-mapped hardware, receives video queue messages, and calls functions in the `0x10014910` to `0x10015458` range. This looks much closer to the actual raster/video path than the USB or PJL layers.

### Engine Thread

`hp1020_engine_thread_candidate` initializes engine state, waits for hardware readiness, registers handlers for event IDs `0x0f` through `0x14`, then loops on an engine queue and dispatches messages through `FUN_10016164`.

This is one of the most important functions for replacement-firmware viability. It is also exactly why the "AI will finish this in a day" assumption breaks down: this path is not just software parsing. It coordinates hardware state and timing.

## Practical Viability Update

The reverse-engineering estimate was not wrong for the hard goal. What changed is that the analysis front-end is moving fast:

- USB enumeration/control: mapped enough for a credible clone/spec.
- Identity/PJL/status: mapped enough to trace responses.
- Task/thread layout: now mapped to real subsystem entry points.
- Print/video/engine control: identified, but not understood deeply enough to safely rewrite.

The project is now past "can we even understand this blob?" and into "can we model the print engine without damaging hardware or getting stuck on missing register docs?"

For an open firmware prototype, the likely next narrow target is not printing. It is a minimal firmware that boots, exposes the same USB printer-class descriptors, and responds correctly to basic USB/PJL identity/status requests. Printing still requires the video and engine paths.

## Next Pass

The next useful pass is a print-engine dispatch map:

- trace `hp1020_engine_thread_candidate`
- label event IDs `0x0f` through `0x14`
- trace `FUN_10016164`
- trace video functions `0x10014910`, `0x10015214`, `0x10015438`, `0x10015458`
- build an MMIO map for engine/video code
