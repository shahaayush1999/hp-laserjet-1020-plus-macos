/* UNEXECUTED DRAFT. New offline ELF layout inside stock-declared spans.
 * Not an HP loader ABI claim, upload image, hardware map or linker-tested file.
 * Guard intervals are symbols, not loadable fill: the runner paints and checks
 * them separately. No PT_LOAD may create zero-fill across a protected gap.
 */
OUTPUT_FORMAT("elf32-xtensa-be")
OUTPUT_ARCH(xtensa)
ENTRY(hp1020_entry_start)

PHDRS
{
  window_vectors PT_LOAD FLAGS(5);
  exception_vectors PT_LOAD FLAGS(5);
  double_vector PT_LOAD FLAGS(5);
  interface_table PT_LOAD FLAGS(4);
  code PT_LOAD FLAGS(5);
  initialized_data PT_LOAD FLAGS(6);
  state PT_LOAD FLAGS(6);
  stack PT_LOAD FLAGS(6);
  mailbox PT_LOAD FLAGS(6);
  entry_island PT_LOAD FLAGS(5);
  memory PT_LOAD FLAGS(6);
  reset_vector PT_LOAD FLAGS(5);
  debug_vector PT_LOAD FLAGS(5);
}

__hp1020_entry_main_start = 0x10003000;
__hp1020_entry_main_end = 0x100351e0;
__hp1020_entry_low_reserved_start = 0x10003000;
__hp1020_entry_low_reserved_end = 0x10007000;

__hp1020_entry_data_guard_lo_start = 0x1000d000;
__hp1020_entry_data_guard_lo_end = 0x1000d020;
__hp1020_entry_data_guard_hi_start = 0x1000d120;
__hp1020_entry_data_guard_hi_end = 0x1000d140;
__hp1020_entry_state_guard_lo_start = 0x1000dfe0;
__hp1020_entry_state_guard_lo_end = 0x1000e000;
__hp1020_entry_state_guard_hi_start = 0x100114b8;
__hp1020_entry_state_guard_hi_end = 0x100114e0;
__hp1020_entry_stack_guard_lo_start = 0x10011fe0;
__hp1020_entry_stack_guard_lo_end = 0x10012000;
__hp1020_entry_stack_guard_hi_start = 0x10014000;
__hp1020_entry_stack_guard_hi_end = 0x10014020;
__hp1020_entry_mailbox_guard_lo_start = 0x10014020;
__hp1020_entry_mailbox_guard_lo_end = 0x10014040;
__hp1020_entry_mailbox_guard_hi_start = 0x10014440;
__hp1020_entry_mailbox_guard_hi_end = 0x10014460;
__hp1020_entry_memory_guard_lo_start = 0x100167e0;
__hp1020_entry_memory_guard_lo_end = 0x10016800;
__hp1020_entry_memory_guard_hi_start = 0x10032810;
__hp1020_entry_memory_guard_hi_end = 0x10032830;

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

  .text 0x10007000 : {
    __hp1020_entry_code_start = .;
    KEEP(*(.entry.normalizer))
    *(.literal .literal.*)
    *(.text .text.*)
    __hp1020_entry_text_end = .;
  } :code
  .rodata : ALIGN(4) {
    __hp1020_entry_rodata_start = .;
    *(.rodata .rodata.*)
    __hp1020_entry_rodata_end = .;
    __hp1020_entry_code_end = .;
  } :code

  .entry_data 0x1000d020 : {
    __hp1020_entry_data_start = .;
    KEEP(*(.entry_data))
    __hp1020_entry_data_end = .;
  } :initialized_data
  .entry_state 0x1000e000 (NOLOAD) : {
    __hp1020_entry_state_start = .;
    KEEP(*(.entry_state))
    __hp1020_entry_state_end = .;
  } :state
  .entry_stack 0x10012000 (NOLOAD) : {
    __hp1020_entry_stack_start = .;
    . += 0x2000;
    __hp1020_entry_stack_end = .;
  } :stack
  .entry_mailbox 0x10014040 (NOLOAD) : {
    __hp1020_entry_mailbox_start = .;
    KEEP(*(.entry_mailbox))
    __hp1020_entry_mailbox_end = .;
  } :mailbox
  .entry_island 0x10016780 : {
    __hp1020_entry_island_start = .;
    KEEP(*(.entry.island))
    __hp1020_entry_island_end = .;
  } :entry_island
  .entry_memory 0x10016800 (NOLOAD) : {
    __hp1020_entry_memory_start = .;
    KEEP(*(.entry_memory))
    __hp1020_entry_memory_end = .;
  } :memory

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

  /* Keep instruction/literal properties for the independent linked ISA audit.
   * These input metadata sections have no SHF_ALLOC and belong to no PT_LOAD. */
  .xtensa.info 0 : { KEEP(*(.xtensa.info)) } :NONE
  .xt.prop 0 : { KEEP(*(.xt.prop .xt.prop.*)) } :NONE
  .xt.lit 0 : { KEEP(*(.xt.lit .xt.lit.*)) } :NONE
  .xt.insn 0 : { KEEP(*(.xt.insn .xt.insn.*)) } :NONE
  /* Pinned libgcc carries these five non-allocated DWARF sections. Preserve
   * them explicitly; none belongs to a load segment or runtime permission. */
  .debug_line 0 : { *(.debug_line) } :NONE
  .debug_info 0 : { *(.debug_info) } :NONE
  .debug_abbrev 0 : { *(.debug_abbrev) } :NONE
  .debug_aranges 0 : { *(.debug_aranges) } :NONE
  .debug_str 0 : { *(.debug_str) } :NONE
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }

  /* No generic zero area or hidden new mutable global may escape the four
   * explicit C object contracts. No unrecognized input section is ignored. */
  .unexpected_rw 0 (NOLOAD) : {
    *(.data .data.* .sdata .sdata.* .bss .bss.* .sbss .sbss.*)
    *(COMMON)
  } :NONE
  .unexpected 0 : { *(*) } :NONE
}

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
ASSERT(__hp1020_entry_code_start == 0x10007000, "wrong code start")
ASSERT(__hp1020_entry_code_end <= 0x1000d000, "code spills into data guard")
ASSERT(hp1020_entry_normalize >= __hp1020_entry_code_start &&
       hp1020_entry_normalize < __hp1020_entry_text_end, "normalizer outside text")
ASSERT(hp1020_entry_after_normalization > hp1020_entry_normalize &&
       hp1020_entry_after_normalization < hp1020_entry_before_c,
       "wrong normalization checkpoint order")
ASSERT(hp1020_entry_before_c < hp1020_entry_park &&
       hp1020_entry_park < __hp1020_entry_text_end, "wrong C/park checkpoint order")
ASSERT(hp1020_entry_c >= __hp1020_entry_code_start &&
       hp1020_entry_c < __hp1020_entry_text_end, "C entry outside text")
ASSERT(hp1020_entry_start == 0x100167a8, "wrong ELF entry address")
ASSERT(SIZEOF(.entry_island) == 0x60, "entry island changed")
ASSERT(__hp1020_entry_island_end == 0x100167e0, "entry spills into memory guard")
ASSERT(SIZEOF(.entry_data) == 256 && __hp1020_entry_data_end == 0x1000d120,
       "initialized data object size changed")
ASSERT(SIZEOF(.entry_state) == 13496 && __hp1020_entry_state_end == 0x100114b8,
       "production document state size changed")
ASSERT(SIZEOF(.entry_mailbox) == 1024 && __hp1020_entry_mailbox_end == 0x10014440,
       "mailbox size changed")
ASSERT(SIZEOF(.entry_memory) == 114704 && __hp1020_entry_memory_end == 0x10032810,
       "production memory size changed")
ASSERT(SIZEOF(.entry_stack) == 0x2000 && __hp1020_entry_stack_end == 0x10014000,
       "stack extent changed")
ASSERT(hp1020_entry_data == __hp1020_entry_data_start, "data object displaced")
ASSERT(hp1020_entry_state == __hp1020_entry_state_start, "state object displaced")
ASSERT(hp1020_entry_mailbox == __hp1020_entry_mailbox_start, "mailbox object displaced")
ASSERT(hp1020_entry_memory == __hp1020_entry_memory_start, "memory object displaced")
ASSERT((__hp1020_entry_state_start & 15) == 0 &&
       (__hp1020_entry_memory_start & 15) == 0 &&
       (__hp1020_entry_mailbox_start & 15) == 0 &&
       (__hp1020_entry_stack_start & 15) == 0 &&
       (__hp1020_entry_stack_end & 15) == 0, "owned spans must be 16-aligned")
ASSERT((__hp1020_entry_state_end & 3) == 0 &&
       (__hp1020_entry_memory_end & 3) == 0 &&
       (__hp1020_entry_mailbox_end & 3) == 0, "zero-span end must be word-aligned")
ASSERT(__hp1020_entry_memory_guard_hi_end <= __hp1020_entry_main_end,
       "memory guard outside stock-declared envelope")
ASSERT(SIZEOF(.unexpected_rw) == 0, "unexpected mutable data/BSS")
ASSERT(SIZEOF(.unexpected) == 0, "unexpected input section")
