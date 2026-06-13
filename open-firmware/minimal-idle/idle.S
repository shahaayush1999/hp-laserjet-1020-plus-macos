    .macro jump_abs target
    j 2f
    .align 4
1:
    .word \target
2:
    l32r a2, 1b
    jx a2
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
    .global hp1020_sys_interface_table
hp1020_sys_interface_table:
    .space 0x12c, 0

    .section .rodata.probe, "a", @progbits
    .align 4
hp1020_probe_banner:
    .asciz "HP1020_OPEN_IDLE_PROBE_20260613"

    .section .text.probe, "ax", @progbits
    .align 4
hp1020_probe_idle_loop:
    movi a2, 0
1:
    j 1b

    .section .text.entry, "ax", @progbits
    .align 4
    .global _start
_start:
    jump_abs hp1020_probe_idle_loop

    .section .ResetVector.text, "ax", @progbits
    .align 4
    .global hp1020_reset_vector
hp1020_reset_vector:
    jump_abs _start
    .space 0x2e0 - (. - hp1020_reset_vector), 0

    .section .DebugExceptionVector.literal, "ax", @progbits
    .align 4
    .word 0

    .section .DebugExceptionVector.text, "ax", @progbits
    .align 4
hp1020_debug_exception_vector:
1:
    j 1b
    .space 0x0c - (. - hp1020_debug_exception_vector), 0
