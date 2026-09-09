# HP 1020 Queue Send Census

This pass decompiles every recovered function and extracts calls to the firmware queue-send wrappers.

## Main Result

- total queue-send call sites found: `54`
- direct static sends of message `0x2d` to queue `1` / PrintMgrQueue: `0`
- data-store writer `0x10010fd0` still emits message `0x2d` through subscriber-selected queue ids: `1` matching site(s)
- Datastore notifications select queue 1 through registered subscribers; lack of a direct constant send does not imply an absent PrintMgr producer.

## Queue 1 / PrintMgr Constant Sends

| Function | Line | Message | Confidence | Call |
|---|---:|---:|---|---|
| `1000e414` `hp1020_job_mgr_thread_candidate` | 227 | `0xf` | medium_payload_history | `hp1020_queue_send_candidate(1,&uStack_90);` |
| `1000e414` `hp1020_job_mgr_thread_candidate` | 354 | `0xb` | medium_payload_history | `hp1020_queue_send_candidate(1,&uStack_90);` |
| `1000ed90` `FUN_1000ed90` | 40 | `0xb` | medium_payload_history | `hp1020_queue_send_candidate(1,local_30);` |
| `1000ed90` `FUN_1000ed90` | 58 | `0xb` | medium_payload_history | `hp1020_queue_send_candidate(1,local_30);` |
| `10013c18` `hp1020_video_thread_candidate` | 69 | `0x10` | medium_payload_history | `hp1020_queue_send_candidate(1,aiStack_30);` |
| `10013d4c` `hp1020_video_reset_dispatch_candidate` | 121 | `0x17` | medium_payload_history | `hp1020_send_or_raise_engine_msg_candidate(1,&local_30);` |
| `10015c68` `hp1020_engine_status_io_candidate` | 56 | `0x17` | medium_payload_history | `hp1020_queue_send_candidate(1,&uStack_30);` |
| `10015df8` `hp1020_engine_status_poll_candidate` | 101 | `0x17` | medium_payload_history | `hp1020_queue_send_candidate(1,&local_40);` |
| `10015df8` `hp1020_engine_status_poll_candidate` | 116 | `0x17` | medium_payload_history | `hp1020_queue_send_candidate(1,&local_40);` |
| `100160a8` `hp1020_engine_preflight_candidate` | 24 | `0x17` | medium_payload_history | `hp1020_queue_send_candidate(1,&local_40);` |
| `100160a8` `hp1020_engine_preflight_candidate` | 57 | `0x17` | medium_payload_history | `hp1020_queue_send_candidate(1,&uStack_30);` |
| `10016164` `hp1020_engine_message_dispatch_candidate` | 19 | `unknown` | low_known_queue_unknown_message | `hp1020_queue_send_candidate(1,param_1);` |
| `10016164` `hp1020_engine_message_dispatch_candidate` | 27 | `0x25` | medium_payload_history | `hp1020_queue_send_candidate(1,&local_40);` |
| `10016164` `hp1020_engine_message_dispatch_candidate` | 54 | `0x16` | medium_payload_history | `hp1020_queue_send_candidate(1,&uStack_30);` |
| `1001635c` `hp1020_engine_delay_thread_candidate` | 16 | `unknown` | low_known_queue_unknown_message | `hp1020_send_or_raise_engine_msg_candidate(1,aiStack_30);` |
| `100163b0` `hp1020_engine_thread_candidate` | 37 | `0x16` | medium_payload_history | `hp1020_queue_send_candidate(1,&uStack_30);` |

## Message 0x2d Sites

| Function | Line | Queue | Confidence | Call |
|---|---:|---|---|---|
| `10010fd0` `hp1020_datastore_write_notify_unlock_candidate` | 92 | `(uint)*(byte *)((int)piVar3 + -5) \| (uint)*(byte *)((int)piVar3 + -6) << 8 \| (uint)*(byte *)((int)piVar3 + -7) << 0x10 \| (uint)*(byte *)(piVar3 + -2) << 0x18` `dynamic` | low_dynamic_queue_known_message | `hp1020_queue_send_candidate ((uint)*(byte *)((int)piVar3 + -5) \| (uint)*(byte *)((int)piVar3 + -6) << 8 \| (uint)*(byte *)((int)piVar3 + -7) << 0x10 \| (uint)*(byte *)(piVar3 + -2) << 0x18,&local_30);` |

## Notes

- `high_direct_wrapper` means the small 4-word wrapper carries the queue and message constants directly in its arguments.
- `medium_payload_history` means the raw queue-send call used a local payload variable whose first word was assigned nearby.
- `unknown` means the send uses a dynamic payload or the assignment is outside the small local history window.
- This is a static pass, so dynamic branch conditions and computed queue ids still need manual follow-up.
