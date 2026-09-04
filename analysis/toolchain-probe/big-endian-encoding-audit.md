# Big-endian instruction encoding audit (2026-09-05)

The earlier manual toolchain was runnable but emitted **little-endian code in
big-endian ELF files**. All open probes generated before this correction must
be treated as superseded. No corrected probe has been uploaded.

## Cause and reproduction

The pinned espressif/binutils-gdb tree `0104f7d3c1` has `XCHAL_HAVE_BE=1` in
`include/xtensa-config.h`, but its `bfd/xtensa-modules.c` describes a little-endian
ISA with FLIX. Assembler/disassembler agreement and ELF EI_DATA=2 did not detect
the inconsistent overlay. Neither `-EB` nor replacing e_machine repairs it.

The previous idle ELF encoded `movi.n a2,0` as `0c02`; stock BE code encodes it
as `c020`. The previous idle backward jump encoded `06ffff`; correct BE code
uses `63fffc`. The idle upload's quiet green printer observation therefore
provides no evidence of custom-code execution; the old program bytes were wrong.

`build-xtensa-binutils-manual.sh` now overlays the upstream BE ISA module from
commit `1e225492405c82b0b7b9973d8f549e1411168e3d` (before the 2010-05-28 module
replacement) onto the pinned tree. The matching BE module has a three-byte
maximum instruction size and no FLIX. No one-bit conversion of the LE tables
is attempted. This changes only the research tools, not installed printing.

## Independent checks

`check-xtensa-instruction-encoding.py` assembles eight fixed instruction fixtures
and both complete stock divide/remainder functions. Both function bodies must
reassemble byte for byte, including branch offsets and `loopnez`. Every probe
builder and the smoke test run this gate before assembly.

The recovered GNU disassembly independently agrees with the repaired Ghidra
mnemonic decode. Ghidra 12.1.1's three loop constructors incorrectly use the
LE BRI8 `at=7` grouping for BE. The isolated recovery script uses the endian-aware
`bri8_m=1, bri8_n=3` fields, giving BE `at=13`. It changes no installed Ghidra
files. The host interpreter implements loop semantics itself because this
mnemonic fix alone does not establish correctness of Ghidra's loop p-code.

## Validation and limits

All four open probes were rebuilt, the offline analysis and open probe suites
passed, and the bulk probe's two clean builds matched byte for byte. These
checks establish encoded instruction compatibility for the tested subset,
layout, source contracts, and static access restrictions. They do not establish
boot execution, USB initialization, controller completion semantics, cache
coherence, or exception/interrupt ABI behavior on the printer.

The generated disassembly contains embedded literal pools. Decoding literals
as instructions is not an execution trace or evidence of an actual access.
