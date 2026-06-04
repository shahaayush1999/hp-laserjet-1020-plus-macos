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
12. `engine-status-poll-report.md` - branch conditions that select engine status event words
13. `engine-event-consumer/engine-event-consumer.md` - scan for the unresolved engine `0x17` consumer path
14. `engine-dispatch-cfg/engine-dispatch-cfg.md` - raw CFG and exact engine dispatch switch table
15. `status-path-report.md` - PJL-visible status/fault string table and bridging functions
16. `status-mask-report.md` - literal masks/constants used by status-state and engine-status paths
17. `status-state-report.md` - status-state object layout and transition rules
18. `data-store-report.md` - indexed firmware state/config table used by PJL/status paths
19. `data-store-subscriber-report.md` - data-store publish/subscribe wiring and known callbacks
20. `printmgr-fallout-report.md` - PrintMgr `0x2d` notification handler and unresolved producer boundary
21. `pjl-status-code-reference.md` - external HP PJL status-code mapping for generated `CODE=` values
22. `dispatch-mmio-report.md` - dispatch tables and MMIO use sites
23. `mmio-semantics-report.md` - first behavioral names for hardware registers
24. `firmware-layout-report.md` - offline upload/image/ELF structural validator output
25. `symbols/apply-labels-report.md` - replay report for portable Ghidra labels
26. `toolchain-probe-report.md` - local build-tool availability for replacement firmware work
27. `prototype-roadmap.md` - practical prototype options and safety gates

Generated Ghidra scripts live in `ghidra-scripts/`.

Generated decompilation/report folders include:

- `boot-abi/`
- `call-clusters/`
- `descriptor-refs/`
- `data-store/`
- `data-store-subscribers/`
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
- `printmgr-fallout/`
- `queue-routing/`
- `queue-table-init/`
- `status-masks/`
- `status-path/`
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
- `analysis/engine-status-poll-report.md` maps the branch conditions that choose event words such as `0xe6100a01`, `0xf6000300`, and `0xe6000d03`.
- The exact engine dispatch table maps `0x17` to the default return/no-op block; `0x17` is produced and received but not consumed as a normal engine command.
- PJL-visible words such as `PAPERLESS`, `FUSER`, `TONEREXP`, and `JAMRECOVERY` are entries in a status command table at `0x10003c8c`, not direct engine dispatch cases.
- `0x10010838` is the current bridge from internal status words to StatusMgr/PJL-visible notifications; `0x1000a2a4` converts status words into PJL `CODE=` values.
- `0x10011178`, `0x100111b4`, and `0x100111d8` are the scalar get/lock/unlock API for an indexed data-store table at `0x1001ce14`; `0x10010f54` and `0x10010fd0` are its read/write-notify path.
- USTATUS `DISPLAY=` uses data-store entry `0x1a`, while `ONLINE=` uses entry `0x18`.
- Data-store subscribers are reached through `0x10006490 -> 0x1002c56c`; writes can notify queue subscribers with message `0x2d` or call direct callbacks.
- Known live subscriptions include ONLINE/status entries `0x18`/`0x19` into the control-panel path and engine entries `0x0f..0x14` into engine callbacks.
- Known queue subscribers from PrintMgr use queue id `1`; the current map labels queue id `1` as `engMsgQ`, where `0x2d` currently dispatches to default/no-op.
- PrintMgr has its own real `0x2d` dispatch case, but the queue-0 producer for that case remains unresolved.
- The status-state object is currently mapped through pointer `0x100063d8 -> 0x1002adb4`, with current status at offset `0x08`, transition status at `0x10`, and source/reason at `0x14`.
- HP's PJL reference anchors firmware-generated `410xx` codes as foreground paper-loading status codes; see `analysis/pjl-status-code-reference.md`.
- Engine/video MMIO has first behavioral names, but register semantics are not complete.
