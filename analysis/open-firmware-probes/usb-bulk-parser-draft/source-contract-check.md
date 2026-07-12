# HP 1020 USB Bulk/Parser Source Check

- source: `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/open-firmware/usb-bulk-parser-draft/usb-bulk-parser.S`
- status: `pass`
- checks: `43`
- fail hits: `0`

| Severity | Check | Detail | Evidence |
|---|---|---|---|
| `pass` | `literal_hp1020_bulk_descriptor_ptr_90021370` | hp1020_bulk_descriptor_ptr_90021370 must resolve to 0x90021370 | `0x90021370` |
| `pass` | `literal_hp1020_bulk_buffer_ptr_900216f0` | hp1020_bulk_buffer_ptr_900216f0 must resolve to 0x900216f0 | `0x900216f0` |
| `pass` | `literal_hp1020_mmio_b3000234` | hp1020_mmio_b3000234 must resolve to 0xb3000234 | `0xb3000234` |
| `pass` | `literal_hp1020_mmio_b3000224` | hp1020_mmio_b3000224 must resolve to 0xb3000224 | `0xb3000224` |
| `pass` | `literal_hp1020_mmio_b3000220` | hp1020_mmio_b3000220 must resolve to 0xb3000220 | `0xb3000220` |
| `pass` | `literal_hp1020_mmio_b3010000` | hp1020_mmio_b3010000 must resolve to 0xb3010000 | `0xb3010000` |
| `pass` | `literal_hp1020_bulk_completion_mask_00000400` | hp1020_bulk_completion_mask_00000400 must resolve to 0x00000400 | `0x00000400` |
| `pass` | `literal_hp1020_bulk_max_transfer_00000400` | hp1020_bulk_max_transfer_00000400 must resolve to 0x00000400 | `0x00000400` |
| `pass` | `literal_hp1020_zjs_max_chunk_01000000` | hp1020_zjs_max_chunk_01000000 must resolve to 0x01000000 | `0x01000000` |
| `pass` | `literal_hp1020_zjs_signature_00005a5a` | hp1020_zjs_signature_00005a5a must resolve to 0x00005a5a | `0x00005a5a` |
| `pass` | `literal_hp1020_zjs_magic_jzjz_4a5a4a5a` | hp1020_zjs_magic_jzjz_4a5a4a5a must resolve to 0x4a5a4a5a | `0x4a5a4a5a` |
| `pass` | `literal_hp1020_status_descriptor_local_ptr_10003400` | hp1020_status_descriptor_local_ptr_10003400 must resolve to 0x10003400 | `0x10003400` |
| `pass` | `literal_hp1020_status_descriptor_hw_ptr_90003400` | hp1020_status_descriptor_hw_ptr_90003400 must resolve to 0x90003400 | `0x90003400` |
| `pass` | `literal_hp1020_device_descriptor_hw_ptr_90003300` | hp1020_device_descriptor_hw_ptr_90003300 must resolve to 0x90003300 | `0x90003300` |
| `pass` | `literal_hp1020_config_high_speed_descriptor_hw_ptr_90003314` | hp1020_config_high_speed_descriptor_hw_ptr_90003314 must resolve to 0x90003314 | `0x90003314` |
| `pass` | `literal_hp1020_config_full_speed_descriptor_hw_ptr_90003334` | hp1020_config_full_speed_descriptor_hw_ptr_90003334 must resolve to 0x90003334 | `0x90003334` |
| `pass` | `literal_hp1020_lang_descriptor_hw_ptr_90003354` | hp1020_lang_descriptor_hw_ptr_90003354 must resolve to 0x90003354 | `0x90003354` |
| `pass` | `literal_hp1020_manufacturer_descriptor_hw_ptr_90003358` | hp1020_manufacturer_descriptor_hw_ptr_90003358 must resolve to 0x90003358 | `0x90003358` |
| `pass` | `exact_16_byte_descriptor_construction` | bulk re-arm must construct exactly four words at offsets 0, 4, 8, and 12 with the stock initial word and buffer pointer | `line 365: s32i a3,a2,0; line 367: s32i a3,a2,4; line 369: s32i a3,a2,8; line 371: s32i a3,a2,12` |
| `pass` | `descriptor_alignment` | the descriptor and buffer addresses must be 4-byte aligned and the re-arm routine must retain its alignment directive | `descriptor=2416055152; buffer=2416056048; previous=.align 4` |
| `pass` | `descriptor_submit` | the completed descriptor must cross a memory barrier before its pointer is written to 0xb3000234 | `line 374: s32i a2,a8,0` |
| `pass` | `bulk_completion_poll` | 0xb3000224 must be polled through the exact 0x400 completion mask | `line 635: l32r a2,hp1020_mmio_b3000224; line 637: l32i a3,a2,0; line 640: l32r a5,hp1020_bulk_completion_mask_00000400; line 641: and a3,a3,a5; line 642: bnez a3,hp1020_usb_bulk_handle_completion` |
| `pass` | `bulk_completion_ack_and_control` | completion must clear 0xb3000224 bit 0x400 and use 0xb3000220 bits 0x80/0x100 for acknowledgement and re-arm | `line 384: write_mmio_const hp1020_mmio_b3000224,hp1020_value_00000400; line 385: or_mmio_const hp1020_mmio_b3000220,hp1020_value_00000080; line 375: or_mmio_const hp1020_mmio_b3000220,hp1020_value_00000100` |
| `pass` | `bulk_rearm_paths` | initialization, invalid descriptors, and consumed transfers must reach re-arm, which must return to the poll loop | `line 359: j hp1020_usb_bulk_rearm; line 403: j hp1020_usb_bulk_rearm; line 424: bgeu a13,a6,hp1020_usb_bulk_rearm; line 380: j hp1020_usb_marker_poll_loop` |
| `pass` | `speed_specific_config_alias_selection` | b3010000 bit 0 must select the 0x90003314 high-speed or 0x90003334 full-speed configuration descriptor | `line 686: l32r a2,hp1020_mmio_b3010000; line 688: l32i a3,a2,0; line 689: movi a5,1; line 690: and a3,a3,a5; line 691: bnez a3,hp1020_usb_marker_select_full_speed_config; line 692: l32r a2,hp1020_config_high_speed_descriptor_hw_ptr_90003314; line 695: l32r a2,hp1020_config_full_speed_descriptor_hw_ptr_90003334` |
| `pass` | `counter_update_bytes_received` | the bytes_received counter must be updated at state offset 0x60 | `line 417: l32i a5,a4,0x60; line 418: add a5,a5,a6; line 419: s32i a5,a4,0x60` |
| `pass` | `counter_update_receive_descriptors_completed` | the receive_descriptors_completed counter must be updated at state offset 0x64 | `line 388: l32i a5,a4,0x64; line 389: addi a5,a5,1; line 390: s32i a5,a4,0x64` |
| `pass` | `counter_update_recognized_chunks` | the recognized_chunks counter must be updated at state offset 0x68 | `line 508: l32i a7,a4,0x68; line 509: addi a7,a7,1; line 510: s32i a7,a4,0x68` |
| `pass` | `counter_update_parser_errors` | the parser_errors counter must be updated at state offset 0x6c | `line 529: l32i a7,a4,0x6c; line 530: addi a7,a7,1; line 531: s32i a7,a4,0x6c` |
| `pass` | `counter_update_unknown_chunks` | the unknown_chunks counter must be updated at state offset 0x70 | `line 502: l32i a7,a4,0x70; line 503: addi a7,a7,1; line 504: s32i a7,a4,0x70` |
| `pass` | `completed_payload_counter_boundary` | recognized/unknown counters must update only in finish_chunk, reached after zero-payload validation or payload exhaustion | `line 484: j hp1020_zjs_finish_chunk; line 496: j hp1020_zjs_finish_chunk; line 508: l32i a7,a4,0x68; line 509: addi a7,a7,1; line 510: s32i a7,a4,0x68; line 502: l32i a7,a4,0x70; line 503: addi a7,a7,1; line 504: s32i a7,a4,0x70` |
| `pass` | `bulk_transfer_length_bound` | the receive descriptor length must be extracted and rejected above 0x400 | `line 406: extui a6,a3,0,16; line 407: l32r a7,hp1020_bulk_max_transfer_00000400; line 408: bltu a7,a6,hp1020_usb_bulk_length_invalid` |
| `pass` | `chunk_header_16_bytes` | the parser must collect exactly 16 header bytes, reject total sizes below 16, and subtract 16 before payload handling | `line 465: l32i a9,a8,0; line 466: l32i a10,a8,4; line 467: l32i a2,a8,12; line 461: bltu a7,a8,hp1020_zjs_parse_transfer_loop; line 472: bltu a9,a7,hp1020_zjs_header_error; line 476: addi a9,a9,-16` |
| `pass` | `chunk_max_0x01000000` | chunk total size must be rejected above 0x01000000 | `line 474: bltu a7,a9,hp1020_zjs_header_error` |
| `pass` | `chunk_signature_0x5a5a` | the low 16 bits of header word 12 must equal 0x5a5a | `line 470: bne a11,a7,hp1020_zjs_header_error` |
| `pass` | `reserved_not_above_payload` | the high 16-bit reserved count must be rejected when it exceeds total_size - 16 | `line 478: bltu a9,a2,hp1020_zjs_header_error` |
| `pass` | `recognized_type_bound_7` | only chunk types below 7 may increment the recognized counter | `line 501: bltu a8,a7,hp1020_zjs_known_chunk` |
| `pass` | `dynamic_status_counter_macro` | the status formatter must read a runtime counter and write eight hexadecimal digits into the local status descriptor | `line 36: l32r a2,hp1020_usb_marker_state_ptr; line 37: l32i a3,a2,\state_offset; line 38: l32r a4,hp1020_status_descriptor_local_ptr_10003400; line 39: addi a4,a4,\descriptor_offset; line 40: movi a5,8; line 41: .Lhex_loop_\@:; line 42: srli a6,a3,28; line 43: movi a7,10; line 44: bltu a6,a7,.Lhex_decimal_\@; line 45: addi a6,a6,55; line 46: j .Lhex_store_\@; line 47: .Lhex_decimal_\@:; line 48: addi a6,a6,48; line 49: .Lhex_store_\@:; line 50: s8i a6,a4,0; line 51: slli a3,a3,4; line 52: addi a4,a4,2; line 53: addi a5,a5,-1; line 54: bnez a5,.Lhex_loop_\@` |
| `pass` | `dynamic_product_status_counter_calls` | the product descriptor path must format bytes, descriptors, recognized chunks, errors, and unknown chunks at their fixed descriptor offsets | `line 720: write_hex_counter 0x60,0x14; line 721: write_hex_counter 0x64,0x2a; line 722: write_hex_counter 0x68,0x40; line 723: write_hex_counter 0x6c,0x56; line 724: write_hex_counter 0x70,0x6c` |
| `pass` | `polling_masks_cpu_interrupts_before_usb_setup` | entry must raise Xtensa INTLEVEL to 15 before the polling probe enables USB service bits, so the trap-only interrupt table cannot steal a completion | `line 778: rsil a2,15; line 779: jump_abs hp1020_usb_bulk_parser_probe` |
| `pass` | `no_alternate_xqx_magic` | the bulk/parser probe must recognize only the JZJZ framing magic | `no XQX magic literal or label found` |
| `pass` | `no_engine_video_mechanical_mmio` | source must not reference the b020, b050, b100, b200, b204, or b208 MMIO families | `no banned MMIO family literals found` |
| `pass` | `hardware_alias_literal_allowlist` | every 0x9... source literal must stay inside the explicit endpoint-0, bulk, or status regions | `12 literals are within: marker_descriptor, standard_descriptors, status_descriptor, setup_packet, bulk_descriptor, bulk_receive_buffer, control_in_descriptor, control_in_staging` |
