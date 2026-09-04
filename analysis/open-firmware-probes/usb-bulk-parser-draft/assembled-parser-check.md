# Assembled parser execution check

Status: pass; 44 cases; 1178483 instructions executed; zero MMIO accesses.

The actual BE ELF parser instructions run in a bounded host RAM interpreter. After every transfer their counters and partial parser state are compared with the independent Python model. Unknown instructions, unmapped reads, MMIO, writes outside parser state, and runaway execution fail closed.

This starts at the parser loop with a synthetic buffer and length, and stops before USB re-arm. It does not validate the descriptor length contract, USB initialization, cache aliases, boot acceptance, or physical I/O. Host-only end-of-input finalization is deliberately excluded because a live stream has no such signal.

| Case | Transfers compared | Instructions |
|---|---:|---:|
| generated::matrix-a4_2400x600 | 10 | 136566 |
| generated::matrix-a4_600x600 | 5 | 71708 |
| generated::matrix-a4_cardstock_media | 7 | 98536 |
| generated::matrix-a4_default | 7 | 98536 |
| generated::matrix-a4_draft | 7 | 98522 |
| generated::matrix-a4_logical_clip | 7 | 98872 |
| generated::matrix-a4_manual_feed | 7 | 98536 |
| generated::matrix-a4_two_copies | 7 | 98536 |
| generated::matrix-legal_default | 7 | 98872 |
| generated::matrix-letter_default | 7 | 98704 |
| generated::minimal-page-a4 | 7 | 98536 |
| header_split_01_of_16 | 2 | 881 |
| header_split_02_of_16 | 2 | 881 |
| header_split_03_of_16 | 2 | 881 |
| header_split_04_of_16 | 2 | 881 |
| header_split_05_of_16 | 2 | 881 |
| header_split_06_of_16 | 2 | 881 |
| header_split_07_of_16 | 2 | 881 |
| header_split_08_of_16 | 2 | 881 |
| header_split_09_of_16 | 2 | 881 |
| header_split_10_of_16 | 2 | 881 |
| header_split_11_of_16 | 2 | 881 |
| header_split_12_of_16 | 2 | 881 |
| header_split_13_of_16 | 2 | 881 |
| header_split_14_of_16 | 2 | 881 |
| header_split_15_of_16 | 2 | 881 |
| magic_split_01_of_4 | 2 | 710 |
| magic_split_02_of_4 | 2 | 710 |
| magic_split_03_of_4 | 2 | 710 |
| payload_split_across_four_boundaries | 5 | 4317 |
| multiple_chunks_single_transfer | 1 | 4010 |
| stock_types_outside_probe_scope_are_unknown | 1 | 4256 |
| valid_zero_payload_chunks | 1 | 1352 |
| zero_size_chunk_recovery | 7 | 1088 |
| oversize_chunk_policy_recovery | 6 | 1088 |
| bad_signature_recovery | 6 | 1084 |
| reserved_exceeds_payload_recovery | 6 | 1133 |
| unknown_chunk_is_counted_and_skipped | 6 | 1212 |
| ring_and_descriptor_wrap_boundary | 2 | 18264 |
| payload_crosses_ring_wrap_boundary | 2 | 15609 |
| three_repeated_documents | 15 | 12348 |
| truncated_chunk_header_at_eof | 3 | 193 |
| truncated_chunk_payload_at_eof | 4 | 548 |
| zero_byte_receive_descriptors | 3 | 712 |
