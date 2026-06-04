# HP 1020 Queue Send Census

This pass decompiles every recovered function and extracts calls to the firmware queue-send wrappers.

## Main Result

- total queue-send call sites found: `55`
- direct static sends of message `0x2d` to queue `0` / PrintMgrQueue: `0`
- data-store writer `0x10010fd0` still emits message `0x2d` through subscriber-selected queue ids: `1` matching site(s)
- No direct constant `queue 0, message 0x2d` producer was found by this pass.

## Queue 0 / PrintMgr Constant Sends

| Function | Line | Message | Confidence | Call |
|---|---:|---:|---|---|
| `1000f324` `hp1020_print_mgr_thread_candidate` | 14 | `0x18` | medium_payload_history | `hp1020_queue_send_candidate(0,aiStack_50);` |
| `1000f574` `hp1020_print_mgr_schedule_or_advance_candidate` | 104 | `0xd` | high_direct_wrapper | `hp1020_queue_send_message4_candidate(0,0xd,0,0,uVar10);` |
| `1000f574` `hp1020_print_mgr_schedule_or_advance_candidate` | 121 | `0xb` | high_direct_wrapper | `hp1020_queue_send_message4_candidate(0,0xb,0,0,uVar10);` |
| `100100a8` `hp1020_print_mgr_status_aux_candidate` | 17 | `0x1a` | high_direct_wrapper | `hp1020_queue_send_message4_candidate(0,0x1a,0,0);` |
| `10010230` `hp1020_print_mgr_idle_or_restart_candidate` | 18 | `0x4a` | high_direct_wrapper | `hp1020_queue_send_message4_candidate(0,0x4a,0,0);` |
| `10010230` `hp1020_print_mgr_idle_or_restart_candidate` | 26 | `0x18` | high_direct_wrapper | `hp1020_queue_send_message4_candidate(0,0x18,0,0);` |
| `10013d4c` `hp1020_video_reset_dispatch_candidate` | 87 | `0x11` | medium_payload_history | `hp1020_send_or_raise_engine_msg_candidate(0,&local_30);` |
| `10016164` `hp1020_engine_message_dispatch_candidate` | 45 | `0xb` | medium_payload_history | `hp1020_send_or_raise_engine_msg_candidate(0,&local_40);` |

## Message 0x2d Sites

| Function | Line | Queue | Confidence | Call |
|---|---:|---|---|---|
| `10010fd0` `hp1020_datastore_write_notify_unlock_candidate` | 92 | `(uint)*(byte *)((int)piVar3 + -5) \| (uint)*(byte *)((int)piVar3 + -6) << 8 \| (uint)*(byte *)((int)piVar3 + -7) << 0x10 \| (uint)*(byte *)(piVar3 + -2) << 0x18` `dynamic` | low_dynamic_queue_known_message | `hp1020_queue_send_candidate ((uint)*(byte *)((int)piVar3 + -5) \| (uint)*(byte *)((int)piVar3 + -6) << 8 \| (uint)*(byte *)((int)piVar3 + -7) << 0x10 \| (uint)*(byte *)(piVar3 + -2) << 0x18,&local_30);` |

## Notes

- `high_direct_wrapper` means the small 4-word wrapper carries the queue and message constants directly in its arguments.
- `medium_payload_history` means the raw queue-send call used a local payload variable whose first word was assigned nearby.
- `unknown` means the send uses a dynamic payload or the assignment is outside the small local history window.
- This is a static pass, so dynamic branch conditions and computed queue ids still need manual follow-up.
