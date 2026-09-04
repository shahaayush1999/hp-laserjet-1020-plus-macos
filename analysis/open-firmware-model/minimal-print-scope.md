# HP 1020 Minimal Printing-Only Replacement Scope

This is a generated offline scope report. It does not contact the printer.

## Goal

Print PDFs by reusing host-side ZjStream generation and implementing only the firmware path required to receive, parse, and print that stream.

## Simple Readout

For the narrow goal, we do not need to clone every HP firmware feature. We need:

1. USB upload and USB identity/control handling.
2. USB bulk receive of the host-generated ZjStream print file.
3. A small ZjStream parser for the chunk types foo2zjs actually emits.
4. Raster handoff into the video/raw-band hardware path.
5. Engine coordination for paper, fuser, motor, and page timing.

USB bulk receive and framing now have an offline-validated inert implementation. That does not implement semantic print dispatch, raster output, video transfer, or engine control.

## Platform Boundary

- `host_side`: PDF/PostScript to ZjStream conversion is host/platform packaging work.
- `device_side`: Open firmware would be platform-independent after bytes reach USB.
- `macos_repo_scope`: This repo's current production print path is macOS glue around HP firmware plus foo2zjs.

## Current Evidence

- parser entry: `0x10009d34`
- JobMgr queue: `3`
- work objects modeled: `1`
- raster nodes modeled: `1`
- print-model invariant failures: `0`
- required JobMgr messages missing: `none`
- endpoint-0 modeled data/stall cases: `24` / `4`
- control completion event object: `0x10021318`
- USB completion status bit candidate: `0x400`
- USB bulk interrupt lane: event bit `0x00020000`, status register `0xb3000224`, ack register `0xb3000220`
- marker rearm-flow checks/failures: `5` / `0`
- USB bulk receive model: `pass`, record stride `0x58`, receive buffer `0x400 bytes`
- USB bulk parser handoff: parser `0x10009d34`, read callback slot present `true`
- USB bulk callback model: `pass`, event bit `0x00020000`, ack register `0xb3000220`
- USB bulk re-arm model: `pass`, descriptor pool `0x90021370`, submit register `0xb3000234`
- sideband access hits classified: `19`
- sideband risk split: `+0x26=critical`, `+0x32=mode_critical`, `+0x30=unknown_low_in_current_static_view`
- remaining-unit active-work source gap: `false`

## Open Bulk Parser Probe Evidence

- component status: `implemented and offline validated`
- offline validated: `true`
- generated samples passed: `11/11`
- deterministic matrix cases passed: `33/33`
- total cases passed: `44/44`
- assertions passed: `425/425`
- recognized chunk scope: `0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06`
- generated sample cases: `generated::matrix-a4_2400x600, generated::matrix-a4_600x600, generated::matrix-a4_cardstock_media, generated::matrix-a4_default, generated::matrix-a4_draft, generated::matrix-a4_logical_clip, generated::matrix-a4_manual_feed, generated::matrix-a4_two_copies, generated::matrix-legal_default, generated::matrix-letter_default, generated::minimal-page-a4`
- deterministic matrix cases: `header_split_01_of_16, header_split_02_of_16, header_split_03_of_16, header_split_04_of_16, header_split_05_of_16, header_split_06_of_16, header_split_07_of_16, header_split_08_of_16, header_split_09_of_16, header_split_10_of_16, header_split_11_of_16, header_split_12_of_16, header_split_13_of_16, header_split_14_of_16, header_split_15_of_16, magic_split_01_of_4, magic_split_02_of_4, magic_split_03_of_4, payload_split_across_four_boundaries, multiple_chunks_single_transfer, stock_types_outside_probe_scope_are_unknown, valid_zero_payload_chunks, zero_size_chunk_recovery, oversize_chunk_policy_recovery, bad_signature_recovery, reserved_exceeds_payload_recovery, unknown_chunk_is_counted_and_skipped, ring_and_descriptor_wrap_boundary, payload_crosses_ring_wrap_boundary, three_repeated_documents, truncated_chunk_header_at_eof, truncated_chunk_payload_at_eof, zero_byte_receive_descriptors`
- mechanically inert across all cases: `true`
- printer/USB contacted during validation: `false`
- report statuses: `combined_contract=pass, parser_model=pass, deterministic_results=pass, safety_scan=pass, usb_contract_scan=pass, usb_mmio_access_scan=pass, memory_boundary_scan=pass, source_contract_check=pass, status_descriptor_check=pass, config_descriptor_check=pass, reproducibility_check=pass`
- report fail counts: `combined_contract=0, parser_model=0, deterministic_results=0, safety_scan=0, usb_contract_scan=0, usb_mmio_access_scan=0, memory_boundary_scan=0, source_contract_check=0, status_descriptor_check=0, config_descriptor_check=0, reproducibility_check=0`
- status descriptor: `HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000` at `0x10003400`
- reproducibility: `pass`

## Component Scope

| Component | Status | Replacement need | Risk |
|---|---|---|---|
| Host PDF-to-ZjStream conversion | `available` | reuse existing GPL foo2zjs path; not firmware work | `low` |
| USB upload envelope | `available` | keep ACL/PJL upload wrapper for volatile firmware load | `low` |
| USB endpoint-0 descriptor/control path | `partially implemented` | live prove marker descriptor; marker now has a tiny gate-clear rearm loop, but not full stock ThreadX/event completion handling | `medium` |
| USB bulk receive to ZjStream parser | `implemented and offline validated` | guarded hardware execution must prove custom-code execution and real controller completion, length, acknowledgement, and repeated descriptor re-arm behavior; this probe discards payloads and has no print handoff | `medium` |
| ZjStream parser and JobMgr object model | `mapped` | portable C semantic construction is native-tested separately; integrate on-device only after boot/USB proof, and keep any print handoff explicitly gated | `medium` |
| JBIG compressed raster handling | `mapped to handoff boundary` | likely no full JBIG decode in firmware if hardware consumes the compressed stream like stock firmware | `high until hardware consumer semantics are proven` |
| Video sideband policy | `direct START_PAGE source verified` | use VIDEO_Y and ECONOMODE from the verified direct builder; calibrate physical counter/completion behavior before print output | `high` |
| Raster processing callbacks | `call contract verified; custom ISA semantics unresolved` | recover custom instruction effects from core-specific ISA definitions or stock input/output traces, or validate the stock-supported callback bypass | `unknown custom instruction side effects; not approved for probe inclusion` |
| Video/raw-band hardware feed | `danger boundary mapped, semantics incomplete` | reproduce page timing, raw-band pointers, channel enable/reset/wait sequence | `high` |
| Engine paper/fuser/motor coordination | `dispatch/status paths mapped, behavior incomplete` | coordinate mechanical state before and during video transfer | `high` |
| Scanner/fax/network/multi-product features | `out of scope` | none for Aayush's narrow goal | `none` |

## Main Blockers

| Blocker | Why | Next test/work |
|---|---|---|
| Guarded hardware execution and USB controller behavior | The bulk receive/framing probe is implemented and validated offline, but hardware has not proved that custom code executes, that boot-ROM controller state is sufficient, or that real completion length/ack/re-arm behavior matches the static contract. | Follow the probe hardware test plan only after a fresh power cycle: prove the status descriptor, send the inert START_DOC/END_DOC stream, and verify counters. Do not send raster or invoke engine/video paths. |
| Video and engine hardware sequencing | The mapped print model reaches raster handoff, but real printing needs synchronized video transfer and mechanical engine control. | Do not test this until USB-only open code is proven; continue static mapping of video/engine semantics first. |
| Video sideband values for the first print path | Static analysis now shows +0x26 is critical for channel-B refill/final accounting, but its active-work source is still not proven. | After USB-only execution is proven, use a non-printing or tightly gated trace/probe to distinguish whether stock leaves +0x26 zero or seeds it from page height/runtime state. |

## Current Decision

The USB bulk receive/framing component is ready only for its guarded mechanically inert hardware test; printing, semantic JobMgr/raster handoff, and all engine/video behavior remain unimplemented or unproven.

