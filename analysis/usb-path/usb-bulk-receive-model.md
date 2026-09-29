# HP 1020 USB Bulk Receive Model

This is an offline static model. It does not contact the printer.

## Key Result

- USB2Thread registers a transfer record through `0x10007c00` using a `0x58` byte record stride.
- The helper allocator seeds a `0x400` byte receive buffer.
- USB2Thread creation loads separate control-block, name, entry and stack literals before calling `0x10018274`.
- Parser entry `0x10009d34` is registered separately in `0x10009b20`; adjacent literals are not a task descriptor.
- `0xb300022c` is the family-matched OUT1 max-packet register, not an endpoint acknowledgement register.
- The parser consumes bytes through a callback at `param_1 + 0x0c`, then sends JobMgr queue `3` messages.

## Constants

| Name | Value |
|---|---:|
| `transfer_token_shift_word` | `0x1001f238` |
| `transfer_ring_index` | `0x1001f214` |
| `transfer_ring_base` | `0x1001ec00` |
| `transfer_prepare_callback` | `0x1000807c` |
| `transfer_callback_a` | `0x100080f0` |
| `transfer_callback_b` | `0x100081f4` |
| `pending_transfer_list` | `0x10022740` |
| `completion_event_flags` | `0x10021318` |
| `transfer_state` | `0x100212d4` |
| `descriptor_pool_a` | `0x1001bc48` |
| `bulk_rx_size_word` | `0x1001bc50` |
| `bulk_rx_token_word` | `0x1001bc40` |
| `endpoint_config_word` | `0x10021590` |
| `bulk_rx_done_flag` | `0x1001bc72` |
| `descriptor_pool_b` | `0x1001bc58` |
| `registered_callback_a` | `0x100087b8` |
| `registered_callback_b` | `0x10008bac` |
| `bulk_rx_mask_word` | `0xfffcfffe` |
| `out1_max_packet_register` | `0xb300022c` |
| `usb2thread_event_bit` | `0x00010000` |
| `usb2thread_control_block` | `0x10021598` |
| `usb2thread_name` | `0x10003530` |
| `usb2thread_entry` | `0x10008ff0` |
| `usb2thread_stack_start` | `0x10022768` |
| `usb_saved_out1_nak_word` | `0x10021588` |
| `usb_saved_out0_nak_word` | `0x10021384` |
| `usb_pause_delay_argument` | `0x00030d40` |
| `parser_entry` | `0x10009d34` |
| `zjs_magic` | `0x1001bc78` |

## Thread Creation and Adjacent Literals

Original call `0x10009a08` invokes `0x10018274` with separately loaded values:

| Argument | Literal | Value |
|---|---|---|
| control block | `0x10005fc0` | `0x10021598` |
| name | `0x10005fc4` | `0x10003530` (`USB2Thread`) |
| entry | `0x10005fc8` | `0x10008ff0` |
| stack start | `0x10005fcc` | `0x10022768` |

The stack-size argument is `0x400` bytes.

The following `0x10005fd0/0x10005fd4` literals point to saved OUT1/OUT0 NAK words, and `0x10005fd8` supplies delay argument 200000. The original pause helper writes the saved words; the restore helper tests them. They are not thread-name/descriptor fields, and their values do not acknowledge DMA cancellation or quiescence.

## Transfer Record

- ring base: `0x1001ec00`
- ring index word: `0x1001f214`
- record stride: `0x58`
- buffer allocation: `0x400 bytes`

| Param word | Value | Record offset | Meaning |
|---:|---:|---:|---|
| `0` | `0x00000001` | `+0x2c` | transfer kind/endpoint selector candidate |
| `1` | `0x00000000` | `+0x38` | flags/timeout candidate |
| `2` | `0x100087b8` | `+0x04` | registered callback/function pointer A |
| `3` | `0x10008bac` | `+0x08` | registered callback/function pointer B |
| `4` | `0x00000000` | `+0x18` | state/argument slot candidate |
| `5` | `0x00000001` | `+0x54` | enable/ownership candidate |

## Parser Handoff

- USB2Thread entry: `0x10008ff0`
- independent parser-entry literal: `0x10005fdc`
- parser entry: `0x10009d34`
- parser registration: `0x10009b20`, call `0x10009b45` to `0x10007c98`
- ZjStream magic pointer: `0x1001bc78`
- parser read callback slot: `param_1 + 0x0c`
- parser output queue: `3`

## Open-Firmware Meaning

- The stock path separates USB transfer registration from ZjStream parsing through a callback table passed as parser param_1.
- An open firmware can keep the host-side ZjStream parser model, but still needs a bulk OUT receiver that can present a blocking/read callback at param_1+0x0c.
- The immediate software target after endpoint-0 proof is not video hardware; it is a small bulk-receive/read-callback shim that feeds the already-modeled ZjStream chunk loop.

## Evidence Checks

- status: `pass`

| Status | Evidence | Needle |
|---|---|---|
| `present` | `analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c` | `uStack_70 = 1;` |
| `present` | `analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c` | `puStack_68 = PTR_LAB_10005efc;` |
| `present` | `analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c` | `puStack_64 = PTR_LAB_10005f00;` |
| `present` | `analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c` | `uVar11 = hp1020_usb_register_transfer_candidate(&uStack_70);` |
| `present` | `analysis/usb-path/decompiled-neighbors/10007c00_hp1020_usb_register_transfer_candidate.c` | `puVar3 + iVar8 * 0x58` |
| `present` | `analysis/usb-path/decompiled-neighbors/10007c00_hp1020_usb_register_transfer_candidate.c` | `piVar6[1] = param_1[2];` |
| `present` | `analysis/usb-path/decompiled-neighbors/10007c00_hp1020_usb_register_transfer_candidate.c` | `piVar6[2] = param_1[3];` |
| `present` | `analysis/usb-path/decompiled-neighbors/10007c00_hp1020_usb_register_transfer_candidate.c` | `piVar6[0xb] = iVar5;` |
| `present` | `analysis/usb-path/decompiled-neighbors/10008034_FUN_10008034.c` | `FUN_10013140(0x400,1)` |
| `present` | `analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c` | `(**(code **)(param_1 + 0xc))` |
| `present` | `analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c` | `hp1020_queue_send_candidate(3,auStack_1d0)` |

## Original-byte Mapping Checks

Stock ELF SHA256: `2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d`.

| Address | Exact bytes | Meaning |
|---|---|---|
| `0x10005f08` | `b300022c` | out1_max_packet_register |
| `0x10005fc0` | `10021598` | usb2thread_control_block |
| `0x10005fc4` | `10003530` | usb2thread_name |
| `0x10005fc8` | `10008ff0` | usb2thread_entry |
| `0x10005fcc` | `10022768` | usb2thread_stack_start |
| `0x10005fd0` | `10021588` | usb_saved_out1_nak_word |
| `0x10005fd4` | `10021384` | usb_saved_out0_nak_word |
| `0x10005fd8` | `00030d40` | usb_pause_delay_argument |
| `0x10005fdc` | `10009d34` | parser_entry |
| `0x100099f2` | `1af173` | l32r a10,0x10005fc0: thread control-block argument |
| `0x100099f7` | `1bf173` | l32r a11,0x10005fc4: thread name argument |
| `0x100099fa` | `1cf173` | l32r a12,0x10005fc8: thread entry argument |
| `0x100099fd` | `1ef173` | l32r a14,0x10005fcc: thread stack argument |
| `0x10009a02` | `2f4a00` | movi a15,0x400: thread stack size |
| `0x10009a08` | `583a1a` | call8 0x10018274: thread creation call |
| `0x10009b23` | `18f12e` | l32r a8,0x10005fdc: separate parser-entry literal |
| `0x10009b26` | `1af12e` | l32r a10,0x10005fe0: separate parser magic literal |
| `0x10009b29` | `9810` | s32i.n a8,a1,0: parser entry in registration record word zero |
| `0x10009b3e` | `da10` | mov.n a10,a1: pass parser registration record |
| `0x10009b45` | `5bf854` | call8 0x10007c98: parser registration call |
| `0x10009a1d` | `1cf16c` | l32r a12,0x10005fd0: saved OUT1 NAK destination |
| `0x10009a28` | `1af112` | l32r a10,0x10005e70: OUT1 control address |
| `0x10009a2b` | `1bf0fe` | l32r a11,0x10005e24: OUT0 control address |
| `0x10009a31` | `88a0` | l32i.n a8,a10,0: read OUT1 control |
| `0x10009a33` | `c4d0` | movi.n a13,64: NAK bit mask |
| `0x10009a38` | `89b0` | l32i.n a9,a11,0: read OUT0 control |
| `0x10009a3a` | `0d8801` | and a8,a8,a13: isolate OUT1 NAK |
| `0x10009a3d` | `98c0` | s32i.n a8,a12,0: save OUT1 NAK word |
| `0x10009a4f` | `1af161` | l32r a10,0x10005fd4: saved OUT0 NAK destination |
| `0x10009a57` | `0d9901` | and a9,a9,a13: isolate OUT0 NAK |
| `0x10009a5a` | `99a0` | s32i.n a9,a10,0: save OUT0 NAK word |
| `0x10009a5f` | `1af15e` | l32r a10,0x10005fd8: delay argument |
| `0x10009a6a` | `581f20` | call8 0x100116ec: delay-service call |
| `0x10009a85` | `12f152` | l32r a2,0x10005fd0: saved OUT1 NAK source |
| `0x10009a88` | `8220` | l32i.n a2,a2,0: read saved OUT1 NAK word |
| `0x10009a8a` | `cd22` | bnez.n a2,0x10009aa0: nonzero saved OUT1 word skips CNAK path |
| `0x10009aa0` | `12f14d` | l32r a2,0x10005fd4: saved OUT0 NAK source |
| `0x10009aa3` | `8220` | l32i.n a2,a2,0: read saved OUT0 NAK word |
| `0x10009aa5` | `cd21` | bnez.n a2,0x10009aba: nonzero saved OUT0 word skips CNAK path |
| `0x1000924e` | `1af32e` | l32r a10,0x10005f08: OUT1 max-packet register address |
| `0x10009262` | `18f2fb` | l32r a8,0x10005e50: packet-size global address |
| `0x10009268` | `8880` | l32i.n a8,a8,0: packet-size value |
| `0x1000926f` | `98a0` | s32i.n a8,a10,0: write packet-size value |
| `0x10003530` | `5553423254687265616400` | actual thread-name string |
| `0x10005e70` | `b3000220` | OUT1 control-address literal |
| `0x10005e24` | `b3000200` | OUT0 control-address literal |

Family layout supports NAK/max-packet naming; it does not identify HP silicon or establish quiescence.

