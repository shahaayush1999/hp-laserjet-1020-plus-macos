/* Synthetic RAM fixture, never a boot/upload image. */
ENTRY(hp1020_image_pump_check)
SECTIONS {
  . = 0x20000000;
  .text : { *(.literal .literal.*) *(.text .text.*) }
  .rodata : ALIGN(4) { *(.rodata .rodata.*) }
  .data : ALIGN(4) { *(.data .data.*) }
  .bss : ALIGN(16) { *(.bss .bss.* COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
