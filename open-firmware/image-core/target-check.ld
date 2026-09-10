/* Synthetic virtual RAM only. No firmware wrapper or device boot entry. */
ENTRY(hp1020_image_run)
SECTIONS {
  . = 0x20000000;
  .text : { *(.literal .literal.*) *(.text .text.*) }
  .rodata : ALIGN(4) { *(.rodata .rodata.*) }
  .data : ALIGN(4) { *(.data .data.*) }
  .bss : ALIGN(16) { *(.bss .bss.* COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
