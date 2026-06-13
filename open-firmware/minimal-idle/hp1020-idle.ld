OUTPUT_FORMAT("elf32-xtensa-be")
OUTPUT_ARCH(xtensa)
ENTRY(_start)

PHDRS
{
  vectors PT_LOAD FLAGS(5);
  kexc_lit PT_LOAD FLAGS(5);
  kexc_text PT_LOAD FLAGS(5);
  uexc_lit PT_LOAD FLAGS(5);
  uexc_text PT_LOAD FLAGS(5);
  dexc_text PT_LOAD FLAGS(5);
  iface PT_LOAD FLAGS(6);
  main PT_LOAD FLAGS(7);
  reset PT_LOAD FLAGS(5);
  debug_lit PT_LOAD FLAGS(5);
  debug_text PT_LOAD FLAGS(5);
}

SECTIONS
{
  . = 0x10000000;
  .WindowVectors.text : { KEEP(*(.WindowVectors.text)) } :vectors

  . = 0x10000180;
  .KernelExceptionVector.literal : { KEEP(*(.KernelExceptionVector.literal)) } :kexc_lit

  . = 0x10000200;
  .KernelExceptionVector.text : { KEEP(*(.KernelExceptionVector.text)) } :kexc_text

  . = 0x1000021c;
  .UserExceptionVector.literal : { KEEP(*(.UserExceptionVector.literal)) } :uexc_lit

  . = 0x10000220;
  .UserExceptionVector.text : { KEEP(*(.UserExceptionVector.text)) } :uexc_text

  . = 0x10000270;
  .DoubleExceptionVector.text : { KEEP(*(.DoubleExceptionVector.text)) } :dexc_text

  . = 0x10000370;
  .sys_interface_table : { KEEP(*(.sys_interface_table)) } :iface

  . = 0x10003000;
  .rodata : { KEEP(*(.rodata.probe)) *(.rodata*) } :main

  . = 0x10005c80;
  .text : {
    KEEP(*(.text.probe))
    *(.text)
  } :main

  . = 0x100167a8;
  .text.entry : { KEEP(*(.text.entry)) } :main

  . = 0x1001bb90;
  .data : { *(.data*) } :main

  . = 0x1001d640;
  .bss (NOLOAD) : { *(.bss*) *(COMMON) } :main

  . = 0x10100020;
  .ResetVector.text : { KEEP(*(.ResetVector.text)) } :reset

  . = 0x10100300;
  .DebugExceptionVector.literal : { KEEP(*(.DebugExceptionVector.literal)) } :debug_lit

  . = 0x10100320;
  .DebugExceptionVector.text : { KEEP(*(.DebugExceptionVector.text)) } :debug_text

  /DISCARD/ : {
    *(.comment)
    *(.xtensa.info)
    *(.xt.prop)
    *(.note*)
  }
}
