# HP 1020 Firmware Analysis Index

This directory contains offline reverse-engineering notes for the HP LaserJet 1020/1020 Plus firmware.

Start here:

1. `firmware-architecture-map.md` - current integrated architecture map
2. `viability-report.md` - first viability snapshot
3. `upload-wrapper-report.md` - `.img` to `.dl` upload envelope
4. `boot-abi-report.md` - ELF/reset/vector/system-interface shape
5. `startup-chain-report.md` - entry path, interrupt dispatch, scheduler notes
6. `rtos-primitives-report.md` - RTOS object signatures and queue/send/receive primitives
7. `object-creation-report.md` - queue/thread creation wrappers
8. `queue-resolution-report.md` - queue IDs and consumers
9. `message-producers-report.md` - message producers by subsystem
10. `message-map-report.md` - consolidated queue/message dictionary
11. `engine-event-report.md` - engine queue `0x17` payload/event-code map
12. `engine-event-consumer/engine-event-consumer.md` - scan for the unresolved engine `0x17` consumer path
13. `engine-dispatch-cfg/engine-dispatch-cfg.md` - raw CFG and exact engine dispatch switch table
14. `dispatch-mmio-report.md` - dispatch tables and MMIO use sites
15. `mmio-semantics-report.md` - first behavioral names for hardware registers
16. `firmware-layout-report.md` - offline upload/image/ELF structural validator output
17. `symbols/apply-labels-report.md` - replay report for portable Ghidra labels
18. `toolchain-probe-report.md` - local build-tool availability for replacement firmware work
19. `prototype-roadmap.md` - practical prototype options and safety gates

Generated Ghidra scripts live in `ghidra-scripts/`.

Generated decompilation/report folders include:

- `boot-abi/`
- `call-clusters/`
- `descriptor-refs/`
- `dispatch-mmio/`
- `engine/`
- `engine-dispatch-cfg/`
- `engine-event-consumer/`
- `engine-events/`
- `firmware-layout/`
- `identity/`
- `labeled/`
- `message-map/`
- `message-producers/`
- `object-creation/`
- `queue-routing/`
- `queue-table-init/`
- `symbols/`
- `toolchain-probe/`
- `tasks/`
- `usb-path/`

Useful current conclusions:

- The upload wrapper is known and reproducible with `scripts/wrap-firmware-acl.py`.
- The upload/image/ELF layout is checkable with `scripts/inspect-firmware-layout.py`.
- The firmware is a date-prefixed Xtensa big-endian ELF inside an HP ACL/PJL envelope.
- Ghidra can analyze it when forced to `Xtensa:BE:32:default`.
- Current labels are portable via `analysis/symbols/hp1020-labels.tsv` and `analysis/ghidra-scripts/ApplyHp1020LabelsFromTsv.java`.
- Local binutils can inspect `elf32-xtensa-be`, but no local Xtensa compiler/assembler/linker is installed.
- The firmware uses ThreadX-style RTOS objects with magic values such as `QUEU` and `THRD`.
- Queue send-by-ID reads from runtime table `0x1002c918`.
- Queue `8` is strongly supported as `Video Queue`, but the exact runtime table write has not been found.
- Message numbers are queue-relative; use `analysis/message-map/queue-message-map.tsv` as the current `(queue, message)` dictionary.
- Engine message `0x17` carries a second-word event/status code; use `analysis/engine-events/engine-0x17-events.tsv` as the current code map.
- The exact engine dispatch table maps `0x17` to the default return/no-op block; `0x17` is produced and received but not consumed as a normal engine command.
- Engine/video MMIO has first behavioral names, but register semantics are not complete.
