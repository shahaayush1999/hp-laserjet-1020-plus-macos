/* SPDX-License-Identifier: GPL-2.0-or-later */
/* UNEXECUTED USB-RUNTIME LAYOUT DRAFT. New offline entry; no stock code or
 * hardware operations. This separate profile does not alter the accepted
 * entry-to-document program. Exact linked bounds/bytes still require audit.
 * Required incoming conditions: privileged usable instruction/data RAM,
 * PC-relative L32R mode, no asynchronous/debug exception and no active hardware
 * loop ending in this entry/prefix before LCOUNT has been cleared. The caller
 * does not supply a valid stack, return address or register-window contents.
 * Actual emitted bytes, relocations and instruction properties need review.
 */

    .section .entry.normalizer, "ax", @progbits
    .balign 4
.Lstack_top:
    .word __hp1020_entry_stack_end
.Lstate_start:
    .word __hp1020_entry_state_start
.Lstate_end:
    .word __hp1020_entry_state_end
.Lmailbox_start:
    .word __hp1020_entry_mailbox_start
.Lmailbox_end:
    .word __hp1020_entry_mailbox_end
.Lmemory_start:
    .word __hp1020_entry_memory_start
.Lmemory_end:
    .word __hp1020_entry_memory_end
.Lwitness_start:
    .word __hp1020_entry_witness_start
.Lwitness_end:
    .word __hp1020_entry_witness_end

    .balign 4
    .global hp1020_entry_normalize
    .type hp1020_entry_normalize, @function
hp1020_entry_normalize:
    /* Only a2 is used before clearing WOE/CALLINC. No ENTRY or stack access. */
    rsil a2, 15
    movi a2, 0
    wsr a2, INTENABLE
    wsr a2, LCOUNT
    wsr a2, LBEG
    wsr a2, LEND
    isync
    movi a2, 15
    wsr a2, PS
    rsync
    movi a2, 0
    wsr a2, WINDOWBASE
    rsync
    /* WINDOWBASE changes the logical registers; reload every needed value. */
    movi a2, 1
    wsr a2, WINDOWSTART
    rsync
    ssai 0
    l32r a1, .Lstack_top
    movi a4, 0

    .global hp1020_entry_after_normalization
hp1020_entry_after_normalization:
    /* Read-only observer checkpoint. No BSS store or C call has occurred.
     * State includes every ordinary .bss/.sbss/COMMON global, but excludes
     * separately placed memory/mailbox/witness and all initialized .data.
     * Actual used section ends, not budget caps, bound these four clears. */
    l32r a2, .Lstate_start
    l32r a3, .Lstate_end
.Lclear_state:
    s32i a4, a2, 0
    addi a2, a2, 4
    bltu a2, a3, .Lclear_state

    l32r a2, .Lmailbox_start
    l32r a3, .Lmailbox_end
.Lclear_mailbox:
    s32i a4, a2, 0
    addi a2, a2, 4
    bltu a2, a3, .Lclear_mailbox

    l32r a2, .Lmemory_start
    l32r a3, .Lmemory_end
.Lclear_memory:
    s32i a4, a2, 0
    addi a2, a2, 4
    bltu a2, a3, .Lclear_memory

    l32r a2, .Lwitness_start
    l32r a3, .Lwitness_end
.Lclear_witness:
    s32i a4, a2, 0
    addi a2, a2, 4
    bltu a2, a3, .Lclear_witness

    /* This known in-range call must stay direct. GAS otherwise reserves a
     * possible relaxation literal even with no-longcalls; none is permitted
     * between this checkpoint, the CALL0 and its immediate return park. */
    .begin no-transform
    .global hp1020_entry_before_c
hp1020_entry_before_c:
    /* Verify exact zero spans here, before any C initializer can mask a bug.
     * CALL0 establishes a0; hp1020_usb_runtime_c(void) needs no arguments.
     * No generic initialized-data or sentinel byte has been written. */
    call0 hp1020_usb_runtime_c

    .global hp1020_entry_park
    .type hp1020_entry_park, @function
hp1020_entry_park:
    j hp1020_entry_park
    .size hp1020_entry_park, . - hp1020_entry_park
    .size hp1020_entry_normalize, . - hp1020_entry_normalize
    .end no-transform

    .balign 4
    .global hp1020_entry_unexpected_park
    .type hp1020_entry_unexpected_park, @function
hp1020_entry_unexpected_park:
    j hp1020_entry_unexpected_park
    .size hp1020_entry_unexpected_park, . - hp1020_entry_unexpected_park

    /* Address convention only. This new island contains no HP entry bytes. */
    .section .entry.island, "ax", @progbits
    .balign 4
    .global hp1020_entry_island
hp1020_entry_island:
    .space 0x28, 0
    .global hp1020_entry_start
    .global _start
    .type hp1020_entry_start, @function
hp1020_entry_start:
_start:
    j hp1020_entry_normalize
    .size hp1020_entry_start, . - hp1020_entry_start
    .space 0x60 - (. - hp1020_entry_island), 0

    /* New inert vector bytes. Each advertised entry parks locally without
     * reading a stack/register or invoking a runtime. This is not an interrupt
     * dispatcher, window spill handler, exception return or cold-boot claim. */
    .section .WindowVectors.text, "ax", @progbits
    .balign 4
    .global hp1020_entry_window_vectors
hp1020_entry_window_vectors:
    .rept 6
1:
    j 1b
    .space 0x40 - (. - 1b), 0
    .endr

    .section .KernelExceptionVector.literal, "a", @progbits
    .balign 4
    .word 0

    .section .KernelExceptionVector.text, "ax", @progbits
    .balign 4
    .global hp1020_entry_kernel_park
hp1020_entry_kernel_park:
    j hp1020_entry_kernel_park
    .space 0x1c - (. - hp1020_entry_kernel_park), 0

    .section .UserExceptionVector.literal, "a", @progbits
    .balign 4
    .word 0

    .section .UserExceptionVector.text, "ax", @progbits
    .balign 4
    .global hp1020_entry_user_park
hp1020_entry_user_park:
    j hp1020_entry_user_park
    .space 0x1c - (. - hp1020_entry_user_park), 0

    .section .DoubleExceptionVector.text, "ax", @progbits
    .balign 4
    .global hp1020_entry_double_park
hp1020_entry_double_park:
    j hp1020_entry_double_park
    .space 0xe0 - (. - hp1020_entry_double_park), 0

    .section .sys_interface_table, "a", @progbits
    .balign 4
    .global hp1020_entry_interface_table
hp1020_entry_interface_table:
    .rept 75
    .word hp1020_entry_unexpected_park
    .endr

    .section .ResetVector.text, "ax", @progbits
    .balign 4
    .global hp1020_entry_reset_park
hp1020_entry_reset_park:
    j hp1020_entry_reset_park
    .space 0x2e0 - (. - hp1020_entry_reset_park), 0

    .section .DebugExceptionVector.literal, "a", @progbits
    .balign 4
    .word 0

    .section .DebugExceptionVector.text, "ax", @progbits
    .balign 4
    .global hp1020_entry_debug_park
hp1020_entry_debug_park:
    j hp1020_entry_debug_park
    .space 0x0c - (. - hp1020_entry_debug_park), 0
