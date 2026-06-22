# Xtensa Binutils Smoke Test

Tool prefix: `/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf`

## File Types

```text
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/toolchain-probe/binutils-smoke/tiny-boot.o:   ELF 32-bit MSB relocatable, Tensilica Xtensa, version 1 (SYSV), not stripped
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/toolchain-probe/binutils-smoke/tiny-boot.elf: ELF 32-bit MSB executable, Tensilica Xtensa, version 1 (SYSV), statically linked, not stripped
/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/toolchain-probe/binutils-smoke/tiny-boot.bin: data
```

## ELF Header

```text
ELF Header:
  Magic:   7f 45 4c 46 01 02 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF32
  Data:                              2's complement, big endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              EXEC (Executable file)
  Machine:                           Tensilica Xtensa Processor
  Version:                           0x1
  Entry point address:               0x10000000
  Start of program headers:          52 (bytes into file)
  Start of section headers:          4392 (bytes into file)
  Flags:                             0x300
  Size of this header:               52 (bytes)
  Size of program headers:           32 (bytes)
  Number of program headers:         1
  Size of section headers:           40 (bytes)
  Number of section headers:         7
  Section header string table index: 6
```

## Sections

```text
There are 7 section headers, starting at offset 0x1128:

Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [ 0]                   NULL            00000000 000000 000000 00      0   0  0
  [ 1] .text             PROGBITS        10000000 001000 000007 00  AX  0   0  1
  [ 2] .xtensa.info      NOTE            00000000 001007 000038 00      0   0  1
  [ 3] .xt.prop          PROGBITS        00000000 00103f 000018 00      0   0  1
  [ 4] .symtab           SYMTAB          00000000 001058 000080 10      5   4  4
  [ 5] .strtab           STRTAB          00000000 0010d8 000019 00      0   0  1
  [ 6] .shstrtab         STRTAB          00000000 0010f1 000037 00      0   0  1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  p (processor specific)
```

## Disassembly

```text

/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/toolchain-probe/binutils-smoke/tiny-boot.elf:     file format elf32-xtensa-be


Disassembly of section .text:

10000000 <_start>:
10000000:	362100               	entry	a1, 16
10000003:	0c02                	movi.n	a2, 0
10000005:	1df0                	retw.n
```

## Raw Binary

- `/Users/aayush/Documents/shahaayush1999/hp-laserjet-1020-plus-macos/analysis/toolchain-probe/binutils-smoke/tiny-boot.bin`
- Size: `7 bytes`
