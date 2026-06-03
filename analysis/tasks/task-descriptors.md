# HP 1020 Task And Queue Descriptor Map

This maps string-anchored task/queue/semaphore descriptor tables. The word windows are intentionally wider than a single struct because the firmware uses adjacent descriptor tables and literal pools.

## Anchors

### `100034f0` `USB2IdleThread`

Pointer references:
- `10005f14`

Nearby words:
- `10005f08`: `0xb300022c` MMIO-looking address
- `10005f0c`: `0x10008208` program .text
- `10005f10`: `0x1002162c` program .bss
- `10005f14`: `0x100034f0` string "USB2IdleThread"
- `10005f18`: `0x10009934` function hp1020_usb2_idle_thread
- `10005f1c`: `0x10021388` program .bss
- `10005f20`: `0x00010000` constant/flags
- `10005f28`: `0x9001bbe0` SRAM/DMA-looking address
- `10005f2c`: `0x020000c1` constant/flags
- `10005f30`: `0x020080c1` constant/flags
- `10005f34`: `0x020000d1` constant/flags
- `10005f38`: `0x9001bc00` SRAM/DMA-looking address
- `10005f3c`: `0x900034d0` SRAM/DMA-looking address
- `10005f40`: `0x10021380` program .bss
- `10005f44`: `0x100034a4` program .rodata
- `10005f48`: `0x10022b70` program .bss
- `10005f4c`: `0x10022b72` program .bss
- `10005f50`: `0x1001bbd0` program .data
- `10005f54`: `0x1001bc20` program .data
- `10005f60`: `0x00400000` constant/flags
- `10005f64`: `0x10003500` program .rodata
- `10005f68`: `0x100216e0` program .bss

### `1000351c` `usbIoFlags`

Pointer references:
- `10005fb8`

Nearby words:
- `10005fa8`: `0x1001bf56` program .data
- `10005fac`: `0x1001bc00` program .data
- `10005fb0`: `0x1001bf58` program .data
- `10005fb4`: `0x900034b0` SRAM/DMA-looking address
- `10005fb8`: `0x1000351c` string "usbIoFlags"
- `10005fbc`: `0x10003528` program .rodata
- `10005fc0`: `0x10021598` program .bss
- `10005fc4`: `0x10003530` string "USB2Thread"
- `10005fc8`: `0x10008ff0` function hp1020_usb2_thread
- `10005fcc`: `0x10022768` program .bss
- `10005fd0`: `0x10021588` program .bss
- `10005fd4`: `0x10021384` program .bss
- `10005fd8`: `0x00030d40` constant/flags
- `10005fdc`: `0x10009d34` program .text
- `10005fe0`: `0x1001bc78` program .data
- `10005fe4`: `0x1001bc80` program .data
- `10005fe8`: `0x10022cd8` program .bss
- `10005fec`: `0x10022ca0` program .bss
- `10005ff0`: `0x10022ca4` program .bss
- `10005ff4`: `0x10022c80` program .bss
- `10005ff8`: `0x10003540` program .rodata
- `10005ffc`: `0x10022ce0` program .bss
- `10006008`: `0x10022ca8` program .bss
- `1000600c`: `0x100036f0` program .rodata
- `10006010`: `0x1001bc74` program .data
- `10006014`: `0x1001be40` program .data

### `10003530` `USB2Thread`

Pointer references:
- `10005fc4`

Nearby words:
- `10005fb4`: `0x900034b0` SRAM/DMA-looking address
- `10005fb8`: `0x1000351c` string "usbIoFlags"
- `10005fbc`: `0x10003528` program .rodata
- `10005fc0`: `0x10021598` program .bss
- `10005fc4`: `0x10003530` string "USB2Thread"
- `10005fc8`: `0x10008ff0` function hp1020_usb2_thread
- `10005fcc`: `0x10022768` program .bss
- `10005fd0`: `0x10021588` program .bss
- `10005fd4`: `0x10021384` program .bss
- `10005fd8`: `0x00030d40` constant/flags
- `10005fdc`: `0x10009d34` program .text
- `10005fe0`: `0x1001bc78` program .data
- `10005fe4`: `0x1001bc80` program .data
- `10005fe8`: `0x10022cd8` program .bss
- `10005fec`: `0x10022ca0` program .bss
- `10005ff0`: `0x10022ca4` program .bss
- `10005ff4`: `0x10022c80` program .bss
- `10005ff8`: `0x10003540` program .rodata
- `10005ffc`: `0x10022ce0` program .bss
- `10006008`: `0x10022ca8` program .bss
- `1000600c`: `0x100036f0` program .rodata
- `10006010`: `0x1001bc74` program .data
- `10006014`: `0x1001be40` program .data
- `10006020`: `0x1001bc84` program .data

### `10003748` `agiACLDownload`

Pointer references:
- `10006054`

Nearby words:
- `10006044`: `0x000f4240` constant/flags
- `1000604c`: `0x04800100` constant/flags
- `10006050`: `0x10022d60` program .bss
- `10006054`: `0x10003748` string "agiACLDownload"
- `10006058`: `0x1000ad44` function hp1020_acl_download
- `10006068`: `0x1001be90` program .data
- `1000606c`: `0x10022e10` program .bss
- `10006070`: `0x10003758` string "TIME=Wed Mar 09 12:27:39 2005 BOI049 PROD=MANGUSTA CFG=GCC_RELEASE"
- `10006078`: `0x0fffffff` constant/flags
- `10006084`: `0x0ffff000` constant/flags
- `10006088`: `0x1000a334` program .text
- `1000608c`: `0x1001be94` program .data
- `10006090`: `0x100040c8` program .rodata
- `10006094`: `0x1000dc34` program .text
- `10006098`: `0x1001bec4` program .data
- `1000609c`: `0x1001bed8` program .data
- `100060a0`: `0x1001becc` program .data
- `100060a4`: `0x1002c61b` program .bss
- `100060a8`: `0x1002379c` program .bss
- `100060ac`: `0x100237a0` program .bss
- `100060b0`: `0x1002352c` program .bss

### `100047d0` `Job Mgr Queue`

Pointer references:
- `100062d4`

Nearby words:
- `100062c4`: `0x10023866` program .bss
- `100062c8`: `0x10004790` program .rodata
- `100062cc`: `0x100047b0` program .rodata
- `100062d0`: `0x10023e40` program .bss
- `100062d4`: `0x100047d0` string "Job Mgr Queue"
- `100062d8`: `0x10023924` program .bss
- `100062dc`: `0x1002386c` program .bss
- `100062e0`: `0x100047e0` string "JobMgrEventFlags"
- `100062e4`: `0x1002467c` program .bss
- `100062e8`: `0x10023e3c` program .bss
- `100062ec`: `0x1002388c` program .bss
- `100062f0`: `0x100047f4` string "tJobMgr"
- `100062f4`: `0x1000e414` function hp1020_job_mgr_thread_candidate
- `100062f8`: `0x10023e7a` program .bss
- `100062fc`: `0x1001beed` program .data
- `10006300`: `0x10023e78` program .bss
- `10006304`: `0x10023e28` program .bss
- `10006308`: `0x1001bee8` program .data
- `1000630c`: `0x1001beec` program .data
- `10006310`: `0x1001bef0` program .data
- `10006314`: `0x10023920` program .bss
- `10006318`: `0x10023e24` program .bss
- `1000631c`: `0x10023e25` program .bss
- `10006320`: `0x10004800` program .rodata
- `10006324`: `0x1002874c` program .bss
- `10006328`: `0x10024684` program .bss
- `1000632c`: `0x10028a74` program .bss
- `10006330`: `0x100048d0` string "PrintMgrQueue"

### `100048d0` `PrintMgrQueue`

Pointer references:
- `10006330`

Nearby words:
- `10006320`: `0x10004800` program .rodata
- `10006324`: `0x1002874c` program .bss
- `10006328`: `0x10024684` program .bss
- `1000632c`: `0x10028a74` program .bss
- `10006330`: `0x100048d0` string "PrintMgrQueue"
- `10006334`: `0x10028754` program .bss
- `10006338`: `0x10024720` program .bss
- `1000633c`: `0x1001bf08` program .data
- `10006340`: `0x10028aac` program .bss
- `10006344`: `0x1001bef4` program .data
- `10006348`: `0x1002468c` program .bss
- `1000634c`: `0x100048e0` string "PrintMgr"
- `10006350`: `0x1000f324` function hp1020_print_mgr_thread_candidate
- `10006354`: `0x10024734` program .bss
- `10006360`: `0x100048f0` program .rodata
- `10006368`: `0x100049e0` program .rodata
- `1000636c`: `0x1001bf1c` program .data
- `10006374`: `0x10000000` program .WindowVectors.text
- `1000637c`: `0x00080000` constant/flags
- `10006380`: `0x00100000` constant/flags

### `100048e0` `PrintMgr`

Pointer references:
- `1000634c`

Nearby words:
- `1000633c`: `0x1001bf08` program .data
- `10006340`: `0x10028aac` program .bss
- `10006344`: `0x1001bef4` program .data
- `10006348`: `0x1002468c` program .bss
- `1000634c`: `0x100048e0` string "PrintMgr"
- `10006350`: `0x1000f324` function hp1020_print_mgr_thread_candidate
- `10006354`: `0x10024734` program .bss
- `10006360`: `0x100048f0` program .rodata
- `10006368`: `0x100049e0` program .rodata
- `1000636c`: `0x1001bf1c` program .data
- `10006374`: `0x10000000` program .WindowVectors.text
- `1000637c`: `0x00080000` constant/flags
- `10006380`: `0x00100000` constant/flags
- `100063a4`: `0x10004a00` program .rodata

### `10004a20` `StatusMgrQueue`

Pointer references:
- `100063b8`

Nearby words:
- `100063ac`: `0x10013140` function FUN_10013140
- `100063b0`: `0x1002aca4` program .bss
- `100063b4`: `0x10028adc` program .bss
- `100063b8`: `0x10004a20` string "StatusMgrQueue"
- `100063bc`: `0x1002ab14` program .bss
- `100063c0`: `0x1002ad20` program .bss
- `100063c4`: `0x10004a30` string "StatusMgr"
- `100063c8`: `0x10010590` function hp1020_status_mgr_thread_candidate
- `100063cc`: `0x10028b14` program .bss
- `100063d0`: `0x1002acf4` program .bss
- `100063d4`: `0x10004a3c` string "st mutex"
- `100063d8`: `0x1002adb4` program .bss
- `100063e0`: `0x1001bf38` program .data
- `10006404`: `0x10004b30` program .rodata
- `10006408`: `0x1001bf3c` program .data
- `10006414`: `0x10004a50` program .rodata

### `10004b4c` `DelayMgr Semaphore`

Pointer references:
- `10006434`

Nearby words:
- `10006428`: `0x1002add0` program .bss
- `1000642c`: `0x1001bf40` program .data
- `10006430`: `0x1001eaac` program .bss
- `10006434`: `0x10004b4c` string "DelayMgr Semaphore"
- `10006438`: `0x1001d694` program .bss
- `1000643c`: `0x10004b60` string "DelayMgr Msg Queue"
- `10006440`: `0x1001d6cc` program .bss
- `10006444`: `0x1001d94c` program .bss
- `10006448`: `0x10004b74` string "tDelayMgrRcvMsg"
- `1000644c`: `0x10010b0c` function hp1020_delay_mgr_receive_thread_candidate
- `10006450`: `0x1001d9e0` program .bss
- `10006454`: `0x1001eaa8` program .bss
- `10006458`: `0x1001d690` program .bss
- `1000645c`: `0x1001e9e0` program .bss
- `10006460`: `0x1001bf4c` program .data
- `10006464`: `0x1002c0b0` program .bss
- `10006468`: `0x1001bf44` program .data
- `1000646c`: `0x1002c090` program .bss
- `10006470`: `0x10004b94` program .rodata
- `10006474`: `0x1002af64` program .bss
- `10006478`: `0x10004b9c` string "set/query mutex"
- `1000647c`: `0x1001ce14` program .data
- `10006480`: `0x1001bf48` program .data
- `10006484`: `0x1002af60` program .bss
- `10006488`: `0x1001cdfc` program .data
- `1000648c`: `0x1002bf90` program .bss
- `10006490`: `0x1002c56c` program .bss

### `10004b60` `DelayMgr Msg Queue`

Pointer references:
- `1000643c`

Nearby words:
- `1000642c`: `0x1001bf40` program .data
- `10006430`: `0x1001eaac` program .bss
- `10006434`: `0x10004b4c` string "DelayMgr Semaphore"
- `10006438`: `0x1001d694` program .bss
- `1000643c`: `0x10004b60` string "DelayMgr Msg Queue"
- `10006440`: `0x1001d6cc` program .bss
- `10006444`: `0x1001d94c` program .bss
- `10006448`: `0x10004b74` string "tDelayMgrRcvMsg"
- `1000644c`: `0x10010b0c` function hp1020_delay_mgr_receive_thread_candidate
- `10006450`: `0x1001d9e0` program .bss
- `10006454`: `0x1001eaa8` program .bss
- `10006458`: `0x1001d690` program .bss
- `1000645c`: `0x1001e9e0` program .bss
- `10006460`: `0x1001bf4c` program .data
- `10006464`: `0x1002c0b0` program .bss
- `10006468`: `0x1001bf44` program .data
- `1000646c`: `0x1002c090` program .bss
- `10006470`: `0x10004b94` program .rodata
- `10006474`: `0x1002af64` program .bss
- `10006478`: `0x10004b9c` string "set/query mutex"
- `1000647c`: `0x1001ce14` program .data
- `10006480`: `0x1001bf48` program .data
- `10006484`: `0x1002af60` program .bss
- `10006488`: `0x1001cdfc` program .data
- `1000648c`: `0x1002bf90` program .bss
- `10006490`: `0x1002c56c` program .bss
- `10006494`: `0x1002c4d8` program .bss
- `10006498`: `0x10004bac` string "DataStore"

### `10004b74` `tDelayMgrRcvMsg`

Pointer references:
- `10006448`

Nearby words:
- `10006438`: `0x1001d694` program .bss
- `1000643c`: `0x10004b60` string "DelayMgr Msg Queue"
- `10006440`: `0x1001d6cc` program .bss
- `10006444`: `0x1001d94c` program .bss
- `10006448`: `0x10004b74` string "tDelayMgrRcvMsg"
- `1000644c`: `0x10010b0c` function hp1020_delay_mgr_receive_thread_candidate
- `10006450`: `0x1001d9e0` program .bss
- `10006454`: `0x1001eaa8` program .bss
- `10006458`: `0x1001d690` program .bss
- `1000645c`: `0x1001e9e0` program .bss
- `10006460`: `0x1001bf4c` program .data
- `10006464`: `0x1002c0b0` program .bss
- `10006468`: `0x1001bf44` program .data
- `1000646c`: `0x1002c090` program .bss
- `10006470`: `0x10004b94` program .rodata
- `10006474`: `0x1002af64` program .bss
- `10006478`: `0x10004b9c` string "set/query mutex"
- `1000647c`: `0x1001ce14` program .data
- `10006480`: `0x1001bf48` program .data
- `10006484`: `0x1002af60` program .bss
- `10006488`: `0x1001cdfc` program .data
- `1000648c`: `0x1002bf90` program .bss
- `10006490`: `0x1002c56c` program .bss
- `10006494`: `0x1002c4d8` program .bss
- `10006498`: `0x10004bac` string "DataStore"
- `1000649c`: `0x1001146c` function hp1020_data_store_thread_candidate
- `100064a0`: `0x1002af90` program .bss
- `100064a4`: `0x10004bc0` program .rodata

### `10005504` `initTimer`

Pointer references:
- `10006730`

Nearby words:
- `10006720`: `0x1001c182` program .data
- `10006724`: `0x1001c180` program .data
- `10006728`: `0x1001c181` program .data
- `1000672c`: `0x1001c184` program .data
- `10006730`: `0x10005504` string "initTimer"
- `10006734`: `0x100138fc` function hp1020_init_timer_candidate
- `10006738`: `0x10013764` program .text
- `1000673c`: `0xb0700014` MMIO-looking address
- `10006740`: `0xb0800014` MMIO-looking address
- `10006744`: `0xb0800010` MMIO-looking address
- `1000674c`: `0xb0700004` MMIO-looking address
- `10006750`: `0xb0800004` MMIO-looking address
- `10006754`: `0x1002d28c` program .bss
- `10006758`: `0x10005510` string "Ctrl Panel"
- `1000675c`: `0x100139e4` function hp1020_control_panel_thread_candidate
- `10006760`: `0x1002d34c` program .bss
- `10006764`: `0x1001ca20` program .data
- `1000676c`: `0x1002ee38` program .bss
- `10006770`: `0x1002efc0` program .bss
- `10006774`: `0x1001cd28` program .data
- `10006778`: `0x100056f0` program .rodata
- `1000677c`: `0x1002ee70` program .bss
- `10006780`: `0x1002dda0` program .bss
- `10006784`: `0x100056fc` string "tVideo"
- `10006788`: `0x10013c18` function hp1020_video_thread_candidate
- `1000678c`: `0x1002de34` program .bss

### `100056ef` `?Video Queue`

Pointer references:
- none found

Nearby words:

### `10005b50` `tEngine`

Pointer references:
- `100069f0`

Nearby words:
- `100069e0`: `0x10030200` program .bss
- `100069e4`: `0x10005b40` string "engDelayMsgQ"
- `100069e8`: `0x10030494` program .bss
- `100069ec`: `0x10030400` program .bss
- `100069f0`: `0x10005b50` string "tEngine"
- `100069f4`: `0x100163b0` function hp1020_engine_thread_candidate
- `100069f8`: `0x1002f16c` program .bss
- `100069fc`: `0x1003016c` program .bss
- `10006a00`: `0x10005b58` string "tEngineDelay"
- `10006a04`: `0x1001635c` function hp1020_engine_delay_thread_candidate
- `10006a08`: `0x100305cc` program .bss
- `10006a0c`: `0x10030de2` program .bss
- `10006a10`: `0x10030de3` program .bss
- `10006a14`: `0x10006cd0` function FUN_10006cd0
- `10006a18`: `0x1001d498` program .data
- `10006a1c`: `0x10016c5c` function FUN_10016c5c
- `10006a20`: `0x00ff0000` constant/flags
- `10006a40`: `0x1001d52c` program .data
- `10006a44`: `0x1001d534` program .data
- `10006a48`: `0x1001d538` program .data
- `10006a4c`: `0x1001d53c` program .data

### `10005b58` `tEngineDelay`

Pointer references:
- `10006a00`

Nearby words:
- `100069f0`: `0x10005b50` string "tEngine"
- `100069f4`: `0x100163b0` function hp1020_engine_thread_candidate
- `100069f8`: `0x1002f16c` program .bss
- `100069fc`: `0x1003016c` program .bss
- `10006a00`: `0x10005b58` string "tEngineDelay"
- `10006a04`: `0x1001635c` function hp1020_engine_delay_thread_candidate
- `10006a08`: `0x100305cc` program .bss
- `10006a0c`: `0x10030de2` program .bss
- `10006a10`: `0x10030de3` program .bss
- `10006a14`: `0x10006cd0` function FUN_10006cd0
- `10006a18`: `0x1001d498` program .data
- `10006a1c`: `0x10016c5c` function FUN_10016c5c
- `10006a20`: `0x00ff0000` constant/flags
- `10006a40`: `0x1001d52c` program .data
- `10006a44`: `0x1001d534` program .data
- `10006a48`: `0x1001d538` program .data
- `10006a4c`: `0x1001d53c` program .data
- `10006a50`: `0x1001d540` program .data
- `10006a54`: `0x1001d544` program .data
- `10006a58`: `0x1001861c` function FUN_1001861c
- `10006a5c`: `0x00040001` constant/flags

### `10005c6c` `System Timer Thread`

Pointer references:
- `10006aec`

Nearby words:
- `10006adc`: `0x1003506c` program .bss
- `10006ae0`: `0x100350fc` program .bss
- `10006ae4`: `0x100350ec` program .bss
- `10006ae8`: `0x10035100` program .bss
- `10006aec`: `0x10005c6c` string "System Timer Thread"
- `10006af0`: `0x1001788c` function hp1020_system_timer_thread_candidate
- `10006af8`: `0x100351a0` program .bss
- `10006afc`: `0x1003519c` program .bss
- `10006b00`: `0x100350f8` program .bss
- `10006b04`: `0x10035198` program .bss
- `10006b08`: `0x100351a4` program .bss
- `10006b18`: `0x1001d4a0` program .data
- `10006b1c`: `0x1001d49c` program .data
- `10006b20`: `0x10016d6f` function FUN_10016d6f
- `10006b24`: `0x1001aac0` function FUN_1001aac0
- `10006b28`: `0x1001ad20` function FUN_1001ad20
- `10006b30`: `0x100187dd` program .text
- `10006b38`: `0x100188f3` inside function FUN_100188f0+3
- `10006b3c`: `0x10018cb0` program .text
- `10006b40`: `0x100351b4` program .bss
- `10006b44`: `0x100351b0` program .bss
- `10006b48`: `0x10018fd4` program .text

## Related Functions

- `10006cd0` `FUN_10006cd0`
- `10008208` `hp1020_task_entry_10008208`
- `10008ff0` `hp1020_usb2_thread`
- `10009934` `hp1020_usb2_idle_thread`
- `10009d34` `hp1020_task_entry_10009d34`
- `1000a334` `hp1020_task_entry_1000a334`
- `1000ad44` `hp1020_acl_download`
- `1000dc34` `hp1020_task_entry_1000dc34`
- `1000e414` `hp1020_job_mgr_thread_candidate`
- `1000f324` `hp1020_print_mgr_thread_candidate`
- `10010590` `hp1020_status_mgr_thread_candidate`
- `10010b0c` `hp1020_delay_mgr_receive_thread_candidate`
- `1001146c` `hp1020_data_store_thread_candidate`
- `1001215c` `hp1020_queue_receive_wrapper_candidate`
- `10013140` `FUN_10013140`
- `10013764` `hp1020_task_entry_10013764`
- `100138fc` `hp1020_init_timer_candidate`
- `100139e4` `hp1020_control_panel_thread_candidate`
- `10013c18` `hp1020_video_thread_candidate`
- `1001635c` `hp1020_engine_delay_thread_candidate`
- `100163b0` `hp1020_engine_thread_candidate`
- `10016c5c` `FUN_10016c5c`
- `10016d6f` `FUN_10016d6f`
- `1001788c` `hp1020_system_timer_thread_candidate`
- `1001861c` `FUN_1001861c`
- `100188f0` `FUN_100188f0`
- `10018cb0` `hp1020_task_entry_10018cb0`
- `10018fd4` `hp1020_task_entry_10018fd4`
- `1001aac0` `FUN_1001aac0`
- `1001ad20` `FUN_1001ad20`

## Interpretation

- `USB2Thread` and `USB2IdleThread` are directly resolved through descriptor-table function pointers.
- `System Timer Thread` also has a direct handler candidate at `0x1001788c`.
- `tJobMgr`, `PrintMgr`, `StatusMgr`, `tDelayMgrRcvMsg`, `tVideo`, `tEngineDelay`, and `tEngine` now have direct handler candidates from descriptor-table function pointers.
- The next pass should trace each queue ID/message code into the dispatch functions, especially `PrintMgr` and `tEngine`.
- Many descriptor words point into `0x1002....`/`0x1003....` BSS-like memory. These are probably ThreadX control blocks, stacks, queues, or engine buffers rather than executable code.
