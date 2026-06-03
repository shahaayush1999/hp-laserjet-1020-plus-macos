# HP 1020 Labeled Firmware Functions

Program: sihp1020.elf
Language: Xtensa:BE:32:default
Seed functions from interesting string references: 10
Total functions: 331

## Labeled Seed Functions

### `10007054` `hp1020_threadx_diag_10007054`

Referenced strings:
- `descriptor:dprintf mutex`

Direct callees:
- none found

Direct callers:
- none found

### `10008ff0` `hp1020_usb2_thread_10008ff0`

Referenced strings:
- `descriptor:USB2Thread`

Direct callees:
- `10007c00` `FUN_10007c00`
- `10007c70` `FUN_10007c70`
- `10008c24` `FUN_10008c24`
- `10008fb0` `FUN_10008fb0`
- `10009ac4` `FUN_10009ac4`
- `10011178` `FUN_10011178`
- `1001214c` `FUN_1001214c`
- `10013658` `FUN_10013658`
- `100169d4` `hp1020_strlen_like`
- `1001716c` `FUN_1001716c`
- `10017184` `FUN_10017184`
- `10017d28` `FUN_10017d28`
- ... 1 more

Direct callers:
- none found

### `10009934` `hp1020_usb2_idle_thread_10009934`

Referenced strings:
- `descriptor:USB2IdleThread`

Direct callees:
- none found

Direct callers:
- none found

### `1000ad44` `hp1020_acl_download_1000ad44`

Referenced strings:
- `descriptor:agiACLDownload`

Direct callees:
- none found

Direct callers:
- none found

### `1000b3f8` `hp1020_error_diag_1000b3f8`

Referenced strings:
- `PARSEERROR`

Direct callees:
- `10007430` `hp1020_format_into_buffer_candidate`
- `1000b1c4` `FUN_1000b1c4`
- `1000b290` `FUN_1000b290`
- `1000dc00` `hp1020_alloc_buffer_candidate`
- `1001693c` `hp1020_copy_string_candidate`
- `100169d4` `hp1020_strlen_like`
- `1001b544` `hp1020_append_string_to_buffer_candidate`

Direct callers:
- none found

### `1000bd04` `hp1020_device_state_1000bd04`

Referenced strings:
- `\tINTRAY2 PAPERTRAY`
- `\tINTRAY3 PAPERTRAY`
- `PAPERS [17 ENUMERATED]`

Direct callees:
- `10007430` `hp1020_format_into_buffer_candidate`
- `1000bad8` `FUN_1000bad8`
- `100111b4` `FUN_100111b4`
- `100111d8` `FUN_100111d8`
- `100134fc` `FUN_100134fc`
- `1001b544` `hp1020_append_string_to_buffer_candidate`

Direct callers:
- `1000c568` `FUN_1000c568`

### `1000cdb0` `hp1020_pjl_status_1000cdb0`

Referenced strings:
- `@PJL ECHO`

Direct callees:
- `1000d6b0` `hp1020_pjl_read_or_poll_candidate`
- `100169d4` `hp1020_strlen_like`

Direct callers:
- `1000d2a8` `FUN_1000d2a8`

### `1001223c` `hp1020_threadx_diag_1001223c`

Referenced strings:
- `TX_READY`
- `TX_COMPLETED`
- `TX_TERMINATED`
- `TX_SUSPENDED`
- `TX_SLEEP`
- `TX_QUEUE_SUSP`
- `TX_SEMAPHORE_SUSP`
- `TX_EVENT_FLAG`
- `TX_BLOCK_MEMORY`
- `TX_BYTE_MEMORY`
- `TX_IO_DRIVER`
- `TX_FILE`
- `TX_TCP_IP`
- `TX_MUTEX_SUSP`

Direct callees:
- none found

Direct callers:
- none found

### `100138fc` `hp1020_threadx_diag_100138fc`

Referenced strings:
- `descriptor:initTimer`

Direct callees:
- none found

Direct callers:
- none found

### `1001788c` `hp1020_threadx_diag_1001788c`

Referenced strings:
- `descriptor:System Timer Thread`

Direct callees:
- `100176c8` `FUN_100176c8`
- `1001a590` `FUN_1001a590`

Direct callers:
- none found

## Conservative Helper Labels

- `10007430` `hp1020_format_into_buffer_candidate`: used with destination buffer plus format/data arguments.
- `100169d4` `hp1020_strlen_like`: return value is used as a string/buffer offset.
- `1001693c` `hp1020_copy_string_candidate`: called after allocation/buffer preparation in PJL response construction.
- `1001b544` `hp1020_append_string_to_buffer_candidate`: heavily used to append literal strings to response buffers.
- `1000dc00` `hp1020_alloc_buffer_candidate`: called with computed output length before buffer population.
- `1000d6b0` `hp1020_pjl_read_or_poll_candidate`: used inside the `@PJL ECHO` scanning loop.

## Descriptor Table Anchors

- `10005d88` string=`dprintf mutex` handler=`10007054` `hp1020_threadx_diag_10007054` words=`0x10003198`, `0x10007054`, `0x100031b0`, `0x10003310`, `0x1001f238`, `0x1001f214`, `0x1001ec00`, `0x1001f218`
- `10005f14` string=`USB2IdleThread` handler=`10009934` `hp1020_usb2_idle_thread_10009934` words=`0x100034f0`, `0x10009934`, `0x10021388`, `0x00010000`, `0x30000000`, `0x9001bbe0`, `0x020000c1`, `0x020080c1`
- `10005fb8` string=`usbIoFlags` words=`0x1000351c`, `0x10003528`, `0x10021598`, `0x10003530`, `0x10008ff0`, `0x10022768`, `0x10021588`, `0x10021384`
- `10005fc4` string=`USB2Thread` handler=`10008ff0` `hp1020_usb2_thread_10008ff0` words=`0x10003530`, `0x10008ff0`, `0x10022768`, `0x10021588`, `0x10021384`, `0x00030d40`, `0x10009d34`, `0x1001bc78`
- `10006054` string=`agiACLDownload` handler=`1000ad44` `hp1020_acl_download_1000ad44` words=`0x10003748`, `0x1000ad44`, `0x00001000`, `0x0000ec1d`, `0x0000ec0d`, `0x1001be90`, `0x10022e10`, `0x10003758`
- `10006070` string=`TIME=Wed Mar 09 12:27:39 2005 BOI049 PROD=MANGUSTA CFG=GCC_RELEASE` words=`0x10003758`, `0x37ffffff`, `0x0fffffff`, `0x0000c0de`, `0x0000d1ee`, `0x0ffff000`, `0x1000a334`, `0x1001be94`
- `10006118` string=`PARSEERROR` words=`0x10004138`, `0x10004144`, `0x10004150`, `0x10004158`, `0x10004168`, `0x10004170`, `0x1000417c`, `0x10004180`
- `100061b4` string=`\tINTRAY2 PAPERTRAY` words=`0x10004288`, `0x1000429c`, `0x100042b0`, `0x100042c8`, `0x100042e4`, `0x100042ec`, `0x100042f4`, `0x100042fc`
- `100061b8` string=`\tINTRAY3 PAPERTRAY` words=`0x1000429c`, `0x100042b0`, `0x100042c8`, `0x100042e4`, `0x100042ec`, `0x100042f4`, `0x100042fc`, `0x10004318`
- `100061bc` string=`PAPERS [17 ENUMERATED]` words=`0x100042b0`, `0x100042c8`, `0x100042e4`, `0x100042ec`, `0x100042f4`, `0x100042fc`, `0x10004318`, `0x10004320`
- `10004668` string=`@PJL ECHO` words=`0x10004728`, `0x10004720`, `0x10004718`, `0x10004710`, `0x1000470c`, `0x100046fc`, `0x10004600`, `0x100046f0`
- `100062d4` string=`Job Mgr Queue` words=`0x100047d0`, `0x10023924`, `0x1002386c`, `0x100047e0`, `0x1002467c`, `0x10023e3c`, `0x1002388c`, `0x100047f4`
- `10006330` string=`PrintMgrQueue` words=`0x100048d0`, `0x10028754`, `0x10024720`, `0x1001bf08`, `0x10028aac`, `0x1001bef4`, `0x1002468c`, `0x100048e0`
- `100063b8` string=`StatusMgrQueue` words=`0x10004a20`, `0x1002ab14`, `0x1002ad20`, `0x10004a30`, `0x10010590`, `0x10028b14`, `0x1002acf4`, `0x10004a3c`
- `10006434` string=`DelayMgr Semaphore` words=`0x10004b4c`, `0x1001d694`, `0x10004b60`, `0x1001d6cc`, `0x1001d94c`, `0x10004b74`, `0x10010b0c`, `0x1001d9e0`
- `1000643c` string=`DelayMgr Msg Queue` words=`0x10004b60`, `0x1001d6cc`, `0x1001d94c`, `0x10004b74`, `0x10010b0c`, `0x1001d9e0`, `0x1001eaa8`, `0x1001d690`
- `10006554` string=`TX_READY` words=`0x10004d34`, `0x10004d40`, `0x10004d50`, `0x10004d60`, `0x10004d70`, `0x10004d7c`, `0x10004d8c`, `0x10004da0`
- `10006558` string=`TX_COMPLETED` words=`0x10004d40`, `0x10004d50`, `0x10004d60`, `0x10004d70`, `0x10004d7c`, `0x10004d8c`, `0x10004da0`, `0x10004db0`
- `1000655c` string=`TX_TERMINATED` words=`0x10004d50`, `0x10004d60`, `0x10004d70`, `0x10004d7c`, `0x10004d8c`, `0x10004da0`, `0x10004db0`, `0x10004dc0`
- `10006560` string=`TX_SUSPENDED` words=`0x10004d60`, `0x10004d70`, `0x10004d7c`, `0x10004d8c`, `0x10004da0`, `0x10004db0`, `0x10004dc0`, `0x10004dd0`
- `10006564` string=`TX_SLEEP` words=`0x10004d70`, `0x10004d7c`, `0x10004d8c`, `0x10004da0`, `0x10004db0`, `0x10004dc0`, `0x10004dd0`, `0x10004de0`
- `10006568` string=`TX_QUEUE_SUSP` words=`0x10004d7c`, `0x10004d8c`, `0x10004da0`, `0x10004db0`, `0x10004dc0`, `0x10004dd0`, `0x10004de0`, `0x10004de8`
- `1000656c` string=`TX_SEMAPHORE_SUSP` words=`0x10004d8c`, `0x10004da0`, `0x10004db0`, `0x10004dc0`, `0x10004dd0`, `0x10004de0`, `0x10004de8`, `0x10004df4`
- `10006570` string=`TX_EVENT_FLAG` words=`0x10004da0`, `0x10004db0`, `0x10004dc0`, `0x10004dd0`, `0x10004de0`, `0x10004de8`, `0x10004df4`, `0x10004e04`
- `10006574` string=`TX_BLOCK_MEMORY` words=`0x10004db0`, `0x10004dc0`, `0x10004dd0`, `0x10004de0`, `0x10004de8`, `0x10004df4`, `0x10004e04`, `0x10004e20`
- `10006578` string=`TX_BYTE_MEMORY` words=`0x10004dc0`, `0x10004dd0`, `0x10004de0`, `0x10004de8`, `0x10004df4`, `0x10004e04`, `0x10004e20`, `0x10004e60`
- `1000657c` string=`TX_IO_DRIVER` words=`0x10004dd0`, `0x10004de0`, `0x10004de8`, `0x10004df4`, `0x10004e04`, `0x10004e20`, `0x10004e60`, `0x10034f48`
- `10006580` string=`TX_FILE` words=`0x10004de0`, `0x10004de8`, `0x10004df4`, `0x10004e04`, `0x10004e20`, `0x10004e60`, `0x10034f48`, `0x10004e98`
- `10006584` string=`TX_TCP_IP` words=`0x10004de8`, `0x10004df4`, `0x10004e04`, `0x10004e20`, `0x10004e60`, `0x10034f48`, `0x10004e98`, `0x10004eb8`
- `10006588` string=`TX_MUTEX_SUSP` words=`0x10004df4`, `0x10004e04`, `0x10004e20`, `0x10004e60`, `0x10034f48`, `0x10004e98`, `0x10004eb8`, `0x10004ec0`
- `1000659c` string=`no threads exist at this time\n` words=`0x10004e98`, `0x10004eb8`, `0x10004ec0`, `0x4456444e`, `0x10004f40`, `0x10004f60`, `0x10004f98`, `0x10004fc8`
- `100065a4` string=`Name: %s  TX_THREAD ptr: 0x%08x\n  Priority: %u  Run Count: %u\n  Stack ptr: 0x%08x  Remaining: %u\n  State: %s  SuspLoc: 0x%08x\n` words=`0x10004ec0`, `0x4456444e`, `0x10004f40`, `0x10004f60`, `0x10004f98`, `0x10004fc8`, `0x53454d41`, `0x10004ff4`
- `100065ac` string=`ERROR corrputed event flag id\n` words=`0x10004f40`, `0x10004f60`, `0x10004f98`, `0x10004fc8`, `0x53454d41`, `0x10004ff4`, `0x10005014`, `0x10005044`
- `100065c0` string=`ERROR corrupted semaphore id\n` words=`0x10004ff4`, `0x10005014`, `0x10005044`, `0x10005078`, `0x4d555445`, `0x100050a4`, `0x100050c0`, `0x100050ec`
- `100065c4` string=`waiting for semaphore 0x%08x named '%s'\n` words=`0x10005014`, `0x10005044`, `0x10005078`, `0x4d555445`, `0x100050a4`, `0x100050c0`, `0x100050ec`, `0x10005120`
- `100065cc` string=`%u threads are currently waiting\n` words=`0x10005078`, `0x4d555445`, `0x100050a4`, `0x100050c0`, `0x100050ec`, `0x10005120`, `0x10005150`, `0x51554555`
- `100065d4` string=`ERROR corrupted mutex id\n` words=`0x100050a4`, `0x100050c0`, `0x100050ec`, `0x10005120`, `0x10005150`, `0x51554555`, `0x10005184`, `0x100051a0`
- `100065d8` string=`waiting for mutex 0x%08x named '%s'\n` words=`0x100050c0`, `0x100050ec`, `0x10005120`, `0x10005150`, `0x51554555`, `0x10005184`, `0x100051a0`, `0x100051d4`
- `100065e0` string=`and is currently owned by thread 0x%08x\n` words=`0x10005120`, `0x10005150`, `0x51554555`, `0x10005184`, `0x100051a0`, `0x100051d4`, `0x100051f0`, `0x10005218`
- `100065e4` string=`sleeping for an additional %u timer ticks\n` words=`0x10005150`, `0x51554555`, `0x10005184`, `0x100051a0`, `0x100051d4`, `0x100051f0`, `0x10005218`, `0x1000521c`
- `100065ec` string=`ERROR corrupted queue id\n` words=`0x10005184`, `0x100051a0`, `0x100051d4`, `0x100051f0`, `0x10005218`, `0x1000521c`, `0x10005240`, `0x10005260`
- `100065f0` string=`waiting on queue at addr: 0x%08x named '%s'\n` words=`0x100051a0`, `0x100051d4`, `0x100051f0`, `0x10005218`, `0x1000521c`, `0x10005240`, `0x10005260`, `0x10005284`
- `10006600` string=`Name: %s  TX_THREAD ptr: 0x%08x\n` words=`0x1000521c`, `0x10005240`, `0x10005260`, `0x10005284`, `0x100052a4`, `0x1001c0d0`, `0x1001c030`, `0x100052d0`
- `10006610` string=`%u threads are currently waiting\n` words=`0x100052a4`, `0x1001c0d0`, `0x1001c030`, `0x100052d0`, `0x100052f8`, `0x1002c8ac`, `0x1000531c`, `0xb0300004`
- `1000661c` string=`Run count unreliable for thread 0x%08x\n` words=`0x100052d0`, `0x100052f8`, `0x1002c8ac`, `0x1000531c`, `0xb0300004`, `0x1001c178`, `0xb0300010`, `0xb0300000`
- `10006620` string=`Thread 0x%08x run count delta = %u\n` words=`0x100052f8`, `0x1002c8ac`, `0x1000531c`, `0xb0300004`, `0x1001c178`, `0xb0300010`, `0xb0300000`, `0xb0300024`
- `100066f4` string=`tx_queue_send() failed, MSG LOST !!\n` words=`0x10005408`, `0x1002c9f8`, `0x10005430`, `0x1002d230`, `0x1002c964`, `0x10005434`, `0x100136d8`, `0x1002ca30`
- `10006730` string=`initTimer` handler=`100138fc` `hp1020_threadx_diag_100138fc` words=`0x10005504`, `0x100138fc`, `0x10013764`, `0xb0700014`, `0xb0800014`, `0xb0800010`, `0xffbfffff`, `0xb0700004`
- `10006aec` string=`System Timer Thread` handler=`1001788c` `hp1020_threadx_diag_1001788c` words=`0x10005c6c`, `0x1001788c`, `0x4154494d`, `0x100351a0`, `0x1003519c`, `0x100350f8`, `0x10035198`, `0x100351a4`

## Unowned Code String References

All instruction string references were associated with a function or nearby function.

## Subsystem Clusters

### USB/Download

Seed count: 3
Cluster size through call depth 2: 79

- `10008ff0` `hp1020_usb2_thread_10008ff0` strings=`descriptor:USB2Thread`
- `10009934` `hp1020_usb2_idle_thread_10009934` strings=`descriptor:USB2IdleThread`
- `1000ad44` `hp1020_acl_download_1000ad44` strings=`descriptor:agiACLDownload`
- `10007c00` `FUN_10007c00`
- `10007c70` `FUN_10007c70`
- `10008c24` `FUN_10008c24`
- `10008fb0` `FUN_10008fb0`
- `10009ac4` `FUN_10009ac4`
- `10011178` `FUN_10011178`
- `1001214c` `FUN_1001214c`
- `10013658` `FUN_10013658`
- `100169d4` `hp1020_strlen_like`
- `1001716c` `FUN_1001716c`
- `10017184` `FUN_10017184`
- `10017d28` `FUN_10017d28`
- `10018274` `FUN_10018274`
- `10008034` `FUN_10008034`
- `100173c8` `FUN_100173c8`
- `1001b38c` `FUN_1001b38c`
- `10013050` `FUN_10013050`
- `100130bc` `FUN_100130bc`
- `10013408` `FUN_10013408`
- `100171b0` `FUN_100171b0`
- `1000ae94` `FUN_1000ae94`
- `1000b624` `FUN_1000b624`
- `1000b870` `FUN_1000b870`
- `1000bfb0` `FUN_1000bfb0`
- `10014910` `FUN_10014910`
- `100160a8` `FUN_100160a8`
- `1001215c` `FUN_1001215c`
- `1000ed4c` `FUN_1000ed4c`
- `1000ed90` `FUN_1000ed90`
- `1000eeb8` `FUN_1000eeb8`
- `1000f164` `FUN_1000f164`
- `1000f814` `FUN_1000f814`
- `10010170` `FUN_10010170`
- `10010218` `FUN_10010218`
- `10010338` `FUN_10010338`
- `10010398` `FUN_10010398`
- `100103f8` `FUN_100103f8`
- `1001040c` `FUN_1001040c`
- `10010838` `FUN_10010838`
- `10010c98` `FUN_10010c98`
- `10010cf0` `FUN_10010cf0`
- `10010fd0` `FUN_10010fd0`
- `10013140` `FUN_10013140`
- `10013668` `FUN_10013668`
- `10015c68` `FUN_10015c68`
- `10015df8` `FUN_10015df8`
- `10016164` `FUN_10016164`
- `100070e0` `FUN_100070e0`
- `10007130` `FUN_10007130`
- `10007180` `FUN_10007180`
- `10007218` `FUN_10007218`
- `100072b0` `FUN_100072b0`
- `10007334` `FUN_10007334`
- `1000b128` `FUN_1000b128`
- `1000b174` `FUN_1000b174`
- `1000b1c4` `FUN_1000b1c4`
- `1000b1d4` `FUN_1000b1d4`
- `1000b290` `FUN_1000b290`
- `1000b2a8` `FUN_1000b2a8`
- `1000b344` `FUN_1000b344`
- `1000b3f8` `hp1020_error_diag_1000b3f8` strings=`PARSEERROR`
- `1000b520` `FUN_1000b520`
- `1000b6d8` `FUN_1000b6d8`
- `1000b774` `FUN_1000b774`
- `1000c568` `FUN_1000c568`
- `1000c69c` `FUN_1000c69c`
- `1000c8fc` `FUN_1000c8fc`
- `1000cd44` `FUN_1000cd44`
- `1000cdb0` `hp1020_pjl_status_1000cdb0` strings=`@PJL ECHO`
- `1000d5b0` `FUN_1000d5b0`
- `1000d700` `FUN_1000d700`
- `1000dba8` `FUN_1000dba8`
- `10015214` `FUN_10015214`
- `10019408` `FUN_10019408`
- `10007cd0` `FUN_10007cd0`
- `1001a610` `FUN_1001a610`

### PJL/Status

Seed count: 1
Cluster size through call depth 2: 41

- `1000cdb0` `hp1020_pjl_status_1000cdb0` strings=`@PJL ECHO`
- `1000d2a8` `FUN_1000d2a8`
- `1000d6b0` `hp1020_pjl_read_or_poll_candidate`
- `100169d4` `hp1020_strlen_like`
- `1000dd60` `FUN_1000dd60`
- `1000dd7c` `FUN_1000dd7c`
- `1000cd64` `FUN_1000cd64`
- `1000d674` `FUN_1000d674`
- `1000d700` `FUN_1000d700`
- `1000d880` `FUN_1000d880`
- `1000d9b0` `FUN_1000d9b0`
- `1000da5c` `FUN_1000da5c`
- `1000dba8` `FUN_1000dba8`
- `1000dde8` `FUN_1000dde8`
- `1000ded8` `FUN_1000ded8`
- `1000dfc8` `FUN_1000dfc8`
- `1000e1dc` `FUN_1000e1dc`
- `100070e0` `FUN_100070e0`
- `10007130` `FUN_10007130`
- `10007180` `FUN_10007180`
- `10007218` `FUN_10007218`
- `100072b0` `FUN_100072b0`
- `10007334` `FUN_10007334`
- `10008ff0` `hp1020_usb2_thread_10008ff0` strings=`descriptor:USB2Thread`
- `1000b128` `FUN_1000b128`
- `1000b174` `FUN_1000b174`
- `1000b1c4` `FUN_1000b1c4`
- `1000b1d4` `FUN_1000b1d4`
- `1000b290` `FUN_1000b290`
- `1000b2a8` `FUN_1000b2a8`
- `1000b344` `FUN_1000b344`
- `1000b3f8` `hp1020_error_diag_1000b3f8` strings=`PARSEERROR`
- `1000b520` `FUN_1000b520`
- `1000b624` `FUN_1000b624`
- `1000b6d8` `FUN_1000b6d8`
- `1000b774` `FUN_1000b774`
- `1000c568` `FUN_1000c568`
- `1000c69c` `FUN_1000c69c`
- `1000c8fc` `FUN_1000c8fc`
- `1000cd44` `FUN_1000cd44`
- `1000d5b0` `FUN_1000d5b0`

### Device State

Seed count: 2
Cluster size through call depth 2: 61

- `1000b3f8` `hp1020_error_diag_1000b3f8` strings=`PARSEERROR`
- `1000bd04` `hp1020_device_state_1000bd04` strings=`\tINTRAY2 PAPERTRAY', '\tINTRAY3 PAPERTRAY', 'PAPERS [17 ENUMERATED]`
- `10007430` `hp1020_format_into_buffer_candidate`
- `1000b1c4` `FUN_1000b1c4`
- `1000b290` `FUN_1000b290`
- `1000dc00` `hp1020_alloc_buffer_candidate`
- `1001693c` `hp1020_copy_string_candidate`
- `100169d4` `hp1020_strlen_like`
- `1001b544` `hp1020_append_string_to_buffer_candidate`
- `1000bad8` `FUN_1000bad8`
- `1000c568` `FUN_1000c568`
- `100111b4` `FUN_100111b4`
- `100111d8` `FUN_100111d8`
- `100134fc` `FUN_100134fc`
- `10006f00` `FUN_10006f00`
- `10007468` `FUN_10007468`
- `1000ae3c` `FUN_1000ae3c`
- `1000b2a8` `FUN_1000b2a8`
- `1000b520` `FUN_1000b520`
- `1000b624` `FUN_1000b624`
- `1000ba48` `FUN_1000ba48`
- `1000ba98` `FUN_1000ba98`
- `1000bfc8` `FUN_1000bfc8`
- `1000c8fc` `FUN_1000c8fc`
- `1000b1d4` `FUN_1000b1d4`
- `1000b344` `FUN_1000b344`
- `1000b6d8` `FUN_1000b6d8`
- `1000b774` `FUN_1000b774`
- `1000c69c` `FUN_1000c69c`
- `1000b128` `FUN_1000b128`
- `1000b174` `FUN_1000b174`
- `1000e1dc` `FUN_1000e1dc`
- `100131b8` `FUN_100131b8`
- `1001766c` `FUN_1001766c`
- `1000d700` `FUN_1000d700`
- `1000e070` `FUN_1000e070`
- `100070e0` `FUN_100070e0`
- `10007130` `FUN_10007130`
- `10007180` `FUN_10007180`
- `10007218` `FUN_10007218`
- `100072b0` `FUN_100072b0`
- `10007334` `FUN_10007334`
- `10008ff0` `hp1020_usb2_thread_10008ff0` strings=`descriptor:USB2Thread`
- `1000cd44` `FUN_1000cd44`
- `1000cdb0` `hp1020_pjl_status_1000cdb0` strings=`@PJL ECHO`
- `1000d5b0` `FUN_1000d5b0`
- `1000dba8` `FUN_1000dba8`
- `1000c230` `FUN_1000c230`
- `1000bfb0` `FUN_1000bfb0`
- `1001684c` `FUN_1001684c`
- `1000a2a4` `FUN_1000a2a4`
- `1000f1c4` `FUN_1000f1c4`
- `1000f84c` `FUN_1000f84c`
- `100100a8` `FUN_100100a8`
- `10010f54` `FUN_10010f54`
- `10011258` `FUN_10011258`
- `1001135c` `FUN_1001135c`
- `100181a4` `FUN_100181a4`
- `1000b870` `FUN_1000b870`
- `10010fd0` `FUN_10010fd0`
- `10018214` `FUN_10018214`

### ThreadX/RTOS Diagnostics

Seed count: 6
Cluster size through call depth 2: 98

- `10007054` `hp1020_threadx_diag_10007054` strings=`descriptor:dprintf mutex`
- `10008ff0` `hp1020_usb2_thread_10008ff0` strings=`descriptor:USB2Thread`
- `10009934` `hp1020_usb2_idle_thread_10009934` strings=`descriptor:USB2IdleThread`
- `1001223c` `hp1020_threadx_diag_1001223c` strings=`TX_READY', 'TX_COMPLETED', 'TX_TERMINATED`, ...
- `100138fc` `hp1020_threadx_diag_100138fc` strings=`descriptor:initTimer`
- `1001788c` `hp1020_threadx_diag_1001788c` strings=`descriptor:System Timer Thread`
- `10007c00` `FUN_10007c00`
- `10007c70` `FUN_10007c70`
- `10008c24` `FUN_10008c24`
- `10008fb0` `FUN_10008fb0`
- `10009ac4` `FUN_10009ac4`
- `10011178` `FUN_10011178`
- `1001214c` `FUN_1001214c`
- `10013658` `FUN_10013658`
- `100169d4` `hp1020_strlen_like`
- `1001716c` `FUN_1001716c`
- `10017184` `FUN_10017184`
- `10017d28` `FUN_10017d28`
- `10018274` `FUN_10018274`
- `100176c8` `FUN_100176c8`
- `1001a590` `FUN_1001a590`
- `10008034` `FUN_10008034`
- `100173c8` `FUN_100173c8`
- `1001b38c` `FUN_1001b38c`
- `10013050` `FUN_10013050`
- `100130bc` `FUN_100130bc`
- `10013408` `FUN_10013408`
- `100171b0` `FUN_100171b0`
- `1000ae94` `FUN_1000ae94`
- `1000b624` `FUN_1000b624`
- `1000b870` `FUN_1000b870`
- `1000bfb0` `FUN_1000bfb0`
- `10014910` `FUN_10014910`
- `100160a8` `FUN_100160a8`
- `1001215c` `FUN_1001215c`
- `1000ed4c` `FUN_1000ed4c`
- `1000ed90` `FUN_1000ed90`
- `1000eeb8` `FUN_1000eeb8`
- `1000f164` `FUN_1000f164`
- `1000f814` `FUN_1000f814`
- `10010170` `FUN_10010170`
- `10010218` `FUN_10010218`
- `10010338` `FUN_10010338`
- `10010398` `FUN_10010398`
- `100103f8` `FUN_100103f8`
- `1001040c` `FUN_1001040c`
- `10010838` `FUN_10010838`
- `10010c98` `FUN_10010c98`
- `10010cf0` `FUN_10010cf0`
- `10010fd0` `FUN_10010fd0`
- `10013140` `FUN_10013140`
- `10013668` `FUN_10013668`
- `10015c68` `FUN_10015c68`
- `10015df8` `FUN_10015df8`
- `10016164` `FUN_10016164`
- `100070e0` `FUN_100070e0`
- `10007130` `FUN_10007130`
- `10007180` `FUN_10007180`
- `10007218` `FUN_10007218`
- `100072b0` `FUN_100072b0`
- `10007334` `FUN_10007334`
- `1000b128` `FUN_1000b128`
- `1000b174` `FUN_1000b174`
- `1000b1c4` `FUN_1000b1c4`
- `1000b1d4` `FUN_1000b1d4`
- `1000b290` `FUN_1000b290`
- `1000b2a8` `FUN_1000b2a8`
- `1000b344` `FUN_1000b344`
- `1000b3f8` `hp1020_error_diag_1000b3f8` strings=`PARSEERROR`
- `1000b520` `FUN_1000b520`
- `1000b6d8` `FUN_1000b6d8`
- `1000b774` `FUN_1000b774`
- `1000c568` `FUN_1000c568`
- `1000c69c` `FUN_1000c69c`
- `1000c8fc` `FUN_1000c8fc`
- `1000cd44` `FUN_1000cd44`
- `1000cdb0` `hp1020_pjl_status_1000cdb0` strings=`@PJL ECHO`
- `1000d5b0` `FUN_1000d5b0`
- `1000d700` `FUN_1000d700`
- `1000dba8` `FUN_1000dba8`
- `10015214` `FUN_10015214`
- `10019408` `FUN_10019408`
- `10007cd0` `FUN_10007cd0`
- `1001a610` `FUN_1001a610`
- `1001766c` `FUN_1001766c`
- `10018750` `FUN_10018750`
- `10018b84` `FUN_10018b84`
- `10018eac` `FUN_10018eac`
- `10019634` `FUN_10019634`
- `10019b7c` `FUN_10019b7c`
- `10019eb4` `FUN_10019eb4`
- `1001a130` `FUN_1001a130`
- `1001a478` `FUN_1001a478`
- `1001ac30` `FUN_1001ac30`
- `1001ac7c` `FUN_1001ac7c`
- `1001b128` `FUN_1001b128`
- `1001a5f4` `FUN_1001a5f4`
- `1001a7c0` `FUN_1001a7c0`
