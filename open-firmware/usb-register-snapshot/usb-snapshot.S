    .macro jump_abs target
    j 2f
    .align 4
1:
    .word \target
2:
    l32r a2, 1b
    jx a2
    .endm

    .macro snapshot_reg reg_label, offset
    l32r a2, \reg_label
    memw
    l32i a3, a2, 0x0
    l32r a4, hp1020_usb_snapshot_state_ptr
    memw
    s32i a3, a4, \offset
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
    .asciz "HP1020_OPEN_USB_SNAPSHOT_PROBE_20260622"
    .align 4
hp1020_usb_snapshot_state_ptr:
    .word hp1020_usb_snapshot_state
hp1020_mmio_b3000000:
    .word 0xb3000000
hp1020_mmio_b300000c:
    .word 0xb300000c
hp1020_mmio_b3000028:
    .word 0xb3000028
hp1020_mmio_b300002c:
    .word 0xb300002c
hp1020_mmio_b3000200:
    .word 0xb3000200
hp1020_mmio_b300020c:
    .word 0xb300020c
hp1020_mmio_b3000214:
    .word 0xb3000214
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
hp1020_snapshot_done_marker:
    .word 0x4850534e

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
    .global hp1020_usb_snapshot_probe
hp1020_usb_snapshot_probe:
    snapshot_reg hp1020_mmio_b3000000, 0x00
    snapshot_reg hp1020_mmio_b300000c, 0x04
    snapshot_reg hp1020_mmio_b3000028, 0x08
    snapshot_reg hp1020_mmio_b300002c, 0x0c
    snapshot_reg hp1020_mmio_b3000200, 0x10
    snapshot_reg hp1020_mmio_b300020c, 0x14
    snapshot_reg hp1020_mmio_b3000214, 0x18
    snapshot_reg hp1020_mmio_b300022c, 0x1c
    snapshot_reg hp1020_mmio_b3000400, 0x20
    snapshot_reg hp1020_mmio_b3000408, 0x24
    snapshot_reg hp1020_mmio_b3000504, 0x28
    snapshot_reg hp1020_mmio_b3000508, 0x2c
    snapshot_reg hp1020_mmio_b300050c, 0x30
    snapshot_reg hp1020_mmio_b3000510, 0x34
    l32r a4, hp1020_usb_snapshot_state_ptr
    l32r a3, hp1020_snapshot_done_marker
    s32i a3, a4, 0x38
    jump_abs hp1020_probe_idle_loop

    .section .runtime_vector.entry, "a", @progbits
    .align 4
    .global hp1020_probe_entry_vector
hp1020_probe_entry_vector:
    .word hp1020_probe_trap_loop
    .word hp1020_usb_snapshot_state
    .word hp1020_probe_trap_loop

    .section .runtime_vector.interrupt, "a", @progbits
    .align 4
    .global hp1020_probe_interrupt_vector
hp1020_probe_interrupt_vector:
    .word hp1020_probe_trap_loop
    .word 0x00040001
    .word hp1020_probe_interrupt_table
    .word hp1020_probe_trap_loop
    .word hp1020_usb_snapshot_state

    .section .text.entry, "ax", @progbits
    .align 4
    .global _start
_start:
    jump_abs hp1020_usb_snapshot_probe

    .section .ResetVector.text, "ax", @progbits
    .align 4
    .global hp1020_reset_vector
hp1020_reset_vector:
    jump_abs _start
    .space 0x2e0 - (. - hp1020_reset_vector), 0

    .section .runtime_state, "aw", @progbits
    .align 4
    .global hp1020_usb_snapshot_state
hp1020_usb_snapshot_state:
    .space 0x58, 0

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
