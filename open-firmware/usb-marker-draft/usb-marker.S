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
    .asciz "HP1020_OPEN_USB_MARKER_DRAFT_20260622"
    .align 4

hp1020_usb_marker_state_ptr:
    .word hp1020_usb_marker_state
hp1020_response_state_base_100212d4:
    .word 0x100212d4
hp1020_setup_packet_base_90021348:
    .word 0x90021348
hp1020_marker_descriptor_hw_ptr_90003200:
    .word 0x90003200
hp1020_device_descriptor_hw_ptr_90003300:
    .word 0x90003300
hp1020_config_descriptor_hw_ptr_90003314:
    .word 0x90003314
hp1020_lang_descriptor_hw_ptr_90003334:
    .word 0x90003334
hp1020_manufacturer_descriptor_hw_ptr_90003338:
    .word 0x90003338
hp1020_staging_buffer_ptr_90022bd0:
    .word 0x90022bd0
hp1020_descriptor_base_ptr_900226f0:
    .word 0x900226f0
hp1020_marker_len_00000026:
    .word 0x00000026
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
hp1020_gate_mask_00006000:
    .word 0x00006000
hp1020_gate_mask_00000003:
    .word 0x00000003

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
hp1020_mmio_b3000400:
    .word 0xb3000400
hp1020_mmio_b3000408:
    .word 0xb3000408
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
    l32r a2, hp1020_config_descriptor_hw_ptr_90003314
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
    l32r a2, hp1020_lang_descriptor_hw_ptr_90003334
    l32r a7, hp1020_lang_len_00000004
    j hp1020_usb_marker_clip_and_dispatch

hp1020_usb_marker_select_manufacturer:
    l32r a2, hp1020_manufacturer_descriptor_hw_ptr_90003338
    l32r a7, hp1020_manufacturer_len_00000020
    j hp1020_usb_marker_clip_and_dispatch

hp1020_usb_marker_select_product:
    l32r a2, hp1020_marker_descriptor_hw_ptr_90003200
    l32r a7, hp1020_marker_len_00000026

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
    jump_abs hp1020_usb_marker_draft_probe

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
    .space 0xa8, 0

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
