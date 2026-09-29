/* Synthetic virtual RAM only; not a firmware wrapper or a device boot image. */
ENTRY(hp1020_rx_fixture_reset)
SECTIONS {
  . = 0x20000000;
  .text : { *(.literal .literal.*) *(.text .text.*) }
  .rodata : ALIGN(4) { *(.rodata .rodata.*) }
  .data : ALIGN(4) { *(.data .data.*) }
  .bss : ALIGN(16) { *(.bss .bss.* COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
