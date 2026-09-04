    .macro jump_abs target
    j 2f
    .align 4
1:
    .word \target
2:
    l32r a2, 1b
    jx a2
    .endm

    .macro snapshot_word source_label, offset
    l32r a2, \source_label
    l32i a3, a2, 0
    l32r a4, hp1020_usb_marker_state_ptr
    s32i a3, a4, \offset
    .endm

    .macro write_mmio_const reg_label, value_label
    l32r a8, \reg_label
    l32r a9, \value_label
    memw
    s32i a9, a8, 0
    .endm

    .macro or_mmio_const reg_label, value_label
    l32r a8, \reg_label
    memw
    l32i a9, a8, 0
    l32r a10, \value_label
    or a9, a9, a10
    memw
    s32i a9, a8, 0
    .endm

    .macro write_hex_counter state_offset, descriptor_offset
    l32r a2, hp1020_usb_marker_state_ptr
    l32i a3, a2, \state_offset
    l32r a4, hp1020_status_descriptor_local_ptr_10003400
    addi a4, a4, \descriptor_offset
    movi a5, 8
.Lhex_loop_\@:
    srli a6, a3, 28
    movi a7, 10
    bltu a6, a7, .Lhex_decimal_\@
    addi a6, a6, 55
    j .Lhex_store_\@
.Lhex_decimal_\@:
    addi a6, a6, 48
.Lhex_store_\@:
    s8i a6, a4, 0
    slli a3, a3, 4
    addi a4, a4, 2
    addi a5, a5, -1
    bnez a5, .Lhex_loop_\@
    .endm

    .section .WindowVectors.text, "ax", @progbits
    .align 4
    .global hp1020_window_vectors
hp1020_window_vectors:
    jump_abs _start
    .space 0x180 - (. - hp1020_window_vectors), 0

    .section .KernelExceptionVector.literal, "ax", @progbits
    .align 4
    .word 0

    .section .KernelExceptionVector.text, "ax", @progbits
    .align 4
hp1020_kernel_exception_vector:
    jump_abs _start
    .space 0x1c - (. - hp1020_kernel_exception_vector), 0

    .section .UserExceptionVector.literal, "ax", @progbits
    .align 4
    .word 0

    .section .UserExceptionVector.text, "ax", @progbits
    .align 4
hp1020_user_exception_vector:
    jump_abs _start
    .space 0x1c - (. - hp1020_user_exception_vector), 0

    .section .DoubleExceptionVector.text, "ax", @progbits
    .align 4
hp1020_double_exception_vector:
    jump_abs _start
    .space 0xe0 - (. - hp1020_double_exception_vector), 0

    .section .sys_interface_table, "aw", @progbits
    .align 4
    .global hp1020_probe_sys_interface_table
hp1020_probe_sys_interface_table:
    .rept 75
    .word hp1020_probe_trap_loop
    .endr

    .section .rodata.probe, "a", @progbits
    .align 4
hp1020_probe_banner:
    .asciz "HP1020_OPEN_USB_BULK_PARSER_DRAFT_20260712"
    .align 4

hp1020_usb_marker_state_ptr:
    .word hp1020_usb_marker_state
hp1020_response_state_base_100212d4:
    .word 0x100212d4
hp1020_setup_packet_base_90021348:
    .word 0x90021348
hp1020_marker_descriptor_hw_ptr_90003200:
    .word 0x90003200
hp1020_status_descriptor_local_ptr_10003400:
    .word 0x10003400
hp1020_status_descriptor_hw_ptr_90003400:
    .word 0x90003400
hp1020_device_descriptor_hw_ptr_90003300:
    .word 0x90003300
hp1020_config_high_speed_descriptor_hw_ptr_90003314:
    .word 0x90003314
hp1020_config_full_speed_descriptor_hw_ptr_90003334:
    .word 0x90003334
hp1020_lang_descriptor_hw_ptr_90003354:
    .word 0x90003354
hp1020_manufacturer_descriptor_hw_ptr_90003358:
    .word 0x90003358
hp1020_staging_buffer_ptr_90022bd0:
    .word 0x90022bd0
hp1020_descriptor_base_ptr_900226f0:
    .word 0x900226f0
hp1020_marker_len_0000007c:
    .word 0x0000007c
hp1020_device_len_00000012:
    .word 0x00000012
hp1020_config_len_00000020:
    .word 0x00000020
hp1020_lang_len_00000004:
    .word 0x00000004
hp1020_manufacturer_len_00000020:
    .word 0x00000020
hp1020_descriptor_final_flag_08000000:
    .word 0x08000000
hp1020_done_marker_48504d4b:
    .word 0x48504d4b
hp1020_no_match_marker_4e4f4d41:
    .word 0x4e4f4d41
hp1020_rearm_marker_52454152:
    .word 0x52454152
hp1020_bulk_init_marker_424c4b50:
    .word 0x424c4b50
hp1020_gate_mask_00006000:
    .word 0x00006000
hp1020_gate_mask_00000003:
    .word 0x00000003
hp1020_bulk_completion_mask_00000400:
    .word 0x00000400
hp1020_bulk_descriptor_ready_mask_c0000000:
    .word 0xc0000000
hp1020_bulk_descriptor_ready_value_80000000:
    .word 0x80000000
hp1020_bulk_descriptor_initial_08000000:
    .word 0x08000000
hp1020_bulk_max_transfer_00000400:
    .word 0x00000400
hp1020_zjs_max_chunk_01000000:
    .word 0x01000000
hp1020_zjs_magic_jzjz_4a5a4a5a:
    .word 0x4a5a4a5a
hp1020_zjs_signature_00005a5a:
    .word 0x00005a5a

hp1020_value_02000000:
    .word 0x02000000
hp1020_value_020000c1:
    .word 0x020000c1
hp1020_value_020080c1:
    .word 0x020080c1
hp1020_value_020000d1:
    .word 0x020000d1
hp1020_value_100000c1:
    .word 0x100000c1
hp1020_value_100080c1:
    .word 0x100080c1
hp1020_value_100000d1:
    .word 0x100000d1
hp1020_value_00000040:
    .word 0x00000040
hp1020_value_00000200:
    .word 0x00000200
hp1020_value_00000002:
    .word 0x00000002
hp1020_value_00000108:
    .word 0x00000108
hp1020_value_00000080:
    .word 0x00000080
hp1020_value_00000100:
    .word 0x00000100
hp1020_value_00000400:
    .word 0x00000400
hp1020_value_00000005:
    .word 0x00000005
hp1020_value_00000008:
    .word 0x00000008
hp1020_value_fffCfffe:
    .word 0xfffcfffe
hp1020_bulk_descriptor_ptr_90021370:
    .word 0x90021370
hp1020_bulk_buffer_ptr_900216f0:
    .word 0x900216f0

hp1020_mmio_b3000000:
    .word 0xb3000000
hp1020_mmio_b3000014:
    .word 0xb3000014
hp1020_mmio_b300000c:
    .word 0xb300000c
hp1020_mmio_b3000028:
    .word 0xb3000028
hp1020_mmio_b300002c:
    .word 0xb300002c
hp1020_mmio_b300020c:
    .word 0xb300020c
hp1020_mmio_b300022c:
    .word 0xb300022c
hp1020_mmio_b3000200:
    .word 0xb3000200
hp1020_mmio_b3000220:
    .word 0xb3000220
hp1020_mmio_b3000224:
    .word 0xb3000224
hp1020_mmio_b3000234:
    .word 0xb3000234
hp1020_mmio_b3000400:
    .word 0xb3000400
hp1020_mmio_b3000404:
    .word 0xb3000404
hp1020_mmio_b3000408:
    .word 0xb3000408
hp1020_mmio_b3000418:
    .word 0xb3000418
hp1020_mmio_b3010000:
    .word 0xb3010000
hp1020_mmio_b3000504:
    .word 0xb3000504
hp1020_mmio_b3000508:
    .word 0xb3000508
hp1020_mmio_b300050c:
    .word 0xb300050c
hp1020_mmio_b3000510:
    .word 0xb3000510

    .section .usb_marker_descriptor, "a", @progbits
    .align 4
    .global hp1020_open_marker_product_string
hp1020_open_marker_product_string:
    .byte 0x26, 0x03
    .byte 0x48, 0x00, 0x50, 0x00, 0x31, 0x00, 0x30, 0x00
    .byte 0x32, 0x00, 0x30, 0x00, 0x20, 0x00, 0x4f, 0x00
    .byte 0x50, 0x00, 0x45, 0x00, 0x4e, 0x00, 0x20, 0x00
    .byte 0x4d, 0x00, 0x41, 0x00, 0x52, 0x00, 0x4b, 0x00
    .byte 0x45, 0x00, 0x52, 0x00

    .section .usb_status_descriptor, "aw", @progbits
    .align 4
    .global hp1020_open_bulk_status_product_string
hp1020_open_bulk_status_product_string:
    .byte 0x7c, 0x03
    .byte 'H',0,'P',0,'1',0,'0',0,'2',0,'0',0,' ',0,'B',0,'=',0
    .byte '0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0
    .byte ' ',0,'D',0,'=',0
    .byte '0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0
    .byte ' ',0,'C',0,'=',0
    .byte '0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0
    .byte ' ',0,'E',0,'=',0
    .byte '0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0
    .byte ' ',0,'U',0,'=',0
    .byte '0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0,'0',0

    .section .usb_standard_descriptors, "a", @progbits
    .align 4
hp1020_open_device_descriptor:
    .byte 0x12, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x40
    .byte 0xf0, 0x03, 0x17, 0x2b, 0x00, 0x01, 0x01, 0x02
    .byte 0x00, 0x01
    .align 4
hp1020_open_config_descriptor:
    .byte 0x09, 0x02, 0x20, 0x00, 0x01, 0x01, 0x00, 0xc0
    .byte 0x31, 0x09, 0x04, 0x00, 0x00, 0x02, 0x07, 0x01
    .byte 0x02, 0x00, 0x07, 0x05, 0x01, 0x02, 0x00, 0x02
    .byte 0x00, 0x07, 0x05, 0x81, 0x02, 0x00, 0x02, 0x00
hp1020_open_full_speed_config_descriptor:
    .byte 0x09, 0x02, 0x20, 0x00, 0x01, 0x01, 0x00, 0xc0
    .byte 0x31, 0x09, 0x04, 0x00, 0x00, 0x02, 0x07, 0x01
    .byte 0x02, 0x00, 0x07, 0x05, 0x01, 0x02, 0x40, 0x00
    .byte 0x00, 0x07, 0x05, 0x81, 0x02, 0x40, 0x00, 0x00
hp1020_open_lang_descriptor:
    .byte 0x04, 0x03, 0x09, 0x04
hp1020_open_manufacturer_string:
    .byte 0x20, 0x03
    .byte 0x48, 0x00, 0x65, 0x00, 0x77, 0x00, 0x6c, 0x00
    .byte 0x65, 0x00, 0x74, 0x00, 0x74, 0x00, 0x2d, 0x00
    .byte 0x50, 0x00, 0x61, 0x00, 0x63, 0x00, 0x6b, 0x00
    .byte 0x61, 0x00, 0x72, 0x00, 0x64, 0x00

    .section .text.probe, "ax", @progbits
    .align 4
hp1020_probe_trap_loop:
    movi a2, 1
1:
    j 1b

    .align 4
hp1020_probe_idle_loop:
    movi a2, 0
1:
    j 1b

    .align 4
    .global hp1020_usb_bulk_parser_probe
hp1020_usb_bulk_parser_probe:
    l32r a2, hp1020_usb_marker_state_ptr
    movi a3, 0
    s32i a3, a2, 0x60
    s32i a3, a2, 0x64
    s32i a3, a2, 0x68
    s32i a3, a2, 0x6c
    s32i a3, a2, 0x70
    s32i a3, a2, 0x74
    s32i a3, a2, 0x78
    s32i a3, a2, 0x7c
    s32i a3, a2, 0x80
    s32i a3, a2, 0x84
    s32i a3, a2, 0x88
    s32i a3, a2, 0x8c
    s32i a3, a2, 0x90

    l32r a8, hp1020_mmio_b3010000
    memw
    l32i a9, a8, 0
    movi a10, 1
    and a10, a9, a10
    bnez a10, hp1020_usb_bulk_full_speed
    l32r a11, hp1020_value_00000200
    j hp1020_usb_bulk_packet_selected
hp1020_usb_bulk_full_speed:
    l32r a11, hp1020_value_00000040
hp1020_usb_bulk_packet_selected:
    s32i a11, a2, 0x94
    l32r a8, hp1020_mmio_b300022c
    memw
    s32i a11, a8, 0
    write_mmio_const hp1020_mmio_b3000418, hp1020_value_fffCfffe
    or_mmio_const hp1020_mmio_b3010000, hp1020_value_00000005
    or_mmio_const hp1020_mmio_b3000404, hp1020_value_00000008
    or_mmio_const hp1020_mmio_b3000220, hp1020_value_00000100
    or_mmio_const hp1020_mmio_b3000200, hp1020_value_00000100
    l32r a3, hp1020_bulk_init_marker_424c4b50
    l32r a2, hp1020_usb_marker_state_ptr
    s32i a3, a2, 0x98
    j hp1020_usb_bulk_rearm

    .align 4
hp1020_usb_bulk_rearm:
    l32r a2, hp1020_bulk_descriptor_ptr_90021370
    l32r a3, hp1020_bulk_descriptor_initial_08000000
    s32i a3, a2, 0
    movi a3, 0
    s32i a3, a2, 4
    l32r a3, hp1020_bulk_buffer_ptr_900216f0
    s32i a3, a2, 8
    movi a3, 0
    s32i a3, a2, 12
    memw
    l32r a8, hp1020_mmio_b3000234
    s32i a2, a8, 0
    or_mmio_const hp1020_mmio_b3000220, hp1020_value_00000100
    l32r a4, hp1020_usb_marker_state_ptr
    l32i a3, a4, 0x90
    addi a3, a3, 1
    s32i a3, a4, 0x90
    j hp1020_usb_marker_poll_loop

    .align 4
hp1020_usb_bulk_handle_completion:
    write_mmio_const hp1020_mmio_b3000224, hp1020_value_00000400
    or_mmio_const hp1020_mmio_b3000220, hp1020_value_00000080

    l32r a4, hp1020_usb_marker_state_ptr
    l32i a5, a4, 0x64
    addi a5, a5, 1
    s32i a5, a4, 0x64

    l32r a2, hp1020_bulk_descriptor_ptr_90021370
    l32i a3, a2, 0
    l32r a5, hp1020_bulk_descriptor_ready_mask_c0000000
    and a6, a3, a5
    l32r a5, hp1020_bulk_descriptor_ready_value_80000000
    beq a6, a5, hp1020_usb_bulk_descriptor_valid
    l32i a5, a4, 0x6c
    addi a5, a5, 1
    s32i a5, a4, 0x6c
    movi a5, 0
    s32i a5, a4, 0x88
    j hp1020_usb_bulk_rearm

hp1020_usb_bulk_descriptor_valid:
    extui a6, a3, 0, 16
    l32r a7, hp1020_bulk_max_transfer_00000400
    bltu a7, a6, hp1020_usb_bulk_length_invalid
    j hp1020_usb_bulk_length_valid
hp1020_usb_bulk_length_invalid:
    l32i a5, a4, 0x6c
    addi a5, a5, 1
    s32i a5, a4, 0x6c
    mov a6, a7
hp1020_usb_bulk_length_valid:
    s32i a6, a4, 0x88
    l32i a5, a4, 0x60
    add a5, a5, a6
    s32i a5, a4, 0x60
    l32r a12, hp1020_bulk_buffer_ptr_900216f0
    movi a13, 0

hp1020_zjs_parse_transfer_loop:
    bgeu a13, a6, hp1020_usb_bulk_rearm
    l8ui a2, a12, 0
    addi a12, a12, 1
    addi a13, a13, 1
    l32r a4, hp1020_usb_marker_state_ptr
    l32i a5, a4, 0x74
    beqz a5, hp1020_zjs_search_magic
    movi a7, 1
    beq a5, a7, hp1020_zjs_collect_header
    j hp1020_zjs_skip_payload

hp1020_zjs_search_magic:
    l32i a7, a4, 0x78
    slli a7, a7, 8
    or a7, a7, a2
    s32i a7, a4, 0x78
    l32r a8, hp1020_zjs_magic_jzjz_4a5a4a5a
    beq a7, a8, hp1020_zjs_magic_found
    j hp1020_zjs_parse_transfer_loop

hp1020_zjs_magic_found:
    movi a5, 1
    s32i a5, a4, 0x74
    movi a5, 0
    s32i a5, a4, 0x78
    s32i a5, a4, 0x7c
    j hp1020_zjs_parse_transfer_loop

hp1020_zjs_collect_header:
    l32i a7, a4, 0x7c
    movi a8, 0xa0
    add a8, a4, a8
    add a8, a8, a7
    s8i a2, a8, 0
    addi a7, a7, 1
    s32i a7, a4, 0x7c
    movi a8, 16
    bltu a7, a8, hp1020_zjs_parse_transfer_loop

    movi a8, 0xa0
    add a8, a4, a8
    l32i a9, a8, 0
    l32i a10, a8, 4
    l32i a2, a8, 12
    extui a11, a2, 0, 16
    l32r a7, hp1020_zjs_signature_00005a5a
    bne a11, a7, hp1020_zjs_header_error
    movi a7, 16
    bltu a9, a7, hp1020_zjs_header_error
    l32r a7, hp1020_zjs_max_chunk_01000000
    bltu a7, a9, hp1020_zjs_header_error

    addi a9, a9, -16
    srli a2, a2, 16
    bltu a9, a2, hp1020_zjs_header_error
    s32i a9, a4, 0x80
    s32i a10, a4, 0x84
    movi a7, 0
    s32i a7, a4, 0x7c
    bnez a9, hp1020_zjs_enter_payload
    j hp1020_zjs_finish_chunk

hp1020_zjs_enter_payload:
    movi a7, 2
    s32i a7, a4, 0x74
    j hp1020_zjs_parse_transfer_loop

hp1020_zjs_skip_payload:
    l32i a7, a4, 0x80
    addi a7, a7, -1
    s32i a7, a4, 0x80
    bnez a7, hp1020_zjs_parse_transfer_loop
    j hp1020_zjs_finish_chunk

hp1020_zjs_finish_chunk:
    l32i a8, a4, 0x84
    movi a7, 7
    bltu a8, a7, hp1020_zjs_known_chunk
    l32i a7, a4, 0x70
    addi a7, a7, 1
    s32i a7, a4, 0x70
    j hp1020_zjs_chunk_counted

hp1020_zjs_known_chunk:
    l32i a7, a4, 0x68
    addi a7, a7, 1
    s32i a7, a4, 0x68
hp1020_zjs_chunk_counted:
    movi a7, 1
    beq a8, a7, hp1020_zjs_return_to_magic
    movi a7, 1
    s32i a7, a4, 0x74
    movi a7, 0
    s32i a7, a4, 0x7c
    j hp1020_zjs_parse_transfer_loop

hp1020_zjs_return_to_magic:
    movi a7, 0
    s32i a7, a4, 0x74
    s32i a7, a4, 0x78
    s32i a7, a4, 0x7c
    s32i a7, a4, 0x80
    j hp1020_zjs_parse_transfer_loop

hp1020_zjs_header_error:
    l32i a7, a4, 0x6c
    addi a7, a7, 1
    s32i a7, a4, 0x6c
    movi a7, 0
    s32i a7, a4, 0x74
    s32i a7, a4, 0x78
    s32i a7, a4, 0x7c
    s32i a7, a4, 0x80
    j hp1020_zjs_parse_transfer_loop

    .align 4
hp1020_usb_marker_no_match:
    l32r a4, hp1020_usb_marker_state_ptr
    l32r a3, hp1020_no_match_marker_4e4f4d41
    s32i a3, a4, 0x40
    j hp1020_usb_marker_poll_loop

    .align 4
hp1020_usb_marker_sequence_a:
    write_mmio_const hp1020_mmio_b3000508, hp1020_value_020000c1
    write_mmio_const hp1020_mmio_b3000510, hp1020_value_020080c1
    write_mmio_const hp1020_mmio_b300050c, hp1020_value_020000d1
    write_mmio_const hp1020_mmio_b300022c, hp1020_value_00000040
    write_mmio_const hp1020_mmio_b300020c, hp1020_value_00000040
    write_mmio_const hp1020_mmio_b300000c, hp1020_value_00000040
    write_mmio_const hp1020_mmio_b300002c, hp1020_value_00000040
    write_mmio_const hp1020_mmio_b3000028, hp1020_value_00000040
    j hp1020_usb_marker_kick_control_in

    .align 4
hp1020_usb_marker_sequence_b:
    write_mmio_const hp1020_mmio_b3000504, hp1020_value_02000000
    write_mmio_const hp1020_mmio_b3000508, hp1020_value_100000c1
    write_mmio_const hp1020_mmio_b3000510, hp1020_value_100080c1
    write_mmio_const hp1020_mmio_b300050c, hp1020_value_100000d1
    write_mmio_const hp1020_mmio_b300022c, hp1020_value_00000200
    write_mmio_const hp1020_mmio_b300020c, hp1020_value_00000040
    write_mmio_const hp1020_mmio_b300000c, hp1020_value_00000040
    write_mmio_const hp1020_mmio_b300002c, hp1020_value_00000200
    write_mmio_const hp1020_mmio_b3000028, hp1020_value_00000040
    j hp1020_usb_marker_kick_control_in

    .align 4
hp1020_usb_marker_kick_control_in:
    mov a2, a12
    l32r a4, hp1020_response_state_base_100212d4
    s32i a6, a4, 0x3c
    mov a5, a6
    l32r a7, hp1020_descriptor_final_flag_08000000
    or a7, a7, a6
    l32r a3, hp1020_staging_buffer_ptr_90022bd0
    s32i a3, a4, 0x40

    l32r a3, hp1020_staging_buffer_ptr_90022bd0
    movi a4, 0
    beq a4, a5, 2f
1:
    l8ui a6, a2, 0
    s8i a6, a3, 0
    addi a2, a2, 1
    addi a3, a3, 1
    addi a4, a4, 1
    bltu a4, a5, 1b

2:
    l32r a4, hp1020_descriptor_base_ptr_900226f0
    s32i a7, a4, 0
    movi a3, 0
    s32i a3, a4, 4
    l32r a3, hp1020_staging_buffer_ptr_90022bd0
    s32i a3, a4, 8
    movi a3, 0
    s32i a3, a4, 12

    or_mmio_const hp1020_mmio_b3000000, hp1020_value_00000002
    write_mmio_const hp1020_mmio_b3000014, hp1020_descriptor_base_ptr_900226f0
    or_mmio_const hp1020_mmio_b3000000, hp1020_value_00000108
    l32r a4, hp1020_usb_marker_state_ptr
    l32r a3, hp1020_done_marker_48504d4b
    s32i a3, a4, 0x44
    j hp1020_usb_marker_wait_gate_clear

hp1020_usb_marker_wait_gate_clear:
    l32r a4, hp1020_usb_marker_state_ptr
    l32r a3, hp1020_rearm_marker_52454152
    s32i a3, a4, 0x48
1:
    l32r a2, hp1020_mmio_b3000408
    l32i a3, a2, 0
    s32i a3, a4, 0x4c
    l32r a5, hp1020_gate_mask_00006000
    and a3, a3, a5
    bnez a3, 1b

    l32r a2, hp1020_mmio_b3000400
    l32i a3, a2, 0
    s32i a3, a4, 0x50
    l32r a5, hp1020_gate_mask_00000003
    and a3, a3, a5
    bnez a3, 1b

    j hp1020_usb_marker_poll_loop

    .align 4
    .global hp1020_usb_marker_draft_probe
hp1020_usb_marker_draft_probe:
hp1020_usb_marker_poll_loop:
    l32r a2, hp1020_mmio_b3000224
    memw
    l32i a3, a2, 0
    l32r a4, hp1020_usb_marker_state_ptr
    s32i a3, a4, 0x8c
    l32r a5, hp1020_bulk_completion_mask_00000400
    and a3, a3, a5
    bnez a3, hp1020_usb_bulk_handle_completion

    snapshot_word hp1020_mmio_b3000408, 0x00
    snapshot_word hp1020_mmio_b3000400, 0x04

    l32r a2, hp1020_setup_packet_base_90021348
    mov a11, a2
    l8ui a3, a2, 0x00
    l32r a4, hp1020_usb_marker_state_ptr
    s32i a3, a4, 0x08
    movi a5, 0x80
    bne a3, a5, hp1020_usb_marker_no_match

    l8ui a3, a2, 0x01
    s32i a3, a4, 0x0c
    movi a5, 0x06
    bne a3, a5, hp1020_usb_marker_no_match

    l8ui a3, a2, 0x02
    s32i a3, a4, 0x10
    mov a9, a3

    l8ui a3, a2, 0x03
    s32i a3, a4, 0x14
    mov a8, a3

    movi a5, 0x01
    beq a8, a5, hp1020_usb_marker_select_device
    movi a5, 0x02
    beq a8, a5, hp1020_usb_marker_select_config
    movi a5, 0x03
    beq a8, a5, hp1020_usb_marker_select_string
    j hp1020_usb_marker_no_match

hp1020_usb_marker_select_device:
    movi a5, 0x00
    bne a9, a5, hp1020_usb_marker_no_match
    l32r a2, hp1020_device_descriptor_hw_ptr_90003300
    l32r a7, hp1020_device_len_00000012
    j hp1020_usb_marker_clip_and_dispatch

hp1020_usb_marker_select_config:
    movi a5, 0x00
    bne a9, a5, hp1020_usb_marker_no_match
    l32r a2, hp1020_mmio_b3010000
    memw
    l32i a3, a2, 0
    movi a5, 1
    and a3, a3, a5
    bnez a3, hp1020_usb_marker_select_full_speed_config
    l32r a2, hp1020_config_high_speed_descriptor_hw_ptr_90003314
    j hp1020_usb_marker_config_selected
hp1020_usb_marker_select_full_speed_config:
    l32r a2, hp1020_config_full_speed_descriptor_hw_ptr_90003334
hp1020_usb_marker_config_selected:
    l32r a7, hp1020_config_len_00000020
    j hp1020_usb_marker_clip_and_dispatch

hp1020_usb_marker_select_string:
    movi a5, 0x00
    beq a9, a5, hp1020_usb_marker_select_lang
    movi a5, 0x01
    beq a9, a5, hp1020_usb_marker_select_manufacturer
    movi a5, 0x02
    beq a9, a5, hp1020_usb_marker_select_product
    j hp1020_usb_marker_no_match

hp1020_usb_marker_select_lang:
    l32r a2, hp1020_lang_descriptor_hw_ptr_90003354
    l32r a7, hp1020_lang_len_00000004
    j hp1020_usb_marker_clip_and_dispatch

hp1020_usb_marker_select_manufacturer:
    l32r a2, hp1020_manufacturer_descriptor_hw_ptr_90003358
    l32r a7, hp1020_manufacturer_len_00000020
    j hp1020_usb_marker_clip_and_dispatch

hp1020_usb_marker_select_product:
    write_hex_counter 0x60, 0x14
    write_hex_counter 0x64, 0x2a
    write_hex_counter 0x68, 0x40
    write_hex_counter 0x6c, 0x56
    write_hex_counter 0x70, 0x6c
    l32r a2, hp1020_status_descriptor_hw_ptr_90003400
    l32r a7, hp1020_marker_len_0000007c

hp1020_usb_marker_clip_and_dispatch:
    # Preserve the selected payload across gate reads and MMIO macros.
    mov a12, a2
    # Counter formatting clobbers a4; length bookkeeping belongs to state.
    l32r a4, hp1020_usb_marker_state_ptr

    l8ui a3, a11, 0x06
    s32i a3, a4, 0x18
    mov a6, a3
    l8ui a3, a11, 0x07
    s32i a3, a4, 0x1c
    slli a3, a3, 8
    or a6, a6, a3
    bltu a6, a7, 1f
    mov a6, a7
1:
    s32i a6, a4, 0x20

    l32r a2, hp1020_mmio_b3000408
    l32i a3, a2, 0
    l32r a5, hp1020_gate_mask_00006000
    and a7, a3, a5
    bnez a7, hp1020_usb_marker_sequence_a

    l32r a2, hp1020_mmio_b3000400
    l32i a3, a2, 0
    l32r a5, hp1020_gate_mask_00000003
    and a7, a3, a5
    bnez a7, hp1020_usb_marker_sequence_b

    j hp1020_usb_marker_no_match

    .section .runtime_vector.entry, "a", @progbits
    .align 4
    .global hp1020_probe_entry_vector
hp1020_probe_entry_vector:
    .word hp1020_probe_trap_loop
    .word hp1020_usb_marker_state
    .word hp1020_probe_trap_loop

    .section .runtime_vector.interrupt, "a", @progbits
    .align 4
    .global hp1020_probe_interrupt_vector
hp1020_probe_interrupt_vector:
    .word hp1020_probe_trap_loop
    .word 0x00040001
    .word hp1020_probe_interrupt_table
    .word hp1020_probe_trap_loop
    .word hp1020_usb_marker_state

    .section .text.entry, "ax", @progbits
    .align 4
    .global _start
_start:
    rsil a2, 15
    jump_abs hp1020_usb_bulk_parser_probe

    .section .ResetVector.text, "ax", @progbits
    .align 4
    .global hp1020_reset_vector
hp1020_reset_vector:
    jump_abs _start
    .space 0x2e0 - (. - hp1020_reset_vector), 0

    .section .runtime_state, "aw", @progbits
    .align 4
    .global hp1020_usb_marker_state
hp1020_usb_marker_state:
    .space 0xc0, 0

    .section .interrupt_table, "aw", @progbits
    .align 4
    .global hp1020_probe_interrupt_table
hp1020_probe_interrupt_table:
    .rept 32
    .word hp1020_probe_trap_loop
    .endr

    .section .DebugExceptionVector.literal, "ax", @progbits
    .align 4
    .word 0

    .section .DebugExceptionVector.text, "ax", @progbits
    .align 4
hp1020_debug_exception_vector:
1:
    j 1b
    .space 0x0c - (. - hp1020_debug_exception_vector), 0
