# Firmware Toolchain Probe Report

This probe checks whether the local machine can merely inspect HP's old Xtensa firmware, or also build a replacement/prototype ELF.

## Result

- Big-endian Xtensa ELF container support is present in GNU binutils/BFD: `elf32-xtensa-be`.
- No local Xtensa compiler, assembler, or linker was found.
- Homebrew search for `xtensa` returned only `xtensor`, not an Xtensa embedded toolchain.
- Apple clang on this machine does not list Xtensa as a registered target.

## Practical Meaning

The current local setup is good for analysis:

- parse the existing ELF
- disassemble/decompile through Ghidra
- inspect sections/program headers
- wrap and validate HP-style `.img`/`.dl` envelopes

It is not yet sufficient to compile real replacement firmware code. For that, the next hard dependency is a working old/big-endian Xtensa build chain. ESP8266/ESP32 toolchains are not automatically suitable because they target specific little-endian Xtensa variants and SoC ABIs, not necessarily the HP printer's `0xabc7` old Xtensa executable format.

## Probe Command

```sh
scripts/probe-firmware-toolchain.sh > analysis/toolchain-probe/latest.md
```

The latest captured probe is in `analysis/toolchain-probe/latest.md`.
