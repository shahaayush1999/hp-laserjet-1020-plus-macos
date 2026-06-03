# HP LaserJet 1020 Firmware Viability Spike

Date: 2026-06-04

## Scope

This spike checks whether the HP LaserJet 1020/1020 Plus firmware blob is practically analyzable with local reverse-engineering tooling. It does not attempt to rewrite firmware or modify the working printer setup.

## Tools Installed

- Ghidra 12.1.1 through Homebrew
- OpenJDK 21 through Homebrew as a Ghidra dependency
- radare2 6.1.6
- GNU binutils 2.46.0
- LLVM 22.1.6

The separate Temurin cask was attempted but failed because it needs an interactive sudo password. It is not needed for this spike because Homebrew OpenJDK 21 works for Ghidra when invoked with `JAVA_HOME=/opt/homebrew/opt/openjdk@21`.

## Extracted Firmware

The raw firmware image has an 8-byte ASCII date prefix:

```text
20050309
```

The actual ELF payload was extracted with:

```sh
mkdir -p analysis
dd if=assets/firmware-source/sihp1020.img of=analysis/sihp1020.elf bs=1 skip=8 status=none
```

The extracted file is:

```text
ELF 32-bit MSB executable, Old Xtensa (unofficial), version 1 (SYSV), statically linked, stripped
```

## Structural Findings

- Architecture: big-endian Tensilica Xtensa
- ELF machine: `0xabc7`, old/unofficial Xtensa value
- Entry point: `0x100167a8`
- Program headers: 11
- Section headers: 39
- Main code section: `.text` at `0x10005c80`, size `0x15f0f`
- Reset vector code: `.ResetVector.text` at `0x10100020`, size `0x2e0`
- Data section: `.data` at `0x1001bb90`, size `0x1ab0`
- BSS: `.bss` at `0x1001d640`, size `0x17ba0`
- Compiler marker: `GCC: (GNU) egcs-2.90.29 (egcs-1.0.3 release) for Xtensa T1050.2/T1050.3`

## Tool Results

GNU `greadelf` parses the ELF cleanly.

GNU `gobjdump` recognizes the binary as `elf32-xtensa-be` and disassembles it.

LLVM reads ELF metadata, but `llvm-objdump` does not disassemble it because it cannot select a target for this old Xtensa ELF.

radare2 reads metadata and sections, but reports the machine as unknown and warns about missing Xtensa parser support. It should not be the primary tool here.

Ghidra imports successfully when forced to:

```text
Xtensa:BE:32:default
```

Automatic Ghidra import does not work because the loader does not pick a load spec for this file by itself. Forced import works and analysis completed in about 9 seconds.

Ghidra found:

- 326 functions
- real memory blocks matching ELF sections
- string references from code into USB/PJL/ACL/ThreadX-related strings
- two decompiler p-code warnings, which suggest some Xtensa instructions or configuration-specific encodings may need manual handling

## Useful Strings With Code References

Ghidra found references to strings including:

- `USB2IdleThread`
- `USB2Thread`
- `agiACLDownload`
- `TIME=Wed Mar 09 12:27:39 2005 BOI049 PROD=MANGUSTA CFG=GCC_RELEASE`
- `@PJL ECHO`
- `FWVER`
- `FUSER`
- `PAPERLESS`
- `TONEREXP`
- `JAMRECOVERY`
- ThreadX diagnostic strings

This means the project is not blind binary archaeology. There are useful anchors for naming functions and reconstructing subsystems.

## Viability Assessment

Reverse-engineering the firmware enough to understand major components is viable.

The current tooling is good enough for a real first pass:

- Ghidra can load and analyze the binary with a forced Xtensa big-endian language.
- GNU objdump can produce repeatable disassembly.
- Strings and references provide usable landmarks.
- The firmware has clear RTOS, USB, PJL/ACL, and device-state clues.

The hard part is not disassembly speed. The hard part is hardware semantics.

AI assistance likely compresses repetitive work significantly: labeling functions from string references, grouping call trees, writing Ghidra scripts, building reports, comparing disassembly, and documenting hypotheses. It does not remove the need to validate hardware behavior, especially around motors, fuser, sensors, laser/scanner timing, page pipeline, memory-mapped registers, and fault states.

Updated estimate after this spike:

- Basic structural report: done
- Label obvious string-referenced functions and call clusters: 1-2 days
- Map likely USB/PJL/ACL receive/download path: 2-5 days
- Map ThreadX/task layout and major firmware subsystems: 1-2 weeks
- Build a confident behavioral model of the existing firmware: 3-6 weeks
- Replacement firmware that boots/responds over USB: still likely weeks, not a weekend
- Replacement firmware that prints reliably: still likely months solo because hardware validation dominates

The earlier "months for replacement firmware" estimate still stands. The "days to understand whether this is tractable" estimate was conservative; after tooling, tractability is already much clearer.

## Next Technical Step

Open the binary in Ghidra with:

```sh
JAVA_HOME=/opt/homebrew/opt/openjdk@21 ghidraRun
```

Import `analysis/sihp1020.elf` manually using:

```text
Language: Xtensa:BE:32:default
Compiler spec: default
```

Then start by renaming functions that reference:

- `USB2Thread`
- `USB2IdleThread`
- `agiACLDownload`
- `@PJL`
- `@PJL ECHO`
- `FWVER`
- `PAPERLESS`
- `FUSER`
- `TONEREXP`
- `JAMRECOVERY`

