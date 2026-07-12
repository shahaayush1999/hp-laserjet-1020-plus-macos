# HP 1020 USB Bulk Parser Draft Model

This generated report executes a host-side receive-ring and ZjStream framing model. It reads checked-in files only; it does not open USB, touch MMIO, send video/engine commands, or cause mechanical activity.

## Result

- status: `pass`
- generated samples: `11/11` passed
- synthetic matrix: `33/33` passed
- assertions: `425/425` passed
- receive ring/descriptor size: `0x400` bytes
- hardware side effects: `0`

## Framing Contract

- The full host stream may contain a PJL envelope. The model scans it for big-endian `JZJZ`, matching the stock HP 1020 parser handoff boundary. The distinct XQX format is intentionally rejected.
- Every chunk starts with `>IIIHH`: total size, type, item count, reserved bytes, and signature.
- Total size includes the 16-byte header; the required signature is `0x5a5a`.
- A size-16 chunk has a valid zero-byte payload. A declared size below 16 is malformed.
- Complete types outside the controlled-sample scope `0x00..0x06` increment `unknown_chunks` and are skipped without invoking print behavior.
- Malformed/truncated framing increments `parser_errors`, aborts the current document, and seeks the next stream marker.

## Required Counters

| Counter | Aggregate | Definition |
|---|---:|---|
| `bytes_received` | `82806` | Bytes delivered by completed host-side receive descriptors, including PJL envelope bytes. |
| `receive_descriptors_completed` | `182` | Every feed_descriptor call, including a zero-byte completion. |
| `recognized_chunks` | `175` | Completely received chunks whose type is in the controlled-sample probe scope 0x00..0x06. |
| `parser_errors` | `6` | Invalid or truncated framing incidents; semantic print validation is intentionally out of scope. |
| `unknown_chunks` | `7` | Completely received chunks outside the narrow probe scope, skipped without error. |

## Stock And Probe Chunk Types

The stock table is derived from `analysis/zjs-parser-boundary/zjs-switch-table.tsv`. The inert probe deliberately recognizes only `0x00..0x06`, the types emitted by the controlled samples; other framed types are counted as unknown.

| Type | Name | Stock parser target |
|---:|---|---:|
| `0x00` | `ZJT_START_DOC` | `0x10009efe` |
| `0x01` | `ZJT_END_DOC` | `0x1000a1b3` |
| `0x02` | `ZJT_START_PAGE` | `0x10009f86` |
| `0x03` | `ZJT_END_PAGE` | `0x1000a19e` |
| `0x04` | `ZJT_JBIG_BIH` | `0x1000a006` |
| `0x05` | `ZJT_JBIG_BID` | `0x1000a014` |
| `0x06` | `ZJT_END_JBIG` | `0x1000a053` |
| `0x07` | `ZJT_SIGNATURE` | `0x1000a1ef` |
| `0x08` | `ZJT_RAW_IMAGE` | `0x1000a1ef` |
| `0x09` | `ZJT_START_PLANE` | `0x1000a1ef` |
| `0x0a` | `ZJT_END_PLANE` | `0x1000a173` |
| `0x0b` | `ZJT_2600N_PAUSE` | `0x1000a1d6` |
| `0x0c` | `ZJT_2600N` | `0x1000a05d` |

## Generated Samples

Every checked-in generated `.zjs` file is fed in complete 0x400-byte receive descriptors, including its PJL prefix and suffix.

| Sample | Bytes | Descriptors | Magic | Chunks | Errors | Status |
|---|---:|---:|---:|---:|---:|---|
| `analysis/samples/generated/matrix-a4_2400x600.zjs` | `9703` | `10` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_600x600.zjs` | `5071` | `5` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_cardstock_media.zjs` | `6987` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_default.zjs` | `6987` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_draft.zjs` | `6986` | `7` | `0x10b` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_logical_clip.zjs` | `7011` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_manual_feed.zjs` | `6987` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-a4_two_copies.zjs` | `6987` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-legal_default.zjs` | `7011` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/matrix-letter_default.zjs` | `6999` | `7` | `0x10c` | `7` | `0` | `pass` |
| `analysis/samples/generated/minimal-page-a4.zjs` | `6987` | `7` | `0x10c` | `7` | `0` | `pass` |

## Deterministic Matrix

| Case | Category | Bytes | Descriptors | Recognized | Errors | Unknown | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `header_split_01_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_02_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_03_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_04_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_05_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_06_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_07_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_08_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_09_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_10_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_11_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_12_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_13_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_14_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `header_split_15_of_16` | `header_split` | `48` | `2` | `2` | `0` | `0` | `pass` |
| `magic_split_01_of_4` | `header_split` | `36` | `2` | `2` | `0` | `0` | `pass` |
| `magic_split_02_of_4` | `header_split` | `36` | `2` | `2` | `0` | `0` | `pass` |
| `magic_split_03_of_4` | `header_split` | `36` | `2` | `2` | `0` | `0` | `pass` |
| `payload_split_across_four_boundaries` | `payload_split` | `293` | `5` | `2` | `0` | `0` | `pass` |
| `multiple_chunks_single_transfer` | `multiple_chunks` | `236` | `1` | `7` | `0` | `0` | `pass` |
| `stock_types_outside_probe_scope_are_unknown` | `known_chunks` | `212` | `1` | `7` | `0` | `6` | `pass` |
| `valid_zero_payload_chunks` | `zero_length` | `68` | `1` | `4` | `0` | `0` | `pass` |
| `zero_size_chunk_recovery` | `malformed_chunk` | `56` | `7` | `2` | `1` | `0` | `pass` |
| `oversize_chunk_policy_recovery` | `malformed_chunk` | `56` | `6` | `2` | `1` | `0` | `pass` |
| `bad_signature_recovery` | `malformed_chunk` | `56` | `6` | `2` | `1` | `0` | `pass` |
| `reserved_exceeds_payload_recovery` | `malformed_chunk` | `59` | `6` | `2` | `1` | `0` | `pass` |
| `unknown_chunk_is_counted_and_skipped` | `unknown_chunk` | `64` | `6` | `2` | `0` | `1` | `pass` |
| `ring_and_descriptor_wrap_boundary` | `ring_wrap` | `1254` | `2` | `7` | `0` | `0` | `pass` |
| `payload_crosses_ring_wrap_boundary` | `ring_wrap` | `1100` | `2` | `2` | `0` | `0` | `pass` |
| `three_repeated_documents` | `repeated_documents` | `729` | `15` | `21` | `0` | `0` | `pass` |
| `truncated_chunk_header_at_eof` | `malformed_chunk` | `11` | `3` | `0` | `1` | `0` | `pass` |
| `truncated_chunk_payload_at_eof` | `malformed_chunk` | `32` | `4` | `0` | `1` | `0` | `pass` |
| `zero_byte_receive_descriptors` | `zero_length` | `36` | `3` | `2` | `0` | `0` | `pass` |

## Evidence Checks

| Check | Source | Detail | Status |
|---|---|---|---|
| `vendor_header_layout` | `vendor/foo2zjs-source/zjs.h` | all framing needles present | `pass` |
| `vendor_writer_framing` | `vendor/foo2zjs-source/foo2zjs.c` | all framing needles present | `pass` |
| `stock_parser_read_and_bounds_checks` | `analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c` | all framing needles present | `pass` |
| `usb_shim_buffer_and_parser_contract` | `analysis/usb-path/usb-parser-shim-contract.json` | buffer=0x400 bytes, parser_entry=0x10009d34 | `pass` |
| `switch_table_matches_stock_0x00_through_0x0c` | `analysis/zjs-parser-boundary/zjs-switch-table.tsv` | loaded 13 chunk types | `pass` |
| `probe_scope_matches_controlled_sample_types_0x00_through_0x06` | `analysis/samples/generated/**/*.zjs` | probe recognizes [0, 1, 2, 3, 4, 5, 6] | `pass` |

## Safety Boundary

All cases stop after framing and counter updates. Payload bytes are never decoded into page/work objects, and no USB, MMIO, video, engine, or mechanical function exists in the executable model.
