# HP 1020 Queue Resolution

This pass ties queue numbers used by `hp1020_queue_send_candidate()` to likely ThreadX queue consumers and descriptor names.

## Queue Send Mechanism

The low-level queue-send wrapper is:

- `0x10013668` `FUN_10013668`

Ghidra decompiles it as:

```c
iVar1 = FUN_100180dc(*(undefined4 *)(param_1 * 4 + DAT_100066f0), param_2, param_3);
```

The word at `0x100066f0` is:

```text
0x1002c918
```

So queue number `N` indexes a runtime table:

```text
queue_control_block = *(0x1002c918 + N * 4)
```

That table lives in BSS/runtime memory, so the firmware populates it during initialization. The practical mapping below is inferred by matching send queue numbers against receiver functions and task descriptor queue objects.

## Candidate Queue Map

| Queue ID | Likely queue | Consumer / owner | Evidence |
|---:|---|---|---|
| `0` | `PrintMgrQueue` | `0x1000f324` `hp1020_print_mgr_thread_candidate` | PrintMgr receives from `PTR_DAT_1000632c` / `0x10028a74`; PrintMgr sends startup message `0x18` to queue `0`. |
| `1` | `engMsgQ` / engine queue | `0x100163b0` `hp1020_engine_thread_candidate` | Engine thread receives from `PTR_DAT_100069bc` / `0x1002f134`; many engine/video/status paths send engine-state messages to queue `1`. |
| `3` | `Job Mgr Queue` | `0x1000e414` `hp1020_job_mgr_thread_candidate` | Job manager queue object appears around `0x1002386c`; job creation/control helpers repeatedly send to queue `3`. |
| `8` | video/deferred engine path, likely `?Video Queue` related | `0x10013c18` `hp1020_video_thread_candidate` or adjacent video queue path | Video reset dispatch sends `0x0b` to queue `8`; video thread receives from `PTR_DAT_1000676c` / `0x1002ee38`. |
| `10` | `StatusMgrQueue` | `0x10010590` `hp1020_status_mgr_thread_candidate` | Status manager receives from `PTR_DAT_100063b4` / `0x10028adc`; job/status functions send `0x2c`/`0x2e`/`0x30`/`0x31` style status messages to queue `10`. |
| `0x0f` | `DelayMgr Msg Queue` | `0x10010b0c` `hp1020_delay_mgr_receive_thread_candidate` | Delay manager helpers send message `0x44` to queue `0x0f`; delay manager descriptor block contains `DelayMgr Msg Queue` and `tDelayMgrRcvMsg`. |

## Receiver Evidence

### Print Manager

`0x1000f324` receives from:

```c
threadx_queue_receive_wait_candidate(PTR_DAT_1000632c, aiStack_50, 0xffffffff);
```

Task descriptor map:

- `PrintMgrQueue`
- nearby queue/control object: `0x10028a74`
- thread entry: `0x1000f324`

### Engine

`0x100163b0` receives from:

```c
threadx_queue_receive_wait_candidate(PTR_DAT_100069bc, &uStack_30, 0x32);
```

Task descriptor map:

- `engMsgQ`
- nearby queue/control object: `0x1002f134`
- thread entry: `0x100163b0`

### Engine Delay

`0x1001635c` receives from:

```c
threadx_queue_receive_wait_candidate(PTR_DAT_1000699c, aiStack_30, 0xffffffff);
```

Task descriptor map:

- `engDelayMsgQ`
- nearby queue/control object: `0x10030494` / `0x10030400`
- thread entry: `0x1001635c`

### Video

`0x10013c18` receives from:

```c
threadx_queue_receive_wait_candidate(PTR_DAT_1000676c, aiStack_30, 0xffffffff);
```

Task descriptor map:

- `Video Queue` / `?Video Queue`
- nearby queue/control object: `0x1002ee38`
- thread entry: `0x10013c18`

### Status Manager

`0x10010590` receives from:

```c
threadx_queue_receive_wait_candidate(PTR_DAT_100063b4, &uStack_30, 0xffffffff);
```

Task descriptor map:

- `StatusMgrQueue`
- nearby queue/control object: `0x10028adc`
- thread entry: `0x10010590`

### Delay Manager

Delay manager helper functions enqueue message `0x44` to queue `0x0f`:

```c
local_30 = 0x44;
hp1020_queue_send_candidate(0xf, &local_30);
```

Task descriptor map:

- `DelayMgr Msg Queue`
- `tDelayMgrRcvMsg`
- thread entry: `0x10010b0c`

## Message IDs By Queue

### Queue `0`: Print Manager

Known produced IDs:

- `0x18`
- `0x11` via video reset path, likely routed back to print manager/high-level control

Consumer:

- `hp1020_print_mgr_thread_candidate`

Dispatch range:

- `0x0b` through `0x43`

### Queue `1`: Engine

Known produced IDs:

- `0x0b`
- `0x0d` -> converted to `0x0e`
- `0x10`
- `0x11`
- `0x16`
- `0x17`
- `0x18`
- `0x19`
- `0x1a`
- `0x25`

Consumer:

- `hp1020_engine_thread_candidate`
- dispatch function: `hp1020_engine_message_dispatch_candidate`

### Queue `3`: Job Manager

Known produced IDs:

- `1`
- `2`
- `3`
- `5`
- `6`
- `0x21`
- `0x25`

Consumer:

- `hp1020_job_mgr_thread_candidate`

### Queue `8`: Video / Deferred Work

Known produced IDs:

- `0x0b`

Producer:

- `hp1020_video_reset_dispatch_candidate`

Likely consumer:

- video queue path, but this needs one more pass because queue `8` is less directly obvious than queues `0`, `1`, `3`, `10`, and `0x0f`.

### Queue `10`: Status Manager

Known produced IDs:

- `0x2c`
- `0x2e`
- `0x30`
- `0x31`

Consumer:

- `hp1020_status_mgr_thread_candidate`

### Queue `0x0f`: Delay Manager

Known produced IDs:

- `0x44`

Consumer:

- `hp1020_delay_mgr_receive_thread_candidate`

## Current State

This gives us a usable firmware-internal routing model:

```text
JobMgr -> PrintMgr / Engine / StatusMgr
PrintMgr -> Print/job dispatch
Video -> Engine
Engine -> Engine/status events
StatusMgr -> PJL-visible status builders
DelayMgr -> timed callbacks back into engine/status queues
```

The next narrow target is queue `8`, because it is the least resolved active queue in the print/video path.

## Queue Worker Note

The descriptor/function pointer near `0x100066f4` points at `0x100136d8`. A forced decompile shows this is not the queue table initializer. It is another queue-consuming worker that waits on `PTR_DAT_100066f8` and handles messages `0x40`, `0x41`, and `0x11`.

Nearby rodata includes the string/table region:

- `0x10005408`: `tx_queue_send() failed, MSG LOST !!`
- `0x10005434`: `Cal`
- `0x10005440`: switch-table-looking entries for code around `0x100136d8`

Working label:

- `0x100136d8` `hp1020_calibration_control_queue_worker_candidate`
