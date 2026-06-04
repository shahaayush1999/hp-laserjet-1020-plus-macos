# HP 1020 Boot ABI Map

This pass maps the firmware startup and runtime interface anchors relevant to any custom firmware experiment.

## Loaded Memory Blocks

| Block | Start | End | Size | Permissions |
|---|---:|---:|---:|---|
| `.WindowVectors.text` | `10000000` | `1000017f` | `384` | `R-X` |
| `.KernelExceptionVector.literal` | `10000180` | `10000183` | `4` | `R-X` |
| `.KernelExceptionVector.text` | `10000200` | `1000021b` | `28` | `R-X` |
| `.UserExceptionVector.literal` | `1000021c` | `1000021f` | `4` | `R-X` |
| `.UserExceptionVector.text` | `10000220` | `1000023b` | `28` | `R-X` |
| `.DoubleExceptionVector.text` | `10000270` | `1000034f` | `224` | `R-X` |
| `.sys_interface_table` | `10000370` | `1000049b` | `300` | `RW-` |
| `.rodata` | `10003000` | `10005c7f` | `11392` | `R--` |
| `.text` | `10005c80` | `1001bb8e` | `89871` | `R-X` |
| `.data` | `1001bb90` | `1001d63f` | `6832` | `RW-` |
| `.bss` | `1001d640` | `100351df` | `97184` | `RW-` |
| `.ResetVector.text` | `10100020` | `101002ff` | `736` | `R-X` |
| `.DebugExceptionVector.literal` | `10100300` | `10100303` | `4` | `R-X` |
| `.DebugExceptionVector.text` | `10100320` | `1010032b` | `12` | `R-X` |
| `.comment` | `.comment::00000000` | `.comment::00002df4` | `11765` | `---` |
| `.shstrtab` | `.shstrtab::00000000` | `.shstrtab::00000308` | `777` | `---` |
| `.xt.insn` | `.xt.insn::00000000` | `.xt.insn::00000d97` | `3480` | `---` |
| `.xt.lit` | `.xt.lit::00000000` | `.xt.lit::0000022f` | `560` | `---` |
| `_elfHeader` | `_elfHeader::00000000` | `_elfHeader::00000033` | `52` | `---` |
| `_elfProgramHeaders` | `_elfProgramHeaders::00000000` | `_elfProgramHeaders::0000015f` | `352` | `---` |
| `_elfSectionHeaders` | `_elfSectionHeaders::00000000` | `_elfSectionHeaders::00000617` | `1560` | `---` |
| `unallocated_0` | `unallocated_0::00000000` | `unallocated_0::00000003` | `4` | `---` |

## Boot Anchors

| Anchor | Address | Notes |
|---|---:|---|
| Reset vector section | `0x10100020` | `.ResetVector.text`, 736 bytes |
| ELF entry point | `0x100167a8` | ELF header entry |
| System interface table | `0x10000370` | 75 function-pointer entries in `.sys_interface_table` |

## System Interface Table

The `.sys_interface_table` is a boot/runtime ABI-looking function pointer table. Queue, sleep, event, and helper functions used by tasks appear here.

| Index | Table address | Function pointer | Label / description |
|---:|---:|---:|---|
| `00` | `0x10000370` | `0x10017af4` | `hp1020_sys_interface_00_candidate` |
| `01` | `0x10000374` | `0x10017b64` | `hp1020_sys_interface_01_candidate` |
| `02` | `0x10000378` | `0x10017bc8` | `hp1020_sys_interface_02_candidate` |
| `03` | `0x1000037c` | `0x10017c00` | `hp1020_sys_interface_03_candidate` |
| `04` | `0x10000380` | `0x10017c3c` | `hp1020_sys_interface_04_candidate` |
| `05` | `0x10000384` | `0x10017c5c` | `hp1020_sys_interface_05_candidate` |
| `06` | `0x10000388` | `0x10017988` | `hp1020_sys_interface_06_candidate` |
| `07` | `0x1000038c` | `0x100179c8` | `hp1020_sys_interface_07_candidate` |
| `08` | `0x10000390` | `0x10017a38` | `hp1020_sys_interface_08_candidate` |
| `09` | `0x10000394` | `0x10017a70` | `hp1020_sys_interface_09_candidate` |
| `10` | `0x10000398` | `0x10017aac` | `hp1020_sys_interface_10_candidate` |
| `11` | `0x1000039c` | `0x10017acc` | `hp1020_sys_interface_11_candidate` |
| `12` | `0x100003a0` | `0x10017ca0` | `hp1020_sys_interface_12_candidate` |
| `13` | `0x100003a4` | `0x10017cf0` | `hp1020_sys_interface_13_candidate` |
| `14` | `0x100003a8` | `0x10017d28` | `hp1020_sys_interface_14_candidate` |
| `15` | `0x100003ac` | `0x10017d74` | `hp1020_sys_interface_15_candidate` |
| `16` | `0x100003b0` | `0x10017dac` | `hp1020_sys_interface_16_candidate` |
| `17` | `0x100003b4` | `0x1001b770` | `hp1020_sys_interface_17_candidate` |
| `18` | `0x100003b8` | `0x10017f18` | `hp1020_sys_interface_18_candidate` |
| `19` | `0x100003bc` | `0x10017f90` | `hp1020_sys_interface_19_candidate` |
| `20` | `0x100003c0` | `0x10017fc8` | `hp1020_sys_interface_20_candidate` |
| `21` | `0x100003c4` | `0x10018040` | `hp1020_sys_interface_21_candidate` |
| `22` | `0x100003c8` | `0x1001809c` | `threadx_queue_receive_wait_candidate` |
| `23` | `0x100003cc` | `0x100180dc` | `threadx_queue_send_candidate` |
| `24` | `0x100003d0` | `0x10018000` | `hp1020_sys_interface_24_candidate` |
| `25` | `0x100003d4` | `0x1001807c` | `hp1020_sys_interface_25_candidate` |
| `26` | `0x100003d8` | `0x1001811c` | `hp1020_sys_interface_26_candidate` |
| `27` | `0x100003dc` | `0x1001816c` | `hp1020_sys_interface_27_candidate` |
| `28` | `0x100003e0` | `0x100181a4` | `threadx_memory_or_copy_candidate` |
| `29` | `0x100003e4` | `0x100181dc` | `hp1020_sys_interface_29_candidate` |
| `30` | `0x100003e8` | `0x10018234` | `hp1020_sys_interface_30_candidate` |
| `31` | `0x100003ec` | `0x10018214` | `hp1020_sys_interface_31_candidate` |
| `32` | `0x100003f0` | `0x10017dd8` | `hp1020_sys_interface_32_candidate` |
| `33` | `0x100003f4` | `0x10017e2c` | `hp1020_sys_interface_33_candidate` |
| `34` | `0x100003f8` | `0x10017e64` | `hp1020_sys_interface_34_candidate` |
| `35` | `0x100003fc` | `0x10017e9c` | `hp1020_sys_interface_35_candidate` |
| `36` | `0x10000400` | `0x10017ef8` | `hp1020_sys_interface_36_candidate` |
| `37` | `0x10000404` | `0x10017ed8` | `hp1020_sys_interface_37_candidate` |
| `38` | `0x10000408` | `0x10018274` | `hp1020_sys_interface_38_candidate` |
| `39` | `0x1000040c` | `0x10018324` | `hp1020_sys_interface_39_candidate` |
| `40` | `0x10000410` | `0x100175c0` | `threadx_or_timer_service_candidate` |
| `41` | `0x10000414` | `0x10018354` | `hp1020_sys_interface_41_candidate` |
| `42` | `0x10000418` | `0x100184ac` | `hp1020_sys_interface_42_candidate` |
| `43` | `0x1000041c` | `0x10018524` | `hp1020_sys_interface_43_candidate` |
| `44` | `0x10000420` | `0x10018508` | `hp1020_sys_interface_44_candidate` |
| `45` | `0x10000424` | `0x100184e8` | `hp1020_sys_interface_45_candidate` |
| `46` | `0x10000428` | `0x1001766c` | `threadx_sleep_candidate` |
| `47` | `0x1000042c` | `0x10018560` | `hp1020_sys_interface_47_candidate` |
| `48` | `0x10000430` | `0x10018590` | `hp1020_sys_interface_48_candidate` |
| `49` | `0x10000434` | `0x100185c0` | `hp1020_sys_interface_49_candidate` |
| `50` | `0x10000438` | `0x100185fc` | `hp1020_sys_interface_50_candidate` |
| `51` | `0x1000043c` | `0x100175cc` | `hp1020_sys_interface_51_candidate` |
| `52` | `0x10000440` | `0x100175e0` | `hp1020_sys_interface_52_candidate` |
| `53` | `0x10000444` | `0x10018254` | `hp1020_sys_interface_53_candidate` |
| `54` | `0x10000448` | `0x1001840c` | `hp1020_sys_interface_54_candidate` |
| `55` | `0x1000044c` | `0x10018444` | `hp1020_sys_interface_55_candidate` |
| `56` | `0x10000450` | `0x10018304` | `hp1020_sys_interface_56_candidate` |
| `57` | `0x10000454` | `0x1001839c` | `hp1020_sys_interface_57_candidate` |
| `58` | `0x10000458` | `0x100183d4` | `hp1020_sys_interface_58_candidate` |
| `59` | `0x1000045c` | `0x100131b8` | `hp1020_runtime_service_candidate` |
| `60` | `0x10000460` | `0x10013408` | `hp1020_runtime_service_2_candidate` |
| `61` | `0x10000464` | `0x100116ec` | `hp1020_system_service_candidate` |
| `62` | `0x10000468` | `0x10010f54` | `hp1020_event_flag_get_candidate` |
| `63` | `0x1000046c` | `0x10010fd0` | `hp1020_event_flag_set_candidate` |
| `64` | `0x10000470` | `0x10010f44` | `hp1020_sys_interface_64_candidate` |
| `65` | `0x10000474` | `0x10011178` | `hp1020_sys_interface_65_candidate` |
| `66` | `0x10000478` | `0x100111b4` | `hp1020_sys_interface_66_candidate` |
| `67` | `0x1000047c` | `0x100111d8` | `hp1020_sys_interface_67_candidate` |
| `68` | `0x10000480` | `0x100111ec` | `hp1020_sys_interface_68_candidate` |
| `69` | `0x10000484` | `0x10011204` | `hp1020_sys_interface_69_candidate` |
| `70` | `0x10000488` | `0x10011218` | `hp1020_sys_interface_70_candidate` |
| `71` | `0x1000048c` | `0x10011258` | `hp1020_register_event_handler_candidate` |
| `72` | `0x10000490` | `0x100112d4` | `hp1020_sys_interface_72_candidate` |
| `73` | `0x10000494` | `0x1001135c` | `hp1020_register_or_signal_message_candidate` |
| `74` | `0x10000498` | `0x100113e4` | `hp1020_sys_interface_74_candidate` |

## Early Function Summary

| Function | Size | Calls | Referenced strings / MMIO |
|---:|---:|---|---|
| `0x10100020` `hp1020_reset_vector_candidate` | `1` |  |  |
| `0x100167a8` `hp1020_elf_entry_candidate` | `25` | `0x10006cd0` `FUN_10006cd0` | program `0x10006a14` block `.text`<br>program `0x10006cd0` `FUN_10006cd0` |
| `0x10006bb0` `hp1020_early_boot_or_init_candidate` | `205` |  | program `0x10005c80` block `.text`<br>MMIO `0xb0800008`<br>program `0x10006bf0` inside `hp1020_early_boot_or_init_candidate` + `0x40`<br>program `0x10006bea` inside `hp1020_early_boot_or_init_candidate` + `0x3a`<br>pr... |
| `0x10010f54` `hp1020_event_flag_get_candidate` | `122` | `0x100111b4` `hp1020_sys_interface_66_candidate`<br>`0x10016a38` `FUN_10016a38`<br>`0x1001b38c` `FUN_1001b38c` | program `0x1000647c` block `.text`<br>program `0x100111b4` `hp1020_sys_interface_66_candidate`<br>program `0x10010fcc` inside `hp1020_event_flag_get_candidate` + `0x78`<br>program `0x1001ce1c` block `.data`<br>program... |
| `0x10010fd0` `hp1020_event_flag_set_candidate` | `403` | `0x10017e64` `hp1020_sys_interface_34_candidate`<br>`0x10016a38` `FUN_10016a38`<br>`0x1001b38c` `FUN_1001b38c`<br>`0x10017dac` `hp1020_sys_interface_16_candidate`<br>`0x10017ed8` `hp1020_sys_interface_37_candidate`<br... | program `0x1000647c` block `.text`<br>program `0x1001ce28` block `.data`<br>program `0x10011031` inside `hp1020_event_flag_set_candidate` + `0x61`<br>program `0x1001ce1c` block `.data`<br>program `0x100064a8` block `.... |
| `0x10011258` `hp1020_register_event_handler_candidate` | `124` | `0x100131b8` `hp1020_runtime_service_candidate`<br>`0x1001766c` `threadx_sleep_candidate`<br>`0x100111b4` `hp1020_sys_interface_66_candidate`<br>`0x1001b290` `FUN_1001b290`<br>`0x1001b2c4` `FUN_1001b2c4`<br>`0x100111d... | program `0x100131b8` `hp1020_runtime_service_candidate`<br>program `0x10011277` inside `hp1020_register_event_handler_candidate` + `0x1f`<br>program `0x1001766c` `threadx_sleep_candidate`<br>program `0x1001125d` insid... |
| `0x1001135c` `hp1020_register_or_signal_message_candidate` | `136` | `0x100131b8` `hp1020_runtime_service_candidate`<br>`0x1001766c` `threadx_sleep_candidate`<br>`0x100111b4` `hp1020_sys_interface_66_candidate`<br>`0x1001b290` `FUN_1001b290`<br>`0x1001b2c4` `FUN_1001b2c4`<br>`0x100111d... | program `0x100131b8` `hp1020_runtime_service_candidate`<br>program `0x1001137b` inside `hp1020_register_or_signal_message_candidate` + `0x1f`<br>program `0x1001766c` `threadx_sleep_candidate`<br>program `0x10011361` i... |
| `0x100116ec` `hp1020_system_service_candidate` | `68` | `0x1001bb5c` `FUN_1001bb5c` | program `0x1001bb5c` `FUN_1001bb5c`<br>program `0x10005dfc` block `.text`<br>program `0x1001bff0` block `.data`<br>program `0x1001171c` inside `hp1020_system_service_candidate` + `0x30`<br>program `0x10011707` inside ... |
| `0x100131b8` `hp1020_runtime_service_candidate` | `578` | `0x100181a4` `threadx_memory_or_copy_candidate`<br>`0x10018214` `hp1020_sys_interface_31_candidate` | program `0x100066bc` block `.text`<br>program `0x1002c90c` block `.bss`<br>program `0x100131d4` inside `hp1020_runtime_service_candidate` + `0x1c`<br>program `0x100131d9` inside `hp1020_runtime_service_candidate` + `0... |
| `0x10013408` `hp1020_runtime_service_2_candidate` | `100` | `0x100181a4` `threadx_memory_or_copy_candidate`<br>`0x10018214` `hp1020_sys_interface_31_candidate` | program `0x10013410` inside `hp1020_runtime_service_2_candidate` + `0x8`<br>program `0x100066ac` block `.text`<br>program `0x100181a4` `threadx_memory_or_copy_candidate`<br>program `0x100066a8` block `.text`<br>progra... |
| `0x100175c0` `threadx_or_timer_service_candidate` | `12` |  | program `0x10006a9c` block `.text`<br>program `0x10034f5c` block `.bss` |
| `0x1001766c` `threadx_sleep_candidate` | `92` | `0x1001a590` `FUN_1001a590`<br>`0x100176c8` `FUN_100176c8` | program `0x10006a9c` block `.text`<br>program `0x10034f5c` block `.bss`<br>program `0x10017684` inside `threadx_sleep_candidate` + `0x18`<br>program `0x10006ae8` block `.text`<br>program `0x10005d80` block `.text`<br>... |
| `0x10017af4` `hp1020_sys_interface_00_candidate` | `112` | `0x10018eac` `FUN_10018eac` | program `0x10017b01` inside `hp1020_sys_interface_00_candidate` + `0xd`<br>program `0x10006b10` block `.text`<br>program `0x10017b05` inside `hp1020_sys_interface_00_candidate` + `0x11`<br>program `0x10017b0c` inside ... |
| `0x10017b64` `hp1020_sys_interface_01_candidate` | `100` | `0x10018f64` `FUN_10018f64` | program `0x10017b71` inside `hp1020_sys_interface_01_candidate` + `0xd`<br>program `0x10006b10` block `.text`<br>program `0x10017b75` inside `hp1020_sys_interface_01_candidate` + `0x11`<br>program `0x10017b7c` inside ... |
| `0x1001809c` `threadx_queue_receive_wait_candidate` | `64` | `0x10019eb4` `FUN_10019eb4` | program `0x100180a9` inside `threadx_queue_receive_wait_candidate` + `0xd`<br>program `0x100065e8` block `.text`<br>program `0x100180ad` inside `threadx_queue_receive_wait_candidate` + `0x11`<br>program `0x100180b4` i... |
| `0x100180dc` `threadx_queue_send_candidate` | `64` | `0x1001a130` `FUN_1001a130` | program `0x100180e9` inside `threadx_queue_send_candidate` + `0xd`<br>program `0x100065e8` block `.text`<br>program `0x100180ed` inside `threadx_queue_send_candidate` + `0x11`<br>program `0x100180f4` inside `threadx_q... |
| `0x100181a4` `threadx_memory_or_copy_candidate` | `56` | `0x1001a478` `FUN_1001a478` | program `0x100181b1` inside `threadx_memory_or_copy_candidate` + `0xd`<br>program `0x100065bc` block `.text`<br>program `0x100181b5` inside `threadx_memory_or_copy_candidate` + `0x11`<br>program `0x100181cd` inside `t... |

## Reset/Entry Reference Notes

Direct references found from the reset vector and ELF entry candidates:

| Function | References |
|---:|---|
| `0x10100020` `hp1020_reset_vector_candidate` |  |
| `0x100167a8` `hp1020_elf_entry_candidate` | program `0x10006a14` block `.text`<br>program `0x10006cd0` `FUN_10006cd0` |

## Interpretation

Current boot/runtime ABI read:

- The ELF is not a freestanding flat binary. It carries Xtensa vectors, a reset vector section, a system interface table, `.data`, and `.bss`.
- `.sys_interface_table` is likely part of the boot ROM / firmware ABI boundary. It contains the queue primitives and task/runtime services used throughout the firmware.
- A custom firmware experiment needs to preserve enough of this ABI shape for the boot ROM to load and jump correctly.
- The immediate next unknown is whether the boot ROM uses only the ELF program headers and entry point, or also validates/uses HP-specific interface table slots.

Practical implication: the safest prototype target is a minimal ELF that keeps the same section/header/interface-table shape and changes behavior only after early startup is understood.
