# HP 1020 RTOS Object Creation Map

This pass scans system-interface functions around queue/thread creation and validation.

## Object Magic Values

| Magic | Hex | Meaning |
|---|---:|---|
| `SEMA` | `0x53454d41` | semaphore |
| `MUTE` | `0x4d555445` | mutex |
| `QUEU` | `0x51554555` | queue |
| `BLOC` | `0x424c4f43` | block pool |
| `BYTE` | `0x42595445` | byte pool |
| `THRD` | `0x54485244` | thread |

## Target Function Scan

| Function | Calls | Object magic refs | Notes |
|---:|---|---|---|
| `0x10017ca0` `FUN_10017ca0` | `0x10019308` `FUN_10019308` |  |  |
| `0x10017cf0` `hp1020_object_target_10017cf0` | `0x10019350` `FUN_10019350` |  |  |
| `0x10017d28` `FUN_10017d28` | `0x10019408` `FUN_10019408` |  |  |
| `0x10017d74` `hp1020_object_target_10017d74` | `0x1001b8c8` `FUN_1001b8c8` |  |  |
| `0x10017dac` `FUN_10017dac` | `0x1001896c` `FUN_1001896c` |  |  |
| `0x10017dd8` `hp1020_object_target_10017dd8` | `0x10019538` `FUN_10019538` | MUTE | mutex object path |
| `0x10017e2c` `hp1020_object_target_10017e2c` | `0x10019580` `FUN_10019580` | MUTE | mutex object path |
| `0x10017e64` `FUN_10017e64` | `0x10019634` `FUN_10019634` | MUTE | mutex object path |
| `0x10017e9c` `hp1020_object_target_10017e9c` | `0x1001b8ec` `FUN_1001b8ec` | MUTE | mutex object path |
| `0x10017ed8` `FUN_10017ed8` | `0x10019708` `FUN_10019708` | MUTE | mutex object path |
| `0x10017ef8` `hp1020_object_target_10017ef8` | `0x1001b918` `FUN_1001b918` | MUTE | mutex object path |
| `0x10017f18` `threadx_queue_create_candidate` | `0x100199a4` `threadx_queue_create_core_candidate` | QUEU | queue object path |
| `0x10017f90` `threadx_queue_delete_candidate` | `0x10019a30` `threadx_queue_delete_core_candidate` | QUEU | queue object path |
| `0x10017fc8` `hp1020_object_target_10017fc8` | `0x10019ae8` `FUN_10019ae8` | QUEU | queue object path |
| `0x10018000` `hp1020_object_target_10018000` | `0x10019b7c` `FUN_10019b7c` | QUEU | queue object path |
| `0x10018040` `hp1020_object_target_10018040` | `0x1001b98c` `FUN_1001b98c` | QUEU | queue object path |
| `0x1001807c` `hp1020_object_target_1001807c` | `0x1001b9b8` `FUN_1001b9b8` | QUEU | queue object path |
| `0x1001809c` `threadx_queue_receive_wait_candidate` | `0x10019eb4` `threadx_queue_receive_core_candidate` | QUEU | queue object path |
| `0x100180dc` `threadx_queue_send_candidate` | `0x1001a130` `threadx_queue_send_core_candidate` | QUEU | queue object path |
| `0x1001811c` `hp1020_object_target_1001811c` | `0x1001a380` `FUN_1001a380` | SEMA | semaphore object path |
| `0x1001816c` `hp1020_object_target_1001816c` | `0x1001a3c4` `FUN_1001a3c4` | SEMA | semaphore object path |
| `0x100181a4` `FUN_100181a4` | `0x1001a478` `FUN_1001a478` | SEMA | semaphore object path |
| `0x100181dc` `hp1020_object_target_100181dc` | `0x1001ba2c` `FUN_1001ba2c` | SEMA | semaphore object path |
| `0x10018214` `FUN_10018214` | `0x1001a508` `FUN_1001a508` | SEMA | semaphore object path |
| `0x10018234` `hp1020_object_target_10018234` | `0x1001ba50` `FUN_1001ba50` | SEMA | semaphore object path |
| `0x10018254` `hp1020_object_target_10018254` | `0x1001a5f4` `FUN_1001a5f4` |  |  |
| `0x10018274` `threadx_thread_create_candidate` | `0x1001a610` `threadx_thread_create_core_candidate` | THRD | thread object path |
| `0x100199a4` `threadx_queue_create_core_candidate` |  | QUEU | queue object path |
| `0x10019a30` `threadx_queue_delete_core_candidate` | `0x1001bac4` `FUN_1001bac4`<br>`0x1001aac0` `rtos_thread_ready_insert_candidate`<br>`0x10018750` `FUN_10018750` |  |  |
| `0x10019ae8` `FUN_10019ae8` | `0x1001bac4` `FUN_1001bac4`<br>`0x1001aac0` `rtos_thread_ready_insert_candidate`<br>`0x10018750` `FUN_10018750` |  |  |
| `0x10019b7c` `FUN_10019b7c` | `0x1001a590` `rtos_timer_insert_candidate`<br>`0x100176c8` `rtos_schedule_candidate`<br>`0x1001bac4` `FUN_1001bac4`<br>`0x1001aac0` `rtos_thread_ready_insert_candidate`<br>`0x10018750` `FUN_10018750` |  |  |
| `0x1001a610` `threadx_thread_create_core_candidate` |  |  |  |
| `0x1001b98c` `FUN_1001b98c` |  |  |  |
| `0x1001b9b8` `FUN_1001b9b8` |  |  |  |

## Current Read

- Queue receive/send wrappers at `0x1001809c` and `0x100180dc` validate `QUEU` and delegate to lower queue cores.
- Thread create wrapper at `0x10018274` rejects objects already marked `THRD` and delegates to `0x1001a610`.
- The next important proof is identifying which nearby wrapper initializes `QUEU`; this pass narrows that search to the system-interface group around `0x10017f18`-`0x1001816c`.
- Queue `8` should become resolvable once queue creation calls are tied back to descriptor blocks and the runtime table at `0x1002c918`.
