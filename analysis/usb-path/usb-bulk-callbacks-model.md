# HP 1020 USB Bulk Callback Model

This offline static model checks saved decompilation against pinned original byte ranges. Historical RX-like export names are retained; the second callback is an outgoing send queue. No function or device is executed.

## Key Result

- `0x100087b8` is the stock read/copy callback: it drains USB receive bytes into the caller buffer and waits for more when empty.
- `0x10008bac` queues outgoing bytes and returns accepted length. It retains the source for later DMA/completion cleanup; it is not a receive-completion callback.
- `0x100081f4` calls that outgoing slot with timeout200. Queue acceptance is distinct from DMA release, FIFO settlement and host-visible receipt.

## Constants

| Name | Value |
|---|---:|
| `usb_status_register` | `0xb3000418` |
| `pending_transfer_list` | `0x10022740` |
| `bulk_tx_queue_state` | `0x100212d0` |
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
| `bulk_tx_queue_lock` | `0x1002274c` |

## Callback Roles

| Address | Name | Role | Meaning |
|---:|---|---|---|
| `0x100087b8` | `bulk_rx_read` | blocking/read-style copy path | Copies bytes from the stock USB receive buffer into the caller destination, waits on event bit 0x20000 when empty, and re-arms/acks the endpoint path. |
| `0x10008bac` | `bulk_tx_queue` | outgoing send/queue acceptance | On the normal queuing path, calls the cache-writeback helper and retains the caller source pointer and requested length in a 0x20-byte queue node, appends to list 0x10022740 and unmasks IN1 via bit1 of 0xb3000418. Returns accepted length before transmission; later done-head cleanup frees the retained source. |
| `0x100080f0` | `transfer_callback_a` | cached read wrapper | Serves cached bytes first, then calls the param_1+4 read slot with timeout policy. |
| `0x100081f4` | `transfer_callback_b` | send wrapper | Calls the registered outgoing slot at record+8 with source, length and timeout200; its return is queue acceptance, not host receipt. |

## Corrected Direction and Original Bytes

Startup registers 0x10008bac at record+8; 0x100081f4 forwards source/length/timeout there. The queue retains source/length and returns length; 0x10008b78 later frees done heads' original sources.

Static original instructions only. No semaphore/cache/MMIO/queue/completion executed. Current PJL transport pointer selection and host receipt remain unproved.

| Check | Status |
|---|---|
| `original_stock_elf` | `present` |
| `registration` | `present` |
| `callback-vtable` | `present` |
| `send-wrapper` | `present` |
| `in1-completed-list-drain` | `present` |
| `in1-submit-queue` | `present` |
| `startup-in1` | `present` |
| `pjl-send` | `present` |
| `cache-helper-call-boundary-only` | `present` |
| `stock-config-hs` | `present` |
| `stock-config-fs` | `present` |
| `registered_send` | `present` |
| `send_wrapper` | `present` |

## Open-Firmware Meaning

- The parser does not need direct USB MMIO access if an open replacement provides the same read-callback behavior.
- Bulk OUT feeds parser input; bulk IN separately carries outgoing replies. The return channel cannot be inferred from receive completion.
- Reuse bounded open ownership and buffers rather than HP heap queues. Keep queue acceptance, source/DMA release, FIFO settlement and host receipt distinct.

## Evidence Checks

- status: `pass`

| Status | Name | Evidence | Needle |
|---|---|---|---|
| `present` | `ghidra_export_has_read_callback` | `analysis/usb-path/usb-bulk-callbacks.md` | `100087b8` `hp1020_usb_bulk_rx_callback_a_candidate` |
| `present` | `ghidra_export_has_historically_rx_named_send_callback` | `analysis/usb-path/usb-bulk-callbacks.md` | `10008bac` `hp1020_usb_bulk_rx_callback_b_candidate` |
| `present` | `prepare_callback_expands_cache` | `analysis/usb-path/bulk-callbacks-decompiled/1000807c_hp1020_usb_transfer_prepare_callback_candidate.c` | `FUN_10013140(*(int *)(param_1 + 0x24) + param_3 + 0x100,1)` |
| `present` | `callback_a_invokes_read_slot` | `analysis/usb-path/bulk-callbacks-decompiled/100080f0_hp1020_usb_transfer_callback_a_candidate.c` | `(**(code **)(param_1 + 4))` |
| `present` | `callback_a_resets_to_0x400_buffer` | `analysis/usb-path/bulk-callbacks-decompiled/100080f0_hp1020_usb_transfer_callback_a_candidate.c` | `FUN_10013140(0x400,1)` |
| `present` | `callback_b_invokes_second_slot` | `analysis/usb-path/bulk-callbacks-decompiled/100081f4_hp1020_usb_transfer_callback_b_candidate.c` | `(**(code **)(param_1 + 8))(param_2,param_3,200)` |
| `present` | `bulk_read_waits_on_event_bit` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `FUN_10017d28(PTR_DAT_10005e18,DAT_10005e74,1,auStack_30,param_3)` |
| `present` | `bulk_read_copies_from_usb_buffer_to_destination` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `FUN_1001b38c(iVar4 + *(int *)PTR_DAT_10005e5c,*(int *)PTR_DAT_10005e44 + *(int *)puVar2` |
| `present` | `bulk_read_acks_endpoint_condition` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `*DAT_10005e70 = *DAT_10005e70 \| 0x100` |
| `present` | `bulk_read_rearms_receive_path` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `FUN_100086f4(0)` |
| `present` | `send_allocates_pending_node` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `FUN_10013140(0x20,1)` |
| `present` | `send_appends_pending_transfer` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `FUN_10013000(puVar1)` |
| `present` | `send_unmasks_in1_interrupt` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `*DAT_10005e00 = *DAT_10005e00 & 0xfffffffd` |
| `present` | `send_sets_queue_state_if_idle` | `analysis/usb-path/bulk-callbacks-decompiled/10008bac_hp1020_usb_bulk_rx_callback_b_candidate.c` | `*(undefined4 *)puVar1 = 1` |

