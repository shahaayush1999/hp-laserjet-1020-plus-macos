/* Synthetic RAM descriptor/document fixture only; never a boot/upload image. */
ENTRY(hp1020_bulk_fixture_reset)
SECTIONS {
  . = 0x20000000;
  .text : { *(.literal .literal.*) *(.text .text.*) }
  .rodata : ALIGN(4) { *(.rodata .rodata.*) }
  .data : ALIGN(4) { *(.data .data.*) }
  .bss : ALIGN(16) { *(.bss .bss.* COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
