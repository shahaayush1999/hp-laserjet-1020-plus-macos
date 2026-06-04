# HP 1020 Status And PJL Fault Path

This report maps PJL-visible status/fault strings, the status command table,
and the functions that bridge firmware state into status responses.

## Status Command Table

- Table pointer word: `10006148`
- Table base: `10003c8c`
- Entry size: `0x24` bytes

| Index | Entry | Kind | Name Pointer | Name | Words |
|---:|---:|---:|---:|---|---|
| `0` | `10003c8c` | `0x0` | `0x10004064` | `AUTOCONT` | `0x0 0x10004064 0x2 0x0 0x2 0x2 0x0 0x0 0x10003a70` |
| `1` | `10003cb0` | `0x1` | `0x1000405c` | `TIMEOUT` | `0x1 0x1000405c 0x3 0x0 0x0 0x6 0x5 0xff 0x0` |
| `2` | `10003cd4` | `0x2` | `0x10004054` | `DENSITY` | `0x2 0x10004054 0x3 0x0 0x0 0x6 0x1 0x5 0x0` |
| `3` | `10003cf8` | `0x4` | `0x10004048` | `SERVICEID` | `0x4 0x10004048 0x3 0x0 0x0 0x6 0x0 0x98967f 0x0` |
| `4` | `10003d1c` | `0x5` | `0x1000403c` | `JAMRECOVERY` | `0x5 0x1000403c 0x2 0x0 0x2 0x2 0x0 0x0 0x10003b8c` |
| `5` | `10003d40` | `0x6` | `0x1000402c` | `TRANSFERMODE` | `0x6 0x1000402c 0x2 0x0 0x2 0x2 0x0 0x0 0x10003b9c` |
| `6` | `10003d64` | `0x7` | `0x10004020` | `MEDIA512` | `0x7 0x10004020 0x3 0x0 0xa 0x6 0x0 0x0 0x10003bb4` |
| `7` | `10003d88` | `0x8` | `0x10004014` | `MEDIA513` | `0x8 0x10004014 0x3 0x0 0xa 0x6 0x0 0x0 0x10003bb4` |
| `8` | `10003dac` | `0x9` | `0x10004008` | `MEDIA514` | `0x9 0x10004008 0x3 0x0 0xa 0x6 0x0 0x0 0x10003bb4` |
| `9` | `10003dd0` | `0xa` | `0x10003ffc` | `MEDIA515` | `0xa 0x10003ffc 0x3 0x0 0xa 0x6 0x0 0x0 0x10003bb4` |
| `10` | `10003df4` | `0xb` | `0x10003ff0` | `MEDIA516` | `0xb 0x10003ff0 0x3 0x0 0xa 0x6 0x0 0x0 0x10003bb4` |
| `11` | `10003e18` | `0xc` | `0x10003fe4` | `PQENHANCE` | `0xc 0x10003fe4 0x3 0x0 0x0 0x6 0x0 0xff 0x0` |
| `12` | `10003e3c` | `0xd` | `0x10003fd8` | `TONEREXP` | `0xd 0x10003fd8 0x3 0x0 0x0 0x6 0x0 0x5 0x0` |
| `13` | `10003e60` | `0xe` | `0x10003fcc` | `LINEAUGMENT` | `0xe 0x10003fcc 0x3 0x0 0x0 0x6 0x0 0x5 0x0` |
| `14` | `10003e84` | `0xf` | `0x10003fc0` | `SETMEMORY` | `0xf 0x10003fc0 0x3 0x0 0x0 0x6 0x0 0x1000000 0x0` |
| `15` | `10003ea8` | `0x10` | `0x10003fb4` | `SETERROR` | `0x10 0x10003fb4 0x3 0x0 0x0 0x6 0x0 0xffffffff 0x0` |
| `16` | `10003ecc` | `0x3` | `0x10003fa8` | `PAPERLESS` | `0x3 0x10003fa8 0x2 0x0 0x2 0x2 0x0 0x0 0x10003b24` |
| `17` | `10003ef0` | `0x11` | `0x10003f9c` | `FLASHSYS` | `0x11 0x10003f9c 0x2 0x0 0x1 0x2 0x0 0x0 0x10003c2c` |
| `18` | `10003f14` | `0x12` | `0x10003f94` | `FUSER` | `0x12 0x10003f94 0x2 0x0 0x1 0x2 0x0 0x0 0x10003c44` |
| `19` | `10003f38` | `0x13` | `0x10003f88` | `ASCIIHEX` | `0x13 0x10003f88 0x4 0x0 0x2 0x2 0x0 0x0 0x10003c4c` |
| `20` | `10003f5c` | `0x14` | `0x10003f80` | `XXXXXX` | `0x14 0x10003f80 0x2 0x0 0x0 0x6 0x0 0x0 0x0` |

## Status/Fault Strings

| Address | String | Direct Refs | Pointer Refs |
|---:|---|---|---|
| `10003f94` | `FUSER` |  | `10003f18` |
| `10003fa8` | `PAPERLESS` |  | `10003ed0` |
| `10003fb4` | `SETERROR` |  | `10003eac` |
| `10003fd8` | `TONEREXP` |  | `10003e40` |
| `1000403c` | `JAMRECOVERY` |  | `10003d20` |
| `10004098` | `USTATUS` | `100060e0`<br>`1001beac` | `100060e0`<br>`1001beac` |
| `10004138` | `PARSEERROR` | `1000b4a8`<br>`10006118` | `10006118` |
| `10004144` | `CANCELED` | `1000b4a8`<br>`1000611c` | `1000611c` |
| `10004158` | `USER_CANCELED` | `10006124` | `10006124` |
| `10004168` | `CODE=` | `1000b630`<br>`1000b638`<br>`1000b642`<br>`10006128` | `10006128` |
| `10004170` | `DISPLAY="` | `1000b668`<br>`1000b672`<br>`1000612c` | `1000612c` |
| `10004350` | `USTATUS [4 ENUMERATED]` | `1000bf04`<br>`100061ec` | `100061ec` |
| `100045c8` | `USTATUSOFF` | `10004590` | `10004590` |
| `100045d4` | `USTATUS` | `10004588` | `10004588` |
| `10004710` | `DISPLAY` |  | `10004674` |

## Related Functions

- `1000a2a4` `hp1020_status_word_to_pjl_code_candidate`
- `1000b1d4` `FUN_1000b1d4`
- `1000b2a8` `hp1020_pjl_status_notify_builder_candidate`
- `1000b344` `FUN_1000b344`
- `1000b3f8` `hp1020_pjl_ustatus_result_builder`
- `1000b520` `hp1020_pjl_ustatus_cancel_builder_candidate`
- `1000b624` `FUN_1000b624`
- `1000b6d8` `FUN_1000b6d8`
- `1000b774` `FUN_1000b774`
- `1000b870` `hp1020_pjl_status_table_get_candidate`
- `1000bd04` `hp1020_pjl_info_capabilities_builder`
- `1000c8fc` `hp1020_pjl_status_table_set_candidate`
- `1000cd44` `hp1020_pjl_response_send_candidate`
- `1000d2a8` `hp1020_pjl_command_dispatch_candidate`
- `10010590` `hp1020_status_mgr_thread_candidate`
- `10010838` `hp1020_status_state_update_candidate`
- `10010a3c` `hp1020_status_notify_pending_candidate`
- `10010a8c` `hp1020_status_event_store_candidate`
- `10010f54` `hp1020_event_flag_get_candidate`
- `10010fd0` `hp1020_event_flag_set_candidate`
- `10011178` `hp1020_get_config_value_candidate`
- `10015c68` `hp1020_engine_status_io_candidate`
- `10015df8` `hp1020_engine_status_poll_candidate`
- `100160a8` `hp1020_engine_preflight_candidate`

## Current Interpretation

- The visible words `FUSER`, `PAPERLESS`, `TONEREXP`, and `JAMRECOVERY` are PJL/status table names, not direct engine event-code names.
- `hp1020_pjl_status_table_set_candidate` walks the table and updates event/config slots based on the matched string name.
- `hp1020_pjl_status_table_get_candidate` reads the same table and converts rows into stored status/config values.
- `hp1020_status_mgr_thread_candidate` consumes `StatusMgrQueue` messages and calls USTATUS/result builders after state transitions.
- `hp1020_status_state_update_candidate` is the current bridge between numeric firmware state words and StatusMgr/PJL-visible notifications.
- `hp1020_status_word_to_pjl_code_candidate` converts an internal status word into the numeric PJL `CODE=` value used by USTATUS DEVICE messages.
- The next useful connection is to name the bit masks used by `hp1020_status_state_update_candidate` and the engine poller, then map those masks to the table rows above.
