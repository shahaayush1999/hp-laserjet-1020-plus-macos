# HP 1020 USB/Download Path Map

Seed handlers:
- `10008ff0` `hp1020_usb2_thread`
- `10009934` `hp1020_usb2_idle_thread`
- `1000ad44` `hp1020_acl_download`
- `1000cdb0` `hp1020_pjl_echo_matcher`
- internal labels `10009476` ... `100096e5` USB `GET_DESCRIPTOR` jump-table blocks

## USB2Thread

Entry: `10008ff0` `hp1020_usb2_thread`

Direct callees:
- `10007c00` `hp1020_usb_register_transfer_candidate` score=25
- `10007c70` `FUN_10007c70` score=2
- `10008c24` `hp1020_usb_control_tx_data_stage_candidate` score=222
- `10008fb0` `hp1020_usb_drain_pending_queue_candidate` score=11
- `10009ac4` `FUN_10009ac4` score=2
- `10011178` `hp1020_datastore_get_value_candidate` score=16
- `1001214c` `FUN_1001214c` score=1
- `10013658` `FUN_10013658` score=1
- `100169d4` `hp1020_strlen_like` score=4
- `1001716c` `FUN_1001716c` score=0
- `10017184` `FUN_10017184` score=0
- `10017d28` `threadx_queue_receive_candidate` score=15
- `10018274` `threadx_thread_create_candidate` score=25
Direct callers:
- none found

Global/pointer symbols seen in decompiler output:
- `DAT_10005e24` count=7
- `DAT_10005e70` count=6
- `DAT_10005eac` count=5
- `DAT_10005e34` count=3
- `DAT_10005ed8` count=3
- `PTR_DAT_10005e50` count=3
- `PTR_DAT_10005ee8` count=3
- `PTR_DAT_10005eec` count=3
- `DAT_10005e30` count=2
- `DAT_10005e88` count=2
- `DAT_10005e90` count=2
- `DAT_10005ea8` count=2
- `DAT_10005edc` count=2
- `DAT_10005ef4` count=2
- `DAT_10005ef8` count=2
- `DAT_10005f74` count=2
- `DAT_10005f80` count=2
- `DAT_10005f8c` count=2
- `PTR_DAT_10005e1c` count=2
- `PTR_DAT_10005e98` count=2

## USB2IdleThread

Entry: `10009934` `hp1020_usb2_idle_thread`

Direct callees:
- none found
Direct callers:
- none found

Global/pointer symbols seen in decompiler output:
- none found

## agiACLDownload

Entry: `1000ad44` `hp1020_acl_download`

Direct callees:
- none found
Direct callers:
- none found

Global/pointer symbols seen in decompiler output:
- `DAT_10005e70` count=2
- `DAT_10005e24` count=1
- `PTR_DAT_10006068` count=1

## @PJL ECHO matcher

Entry: `1000cdb0` `hp1020_pjl_echo_matcher`

Direct callees:
- `1000d6b0` `hp1020_pjl_read_or_poll_candidate` score=26
- `100169d4` `hp1020_strlen_like` score=4
Direct callers:
- `1000d2a8` `FUN_1000d2a8` score=38

Global/pointer symbols seen in decompiler output:
- `PTR_DAT_1000626c` count=1
- `PTR_DAT_10006270` count=1

## Focus Function List

- `10007c00` `hp1020_usb_register_transfer_candidate` score=25
- `10007c70` `FUN_10007c70` score=2
- `10008034` `FUN_10008034` score=2
- `10008c24` `hp1020_usb_control_tx_data_stage_candidate` score=222
- `10008fb0` `hp1020_usb_drain_pending_queue_candidate` score=11
- `10008ff0` `hp1020_usb2_thread` score=564
- `10009934` `hp1020_usb2_idle_thread` score=2
- `10009ac4` `FUN_10009ac4` score=2
- `1000ad44` `hp1020_acl_download` score=27
- `1000cdb0` `hp1020_pjl_echo_matcher` score=12
- `1000d2a8` `FUN_1000d2a8` score=38
- `1000d6b0` `hp1020_pjl_read_or_poll_candidate` score=26
- `10011178` `hp1020_datastore_get_value_candidate` score=16
- `1001214c` `FUN_1001214c` score=1
- `1001215c` `FUN_1001215c` score=5
- `10013050` `FUN_10013050` score=1
- `100130bc` `FUN_100130bc` score=0
- `10013408` `FUN_10013408` score=18
- `10013658` `FUN_10013658` score=1
- `10013668` `FUN_10013668` score=3
- `100169d4` `hp1020_strlen_like` score=4
- `1001716c` `FUN_1001716c` score=0
- `10017184` `FUN_10017184` score=0
- `100171b0` `FUN_100171b0` score=0
- `100173c8` `FUN_100173c8` score=0
- `10017d28` `threadx_queue_receive_candidate` score=15
- `10018274` `threadx_thread_create_candidate` score=25
- `10019408` `FUN_10019408` score=10
- `1001a610` `FUN_1001a610` score=0
- `1001b38c` `FUN_1001b38c` score=0

## Register-Like Global Candidates

- `DAT_10005e24` count=8
- `DAT_10005e70` count=8
- `PTR_DAT_10005e1c` count=8
- `PTR_DAT_10006270` count=8
- `DAT_10005e90` count=5
- `DAT_10005eac` count=5
- `PTR_DAT_1000626c` count=5
- `PTR_DAT_10005e98` count=4
- `PTR_DAT_1000647c` count=4
- `PTR_DAT_10006a9c` count=4
- `DAT_10005e34` count=3
- `DAT_10005e80` count=3
- `DAT_10005ea0` count=3
- `DAT_10005ed8` count=3
- `DAT_10005f74` count=3
- `DAT_100066ac` count=3
- `PTR_DAT_10005d80` count=3
- `PTR_DAT_10005e18` count=3
- `PTR_DAT_10005e50` count=3
- `PTR_DAT_10005ee8` count=3
- `PTR_DAT_10005eec` count=3
- `DAT_10005e30` count=2
- `DAT_10005e88` count=2
- `DAT_10005e9c` count=2
- `DAT_10005ea8` count=2
- `DAT_10005edc` count=2
- `DAT_10005ef4` count=2
- `DAT_10005ef8` count=2
- `DAT_10005f80` count=2
- `DAT_10005f8c` count=2
- `PTR_DAT_10005d98` count=2
- `PTR_DAT_10005d9c` count=2
- `PTR_DAT_10005da0` count=2
- `PTR_DAT_10005e10` count=2
- `PTR_DAT_10005e94` count=2
- `PTR_DAT_10006298` count=2
- `PTR_DAT_10006ae8` count=2
- `DAT_10005c84` count=1
- `DAT_10005c88` count=1
- `DAT_10005da8` count=1
- `DAT_10005df4` count=1
- `DAT_10005e00` count=1
- `DAT_10005e60` count=1
- `DAT_10005eb0` count=1
- `DAT_10005eb4` count=1
- `DAT_10005eb8` count=1
- `DAT_10005ebc` count=1
- `DAT_10005ec0` count=1
- `DAT_10005ec8` count=1
- `DAT_10005ed0` count=1
- `DAT_10005ee0` count=1
- `DAT_10005ee4` count=1
- `DAT_10005f04` count=1
- `DAT_10005f08` count=1
- `DAT_10005f20` count=1
- `DAT_10005f24` count=1
- `DAT_10005f6c` count=1
- `DAT_10005f70` count=1
- `DAT_10005f78` count=1
- `DAT_10005f7c` count=1
- `DAT_10005f84` count=1
- `DAT_10005f88` count=1
- `DAT_10005f90` count=1
- `DAT_10005f94` count=1
- `DAT_1000628c` count=1
- `DAT_100065a8` count=1
- `DAT_100066a4` count=1
- `DAT_100066f0` count=1
- `DAT_10006a24` count=1
- `DAT_10006a94` count=1
- `DAT_10006b14` count=1
- `PTR_DAT_10005df0` count=1
- `PTR_DAT_10005e20` count=1
- `PTR_DAT_10005e2c` count=1
- `PTR_DAT_10005e38` count=1
- `PTR_DAT_10005e44` count=1
- `PTR_DAT_10005e64` count=1
- `PTR_DAT_10005ec4` count=1
- `PTR_DAT_10005ed4` count=1
- `PTR_DAT_10005ef0` count=1

## Working Interpretation

- `hp1020_usb2_thread` is the main USB service/init loop. It touches many globals through `memw()` barriers, which strongly points to memory-mapped hardware registers or DMA descriptors.
- `hp1020_usb2_idle_thread` is a tight service loop around a nearby helper at `0x10008f40`.
- `hp1020_acl_download` sets bit `0x80` in two control-looking globals, then dispatches through a function pointer loaded from a table at `PTR_DAT_10006068`.
- `hp1020_pjl_echo_matcher` compares incoming bytes against the literal `@PJL ECHO` path and calls a polling/read helper.

## USB Setup Request Constants

Resolved from the literal table near `0x10005f64`:
- `0x8006`: standard USB `GET_DESCRIPTOR` request.
- `0x2102`: class/interface request shape, likely `SET_REPORT` or a related class control transfer.
- `0xa100`, `0xa101`, `0xc100`, `0xc101`: vendor/class IN request shapes used by this device.
- jump table at `0x10003500`: seven setup-request handlers reached from the `0x8006` path by request/index byte.

## ACL Dispatch

`PTR_DAT_10006068` resolves to data at `0x1001be90`. The first word there is `0x10000350`, which is outside the normal loaded `.text` functions and lines up with the zero-sized bootcode interface area. Current interpretation: `agiACLDownload` sets USB/control bits and dispatches into a resident bootcode/interface table rather than a normal firmware-local function.
