/* SPDX-License-Identifier: GPL-2.0-or-later */
/* UNEXECUTED DRAFT. Split-object RAM-only USB runtime, not the accepted earlier
 * entry-to-document ELF. Stock-declared address envelopes bound this new layout;
 * neither physical RAM ownership nor HP-loader compatibility is established.
 * Used section ends are distinct from capacity caps. Unused gaps and guards
 * are symbols only: no output section or load tail may fill them. No .dl image.
 */
OUTPUT_FORMAT("elf32-xtensa-be")
OUTPUT_ARCH(xtensa)
ENTRY(hp1020_entry_start)

/* Keep every named observation entry, including the unused compatibility
 * initializer whose zero invocation count is independently checked. */
EXTERN(hp1020_usb_runtime_c hp1020_usb_document_init hp1020_usb_document_init_documents
       hp1020_tusb_adapter_init hp1020_udc_setup_bus_reset hp1020_udc_setup_offer
       hp1020_udc_setup_dispatch hp1020_udc_ep0_take_submission hp1020_udc_ep0_observe
       hp1020_tusb_adapter_pending_reset hp1020_tusb_adapter_ack_reset
       hp1020_tusb_adapter_finish_reset hp1020_tusb_adapter_pump
       hp1020_usb_document_restart tusb_rhport_init hp1020_udc_publish_arm_out
       hp1020_udc_acquire_packet hp1020_udc_publish_service
       hp1020_tusb_adapter_close_input hp1020_tusb_adapter_finish)

PHDRS
{
  window_vectors PT_LOAD FLAGS(5);
  exception_vectors PT_LOAD FLAGS(5);
  double_vector PT_LOAD FLAGS(5);
  interface_table PT_LOAD FLAGS(4);
  code PT_LOAD FLAGS(5);
  state PT_LOAD FLAGS(6);
  stack PT_LOAD FLAGS(6);
  mailbox PT_LOAD FLAGS(6);
  initialized_data PT_LOAD FLAGS(6);
  sentinel PT_LOAD FLAGS(6);
  entry_island PT_LOAD FLAGS(5);
  memory PT_LOAD FLAGS(6);
  witness PT_LOAD FLAGS(6);
  reset_vector PT_LOAD FLAGS(5);
  debug_vector PT_LOAD FLAGS(5);
}

__hp1020_entry_main_start = 0x10003000;
__hp1020_entry_main_end = 0x100351e0;
__hp1020_entry_code_cap = 0x1000ffe0;
__hp1020_entry_state_cap = 0x10013fe0;
__hp1020_entry_data_cap = 0x10016500;
__hp1020_entry_witness_cap = 0x10034ff0;

__hp1020_entry_code_guard_hi_start = 0x1000ffe0;
__hp1020_entry_code_guard_hi_end = 0x10010000;
__hp1020_entry_state_guard_lo_start = 0x1000ffe0;
__hp1020_entry_state_guard_lo_end = 0x10010000;
__hp1020_entry_state_guard_hi_start = 0x10013fe0;
__hp1020_entry_state_guard_hi_end = 0x10014000;
__hp1020_entry_stack_guard_lo_start = 0x10014000;
__hp1020_entry_stack_guard_lo_end = 0x10014020;
__hp1020_entry_stack_guard_hi_start = 0x10016020;
__hp1020_entry_stack_guard_hi_end = 0x10016040;
__hp1020_entry_mailbox_guard_lo_start = 0x10016040;
__hp1020_entry_mailbox_guard_lo_end = 0x10016060;
__hp1020_entry_mailbox_guard_hi_start = 0x10016460;
__hp1020_entry_mailbox_guard_hi_end = 0x10016480;
__hp1020_entry_data_guard_lo_start = 0x10016480;
__hp1020_entry_data_guard_lo_end = 0x100164a0;
__hp1020_entry_data_guard_hi_start = 0x10016600;
__hp1020_entry_data_guard_hi_end = 0x10016620;
__hp1020_entry_pre_island_gap_start = 0x10016620;
__hp1020_entry_pre_island_gap_end = 0x10016780;
__hp1020_entry_memory_guard_lo_start = 0x100167e0;
__hp1020_entry_memory_guard_lo_end = 0x10016800;
__hp1020_entry_memory_guard_hi_start = 0x10032810;
__hp1020_entry_memory_guard_hi_end = 0x10032830;
__hp1020_entry_witness_guard_lo_start = 0x10032810;
__hp1020_entry_witness_guard_lo_end = 0x10032830;
__hp1020_entry_witness_guard_hi_start = 0x10034ff0;
__hp1020_entry_witness_guard_hi_end = 0x10035010;
__hp1020_entry_tail_gap_start = 0x10035010;
__hp1020_entry_tail_gap_end = 0x100351e0;

SECTIONS
{
  .WindowVectors.text 0x10000000 : {
    __hp1020_entry_window_start = .;
    KEEP(*(.WindowVectors.text))
    __hp1020_entry_window_end = .;
  } :window_vectors
  .KernelExceptionVector.literal 0x10000180 : {
    __hp1020_entry_kernel_literal_start = .;
    KEEP(*(.KernelExceptionVector.literal))
    __hp1020_entry_kernel_literal_end = .;
  } :window_vectors
  .KernelExceptionVector.text 0x10000200 : {
    __hp1020_entry_kernel_start = .;
    KEEP(*(.KernelExceptionVector.text))
    __hp1020_entry_kernel_end = .;
  } :exception_vectors
  .UserExceptionVector.literal 0x1000021c : {
    __hp1020_entry_user_literal_start = .;
    KEEP(*(.UserExceptionVector.literal))
    __hp1020_entry_user_literal_end = .;
  } :exception_vectors
  .UserExceptionVector.text 0x10000220 : {
    __hp1020_entry_user_start = .;
    KEEP(*(.UserExceptionVector.text))
    __hp1020_entry_user_end = .;
  } :exception_vectors
  .DoubleExceptionVector.text 0x10000270 : {
    __hp1020_entry_double_start = .;
    KEEP(*(.DoubleExceptionVector.text))
    __hp1020_entry_double_end = .;
  } :double_vector
  .sys_interface_table 0x10000370 : {
    __hp1020_entry_interface_start = .;
    KEEP(*(.sys_interface_table))
    __hp1020_entry_interface_end = .;
  } :interface_table

  .text 0x10003000 : {
    __hp1020_entry_code_start = .;
    KEEP(*(.entry.normalizer))
    *(.literal .literal.*)
    *(.text .text.*)
    __hp1020_entry_text_end = .;
  } :code
  .rodata : ALIGN(4) {
    __hp1020_entry_rodata_start = .;
    KEEP(*(.rodata.hp1020_usb_runtime_layout))
    *(.rodata .rodata.*)
    __hp1020_entry_rodata_end = .;
    __hp1020_entry_code_end = .;
  } :code

  /* This is the sole generic zero area. The full production document is first;
   * separate class/adapter/controller/runtime objects and TinyUSB globals follow.
   * The large production memory object is explicitly elsewhere, never inside a
   * private aggregate that would cross the entry island. Custom .runtime_*
   * objects assigned to NOLOAD must be uninitialized/zero-initialized in C. */
  .bss 0x10010000 (NOLOAD) : {
    __hp1020_entry_state_start = .;
    __hp1020_runtime_document_start = .;
    KEEP(*(.runtime_document))
    __hp1020_runtime_document_end = .;
    __hp1020_runtime_other_bss_start = .;
    KEEP(*(.bss .bss.* .sbss .sbss.*))
    KEEP(*(COMMON))
    __hp1020_runtime_bss_unaligned_end = .;
    . = ALIGN(4);
    __hp1020_entry_state_end = .;
  } :state
  .runtime_stack 0x10014020 (NOLOAD) : {
    __hp1020_entry_stack_start = .;
    . += 0x2000;
    __hp1020_entry_stack_end = .;
  } :stack
  .runtime_mailbox 0x10016060 (NOLOAD) : {
    __hp1020_entry_mailbox_start = .;
    KEEP(*(.runtime_mailbox))
    __hp1020_entry_mailbox_end = .;
  } :mailbox

  /* Preserve actual compiler initialized bytes, including TinyUSB's queue/spin/
   * rhport objects. This segment does not extend to the cap or into the sentinel.
   * C may change generic .data; only the separate sentinel remains immutable. */
  .data 0x100164a0 : {
    __hp1020_entry_data_start = .;
    KEEP(*(.data .data.* .sdata .sdata.*))
    __hp1020_entry_data_end = .;
  } :initialized_data
  .runtime_sentinel 0x10016500 : {
    __hp1020_entry_sentinel_start = .;
    KEEP(*(.runtime_sentinel))
    __hp1020_entry_sentinel_end = .;
  } :sentinel

  .entry_island 0x10016780 : {
    __hp1020_entry_island_start = .;
    KEEP(*(.entry.island))
    __hp1020_entry_island_end = .;
  } :entry_island
  .runtime_memory 0x10016800 (NOLOAD) : {
    __hp1020_entry_memory_start = .;
    KEEP(*(.runtime_memory))
    __hp1020_entry_memory_end = .;
  } :memory
  .runtime_witness 0x10032830 (NOLOAD) : {
    __hp1020_entry_witness_start = .;
    KEEP(*(.runtime_witness))
    __hp1020_runtime_witness_unaligned_end = .;
    . = ALIGN(4);
    __hp1020_entry_witness_end = .;
  } :witness

  .ResetVector.text 0x10100020 : {
    __hp1020_entry_reset_start = .;
    KEEP(*(.ResetVector.text))
    __hp1020_entry_reset_end = .;
  } :reset_vector
  .DebugExceptionVector.literal 0x10100300 : {
    __hp1020_entry_debug_literal_start = .;
    KEEP(*(.DebugExceptionVector.literal))
    __hp1020_entry_debug_literal_end = .;
  } :reset_vector
  .DebugExceptionVector.text 0x10100320 : {
    __hp1020_entry_debug_start = .;
    KEEP(*(.DebugExceptionVector.text))
    __hp1020_entry_debug_end = .;
  } :debug_vector

  /* These exact metadata families do not provide runtime permissions. Their
   * non-SHF_ALLOC flags and exclusion from every PT_LOAD still require audit. */
  .xtensa.info 0 : { KEEP(*(.xtensa.info)) } :NONE
  .xt.prop 0 : { KEEP(*(.xt.prop .xt.prop.*)) } :NONE
  .xt.lit 0 : { KEEP(*(.xt.lit .xt.lit.*)) } :NONE
  .xt.insn 0 : { KEEP(*(.xt.insn .xt.insn.*)) } :NONE
  .debug_line 0 : { *(.debug_line) } :NONE
  .debug_info 0 : { *(.debug_info) } :NONE
  .debug_abbrev 0 : { *(.debug_abbrev) } :NONE
  .debug_aranges 0 : { *(.debug_aranges) } :NONE
  .debug_str 0 : { *(.debug_str) } :NONE
  /DISCARD/ : { *(.comment) *(.note.GNU-stack) }

  /* No broad note/unwind/dynamic/TLS/constructor or linkonce catch-all is
   * accepted. Unknown nonempty inputs fail, including unexpected allocations. */
  .unexpected 0 : { *(*) } :NONE
}

/* Used-end-to-cap intervals are preserved, just like the fixed guards. */
__hp1020_entry_code_unused_start = __hp1020_entry_code_end;
__hp1020_entry_code_unused_end = __hp1020_entry_code_cap;
__hp1020_entry_state_unused_start = __hp1020_entry_state_end;
__hp1020_entry_state_unused_end = __hp1020_entry_state_cap;
__hp1020_entry_data_unused_start = __hp1020_entry_data_end;
__hp1020_entry_data_unused_end = __hp1020_entry_data_cap;
__hp1020_entry_witness_unused_start = __hp1020_entry_witness_end;
__hp1020_entry_witness_unused_end = __hp1020_entry_witness_cap;

ASSERT(SIZEOF(.WindowVectors.text) == 0x180, "wrong window-vector size")
ASSERT(SIZEOF(.KernelExceptionVector.literal) == 4, "wrong kernel literal size")
ASSERT(SIZEOF(.KernelExceptionVector.text) == 0x1c, "wrong kernel-vector size")
ASSERT(SIZEOF(.UserExceptionVector.literal) == 4, "wrong user literal size")
ASSERT(SIZEOF(.UserExceptionVector.text) == 0x1c, "wrong user-vector size")
ASSERT(SIZEOF(.DoubleExceptionVector.text) == 0xe0, "wrong double-vector size")
ASSERT(SIZEOF(.sys_interface_table) == 0x12c, "wrong interface-table size")
ASSERT(SIZEOF(.ResetVector.text) == 0x2e0, "wrong reset-vector size")
ASSERT(SIZEOF(.DebugExceptionVector.literal) == 4, "wrong debug literal size")
ASSERT(SIZEOF(.DebugExceptionVector.text) == 0x0c, "wrong debug-vector size")

ASSERT(__hp1020_entry_code_start == 0x10003000, "wrong code start")
ASSERT(__hp1020_entry_code_end <= __hp1020_entry_code_cap,
       "code/constant inputs exceed 53216-byte budget")
ASSERT(hp1020_entry_normalize == __hp1020_entry_code_start + 36,
       "normalizer must follow exactly nine startup literal words")
ASSERT(hp1020_entry_after_normalization > hp1020_entry_normalize &&
       hp1020_entry_after_normalization < hp1020_entry_before_c,
       "wrong normalization checkpoint order")
ASSERT(hp1020_entry_park == hp1020_entry_before_c + 3 &&
       hp1020_entry_park < __hp1020_entry_text_end,
       "CALL0 must return directly to its three-byte park")
ASSERT(hp1020_entry_unexpected_park > hp1020_entry_park &&
       hp1020_entry_unexpected_park < __hp1020_entry_text_end,
       "unexpected-vector target outside startup text")
ASSERT(hp1020_usb_runtime_c >= __hp1020_entry_code_start &&
       hp1020_usb_runtime_c < __hp1020_entry_text_end,
       "USB runtime entry outside text")
ASSERT(hp1020_entry_start == 0x100167a8, "wrong ELF entry address")
ASSERT(SIZEOF(.entry_island) == 0x60 &&
       __hp1020_entry_island_end == 0x100167e0, "entry island changed")

ASSERT(__hp1020_entry_state_start == 0x10010000 &&
       __hp1020_entry_state_end > __hp1020_entry_state_start &&
       __hp1020_entry_state_end <= __hp1020_entry_state_cap,
       "generic zero-state exceeds 16352-byte budget")
ASSERT(__hp1020_runtime_document_end - __hp1020_runtime_document_start == 13512,
       "production document state size changed")
ASSERT(hp1020_usb_runtime_document == __hp1020_runtime_document_start,
       "production document object displaced")
ASSERT(__hp1020_entry_state_end - __hp1020_runtime_bss_unaligned_end < 4,
       "generic BSS contains unexpected trailing padding")
ASSERT(SIZEOF(.runtime_stack) == 8192 &&
       __hp1020_entry_stack_start == 0x10014020 &&
       __hp1020_entry_stack_end == 0x10016020, "stack extent changed")
ASSERT(SIZEOF(.runtime_mailbox) == 1024 &&
       __hp1020_entry_mailbox_start == 0x10016060 &&
       __hp1020_entry_mailbox_end == 0x10016460, "mailbox extent changed")
ASSERT(hp1020_usb_runtime_mailbox == __hp1020_entry_mailbox_start,
       "mailbox object displaced")

ASSERT(__hp1020_entry_data_start == 0x100164a0 &&
       __hp1020_entry_data_end > __hp1020_entry_data_start &&
       __hp1020_entry_data_end <= __hp1020_entry_data_cap,
       "generic initialized data missing or exceeds 96-byte budget")
ASSERT(SIZEOF(.runtime_sentinel) == 256 &&
       __hp1020_entry_sentinel_start == 0x10016500 &&
       __hp1020_entry_sentinel_end == 0x10016600, "sentinel extent changed")
ASSERT(hp1020_usb_runtime_sentinel == __hp1020_entry_sentinel_start,
       "sentinel object displaced")
ASSERT(SIZEOF(.runtime_memory) == 114704 &&
       __hp1020_entry_memory_start == 0x10016800 &&
       __hp1020_entry_memory_end == 0x10032810,
       "full contiguous production memory extent changed")
ASSERT(hp1020_usb_runtime_memory == __hp1020_entry_memory_start,
       "production memory object displaced")
ASSERT(__hp1020_entry_witness_start == 0x10032830 &&
       __hp1020_runtime_witness_unaligned_end > __hp1020_entry_witness_start &&
       __hp1020_entry_witness_end <= __hp1020_entry_witness_cap,
       "nonempty witness exceeds 10176-byte payload budget")
ASSERT(hp1020_usb_runtime_witness == __hp1020_entry_witness_start,
       "witness object displaced")
ASSERT(__hp1020_entry_witness_end - __hp1020_runtime_witness_unaligned_end < 4,
       "witness contains unexpected trailing padding")
ASSERT(__hp1020_entry_witness_guard_hi_end -
       __hp1020_entry_witness_guard_lo_start == 10240,
       "witness window including two guards must be exactly 10KiB")

ASSERT((__hp1020_entry_state_start & 15) == 0 &&
       (__hp1020_entry_memory_start & 15) == 0 &&
       (__hp1020_entry_mailbox_start & 15) == 0 &&
       (__hp1020_entry_witness_start & 15) == 0 &&
       (__hp1020_entry_stack_start & 15) == 0 &&
       (__hp1020_entry_stack_end & 15) == 0, "owned span starts must be 16-aligned")
ASSERT((__hp1020_entry_state_end & 3) == 0 &&
       (__hp1020_entry_memory_end & 3) == 0 &&
       (__hp1020_entry_mailbox_end & 3) == 0 &&
       (__hp1020_entry_witness_end & 3) == 0, "zero-span ends must be word-aligned")
ASSERT(__hp1020_entry_witness_guard_hi_end <= __hp1020_entry_main_end,
       "witness guard outside stock-declared envelope")
ASSERT(SIZEOF(.unexpected) == 0, "unexpected input section")
