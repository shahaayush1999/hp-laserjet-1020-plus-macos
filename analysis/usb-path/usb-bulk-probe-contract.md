# HP 1020 USB Bulk Probe Contract

This generated allowlist combines the existing endpoint-0 map with only the stock-evidenced bulk OUT registers needed by the non-printing parser probe.

- status: `pass`
- total allowed USB registers: `21`
- bulk-specific registers: `8`

## Bulk Registers

| Register | Access | Role | Permitted writes | Evidence |
|---:|---|---|---|---|
| `0xb3000200` | `read, write` | EP0 OUT control (CNAK request) | `or 0x00000100` | stock USB2Thread sets CNAK bit 8; this is endpoint control, not interrupt acknowledgement |
| `0xb3000220` | `read, write` | EP1 OUT control (SNAK/CNAK requests) | `or 0x00000080, or 0x00000100` | stock interrupt path requests SNAK 0x80; the bulk callback requests CNAK 0x100; neither proves DMA quiescence |
| `0xb3000224` | `read, write` | bank-1 lane-1 bulk OUT status | `0x00000400` | stock interrupt task acknowledges latched TDC status 0x400; successful completion still needs ownership/error validation |
| `0xb300022c` | `write` | bulk OUT endpoint maximum-packet/config word | `0x00000040, 0x00000200` | stock USB2Thread selects 64-byte full-speed or 512-byte high-speed receive packets |
| `0xb3000234` | `write` | bulk OUT receive descriptor submit register | `0x90021370` | stock re-arm helper submits descriptor pool 0x90021370 |
| `0xb3000404` | `read, write` | USB device control (DEVCTL), transmit-DMA enable request | `or 0x00000008` | stock sets bit 0x8, named TDE by the pinned family header; RDE is the separate bit 0x4 |
| `0xb3000418` | `write` | USB event-lane mask word | `0xfffcfffe` | stock USB2Thread leaves endpoint-0 and bank-1 service lanes unmasked |
| `0xb3010000` | `read, write` | HP USB wrapper control; bit meanings incompletely established | `or 0x00000005` | stock USB2Thread tests bit 0 and sets bits 0/2; the family UDC header does not define this wrapper register |

## Allowed Memory

| Region | Start | End |
|---|---:|---:|
| `bulk_descriptor` | `0x90021370` | `0x9002137f` |
| `bulk_buffer` | `0x900216f0` | `0x90021aef` |
| `setup_packet` | `0x90021348` | `0x9002134f` |
| `control_in_descriptor` | `0x900226f0` | `0x900226ff` |
| `control_in_staging` | `0x90022bd0` | `0x90022c4b` |
| `open_marker_descriptor` | `0x90003200` | `0x90003225` |
| `open_standard_descriptors` | `0x90003300` | `0x90003377` |
| `probe_status_descriptor_hardware_alias` | `0x90003400` | `0x9000347b` |
| `probe_status_descriptor` | `0x10003400` | `0x1000347b` |
| `probe_runtime_state` | `0x1001d498` | `0x1001d557` |
| `stock_control_response_state` | `0x100212d4` | `0x10021314` |

## Independent Stock Evidence

- stock ELF: `analysis/sihp1020.elf`
- `0x00020000` big-endian literal occurrences: `80`
- `0xb3000220` big-endian literal occurrences: `1`
- `0xb3000234` big-endian literal occurrences: `1`
- `0x90021370` big-endian literal occurrences: `1`
- `0x900216f0` big-endian literal occurrences: `1`
- `0xb3000224` big-endian literal occurrences: `0`
- `0xb3000224` derivation: lane status word at 0xb3000220 + 0x4; not stored as a standalone stock ELF literal

| Status | Check | Source | Missing needles |
|---|---|---|---|
| `present` | `usb2thread_descriptor_initialization` | `analysis/usb-path/decompiled-neighbors/10008ff0_hp1020_usb2_thread.c` | `none` |
| `present` | `interrupt_bank_lane_completion` | `analysis/tasks/task-decompiled/10008208_hp1020_task_entry_10008208.c` | `none` |
| `present` | `bulk_rearm_descriptor_shape` | `analysis/call-clusters/seed-decompiled/100086f4_FUN_100086f4.c` | `none` |
| `present` | `bulk_callback_wait_copy_rearm` | `analysis/usb-path/bulk-callbacks-decompiled/100087b8_hp1020_usb_bulk_rx_callback_a_candidate.c` | `none` |
| `present` | `parser_callback_boundary` | `analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c` | `none` |

## Checks

| Status | Check | Detail |
|---|---|---|
| `present` | `bulk_lane_matches_interrupt_model` | bank-1/lane-1 status and control addresses remain fixed; wake hints do not assert success |
| `present` | `descriptor_submit_matches_rearm_model` | descriptor pool, buffer, and submit register remain fixed |
| `present` | `callback_ack_matches_contract` | legacy callback field usb_endpoint_ack_register denotes OUT1 control; its address and the lane mask remain in the unchanged probe allowlist |
| `present` | `all_bulk_registers_are_usb_only` | all additions stay in the mapped USB controller families |
| `present` | `stock_elf_contains_resolved_bulk_literals` | raw stock ELF contains the direct literals; byte-gated interrupt evidence derives lane EPSTS 0xb3000224 independently of EPCTL 0xb3000220 |
| `present` | `saved_decompilation_preserves_bulk_contract` | USB2Thread, interrupt task, re-arm helper, callback, and parser boundary evidence all remain present |
