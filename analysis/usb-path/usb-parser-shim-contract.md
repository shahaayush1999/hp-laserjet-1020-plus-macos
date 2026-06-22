# HP 1020 USB Parser Shim Contract

This generated report combines the current USB receive models into one implementation contract. It does not contact the printer.

## Plain-English Meaning

The stock firmware keeps the print parser away from raw USB hardware. USB fills a buffer, wakes a read callback, and that callback feeds parser bytes. For open firmware, the next narrow software target is to reproduce that shim: accept bulk bytes, maintain the buffer counters, and provide a parser-facing read function.

## Parser Boundary

- `parser_entry`: 0x10009d34
- `parser_read_callback_slot`: param_1 + 0x0c
- `stock_parser_output_queue`: 3
- `meaning`: The ZjStream parser is decoupled from USB hardware behind a read callback.

## Transfer Registration

- `record_stride`: `0x58`
- `ring_base`: `0x1001ec00`
- `ring_index_word`: `0x1001f214`
- `buffer_allocation`: `0x400 bytes`
- `registered_low_level_read_callback`: `0x100087b8`
- `registered_completion_callback`: `0x10008bac`

## Bulk Read State

- `event_flags_object`: `0x10021318`
- `wait_event_bit`: `0x00020000`
- `available_size_word`: `0x1001bc50`
- `source_offset_word`: `0x1001bc4c`
- `destination_offset_word`: `0x10021594`
- `remaining_request_word`: `0x1001bc54`
- `threshold_word`: `0x10021590`
- `next_pointer_word`: `0x1001bc44`
- `buffer_base_word`: `0x1001bc40`

## Hardware Receive Lane

- `event_bit`: `0x00020000`
- `lane_status_register`: `0xb3000224`
- `lane_ack_register`: `0xb3000220`
- `completion_status_bit`: `0x400`
- `ack_bits`: `0x80`, `0x400`

## Descriptor Re-Arm

- `descriptor_pool`: `0x90021370`
- `bulk_buffer_base`: `0x900216f0`
- `descriptor_submit_register`: `0xb3000234`
- `descriptor_target_bytes`: `+0x08..+0x0b`
- `alignment_rule`: `use next aligned pointer only when non-zero and 16-byte aligned; otherwise use bulk_buffer_base + offset`
- `done_flags`:
  - `bulk_done_byte`: `0x1001bc70`
  - `bulk_rx_done_flag`: `0x1001bc72`

## Staged Plan

| Stage | Purpose | Requires printer | Risk |
|---|---|---:|---|
| `bulk_counter_probe` | Observe bank-1/lane-1 completion and buffer counters without printing. | `true` | `low if it never sends engine/video commands` |
| `bulk_echo_or_discard_firmware` | Accept bulk OUT bytes, update a counter/state marker, and keep the printer mechanically idle. | `true` | `low-to-medium until endpoint-0 marker execution is proven` |
| `minimal_zjs_chunk_reader` | Parse only enough ZjStream framing to count document/page/raster chunks, still without video or engine output. | `false` | `software-only until connected to USB receive` |
| `print_path_handoff` | Only after USB receive and chunk parsing are proven, connect parsed raster/page objects to video/engine models. | `true` | `high` |

## Current Decision

Do not drive video/engine hardware from open code until endpoint-0 execution, bulk receive, and non-printing chunk parsing are proven.

## Evidence Checks

- status: `pass`

| Status | Name | Evidence | Detail |
|---|---|---|---|
| `present` | `bulk_receive_model_passes` | `analysis/usb-path/usb-bulk-receive-model.json` | Bulk receive registration model must be green. |
| `present` | `bulk_callback_model_passes` | `analysis/usb-path/usb-bulk-callbacks-model.json` | Bulk callback model must be green. |
| `present` | `bulk_rearm_model_passes` | `analysis/usb-path/usb-bulk-rearm-model.json` | Bulk re-arm model must be green. |
| `present` | `interrupt_model_has_bulk_lane` | `analysis/usb-path/usb-interrupt-events.json` | USB interrupt model must preserve the bank-1/lane-1 bulk receive lane. |
| `present` | `descriptor_rearm_constants_resolved` | `analysis/usb-path/usb-bulk-rearm-model.json` | Descriptor pool, buffer base, and submit register must be concrete. |

