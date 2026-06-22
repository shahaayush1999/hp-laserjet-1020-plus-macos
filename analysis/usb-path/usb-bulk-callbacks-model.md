# HP 1020 USB Bulk Callback Model

This is an offline static model built from saved Ghidra decompilation. It does not contact the printer.

## Key Result

- `0x100087b8` is the stock read/copy callback: it drains USB receive bytes into the caller buffer and waits for more when empty.
- `0x10008bac` is the stock completion/queue callback: it creates a pending-transfer node, clears a USB status bit, and wakes the receive state.
- The ZjStream parser can be kept behind a read-callback shim; the missing open-code piece is the USB bulk OUT producer that feeds that shim.

## Constants

| Name | Value |
|---|---:|
| `usb_status_register` | `0xb3000418` |
| `pending_transfer_list` | `0x10022740` |
| `bulk_completion_state` | `0x100212d0` |
| `completion_event_flags` | `0x10021318` |
| `bulk_done_byte` | `0x1001bc70` |
| `bulk_destination_alias` | `0x80000000` |
| `bulk_available_size_word` | `0x1001bc50` |
| `bulk_source_offset_word` | `0x1001bc4c` |
| `bulk_rearm_word` | `0x100216c0` |
| `bulk_source_base_word` | `0x1001bc40` |
| `bulk_suppress_copy_byte` | `0x1001bc6f` |
| `bulk_remaining_request_word` | `0x1001bc54` |
| `bulk_threshold_word` | `0x10021590` |
| `bulk_next_pointer_word` | `0x1001bc44` |
| `bulk_destination_offset_word` | `0x10021594` |
| `usb_setup_status_register` | `0xb3000408` |
| `usb_setup_status_mask` | `0x00008000` |
| `usb_endpoint_ack_register` | `0xb3000220` |
| `bulk_event_bit` | `0x00020000` |
| `bulk_rearm_flag_byte` | `0x1001bc71` |
| `bulk_completion_lock` | `0x1002274c` |

## Callback Roles

| Address | Name | Role | Meaning |
|---:|---|---|---|
| `0x100087b8` | `bulk_rx_read` | blocking/read-style copy path | Copies bytes from the stock USB receive buffer into the caller destination, waits on event bit 0x20000 when empty, and re-arms/acks the endpoint path. |
| `0x10008bac` | `bulk_rx_complete` | completion/queue path | Allocates a 0x20 byte pending-transfer node, appends it to list 0x10022740, clears bit 1 in USB status register 0xb3000418, and marks completion state 0x100212d0 active when idle. |
| `0x100080f0` | `transfer_callback_a` | cached read wrapper | Serves cached bytes first, then calls the param_1+4 read slot with timeout policy. |
| `0x100081f4` | `transfer_callback_b` | secondary read wrapper | Calls the param_1+8 slot with a fixed timeout of 200. |

## Open-Firmware Meaning

- The parser does not need direct USB MMIO access if an open replacement provides the same read-callback behavior.
- The real USB work is a bulk OUT producer that fills a buffer, sets event bit 0x20000, tracks remaining bytes, and re-arms endpoint receive.
- The next open-code prototype target after endpoint-0 proof is a small bulk-receive ring plus parser callback shim, not the print engine.

## Evidence Checks

- status: `pass`

| Status | Name | Evidence | Needle |
|---|---|---|---|
| `present` | `ghidra_export_has_read_callback` | `analysis/usb-path/usb-bulk-callbacks.md` | `100087b8` `hp1020_usb_bulk_rx_callback_a_candidate` |
| `present` | `ghidra_export_has_completion_callback` | `analysis/usb-path/usb-bulk-callbacks.md` | `10008bac` `hp1020_usb_bulk_rx_callback_b_candidate` |
| `present` | `prepare_callback_expands_cache` | `analysis/usb-path/bulk-callbacks-decompiled/1000807c_hp1020_usb_transfer_prepare_callback_candidate.c` | `FUN_10013140(*(int *)(param_1 + 0x24) + param_3 + 0x100,1)` |
| `present` | `callback_a_invokes_read_slot` | `analysis/usb-path/bulk-callbacks-decompiled/100080f0_hp1020_usb_transfer_callback_a_candidate.c` | `(**(code **)(param_1 + 4))` |
| `present` | `callback_a_resets_to_0x400_buffer` | `analysis/usb-path/bulk-callbacks-decompiled/100080f0_hp1020_usb_transfer_callback_a_candidate.c` | `FUN_10013140(0x400,1)` |
| `present` | `callback_b_invokes_second_slot` | `analysis/usb-path/bulk-callbacks-decompiled/100081f4_hp1020_usb_transfer_callback_b_candidate.c` | `(**(code **)(param_1 + 8))(param_2,param_3,200)` |
| `present` | `bulk_read_waits_on_event_bit` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `FUN_10017d28(PTR_DAT_10005e18,DAT_10005e74,1,auStack_30,param_3)` |
| `present` | `bulk_read_copies_from_usb_buffer_to_destination` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `FUN_1001b38c(iVar4 + *(int *)PTR_DAT_10005e5c,*(int *)PTR_DAT_10005e44 + *(int *)puVar2` |
| `present` | `bulk_read_acks_endpoint_condition` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `*DAT_10005e70 = *DAT_10005e70 \| 0x100` |
| `present` | `bulk_read_rearms_receive_path` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `FUN_100086f4(0)` |
| `present` | `completion_allocates_pending_node` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `FUN_10013140(0x20,1)` |
| `present` | `completion_appends_pending_transfer` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `FUN_10013000(puVar1)` |
| `present` | `completion_clears_usb_status_bit` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `*DAT_10005e00 = *DAT_10005e00 & 0xfffffffd` |
| `present` | `completion_sets_state_if_idle` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `*(undefined4 *)puVar1 = 1` |

