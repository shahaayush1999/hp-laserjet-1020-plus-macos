# HP 1020 Engine And Video Path Map

This maps the queue-driven print-engine/video path starting from the task descriptors.

- Seed functions: `13`
- Neighborhood through call depth 2: `125`

## Seed Functions

- `1000f324` `hp1020_print_mgr_thread_candidate`
- `10013c18` `hp1020_video_thread_candidate`
- `10014910` `hp1020_video_prepare_page_candidate`
- `10015214` `hp1020_video_render_or_dma_candidate`
- `10015438` `hp1020_video_alt_render_candidate`
- `10015458` `hp1020_video_reset_or_flush_candidate`
- `10015df8` `hp1020_engine_status_poll_candidate`
- `10016024` `hp1020_engine_init_step_candidate`
- `100160a8` `hp1020_engine_preflight_candidate`
- `10016164` `hp1020_engine_message_dispatch_candidate`
- `1001635c` `hp1020_engine_delay_thread_candidate`
- `100163b0` `hp1020_engine_thread_candidate`
- `100165a4` `hp1020_engine_register_handlers_candidate`

## Descriptor And Switch Table Windows

### Window at `0x100048f0`

- `100048f0`: `0x1000f392` inside function hp1020_print_mgr_thread_candidate+6e
- `100048f4`: `0x1000f37a` inside function hp1020_print_mgr_thread_candidate+56
- `100048f8`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `100048fc`: `0x1000f44c` inside function hp1020_print_mgr_thread_candidate+128
- `10004900`: `0x1000f399` inside function hp1020_print_mgr_thread_candidate+75
- `10004904`: `0x1000f460` inside function hp1020_print_mgr_thread_candidate+13c
- `10004908`: `0x1000f3ca` inside function hp1020_print_mgr_thread_candidate+a6
- `1000490c`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004910`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004914`: `0x1000f474` inside function hp1020_print_mgr_thread_candidate+150
- `10004918`: `0x1000f47d` inside function hp1020_print_mgr_thread_candidate+159
- `1000491c`: `0x1000f485` inside function hp1020_print_mgr_thread_candidate+161
- `10004920`: `0x1000f4c2` inside function hp1020_print_mgr_thread_candidate+19e
- `10004924`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004928`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `1000492c`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004930`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004934`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004938`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `1000493c`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004940`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004944`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `10004948`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34
- `1000494c`: `0x1000f358` inside function hp1020_print_mgr_thread_candidate+34

### Window at `0x100056f0`

- `100056f0`: `0x56696465` constant
- `100056f4`: `0x6f205175` constant
- `100056f8`: `0x65756500` constant
- `100056fc`: `0x74566964` constant
- `10005700`: `0x656f0000` constant
- `10005704`: `0x00000000` zero
- `10005708`: `0x00000000` zero
- `1000570c`: `0x00000000` zero
- `10005710`: `0x10013e90` inside function FUN_10013d4c+144
- `10005714`: `0x10013ecd` inside function FUN_10013d4c+181
- `10005718`: `0x10013f14` inside function FUN_10013d4c+1c8
- `1000571c`: `0x10013ee4` inside function FUN_10013d4c+198
- `10005720`: `0x10013ef0` inside function FUN_10013d4c+1a4
- `10005724`: `0x10013efc` inside function FUN_10013d4c+1b0
- `10005728`: `0x10013f08` inside function FUN_10013d4c+1bc
- `1000572c`: `0x10013f14` inside function FUN_10013d4c+1c8
- `10005730`: `0x72656672` constant
- `10005734`: `0x65736852` constant
- `10005738`: `0x61774261` constant
- `1000573c`: `0x6e64732c` constant
- `10005740`: `0x2069632e` constant
- `10005744`: `0x70426964` constant
- `10005748`: `0x426c6f63` constant
- `1000574c`: `0x6b3d3078` constant

### Window at `0x10006784`

- `10006784`: `0x100056fc` string "tVideo"
- `10006788`: `0x10013c18` function hp1020_video_thread_candidate
- `1000678c`: `0x1002de34` program .bss
- `10006790`: `0xb2000010` MMIO-looking address
- `10006794`: `0xb2080000` MMIO-looking address
- `10006798`: `0xb2040000` MMIO-looking address
- `1000679c`: `0xb204000c` MMIO-looking address
- `100067a0`: `0xb208000c` MMIO-looking address
- `100067a4`: `0xe6e01201` constant
- `100067a8`: `0xe6e01202` constant
- `100067ac`: `0xeee01b02` constant
- `100067b0`: `0xeee01b04` constant
- `100067b4`: `0xeee01b01` constant
- `100067b8`: `0x10005710` program .rodata
- `100067bc`: `0x1002efe0` program .bss
- `100067c0`: `0xb1000004` MMIO-looking address
- `100067c4`: `0x1002efb0` program .bss
- `100067c8`: `0x1001cdac` program .data
- `100067cc`: `0xb1000008` MMIO-looking address
- `100067d0`: `0xb1000108` MMIO-looking address
- `100067d4`: `0xb100000c` MMIO-looking address
- `100067d8`: `0xb1000104` MMIO-looking address
- `100067dc`: `0xb100010c` MMIO-looking address
- `100067e0`: `0x10005730` string "refreshRawBands, ic.pBidBlock=0x%08x, nBackloggedBands=%u\n"

### Window at `0x10006920`

- `10006920`: `0x1002f0c4` program .bss
- `10006924`: `0xfeffffff` constant
- `10006928`: `0xb0500004` MMIO-looking address
- `1000692c`: `0xfe001401` constant
- `10006930`: `0x00006400` constant
- `10006934`: `0x00005480` constant
- `10006938`: `0x00005300` constant
- `1000693c`: `0x00003300` constant
- `10006940`: `0x00004040` constant
- `10006944`: `0xf6000300` constant
- `10006948`: `0xf6000400` constant
- `1000694c`: `0xe6100b0a` constant
- `10006950`: `0xe6100b0b` constant
- `10006954`: `0x100059c0` program .rodata
- `10006958`: `0xe6100a01` constant
- `1000695c`: `0xe6000d03` constant
- `10006960`: `0xe6000d06` constant
- `10006964`: `0xe6000d04` constant
- `10006968`: `0x0000501a` constant
- `1000696c`: `0xe6100800` constant
- `10006970`: `0xe6100e00` constant
- `10006974`: `0x00000a01` constant
- `10006978`: `0x14000a04` constant
- `1000697c`: `0x00005043` constant

### Window at `0x100069b4`

- `100069b4`: `0x10016318` function FUN_10016318
- `100069b8`: `0x100162cc` program .text
- `100069bc`: `0x1002f134` program .bss
- `100069c0`: `0xb0500000` MMIO-looking address
- `100069c4`: `0x04fffe00` constant
- `100069c8`: `0xb0501000` MMIO-looking address
- `100069cc`: `0x10005780` program .rodata
- `100069d0`: `0x04fffe01` constant
- `100069d4`: `0x10015bc8` program .text
- `100069d8`: `0x10005b24` string "engineEventFlags"
- `100069dc`: `0x10005b38` string "engMsgQ"
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

### Window at `0x100069f0`

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
- `10006a20`: `0x00ff0000` constant
- `10006a24`: `0x000000ff` constant
- `10006a28`: `0x40404040` constant
- `10006a2c`: `0x7340000c` constant
- `10006a30`: `0xb0200004` MMIO-looking address
- `10006a34`: `0xb020000c` MMIO-looking address
- `10006a38`: `0xb0200008` MMIO-looking address
- `10006a3c`: `0xb0200000` MMIO-looking address
- `10006a40`: `0x1001d52c` program .data
- `10006a44`: `0x1001d534` program .data
- `10006a48`: `0x1001d538` program .data
- `10006a4c`: `0x1001d53c` program .data

## Function Neighborhood

### `10014910` `hp1020_video_prepare_page_candidate`

- size: `2305`
- callers: `1`; calls: `6`
- calls: `10011178 FUN_10011178`, `100181a4 FUN_100181a4`, `100171b0 FUN_100171b0`, `1001b668 FUN_1001b668`, `1001b4c8 FUN_1001b4c8`, `10017184 FUN_10017184`
- MMIO refs: `0xb1000000`, `0xb1000100`, `0xb1000004`, `0xb1000104`, `0xb1000020`, `0xb1000024`, `0xb1000120`, `0xb1000124`, `0xb100001c`, `0xb100011c`, `0xb1000400`, `0xb1000410`, `0xb100042...`
- SRAM refs: `0x900236ca`, `0x90010598`, `0x90028688`, `0x9001087d`

### `1000f324` `hp1020_print_mgr_thread_candidate`

- size: `591`
- callers: `0`; calls: `15`
- calls: `1001214c hp1020_task_ready_or_init_candidate`, `1001135c FUN_1001135c`, `10013658 hp1020_queue_send_candidate`, `1001809c threadx_queue_receive_wait_candidate`, `10010298 FUN_10...`

### `10015df8` `hp1020_engine_status_poll_candidate`

- size: `556`
- callers: `2`; calls: `4`
- calls: `10015c68 FUN_10015c68`, `10015dd0 FUN_10015dd0`, `10013658 hp1020_queue_send_candidate`, `10013d4c FUN_10013d4c`

### `10015214` `hp1020_video_render_or_dma_candidate`

- size: `548`
- callers: `1`; calls: `4`
- calls: `1001b770 FUN_1001b770`, `10017184 FUN_10017184`, `10017414 FUN_10017414`, `10014244 FUN_10014244`
- MMIO refs: `0xb2040000`, `0xb204000c`, `0xb2080000`, `0xb208000c`, `0xb2000010`, `0xb2000008`, `0xb200000c`, `0xb2000024`, `0xb2000000`, `0xb2040004`, `0xb2040008`

### `10016164` `hp1020_engine_message_dispatch_candidate`

- size: `332`
- callers: `1`; calls: `10`
- calls: `10013658 hp1020_queue_send_candidate`, `10016098 FUN_10016098`, `10015df8 hp1020_engine_status_poll_candidate`, `100180dc FUN_100180dc`, `10013620 hp1020_send_or_raise_engine_ms...`

### `100165a4` `hp1020_engine_register_handlers_candidate`

- size: `270`
- callers: `1`; calls: `2`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`

### `10013c18` `hp1020_video_thread_candidate`

- size: `225`
- callers: `0`; calls: `8`
- calls: `1001214c hp1020_task_ready_or_init_candidate`, `1001809c threadx_queue_receive_wait_candidate`, `10014910 hp1020_video_prepare_page_candidate`, `10015214 hp1020_video_render_or_...`
- MMIO refs: `0xb0000004`, `0xb0886f82`

### `100163b0` `hp1020_engine_thread_candidate`

- size: `208`
- callers: `0`; calls: `11`
- calls: `1001215c FUN_1001215c`, `100160a8 hp1020_engine_preflight_candidate`, `10015df8 hp1020_engine_status_poll_candidate`, `1001766c threadx_sleep_candidate`, `10016024 hp1020_engine...`

### `100160a8` `hp1020_engine_preflight_candidate`

- size: `186`
- callers: `2`; calls: `5`
- calls: `10013658 hp1020_queue_send_candidate`, `1001766c threadx_sleep_candidate`, `10011178 FUN_10011178`, `10016318 FUN_10016318`, `10015d14 FUN_10015d14`
- MMIO refs: `0xb0500004`

### `10015458` `hp1020_video_reset_or_flush_candidate`

- size: `176`
- callers: `1`; calls: `2`
- calls: `10013d4c FUN_10013d4c`, `10018214 FUN_10018214`
- MMIO refs: `0xb1000000`, `0xb1000004`, `0xb1000100`, `0xb1000104`

### `10011258` `hp1020_register_event_handler_candidate`

- size: `124`
- callers: `1`; calls: `6`
- calls: `100131b8 FUN_100131b8`, `1001766c threadx_sleep_candidate`, `100111b4 FUN_100111b4`, `1001b290 FUN_1001b290`, `1001b2c4 FUN_1001b2c4`, `100111d8 FUN_100111d8`

### `10016024` `hp1020_engine_init_step_candidate`

- size: `102`
- callers: `1`; calls: `1`
- calls: `10015c68 FUN_10015c68`
- MMIO refs: `0xb0500004`

### `10012184` `hp1020_task_ready_done_candidate`

- size: `94`
- callers: `1`; calls: `1`
- calls: `10017dac FUN_10017dac`

### `1001766c` `threadx_sleep_candidate`

- size: `92`
- callers: `11`; calls: `2`
- calls: `1001a590 FUN_1001a590`, `100176c8 FUN_100176c8`

### `1001635c` `hp1020_engine_delay_thread_candidate`

- size: `84`
- callers: `0`; calls: `4`
- calls: `1001214c hp1020_task_ready_or_init_candidate`, `1001809c threadx_queue_receive_wait_candidate`, `1001766c threadx_sleep_candidate`, `10013620 hp1020_send_or_raise_engine_msg_can...`

### `1001809c` `threadx_queue_receive_wait_candidate`

- size: `64`
- callers: `4`; calls: `1`
- calls: `10019eb4 FUN_10019eb4`

### `10013620` `hp1020_send_or_raise_engine_msg_candidate`

- size: `37`
- callers: `3`; calls: `2`
- calls: `10013668 FUN_10013668`, `10006f00 FUN_10006f00`

### `10015438` `hp1020_video_alt_render_candidate`

- size: `32`
- callers: `1`; calls: `1`
- calls: `100140f8 FUN_100140f8`

### `10013658` `hp1020_queue_send_candidate`

- size: `16`
- callers: `23`; calls: `1`
- calls: `10013668 FUN_10013668`

### `1001214c` `hp1020_task_ready_or_init_candidate`

- size: `14`
- callers: `3`; calls: `1`
- calls: `1001215c FUN_1001215c`

### `1000c8fc` `FUN_1000c8fc`

- size: `1094`
- callers: `1`; calls: `15`
- calls: `1001684c FUN_1001684c`, `1000c89c FUN_1000c89c`, `1000c850 FUN_1000c850`, `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`, `100169d4 FUN_100169d4`, `1001693c FUN_1001693c`, `10...`
- strings: `AUTOCONT`
- MMIO refs: `0xb1660609`

### `1000c230` `FUN_1000c230`

- size: `821`
- callers: `1`; calls: `6`
- calls: `1001b544 FUN_1001b544`, `1000b870 FUN_1000b870`, `1000ae3c FUN_1000ae3c`, `1001b668 FUN_1001b668`, `1001b6b0 FUN_1001b6b0`, `1000b9d8 FUN_1000b9d8`
- strings: `LPARM:`, `AUTOCONT`, `TIMEOUT`, `[2 RANGE]`, `ENUMERATED  READONLY]`, `ENUMERATED]`

### `1000f574` `FUN_1000f574`

- size: `672`
- callers: `1`; calls: `10`
- calls: `100130bc FUN_100130bc`, `1000fcb0 FUN_1000fcb0`, `10010158 FUN_10010158`, `10010170 FUN_10010170`, `1000f84c FUN_1000f84c`, `10010218 FUN_10010218`, `10013050 FUN_10013050`, `10...`

### `10019eb4` `FUN_10019eb4`

- size: `636`
- callers: `1`; calls: `5`
- calls: `1001bac4 FUN_1001bac4`, `1001aac0 FUN_1001aac0`, `10018750 FUN_10018750`, `1001a590 FUN_1001a590`, `100176c8 FUN_100176c8`

### `1000f84c` `FUN_1000f84c`

- size: `624`
- callers: `1`; calls: `5`
- calls: `100111b4 FUN_100111b4`, `1001005c FUN_1001005c`, `1000fabc FUN_1000fabc`, `10010158 FUN_10010158`, `100111d8 FUN_100111d8`
- MMIO refs: `0xb0986f82`

### `100144d0` `FUN_100144d0`

- size: `614`
- callers: `0`; calls: `8`
- calls: `10017dac FUN_10017dac`, `100140f8 FUN_100140f8`, `10014244 FUN_10014244`, `10013f34 FUN_10013f34`, `10013d4c FUN_10013d4c`, `10018214 FUN_10018214`, `100181a4 FUN_100181a4`, `10...`
- MMIO refs: `0xb1000004`, `0xb1000104`, `0xb1000000`, `0xb1000100`

### `1001a130` `FUN_1001a130`

- size: `592`
- callers: `1`; calls: `5`
- calls: `1001bac4 FUN_1001bac4`, `1001aac0 FUN_1001aac0`, `10018750 FUN_10018750`, `1001a590 FUN_1001a590`, `100176c8 FUN_100176c8`

### `100131b8` `FUN_100131b8`

- size: `578`
- callers: `7`; calls: `2`
- calls: `100181a4 FUN_100181a4`, `10018214 FUN_10018214`

### `10010838` `FUN_10010838`

- size: `516`
- callers: `0`; calls: `5`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`, `10013658 hp1020_queue_send_candidate`, `10010a8c FUN_10010a8c`, `10010a3c FUN_10010a3c`

### `10013d4c` `FUN_10013d4c`

- size: `456`
- callers: `3`; calls: `4`
- calls: `100171b0 FUN_100171b0`, `10017dac FUN_10017dac`, `1001608c FUN_1001608c`, `10013620 hp1020_send_or_raise_engine_msg_candidate`
- MMIO refs: `0xb2000010`, `0xb2080000`, `0xb2040000`, `0xb204000c`, `0xb208000c`

### `10013f34` `FUN_10013f34`

- size: `452`
- callers: `1`; calls: `1`
- calls: `1001b668 FUN_1001b668`
- MMIO refs: `0xb1000004`, `0xb1000008`, `0xb1000108`, `0xb100000c`, `0xb1000104`, `0xb100010c`

### `100176c8` `FUN_100176c8`

- size: `450`
- callers: `12`; calls: `1`
- calls: `10018750 FUN_10018750`

### `10010fd0` `FUN_10010fd0`

- size: `403`
- callers: `12`; calls: `7`
- calls: `10017e64 FUN_10017e64`, `10016a38 FUN_10016a38`, `1001b38c FUN_1001b38c`, `10017dac FUN_10017dac`, `10017ed8 FUN_10017ed8`, `10013658 hp1020_queue_send_candidate`, `100111d8 FUN...`

### `1000b870` `FUN_1000b870`

- size: `360`
- callers: `2`; calls: `4`
- calls: `10011178 FUN_10011178`, `10010f54 FUN_10010f54`, `100111d8 FUN_100111d8`, `100167f4 FUN_100167f4`

### `100140f8` `FUN_100140f8`

- size: `332`
- callers: `2`; calls: `2`
- calls: `10006f00 FUN_10006f00`, `1001b668 FUN_1001b668`
- strings: `refreshRawBands, ic.pBidBlock=0x%08x, nBackloggedBands=%u\n`
- MMIO refs: `0xb1000004`, `0xb1000008`, `0xb1000108`, `0xb100000c`, `0xb1000104`, `0xb100010c`

### `1000fcb0` `FUN_1000fcb0`

- size: `268`
- callers: `1`; calls: `1`
- calls: `10010218 FUN_10010218`

### `10016b50` `FUN_10016b50`

- size: `268`
- callers: `1`; calls: `2`
- calls: `1001b6b0 FUN_1001b6b0`, `1001b668 FUN_1001b668`
- MMIO refs: `0xb166c841`

### `1000fdbc` `FUN_1000fdbc`

- size: `229`
- callers: `1`; calls: `1`
- calls: `100130bc FUN_100130bc`

### `1000ed90` `FUN_1000ed90`

- size: `220`
- callers: `0`; calls: `1`
- calls: `10013658 hp1020_queue_send_candidate`

### `10015d14` `FUN_10015d14`

- size: `188`
- callers: `2`; calls: `1`
- calls: `10015c68 FUN_10015c68`

### `1000eeb8` `FUN_1000eeb8`

- size: `186`
- callers: `1`; calls: `7`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`, `100131b8 FUN_100131b8`, `10013658 hp1020_queue_send_candidate`, `10013408 FUN_10013408`, `10013050 FUN_10013050`, `1000f164 FUN...`

### `1000b624` `FUN_1000b624`

- size: `177`
- callers: `3`; calls: `7`
- calls: `1001b544 FUN_1001b544`, `1000a2a4 FUN_1000a2a4`, `100169d4 FUN_100169d4`, `10007430 FUN_10007430`, `100111b4 FUN_100111b4`, `100111d8 FUN_100111d8`, `10011178 FUN_10011178`
- strings: `CODE=`, `DISPLAY="`, `ONLINE=`, `FALSE`

### `1000aec0` `FUN_1000aec0`

- size: `176`
- callers: `1`; calls: `2`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`

### `10015c68` `FUN_10015c68`

- size: `172`
- callers: `4`; calls: `4`
- calls: `10017184 FUN_10017184`, `10017d28 FUN_10017d28`, `1001766c threadx_sleep_candidate`, `10013658 hp1020_queue_send_candidate`
- MMIO refs: `0xb0500004`, `0xb050000c`

### `10010170` `FUN_10010170`

- size: `168`
- callers: `1`; calls: `4`
- calls: `10010f54 FUN_10010f54`, `10010308 FUN_10010308`, `10010fd0 FUN_10010fd0`, `10013658 hp1020_queue_send_candidate`

### `10016a38` `FUN_10016a38`

- size: `155`
- callers: `2`; calls: `0`

### `10007180` `FUN_10007180`

- size: `152`
- callers: `1`; calls: `5`
- calls: `1001b38c FUN_1001b38c`, `1001b6b0 FUN_1001b6b0`, `1001b668 FUN_1001b668`, `100169d4 FUN_100169d4`, `10007070 FUN_10007070`

### `10007218` `FUN_10007218`

- size: `152`
- callers: `0`; calls: `5`
- calls: `1001b38c FUN_1001b38c`, `1001b6b0 FUN_1001b6b0`, `1001b668 FUN_1001b668`, `100169d4 FUN_100169d4`, `100070a8 FUN_100070a8`

### `1001a478` `FUN_1001a478`

- size: `144`
- callers: `1`; calls: `2`
- calls: `1001a590 FUN_1001a590`, `100176c8 FUN_100176c8`

### `10006f00` `FUN_10006f00`

- size: `140`
- callers: `2`; calls: `2`
- calls: `1001bb5c FUN_1001bb5c`, `10007430 FUN_10007430`
- strings: `%3d 0x%08x %8u`

### `10010cf0` `FUN_10010cf0`

- size: `137`
- callers: `1`; calls: `4`
- calls: `100181a4 FUN_100181a4`, `1001b38c FUN_1001b38c`, `10013658 hp1020_queue_send_candidate`, `10018214 FUN_10018214`

### `1001135c` `FUN_1001135c`

- size: `136`
- callers: `1`; calls: `6`
- calls: `100131b8 FUN_100131b8`, `1001766c threadx_sleep_candidate`, `100111b4 FUN_100111b4`, `1001b290 FUN_1001b290`, `1001b2c4 FUN_1001b2c4`, `100111d8 FUN_100111d8`

### `1001a508` `FUN_1001a508`

- size: `136`
- callers: `1`; calls: `3`
- calls: `1001bac4 FUN_1001bac4`, `1001aac0 FUN_1001aac0`, `10018750 FUN_10018750`

### `100072b0` `FUN_100072b0`

- size: `132`
- callers: `1`; calls: `5`
- calls: `1001b38c FUN_1001b38c`, `1001b6b0 FUN_1001b6b0`, `1001b668 FUN_1001b668`, `100169d4 FUN_100169d4`, `10007070 FUN_10007070`

### `10007334` `FUN_10007334`

- size: `132`
- callers: `0`; calls: `5`
- calls: `1001b38c FUN_1001b38c`, `1001b6b0 FUN_1001b6b0`, `1001b668 FUN_1001b668`, `100169d4 FUN_100169d4`, `100070a8 FUN_100070a8`

### `1000f0a8` `FUN_1000f0a8`

- size: `128`
- callers: `4`; calls: `2`
- calls: `10013050 FUN_10013050`, `10013408 FUN_10013408`

### `10010f54` `FUN_10010f54`

- size: `122`
- callers: `13`; calls: `3`
- calls: `100111b4 FUN_100111b4`, `10016a38 FUN_10016a38`, `1001b38c FUN_1001b38c`

### `10013140` `FUN_10013140`

- size: `118`
- callers: `4`; calls: `3`
- calls: `100131b8 FUN_100131b8`, `1001766c threadx_sleep_candidate`, `10013658 hp1020_queue_send_candidate`

### `10010298` `FUN_10010298`

- size: `110`
- callers: `1`; calls: `4`
- calls: `100130bc FUN_100130bc`, `100131b8 FUN_100131b8`, `1001766c threadx_sleep_candidate`, `10013000 FUN_10013000`

### `10010230` `FUN_10010230`

- size: `104`
- callers: `1`; calls: `1`
- calls: `10010218 FUN_10010218`

### `10013408` `FUN_10013408`

- size: `100`
- callers: `12`; calls: `2`
- calls: `100181a4 FUN_100181a4`, `10018214 FUN_10018214`

### `1001a590` `FUN_1001a590`

- size: `100`
- callers: `11`; calls: `0`

### `1000c89c` `FUN_1000c89c`

- size: `96`
- callers: `1`; calls: `3`
- calls: `1000d5b0 FUN_1000d5b0`, `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`

### `1000f164` `FUN_1000f164`

- size: `96`
- callers: `1`; calls: `3`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`, `10013658 hp1020_queue_send_candidate`

### `10010338` `FUN_10010338`

- size: `96`
- callers: `0`; calls: `4`
- calls: `10013140 FUN_10013140`, `1000f204 FUN_1000f204`, `100104c8 FUN_100104c8`, `10013658 hp1020_queue_send_candidate`

### `10010398` `FUN_10010398`

- size: `96`
- callers: `0`; calls: `5`
- calls: `10013140 FUN_10013140`, `1000f204 FUN_1000f204`, `10013658 hp1020_queue_send_candidate`, `1000f228 FUN_1000f228`, `100104c8 FUN_100104c8`

### `10010c98` `FUN_10010c98`

- size: `88`
- callers: `1`; calls: `3`
- calls: `100181a4 FUN_100181a4`, `10013658 hp1020_queue_send_candidate`, `10018214 FUN_10018214`

### `10014244` `FUN_10014244`

- size: `88`
- callers: `2`; calls: `0`
- MMIO refs: `0xb2080008`, `0xb2080004`

### `1001b38c` `FUN_1001b38c`

- size: `83`
- callers: `10`; calls: `0`

### `100100a8` `FUN_100100a8`

- size: `81`
- callers: `1`; calls: `3`
- calls: `100111b4 FUN_100111b4`, `100111d8 FUN_100111d8`, `10010218 FUN_10010218`

### `10010a3c` `FUN_10010a3c`

- size: `80`
- callers: `1`; calls: `4`
- calls: `10017e64 FUN_10017e64`, `1001766c threadx_sleep_candidate`, `1000b6d8 FUN_1000b6d8`, `10017ed8 FUN_10017ed8`

### `1000b174` `FUN_1000b174`

- size: `77`
- callers: `0`; calls: `6`
- calls: `10010f54 FUN_10010f54`, `10013408 FUN_10013408`, `100169d4 FUN_100169d4`, `1000dc00 FUN_1000dc00`, `1001693c FUN_1001693c`, `10010fd0 FUN_10010fd0`

### `1000b128` `FUN_1000b128`

- size: `76`
- callers: `0`; calls: `4`
- calls: `10013408 FUN_10013408`, `100169d4 FUN_100169d4`, `1000dc00 FUN_1000dc00`, `1001693c FUN_1001693c`

### `10017d28` `FUN_10017d28`

- size: `76`
- callers: `3`; calls: `1`
- calls: `10019408 FUN_10019408`

### `1000ed4c` `FUN_1000ed4c`

- size: `68`
- callers: `0`; calls: `2`
- calls: `100131b8 FUN_100131b8`, `10013658 hp1020_queue_send_candidate`

### `10016318` `FUN_10016318`

- size: `68`
- callers: `1`; calls: `0`

### `10008fb0` `FUN_10008fb0`

- size: `64`
- callers: `0`; calls: `5`
- calls: `100171b0 FUN_100171b0`, `100130bc FUN_100130bc`, `10013408 FUN_10013408`, `10013050 FUN_10013050`, `10017184 FUN_10017184`

### `1001307c` `FUN_1001307c`

- size: `64`
- callers: `0`; calls: `1`
- calls: `1001b770 FUN_1001b770`

### `100180dc` `FUN_100180dc`

- size: `64`
- callers: `2`; calls: `1`
- calls: `1001a130 FUN_1001a130`

### `10011178` `FUN_10011178`

- size: `60`
- callers: `6`; calls: `0`

### `1001b4c8` `FUN_1001b4c8`

- size: `59`
- callers: `2`; calls: `0`

### `1000eff8` `FUN_1000eff8`

- size: `56`
- callers: `0`; calls: `4`
- calls: `1000efd8 FUN_1000efd8`, `10013050 FUN_10013050`, `10013408 FUN_10013408`, `1000eeb8 FUN_1000eeb8`

### `10017e64` `FUN_10017e64`

- size: `56`
- callers: `4`; calls: `1`
- calls: `10019634 FUN_10019634`

### `100181a4` `FUN_100181a4`

- size: `56`
- callers: `8`; calls: `1`
- calls: `1001a478 FUN_1001a478`

### `1000f814` `FUN_1000f814`

- size: `54`
- callers: `1`; calls: `3`
- calls: `10013050 FUN_10013050`, `10013408 FUN_10013408`, `10013658 hp1020_queue_send_candidate`

### `1000f030` `FUN_1000f030`

- size: `53`
- callers: `0`; calls: `3`
- calls: `1000f0a8 FUN_1000f0a8`, `10013408 FUN_10013408`, `1000ef74 FUN_1000ef74`

### `10008b78` `FUN_10008b78`

- size: `52`
- callers: `0`; calls: `3`
- calls: `100130bc FUN_100130bc`, `10013408 FUN_10013408`, `10013050 FUN_10013050`

### `10013000` `FUN_10013000`

- size: `48`
- callers: `2`; calls: `1`
- calls: `1001b770 FUN_1001b770`

### `1001b668` `FUN_1001b668`

- size: `47`
- callers: `9`; calls: `0`

### `10012644` `FUN_10012644`

- size: `44`
- callers: `0`; calls: `2`
- calls: `100181a4 FUN_100181a4`, `1001766c threadx_sleep_candidate`

### `10013050` `FUN_10013050`

- size: `44`
- callers: `8`; calls: `1`
- calls: `1001b770 FUN_1001b770`

### `10017dac` `FUN_10017dac`

- size: `44`
- callers: `5`; calls: `1`
- calls: `1001896c FUN_1001896c`

### `1000ae94` `FUN_1000ae94`

- size: `42`
- callers: `2`; calls: `3`
- calls: `10010f54 FUN_10010f54`, `10011178 FUN_10011178`, `10010fd0 FUN_10010fd0`

### `1000ef90` `FUN_1000ef90`

- size: `42`
- callers: `0`; calls: `2`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`

### `100171b0` `FUN_100171b0`

- size: `39`
- callers: `5`; calls: `0`

### `1001215c` `FUN_1001215c`

- size: `38`
- callers: `2`; calls: `1`
- calls: `10017d28 FUN_10017d28`

### `10015dd0` `FUN_10015dd0`

- size: `37`
- callers: `2`; calls: `2`
- calls: `10010f54 FUN_10010f54`, `10010fd0 FUN_10010fd0`

### `1000f204` `FUN_1000f204`

- size: `36`
- callers: `4`; calls: `1`
- calls: `1001b4c8 FUN_1001b4c8`

### `100121e4` `FUN_100121e4`

- size: `36`
- callers: `0`; calls: `3`
- calls: `1001b770 FUN_1001b770`, `10009a10 FUN_10009a10`, `1001658c FUN_1001658c`

### `10017184` `FUN_10017184`

- size: `34`
- callers: `4`; calls: `0`

### `1000dc00` `FUN_1000dc00`

- size: `33`
- callers: `13`; calls: `2`
- calls: `100131b8 FUN_100131b8`, `1001766c threadx_sleep_candidate`

### `100111b4` `FUN_100111b4`

- size: `33`
- callers: `11`; calls: `1`
- calls: `100181a4 FUN_100181a4`

### `10013668` `FUN_10013668`

- size: `32`
- callers: `2`; calls: `1`
- calls: `100180dc FUN_100180dc`

### `10017ed8` `FUN_10017ed8`

- size: `29`
- callers: `4`; calls: `1`
- calls: `10019708 FUN_10019708`

### `10018214` `FUN_10018214`

- size: `29`
- callers: `8`; calls: `1`
- calls: `1001a508 FUN_1001a508`

### `1000efbc` `FUN_1000efbc`

- size: `26`
- callers: `1`; calls: `2`
- calls: `1000f0a8 FUN_1000f0a8`, `10013408 FUN_10013408`

### `1000bfb0` `FUN_1000bfb0`

- size: `24`
- callers: `1`; calls: `2`
- calls: `10011178 FUN_10011178`, `1000b624 FUN_1000b624`

### `10010158` `FUN_10010158`

- size: `24`
- callers: `3`; calls: `0`

### `10010218` `FUN_10010218`

- size: `24`
- callers: `5`; calls: `1`
- calls: `10013658 hp1020_queue_send_candidate`

### `1001b770` `FUN_1001b770`

- size: `24`
- callers: `5`; calls: `0`

### `1001658c` `FUN_1001658c`

- size: `21`
- callers: `1`; calls: `1`
- calls: `100171b0 FUN_100171b0`

### `100103f8` `FUN_100103f8`

- size: `20`
- callers: `0`; calls: `1`
- calls: `10013658 hp1020_queue_send_candidate`

### `1001040c` `FUN_1001040c`

- size: `20`
- callers: `0`; calls: `1`
- calls: `10013658 hp1020_queue_send_candidate`

### `100111d8` `FUN_100111d8`

- size: `20`
- callers: `12`; calls: `1`
- calls: `10018214 FUN_10018214`

### `100126b0` `FUN_100126b0`

- size: `20`
- callers: `0`; calls: `1`
- calls: `10018214 FUN_10018214`

### `1001b2c4` `FUN_1001b2c4`

- size: `17`
- callers: `2`; calls: `0`

### `1000dc24` `FUN_1000dc24`

- size: `14`
- callers: `1`; calls: `1`
- calls: `10013408 FUN_10013408`

### `10016098` `FUN_10016098`

- size: `13`
- callers: `1`; calls: `0`

### `10017414` `FUN_10017414`

- size: `13`
- callers: `1`; calls: `0`

### `1001608c` `FUN_1001608c`

- size: `12`
- callers: `1`; calls: `0`

### `100162b0` `FUN_100162b0`

- size: `10`
- callers: `1`; calls: `0`

### `1001b290` `FUN_1001b290`

- size: `9`
- callers: `2`; calls: `0`

### `100130bc` `FUN_100130bc`

- size: `8`
- callers: `6`; calls: `0`

### `10010310` `FUN_10010310`

- size: `5`
- callers: `1`; calls: `0`

### `10010318` `FUN_10010318`

- size: `5`
- callers: `1`; calls: `0`

## Interpretation

- `hp1020_engine_thread_candidate` is the main engine task entry and receives engine queue messages.
- `hp1020_engine_message_dispatch_candidate` is the next key dispatch function to understand.
- `hp1020_video_thread_candidate` receives video queue messages and calls the raster/video functions around `0x10014910`-`0x10015458`.
- MMIO references in this report are still partial but are now concentrated around engine/video functions instead of the whole firmware.
