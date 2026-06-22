# HP 1020 USB Bulk Receive Model

This is an offline static model. It does not contact the printer.

## Key Result

- USB2Thread registers a transfer record through `0x10007c00` using a `0x58` byte record stride.
- The helper allocator seeds a `0x400` byte receive buffer.
- The task descriptor at `0x10005fc4` wires USB2Thread to parser entry `0x10009d34`.
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
| `endpoint_ack_register` | `0xb300022c` |
| `usb2thread_event_bit` | `0x00010000` |
| `usb2thread_descriptor_word0` | `0x10003530` |
| `usb2thread_name` | `0x10021588` |
| `parser_entry` | `0x10009d34` |
| `zjs_magic` | `0x1001bc78` |

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

- USB2Thread descriptor: `0x10005fc4`
- USB2Thread entry: `0x10008ff0`
- parser entry: `0x10009d34`
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

