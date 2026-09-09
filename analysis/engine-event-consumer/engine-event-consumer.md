# HP 1020 Engine Event Consumer Scan

This pass scans for engine queue/event evidence that the normal decompile did not fully resolve.

## Key Result

- `engMsgQ` object pointer word: `0x100069bc` -> object `0x1002f134`.
- The only direct `engMsgQ` receive found in this pass is the engine thread at `0x100163b0`.
- The recovered engine dispatch switch at `0x10016164` still has no visible `0x17` case.
- `0x17` producers are confirmed through status I/O, status poll, preflight, and video reset paths.
- Generic queue-helper users were filtered out unless they also touch engine/event evidence.

## Functions With Relevant Hits

| Function | Reasons |
|---:|---|
| `10007468` `FUN_10007468` | `literal_0x17` |
| `1000e1dc` `FUN_1000e1dc` | `literal_0x17` |
| `10010230` `FUN_10010230` | `literal_0x17` |
| `10010fd0` `FUN_10010fd0` | `call_hp1020_queue_send_candidate`, `ref_hp1020_event_handler_table_ptr_word`, `ref_hp1020_queue_send_candidate` |
| `10011258` `FUN_10011258` | `ref_hp1020_event_handler_table_ptr_word` |
| `1001135c` `FUN_1001135c` | `ref_hp1020_event_handler_table_ptr_word` |
| `10013d4c` `hp1020_video_reset_dispatch_candidate` | `call_hp1020_send_or_raise_engine_msg_candidate`, `literal_0x17`, `ref_hp1020_send_or_raise_engine_msg_candidate` |
| `10015c68` `hp1020_engine_status_io_candidate` | `call_FUN_10017d28`, `call_hp1020_queue_send_candidate`, `literal_0x17`, `ref_hp1020_queue_send_candidate` |
| `10015df8` `hp1020_engine_status_poll_candidate` | `call_hp1020_engine_status_io_candidate`, `call_hp1020_queue_send_candidate`, `call_hp1020_video_reset_dispatch_candidate`, `literal_0x17`, `ref_hp1020_engine_status_io_candidate`, `ref_hp1020_queue_send_candidate`, `ref_hp1020_video_reset_dispatch_candidate` |
| `100160a8` `hp1020_engine_preflight_candidate` | `call_hp1020_engine_event_0x0f_config_callback_candidate`, `call_hp1020_queue_send_candidate`, `literal_0x17`, `ref_hp1020_engine_event_0x0f_config_callback_candidate`, `ref_hp1020_queue_send_candidate` |
| `10016164` `hp1020_engine_message_dispatch_candidate` | `call_hp1020_engine_preflight_candidate`, `call_hp1020_engine_status_io_candidate`, `call_hp1020_engine_status_poll_candidate`, `call_hp1020_queue_send_candidate`, `call_hp1020_send_or_raise_engine_msg_candidate`, `call_threadx_queue_send_candidate`, `ref_hp1020_engine_preflight_candidate`, `ref_hp1020_engine_status_io_candidate`, ... |
| `10016318` `hp1020_engine_event_0x0f_config_callback_candidate` | `` |
| `1001a5f4` `FUN_1001a5f4` | `literal_0x17` |

## Instruction Evidence


### `10007468` `FUN_10007468`

- `100074c9` `movi.n` `movi.n a4,0x17` -> `literal_0x17`

### `1000e1dc` `FUN_1000e1dc`

- `1000e265` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `1000e280` `movi` `movi a2,0x17` -> `literal_0x17`
- `1000e34b` `movi.n` `movi.n a2,0x17` -> `literal_0x17`
- `1000e387` `movi.n` `movi.n a2,0x17` -> `literal_0x17`

### `10010230` `FUN_10010230`

- `10010235` `movi.n` `movi.n a8,0x17` -> `literal_0x17`

### `10010fd0` `FUN_10010fd0`

- `100110d6` `l32r` `l32r a8,0x10006490` -> `ref_hp1020_event_handler_table_ptr_word`
- `10011100` `l32r` `l32r a8,0x10006490` -> `ref_hp1020_event_handler_table_ptr_word`
- `1001115e` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `1001115e` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`

### `10011258` `FUN_10011258`

- `100112a6` `l32r` `l32r a8,0x10006490` -> `ref_hp1020_event_handler_table_ptr_word`

### `1001135c` `FUN_1001135c`

- `100113b8` `l32r` `l32r a8,0x10006490` -> `ref_hp1020_event_handler_table_ptr_word`

### `10013d4c` `hp1020_video_reset_dispatch_candidate`

- `10013ea8` `call8` `call8 0x10013620` -> `ref_hp1020_send_or_raise_engine_msg_candidate`
- `10013ea8` `call8` `call8 0x10013620` -> `call_hp1020_send_or_raise_engine_msg_candidate`
- `10013ec4` `call8` `call8 0x10013620` -> `ref_hp1020_send_or_raise_engine_msg_candidate`
- `10013ec4` `call8` `call8 0x10013620` -> `call_hp1020_send_or_raise_engine_msg_candidate`
- `10013ee4` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10013ef0` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10013efc` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10013f08` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10013f14` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10013f24` `call8` `call8 0x10013620` -> `ref_hp1020_send_or_raise_engine_msg_candidate`
- `10013f24` `call8` `call8 0x10013620` -> `call_hp1020_send_or_raise_engine_msg_candidate`

### `10015c68` `hp1020_engine_status_io_candidate`

- `10015cd4` `call8` `call8 0x10017d28` -> `call_FUN_10017d28`
- `10015cef` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10015d04` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `10015d04` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`

### `10015df8` `hp1020_engine_status_poll_candidate`

- `10015e09` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015e09` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015e29` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015e29` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015e43` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015e43` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015e49` `bbci` `bbci a7,0x17,0x10015e79` -> `literal_0x17`
- `10015e4e` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015e4e` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015e73` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015e73` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015e82` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015e82` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015eb5` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015eb5` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015eca` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015eca` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015f40` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10015f55` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `10015f55` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `10015f70` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10015f70` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `10015f90` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `10015fa4` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `10015fa4` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `10015fc8` `call8` `call8 0x10013d4c` -> `ref_hp1020_video_reset_dispatch_candidate`
- `10015fc8` `call8` `call8 0x10013d4c` -> `call_hp1020_video_reset_dispatch_candidate`

### `100160a8` `hp1020_engine_preflight_candidate`

- `100160ad` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `100160c1` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `100160c1` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `100160f9` `movi.n` `movi.n a8,0x17` -> `literal_0x17`
- `1001610e` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `1001610e` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `1001615a` `call8` `call8 0x10016318` -> `ref_hp1020_engine_event_0x0f_config_callback_candidate`
- `1001615a` `call8` `call8 0x10016318` -> `call_hp1020_engine_event_0x0f_config_callback_candidate`

### `10016164` `hp1020_engine_message_dispatch_candidate`

- `1001619e` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `1001619e` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `100161b4` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `100161b4` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `100161bd` `call8` `call8 0x10015df8` -> `ref_hp1020_engine_status_poll_candidate`
- `100161bd` `call8` `call8 0x10015df8` -> `call_hp1020_engine_status_poll_candidate`
- `100161e4` `call8` `call8 0x100180dc` -> `ref_threadx_queue_send_candidate`
- `100161e4` `call8` `call8 0x100180dc` -> `call_threadx_queue_send_candidate`
- `100161fe` `call8` `call8 0x10013620` -> `ref_hp1020_send_or_raise_engine_msg_candidate`
- `100161fe` `call8` `call8 0x10013620` -> `call_hp1020_send_or_raise_engine_msg_candidate`
- `1001620d` `call8` `call8 0x100160a8` -> `ref_hp1020_engine_preflight_candidate`
- `1001620d` `call8` `call8 0x100160a8` -> `call_hp1020_engine_preflight_candidate`
- `10016212` `call8` `call8 0x10015df8` -> `ref_hp1020_engine_status_poll_candidate`
- `10016212` `call8` `call8 0x10015df8` -> `call_hp1020_engine_status_poll_candidate`
- `10016229` `call8` `call8 0x10013658` -> `ref_hp1020_queue_send_candidate`
- `10016229` `call8` `call8 0x10013658` -> `call_hp1020_queue_send_candidate`
- `10016232` `call8` `call8 0x10015df8` -> `ref_hp1020_engine_status_poll_candidate`
- `10016232` `call8` `call8 0x10015df8` -> `call_hp1020_engine_status_poll_candidate`
- `10016249` `call8` `call8 0x10015df8` -> `ref_hp1020_engine_status_poll_candidate`
- `10016249` `call8` `call8 0x10015df8` -> `call_hp1020_engine_status_poll_candidate`
- `10016293` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `10016293` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`
- `100162a7` `call8` `call8 0x10015c68` -> `ref_hp1020_engine_status_io_candidate`
- `100162a7` `call8` `call8 0x10015c68` -> `call_hp1020_engine_status_io_candidate`

### `10016318` `hp1020_engine_event_0x0f_config_callback_candidate`


### `1001a5f4` `FUN_1001a5f4`

- `1001a600` `movi.n` `movi.n a2,0x17` -> `literal_0x17`

## Interpretation

Constructor registration proves queue 1 is PrintMgr and queue 0 is engine. The queue-1 0x17 producers reach PrintMgr target 0x1000f4c2; the older missing-engine-consumer conclusion was a routing error.
See `analysis/queue-routing/registration.md`. The engine default case remains correct for queue 0, but does not describe those queue-1 events.
