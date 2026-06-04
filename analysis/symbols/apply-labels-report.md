# Ghidra Label Application Report

This report records an offline label replay against the HP 1020 firmware Ghidra import.

- Program: `sihp1020.elf`
- Language: `Xtensa:BE:32:default`
- Label file: `analysis/symbols/hp1020-labels.tsv`
- Labels read: `109`
- Function labels applied: `81`
- Data labels applied: `28`
- Warnings: `0`

## Meaning

The TSV file is the portable label source of truth. The Java script lets a fresh Ghidra project
recover the current function/data names before running deeper manual analysis.
