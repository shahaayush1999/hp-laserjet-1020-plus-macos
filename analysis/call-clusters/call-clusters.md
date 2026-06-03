# HP 1020 Function Call Clusters

This is a coarse automated clustering pass over Ghidra functions. It is intended to guide manual reverse engineering, not to be treated as final naming.

- Total functions: `326`
- Known labels are seeded from earlier USB/PJL/identity passes.
- Hardware references are partial because many MMIO addresses are loaded through literal tables.

## Cluster Counts

- USB control and enumeration: `12`
- PJL, ACL, and printer identity/status: `4`
- Memory/string/runtime helpers: `33`
- RTOS/threading/scheduler candidates: `96`
- Hardware register or SRAM touch points: `0`
- Other or unresolved: `181`

## USB control and enumeration

### `10008c24` `hp1020_usb_control_tx_data_stage_candidate`

- size: `796` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_100173c8@100173c8`, `FUN_1001b38c@1001b38c`, `threadx_queue_receive_candidate@10017d28`
- MMIO refs: `b3000000`, `b300000c`, `b3000014`
- SRAM refs: `900226f8`, `900226f9`, `900226fa`, `900226fb`, `900226f4`, `900226f5`, `900226f6`, `900226f7`, `900226fc`, `900226fd`

### `10007c00` `hp1020_usb_register_transfer_candidate`

- size: `92` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_10008034@10008034`

### `10008fb0` `hp1020_usb_drain_pending_queue_candidate`

- size: `64` bytes/addresses
- callers: `0`; calls: `5`
- calls: `FUN_100171b0@100171b0`, `FUN_100130bc@100130bc`, `FUN_10013408@10013408`, `FUN_10013050@10013050`, `FUN_10017184@10017184`

### `1000899c` `FUN_1000899c`

- size: `476` bytes/addresses
- callers: `0`; calls: `0`
- MMIO refs: `b3000034`, `b3000418`, `b3000020`
- SRAM refs: `900216d0`, `900216d1`, `900216d2`, `900216d3`

### `100086f4` `FUN_100086f4`

- size: `196` bytes/addresses
- callers: `0`; calls: `0`
- MMIO refs: `b3000234`
- SRAM refs: `90021378`, `90021379`, `9002137a`, `9002137b`, `90021370`, `9002137c`, `9002137d`, `9002137e`, `9002137f`, `90021371`

### `10009a10` `FUN_10009a10`

- size: `96` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_100116ec@100116ec`
- MMIO refs: `b3000404`, `b3000220`, `b3000200`

### `10007cd0` `FUN_10007cd0`

- size: `73` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_10017ca0@10017ca0`, `threadx_thread_create_candidate@10018274`
- strings: `SysParserEventFlags`

### `10008034` `FUN_10008034`

- size: `72` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_10013140@10013140`, `FUN_1001b38c@1001b38c`

### `10008b78` `FUN_10008b78`

- size: `52` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_100130bc@100130bc`, `FUN_10013408@10013408`, `FUN_10013050@10013050`

### `10007c70` `FUN_10007c70`

- size: `37` bytes/addresses
- callers: `0`; calls: `0`

### `10009ac4` `FUN_10009ac4`

- size: `28` bytes/addresses
- callers: `0`; calls: `0`

### `10007c5c` `FUN_10007c5c`

- size: `18` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_10017dac@10017dac`

## PJL, ACL, and printer identity/status

### `1000bd04` `hp1020_pjl_info_capabilities_builder`

- size: `684` bytes/addresses
- callers: `1`; calls: `6`
- calls: `FUN_100111b4@100111b4`, `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_100111d8@100111d8`, `FUN_1000bad8@1000bad8`, `FUN_100134fc@100134fc`, `hp10...`
- strings: `IN TRAYS [`, ` ENUMERATED]`, `\tINTRAY1 PRIORITY`, `\tINTRAY1 MP`, `\tINTRAY2 PAPERTRAY`, `\tINTRAY3 PAPERTRAY`, `PAPERS [17 ENUMERATED]`, `LANGUAGES [3 ENUM...`

### `1000b3f8` `hp1020_pjl_ustatus_result_builder`

- size: `294` bytes/addresses
- callers: `0`; calls: `7`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_strlen_like@100169d4`, `hp1020_format_into_buffer_candidate@10007430`, `hp1020_alloc_buffer_candi...`
- strings: `RESULT=`, `CANCELED`, `PARSEERROR`

### `1000d6b0` `hp1020_pjl_read_or_poll_candidate`

- size: `80` bytes/addresses
- callers: `12`; calls: `2`
- calls: `FUN_1000d674@1000d674`, `FUN_1000dd60@1000dd60`

### `1000cdb0` `hp1020_pjl_echo_matcher`

- size: `76` bytes/addresses
- callers: `1`; calls: `2`
- calls: `hp1020_strlen_like@100169d4`, `hp1020_pjl_read_or_poll_candidate@1000d6b0`

## Memory/string/runtime helpers

### `100169d4` `hp1020_strlen_like`

- size: `73` bytes/addresses
- callers: `26`; calls: `0`

### `10007430` `hp1020_format_into_buffer_candidate`

- size: `56` bytes/addresses
- callers: `11`; calls: `1`
- calls: `FUN_10007468@10007468`

### `1001b544` `hp1020_append_string_to_buffer_candidate`

- size: `40` bytes/addresses
- callers: `17`; calls: `0`

### `1000dc00` `hp1020_alloc_buffer_candidate`

- size: `33` bytes/addresses
- callers: `13`; calls: `2`
- calls: `FUN_100131b8@100131b8`, `FUN_1001766c@1001766c`

### `1000c8fc` `FUN_1000c8fc`

- size: `1094` bytes/addresses
- callers: `1`; calls: `15`
- calls: `FUN_1001684c@1001684c`, `FUN_1000c89c@1000c89c`, `FUN_1000c850@1000c850`, `FUN_10010f54@10010f54`, `FUN_10010fd0@10010fd0`, `hp1020_strlen_like@100169d4`, `h...`
- strings: `AUTOCONT`

### `1000c230` `FUN_1000c230`

- size: `821` bytes/addresses
- callers: `1`; calls: `6`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_1000b870@1000b870`, `FUN_1000ae3c@1000ae3c`, `FUN_1001b668@1001b668`, `FUN_1001b6b0@1001b6b0`, `FUN_...`
- strings: `LPARM:`, `AUTOCONT`, `TIMEOUT`, ` [2 RANGE]`, ` ENUMERATED  READONLY]`, ` ENUMERATED]`

### `1000bfc8` `FUN_1000bfc8`

- size: `613` bytes/addresses
- callers: `1`; calls: `2`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_format_into_buffer_candidate@10007430`
- strings: ` [2 ENUMERATED]`, `PAGE=`, `DEVICE=`, `VERBOSE`, ` [3 ENUMERATED]`, `TIMED=`, ` [2 RANGE]`

### `1000bad8` `FUN_1000bad8`

- size: `556` bytes/addresses
- callers: `1`; calls: `1`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`
- strings: `LETTER`, `LEGAL`, `EXECUTIVE`, `COM10`, `MONARCH`, `B5 ENVELOPE`, `B5 (JIS)`, `JAPANESE POSTCARD`

### `1000c69c` `FUN_1000c69c`

- size: `436` bytes/addresses
- callers: `1`; calls: `13`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_1000b808@1000b808`, `FUN_1001684c@1001684c`, `FUN_1000b870@1000b870`, `FUN_1000ae3c@1000ae3c`, `FUN_...`
- strings: `INQUIRE `

### `1000d700` `FUN_1000d700`

- size: `381` bytes/addresses
- callers: `0`; calls: `7`
- calls: `hp1020_strlen_like@100169d4`, `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd60@1000dd60`, `FUN_1000af88@1000af88`, `FUN_1000dda8@1000dda8`, `hp102...`
- strings: `AUXINIT`, `AUXSAVE`

### `1000c568` `FUN_1000c568`

- size: `305` bytes/addresses
- callers: `0`; calls: `15`
- calls: `FUN_1001684c@1001684c`, `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_100111b4@100111b4`, `FUN_100111d8@100111d8`, `hp1020_pjl_info_capabilities_...`
- strings: `CONFIG`

### `1000b520` `FUN_1000b520`

- size: `258` bytes/addresses
- callers: `0`; calls: `7`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_strlen_like@100169d4`, `hp1020_format_into_buffer_candidate@10007430`, `hp1020_alloc_buffer_candi...`
- strings: `RESULT=`

### `1000d5b0` `FUN_1000d5b0`

- size: `193` bytes/addresses
- callers: `3`; calls: `2`
- calls: `hp1020_strlen_like@100169d4`, `FUN_1001684c@1001684c`

### `1000b1d4` `FUN_1000b1d4`

- size: `188` bytes/addresses
- callers: `3`; calls: `7`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_1000ae3c@1000ae3c`, `hp1020_strlen_like@100169d4`, `hp1020_alloc_buffer_candidate@1000dc00`, `hp1020...`

### `1000b344` `FUN_1000b344`

- size: `178` bytes/addresses
- callers: `0`; calls: `6`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_strlen_like@100169d4`, `hp1020_alloc_buffer_candidate@1000dc00`, `hp1020_copy_string_candidate@10...`

### `1000b624` `FUN_1000b624`

- size: `177` bytes/addresses
- callers: `3`; calls: `7`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_1000a2a4@1000a2a4`, `hp1020_strlen_like@100169d4`, `hp1020_format_into_buffer_candidate@10007430`, `...`
- strings: `CODE=`, `DISPLAY="`, `ONLINE=`, `FALSE`

### `1000b6d8` `FUN_1000b6d8`

- size: `156` bytes/addresses
- callers: `1`; calls: `8`
- calls: `FUN_1000a2a4@1000a2a4`, `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_strlen_like@100169d4`, `FUN_1000b624@1000b624`, `FUN_1000b1c4@1000b1c4`,...`

### `1000b2a8` `FUN_1000b2a8`

- size: `154` bytes/addresses
- callers: `0`; calls: `7`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_strlen_like@100169d4`, `hp1020_format_into_buffer_candidate@10007430`, `hp1020_alloc_buffer_candi...`

### `10007180` `FUN_10007180`

- size: `152` bytes/addresses
- callers: `1`; calls: `5`
- calls: `FUN_1001b38c@1001b38c`, `FUN_1001b6b0@1001b6b0`, `FUN_1001b668@1001b668`, `hp1020_strlen_like@100169d4`, `FUN_10007070@10007070`

### `10007218` `FUN_10007218`

- size: `152` bytes/addresses
- callers: `0`; calls: `5`
- calls: `FUN_1001b38c@1001b38c`, `FUN_1001b6b0@1001b6b0`, `FUN_1001b668@1001b668`, `hp1020_strlen_like@100169d4`, `FUN_100070a8@100070a8`

### `1000b774` `FUN_1000b774`

- size: `148` bytes/addresses
- callers: `0`; calls: `8`
- calls: `FUN_1000a2a4@1000a2a4`, `hp1020_append_string_to_buffer_candidate@1001b544`, `hp1020_strlen_like@100169d4`, `FUN_1000b624@1000b624`, `FUN_1000b1c4@1000b1c4`,...`

### `100072b0` `FUN_100072b0`

- size: `132` bytes/addresses
- callers: `1`; calls: `5`
- calls: `FUN_1001b38c@1001b38c`, `FUN_1001b6b0@1001b6b0`, `FUN_1001b668@1001b668`, `hp1020_strlen_like@100169d4`, `FUN_10007070@10007070`

### `10007334` `FUN_10007334`

- size: `132` bytes/addresses
- callers: `0`; calls: `5`
- calls: `FUN_1001b38c@1001b38c`, `FUN_1001b6b0@1001b6b0`, `FUN_1001b668@1001b668`, `hp1020_strlen_like@100169d4`, `FUN_100070a8@100070a8`

### `1000dba8` `FUN_1000dba8`

- size: `88` bytes/addresses
- callers: `0`; calls: `3`
- calls: `hp1020_strlen_like@100169d4`, `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd60@1000dd60`

### `100070e0` `FUN_100070e0`

- size: `80` bytes/addresses
- callers: `1`; calls: `2`
- calls: `hp1020_strlen_like@100169d4`, `FUN_10007070@10007070`

### `10007130` `FUN_10007130`

- size: `80` bytes/addresses
- callers: `0`; calls: `2`
- calls: `hp1020_strlen_like@100169d4`, `FUN_100070a8@100070a8`

### `1000ba48` `FUN_1000ba48`

- size: `80` bytes/addresses
- callers: `1`; calls: `3`
- calls: `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_100134fc@100134fc`, `hp1020_format_into_buffer_candidate@10007430`
- strings: `TOTAL=`

### `1000b174` `FUN_1000b174`

- size: `77` bytes/addresses
- callers: `0`; calls: `6`
- calls: `FUN_10010f54@10010f54`, `FUN_10013408@10013408`, `hp1020_strlen_like@100169d4`, `hp1020_alloc_buffer_candidate@1000dc00`, `hp1020_copy_string_candidate@10016...`

### `1000b128` `FUN_1000b128`

- size: `76` bytes/addresses
- callers: `0`; calls: `4`
- calls: `FUN_10013408@10013408`, `hp1020_strlen_like@100169d4`, `hp1020_alloc_buffer_candidate@1000dc00`, `hp1020_copy_string_candidate@1001693c`

### `1000ba98` `FUN_1000ba98`

- size: `64` bytes/addresses
- callers: `1`; calls: `4`
- calls: `FUN_100111b4@100111b4`, `hp1020_format_into_buffer_candidate@10007430`, `hp1020_append_string_to_buffer_candidate@1001b544`, `FUN_100111d8@100111d8`

### `1000cd44` `FUN_1000cd44`

- size: `30` bytes/addresses
- callers: `5`; calls: `1`
- calls: `hp1020_strlen_like@100169d4`

### `1000b290` `FUN_1000b290`

- size: `24` bytes/addresses
- callers: `6`; calls: `1`
- calls: `hp1020_strlen_like@100169d4`

### `1000b1c4` `FUN_1000b1c4`

- size: `14` bytes/addresses
- callers: `9`; calls: `1`
- calls: `hp1020_strlen_like@100169d4`

## RTOS/threading/scheduler candidates

### `10018274` `threadx_thread_create_candidate`

- size: `144` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_1001a610@1001a610`

### `10017d28` `threadx_queue_receive_candidate`

- size: `76` bytes/addresses
- callers: `3`; calls: `1`
- calls: `FUN_10019408@10019408`

### `10019b7c` `FUN_10019b7c`

- size: `824` bytes/addresses
- callers: `0`; calls: `5`
- calls: `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`, `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019eb4` `FUN_10019eb4`

- size: `636` bytes/addresses
- callers: `1`; calls: `5`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`, `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `1001a130` `FUN_1001a130`

- size: `592` bytes/addresses
- callers: `1`; calls: `5`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`, `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `1001896c` `FUN_1001896c`

- size: `536` bytes/addresses
- callers: `1`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `100176c8` `FUN_100176c8`

- size: `450` bytes/addresses
- callers: `12`; calls: `1`
- calls: `FUN_10018750@10018750`

### `1001a950` `FUN_1001a950`

- size: `365` bytes/addresses
- callers: `0`; calls: `2`
- calls: `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019708` `FUN_10019708`

- size: `344` bytes/addresses
- callers: `1`; calls: `5`
- calls: `FUN_1001b918@1001b918`, `FUN_10019860@10019860`, `FUN_10018750@10018750`, `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`

### `10019860` `FUN_10019860`

- size: `324` bytes/addresses
- callers: `2`; calls: `1`
- calls: `FUN_1001aac0@1001aac0`

### `1001b128` `FUN_1001b128`

- size: `311` bytes/addresses
- callers: `2`; calls: `1`
- calls: `FUN_100176c8@100176c8`

### `100187e0` `FUN_100187e0`

- size: `271` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_1001b128@1001b128`

### `10019138` `FUN_10019138`

- size: `252` bytes/addresses
- callers: `0`; calls: `4`
- calls: `FUN_10019234@10019234`, `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019234` `FUN_10019234`

- size: `212` bytes/addresses
- callers: `2`; calls: `0`

### `10019634` `FUN_10019634`

- size: `212` bytes/addresses
- callers: `1`; calls: `3`
- calls: `FUN_10019860@10019860`, `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `10019408` `FUN_10019408`

- size: `204` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `1001aac0` `FUN_1001aac0`

- size: `185` bytes/addresses
- callers: `19`; calls: `0`

### `10018d48` `FUN_10018d48`

- size: `184` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10018eac` `FUN_10018eac`

- size: `184` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_10019234@10019234`, `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `1001906c` `FUN_1001906c`

- size: `184` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019350` `FUN_10019350`

- size: `184` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019a30` `FUN_10019a30`

- size: `184` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019580` `FUN_10019580`

- size: `180` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `1001a3c4` `FUN_1001a3c4`

- size: `180` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10018b84` `FUN_10018b84`

- size: `164` bytes/addresses
- callers: `0`; calls: `2`
- calls: `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `10018e14` `FUN_10018e14`

- size: `152` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10019ae8` `FUN_10019ae8`

- size: `148` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `1001a478` `FUN_1001a478`

- size: `144` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `1001a6dc` `FUN_1001a6dc`

- size: `144` bytes/addresses
- callers: `1`; calls: `0`

### `1001ad9c` `FUN_1001ad9c`

- size: `144` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `10018750` `FUN_10018750`

- size: `141` bytes/addresses
- callers: `21`; calls: `1`
- calls: `FUN_1001b128@1001b128`

### `100199a4` `FUN_100199a4`

- size: `140` bytes/addresses
- callers: `0`; calls: `0`

### `1001861c` `FUN_1001861c`

- size: `139` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_10016d6f@10016d6f`

### `10018c28` `FUN_10018c28`

- size: `136` bytes/addresses
- callers: `0`; calls: `0`

### `1001a508` `FUN_1001a508`

- size: `136` bytes/addresses
- callers: `1`; calls: `3`
- calls: `FUN_1001bac4@1001bac4`, `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `100188f0` `FUN_100188f0`

- size: `122` bytes/addresses
- callers: `1`; calls: `0`

### `1001a8d8` `FUN_1001a8d8`

- size: `120` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_10018750@10018750`

### `1001b7b4` `FUN_1001b7b4`

- size: `116` bytes/addresses
- callers: `0`; calls: `0`

### `1001b854` `FUN_1001b854`

- size: `116` bytes/addresses
- callers: `0`; calls: `0`

### `1001b918` `FUN_1001b918`

- size: `116` bytes/addresses
- callers: `1`; calls: `0`

### `1001b9b8` `FUN_1001b9b8`

- size: `116` bytes/addresses
- callers: `0`; calls: `0`

### `1001ba50` `FUN_1001ba50`

- size: `116` bytes/addresses
- callers: `0`; calls: `0`

### `10018f64` `FUN_10018f64`

- size: `112` bytes/addresses
- callers: `0`; calls: `0`

### `1001a868` `FUN_1001a868`

- size: `112` bytes/addresses
- callers: `0`; calls: `0`

### `1001ac7c` `FUN_1001ac7c`

- size: `104` bytes/addresses
- callers: `0`; calls: `2`
- calls: `FUN_1001bac4@1001bac4`, `FUN_100176c8@100176c8`

### `1001a590` `FUN_1001a590`

- size: `100` bytes/addresses
- callers: `11`; calls: `0`

### `1001abcc` `FUN_1001abcc`

- size: `98` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_10018750@10018750`

### `1001766c` `FUN_1001766c`

- size: `92` bytes/addresses
- callers: `9`; calls: `2`
- calls: `FUN_1001a590@1001a590`, `FUN_100176c8@100176c8`

### `1001b718` `FUN_1001b718`

- size: `86` bytes/addresses
- callers: `1`; calls: `0`

### `1001a7c0` `FUN_1001a7c0`

- size: `85` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_1001a590@1001a590`

### `1001a76c` `FUN_1001a76c`

- size: `84` bytes/addresses
- callers: `0`; calls: `0`

### `1001ad20` `FUN_1001ad20`

- size: `84` bytes/addresses
- callers: `0`; calls: `0`

### `1001b38c` `FUN_1001b38c`

- size: `83` bytes/addresses
- callers: `10`; calls: `0`

### `10017ca0` `FUN_10017ca0`

- size: `80` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_10019308@10019308`

### `100194e8` `FUN_100194e8`

- size: `80` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_10017554@10017554`, `FUN_100175f4@100175f4`

### `1001a818` `FUN_1001a818`

- size: `80` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_1001bac4@1001bac4`

### `1001ab7c` `FUN_1001ab7c`

- size: `80` bytes/addresses
- callers: `0`; calls: `2`
- calls: `FUN_1001aac0@1001aac0`, `FUN_10018750@10018750`

### `1001ac30` `FUN_1001ac30`

- size: `76` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_100176c8@100176c8`

### `10019308` `FUN_10019308`

- size: `72` bytes/addresses
- callers: `1`; calls: `0`

### `10019538` `FUN_10019538`

- size: `72` bytes/addresses
- callers: `0`; calls: `0`

### `1001a380` `FUN_1001a380`

- size: `68` bytes/addresses
- callers: `0`; calls: `0`

### `1001bac4` `FUN_1001bac4`

- size: `68` bytes/addresses
- callers: `18`; calls: `0`

### `1001b5b8` `FUN_1001b5b8`

- size: `65` bytes/addresses
- callers: `1`; calls: `0`

### `1001809c` `FUN_1001809c`

- size: `64` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_10019eb4@10019eb4`

### `100180dc` `FUN_100180dc`

- size: `64` bytes/addresses
- callers: `2`; calls: `1`
- calls: `FUN_1001a130@1001a130`

### `1001b488` `FUN_1001b488`

- size: `64` bytes/addresses
- callers: `0`; calls: `0`

### `1001b4c8` `FUN_1001b4c8`

- size: `59` bytes/addresses
- callers: `2`; calls: `0`

### `10017e64` `FUN_10017e64`

- size: `56` bytes/addresses
- callers: `4`; calls: `1`
- calls: `FUN_10019634@10019634`

### `100181a4` `FUN_100181a4`

- size: `56` bytes/addresses
- callers: `8`; calls: `1`
- calls: `FUN_1001a478@1001a478`

### `1001bb08` `FUN_1001bb08`

- size: `56` bytes/addresses
- callers: `0`; calls: `0`

### `1001839c` `FUN_1001839c`

- size: `53` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_1001a818@1001a818`

### `1001b618` `FUN_1001b618`

- size: `53` bytes/addresses
- callers: `2`; calls: `0`

### `1001b668` `FUN_1001b668`

- size: `47` bytes/addresses
- callers: `9`; calls: `0`

### `10017dac` `FUN_10017dac`

- size: `44` bytes/addresses
- callers: `5`; calls: `1`
- calls: `FUN_1001896c@1001896c`

### `1001b788` `FUN_1001b788`

- size: `44` bytes/addresses
- callers: `0`; calls: `0`

### `1001b828` `FUN_1001b828`

- size: `44` bytes/addresses
- callers: `0`; calls: `0`

### `1001b8ec` `FUN_1001b8ec`

- size: `44` bytes/addresses
- callers: `0`; calls: `0`

### `1001b98c` `FUN_1001b98c`

- size: `44` bytes/addresses
- callers: `0`; calls: `0`

### `1001ad74` `FUN_1001ad74`

- size: `40` bytes/addresses
- callers: `0`; calls: `0`

### `1001b6b0` `FUN_1001b6b0`

- size: `40` bytes/addresses
- callers: `6`; calls: `0`

- ... `16` more
## Hardware register or SRAM touch points

## Other or unresolved

### `1001693c` `hp1020_copy_string_candidate`

- size: `75` bytes/addresses
- callers: `15`; calls: `0`

### `10011178` `hp1020_get_config_value_candidate`

- size: `60` bytes/addresses
- callers: `6`; calls: `0`

### `10014910` `FUN_10014910`

- size: `2305` bytes/addresses
- callers: `0`; calls: `6`
- calls: `hp1020_get_config_value_candidate@10011178`, `FUN_100181a4@100181a4`, `FUN_100171b0@100171b0`, `FUN_1001b668@1001b668`, `FUN_1001b4c8@1001b4c8`, `FUN_1001718...`

### `100117e8` `FUN_100117e8`

- size: `696` bytes/addresses
- callers: `1`; calls: `7`
- calls: `FUN_10011ba0@10011ba0`, `FUN_10011aa0@10011aa0`, `FUN_10011c44@10011c44`, `FUN_10011d2c@10011d2c`, `FUN_100116ec@100116ec`, `FUN_1001b618@1001b618`, `FUN_100...`

### `1000f574` `FUN_1000f574`

- size: `672` bytes/addresses
- callers: `0`; calls: `10`
- calls: `FUN_100130bc@100130bc`, `FUN_1000fcb0@1000fcb0`, `FUN_10010158@10010158`, `FUN_10010170@10010170`, `FUN_1000f84c@1000f84c`, `FUN_10010218@10010218`, `FUN_100...`

### `1000f84c` `FUN_1000f84c`

- size: `624` bytes/addresses
- callers: `1`; calls: `5`
- calls: `FUN_100111b4@100111b4`, `FUN_1001005c@1001005c`, `FUN_1000fabc@1000fabc`, `FUN_10010158@10010158`, `FUN_100111d8@100111d8`

### `100144d0` `FUN_100144d0`

- size: `614` bytes/addresses
- callers: `0`; calls: `8`
- calls: `FUN_10017dac@10017dac`, `FUN_100140f8@100140f8`, `FUN_10014244@10014244`, `FUN_10013f34@10013f34`, `FUN_10013d4c@10013d4c`, `FUN_10018214@10018214`, `FUN_100...`

### `10007468` `FUN_10007468`

- size: `605` bytes/addresses
- callers: `1`; calls: `6`
- calls: `FUN_10016cc8@10016cc8`, `FUN_10007038@10007038`, `FUN_100073b8@100073b8`, `FUN_10007180@10007180`, `FUN_100072b0@100072b0`, `FUN_100070e0@100070e0`

### `100131b8` `FUN_100131b8`

- size: `578` bytes/addresses
- callers: `7`; calls: `2`
- calls: `FUN_100181a4@100181a4`, `FUN_10018214@10018214`

### `10015df8` `FUN_10015df8`

- size: `556` bytes/addresses
- callers: `1`; calls: `4`
- calls: `FUN_10015c68@10015c68`, `FUN_10015dd0@10015dd0`, `FUN_10013658@10013658`, `FUN_10013d4c@10013d4c`

### `10015214` `FUN_10015214`

- size: `548` bytes/addresses
- callers: `0`; calls: `4`
- calls: `FUN_1001b770@1001b770`, `FUN_10017184@10017184`, `FUN_10017414@10017414`, `FUN_10014244@10014244`

### `10010838` `FUN_10010838`

- size: `516` bytes/addresses
- callers: `0`; calls: `5`
- calls: `FUN_10010f54@10010f54`, `FUN_10010fd0@10010fd0`, `FUN_10013658@10013658`, `FUN_10010a8c@10010a8c`, `FUN_10010a3c@10010a3c`

### `1000fabc` `FUN_1000fabc`

- size: `500` bytes/addresses
- callers: `1`; calls: `4`
- calls: `FUN_1000fea4@1000fea4`, `FUN_100100fc@100100fc`, `FUN_10010128@10010128`, `FUN_1000fee8@1000fee8`

### `10016ef8` `FUN_10016ef8`

- size: `494` bytes/addresses
- callers: `1`; calls: `0`

### `10009b4c` `FUN_10009b4c`

- size: `488` bytes/addresses
- callers: `0`; calls: `2`
- calls: `FUN_1000f204@1000f204`, `FUN_1000f1c4@1000f1c4`

### `10013d4c` `FUN_10013d4c`

- size: `456` bytes/addresses
- callers: `3`; calls: `4`
- calls: `FUN_100171b0@100171b0`, `FUN_10017dac@10017dac`, `FUN_1001608c@1001608c`, `FUN_10013620@10013620`

### `10013f34` `FUN_10013f34`

- size: `452` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_1001b668@1001b668`

### `1000e1dc` `FUN_1000e1dc`

- size: `440` bytes/addresses
- callers: `0`; calls: `13`
- calls: `FUN_1000da5c@1000da5c`, `FUN_1001684c@1001684c`, `hp1020_alloc_buffer_candidate@1000dc00`, `hp1020_copy_string_candidate@1001693c`, `FUN_1000dda8@1000dda8`, ...`
- strings: `LPARM`

### `10010fd0` `FUN_10010fd0`

- size: `403` bytes/addresses
- callers: `12`; calls: `7`
- calls: `FUN_10017e64@10017e64`, `FUN_10016a38@10016a38`, `FUN_1001b38c@1001b38c`, `FUN_10017dac@10017dac`, `FUN_10017ed8@10017ed8`, `FUN_10013658@10013658`, `FUN_100...`

### `1000fee8` `FUN_1000fee8`

- size: `369` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_100100fc@100100fc`, `FUN_10010128@10010128`

### `1000e070` `FUN_1000e070`

- size: `362` bytes/addresses
- callers: `1`; calls: `4`
- calls: `hp1020_copy_string_candidate@1001693c`, `FUN_1000dda8@1000dda8`, `FUN_1001684c@1001684c`, `FUN_1000d5b0@1000d5b0`

### `1000b870` `FUN_1000b870`

- size: `360` bytes/addresses
- callers: `2`; calls: `4`
- calls: `hp1020_get_config_value_candidate@10011178`, `FUN_10010f54@10010f54`, `FUN_100111d8@100111d8`, `FUN_100167f4@100167f4`

### `1000da5c` `FUN_1000da5c`

- size: `332` bytes/addresses
- callers: `2`; calls: `3`
- calls: `FUN_1000d9b0@1000d9b0`, `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd60@1000dd60`

### `100140f8` `FUN_100140f8`

- size: `332` bytes/addresses
- callers: `2`; calls: `2`
- calls: `FUN_10006f00@10006f00`, `FUN_1001b668@1001b668`
- strings: `refreshRawBands, ic.pBidBlock=0x%08x, nBackloggedBands=%u\n`

### `10016164` `FUN_10016164`

- size: `332` bytes/addresses
- callers: `0`; calls: `10`
- calls: `FUN_10013658@10013658`, `FUN_10016098@10016098`, `FUN_10015df8@10015df8`, `FUN_100180dc@100180dc`, `FUN_10013620@10013620`, `FUN_10015dd0@10015dd0`, `FUN_100...`

### `1000afec` `FUN_1000afec`

- size: `314` bytes/addresses
- callers: `0`; calls: `4`
- calls: `FUN_100107fc@100107fc`, `FUN_1001079c@1001079c`, `FUN_10010cf0@10010cf0`, `FUN_10010c98@10010c98`

### `1000d880` `FUN_1000d880`

- size: `304` bytes/addresses
- callers: `0`; calls: `6`
- calls: `FUN_1000da5c@1000da5c`, `FUN_1001684c@1001684c`, `FUN_1000dda8@1000dda8`, `FUN_1000e070@1000e070`, `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd6...`

### `10016d23` `FUN_10016d23`

- size: `298` bytes/addresses
- callers: `0`; calls: `3`
- calls: `FUN_10016ef8@10016ef8`, `FUN_10016eb8@10016eb8`, `FUN_1001861c@1001861c`

### `1000d2a8` `FUN_1000d2a8`

- size: `276` bytes/addresses
- callers: `0`; calls: `4`
- calls: `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd60@1000dd60`, `FUN_1000dd7c@1000dd7c`, `hp1020_pjl_echo_matcher@1000cdb0`
- strings: `FORMAT : BINARY`

### `10011d2c` `FUN_10011d2c`

- size: `270` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_100116ec@100116ec`

### `100165a4` `FUN_100165a4`

- size: `270` bytes/addresses
- callers: `0`; calls: `2`
- calls: `FUN_10010f54@10010f54`, `FUN_10010fd0@10010fd0`

### `1000fcb0` `FUN_1000fcb0`

- size: `268` bytes/addresses
- callers: `1`; calls: `1`
- calls: `FUN_10010218@10010218`

### `10016b50` `FUN_10016b50`

- size: `268` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_1001b6b0@1001b6b0`, `FUN_1001b668@1001b668`

### `1000dde8` `FUN_1000dde8`

- size: `240` bytes/addresses
- callers: `1`; calls: `3`
- calls: `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd60@1000dd60`, `FUN_1000dda8@1000dda8`

### `1000ded8` `FUN_1000ded8`

- size: `240` bytes/addresses
- callers: `1`; calls: `3`
- calls: `hp1020_pjl_read_or_poll_candidate@1000d6b0`, `FUN_1000dd60@1000dd60`, `FUN_1000dda8@1000dda8`

### `10011c44` `FUN_10011c44`

- size: `232` bytes/addresses
- callers: `1`; calls: `2`
- calls: `FUN_10011b20@10011b20`, `FUN_100116ec@100116ec`

### `1000fdbc` `FUN_1000fdbc`

- size: `229` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_100130bc@100130bc`

### `1000ed90` `FUN_1000ed90`

- size: `220` bytes/addresses
- callers: `0`; calls: `1`
- calls: `FUN_10013658@10013658`

### `10006cd0` `FUN_10006cd0`

- size: `211` bytes/addresses
- callers: `1`; calls: `0`

### `10015d14` `FUN_10015d14`

- size: `188` bytes/addresses
- callers: `2`; calls: `1`
- calls: `FUN_10015c68@10015c68`

- ... `141` more
