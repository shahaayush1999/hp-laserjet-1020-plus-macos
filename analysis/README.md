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
10. `dispatch-mmio-report.md` - dispatch tables and MMIO use sites
11. `mmio-semantics-report.md` - first behavioral names for hardware registers

Generated Ghidra scripts live in `ghidra-scripts/`.

Generated decompilation/report folders include:

- `boot-abi/`
- `call-clusters/`
- `descriptor-refs/`
- `dispatch-mmio/`
- `engine/`
- `identity/`
- `labeled/`
- `message-producers/`
- `object-creation/`
- `queue-routing/`
- `queue-table-init/`
- `tasks/`
- `usb-path/`

Useful current conclusions:

- The upload wrapper is known and reproducible with `scripts/wrap-firmware-acl.py`.
- The firmware is a date-prefixed Xtensa big-endian ELF inside an HP ACL/PJL envelope.
- Ghidra can analyze it when forced to `Xtensa:BE:32:default`.
- The firmware uses ThreadX-style RTOS objects with magic values such as `QUEU` and `THRD`.
- Queue send-by-ID reads from runtime table `0x1002c918`.
- Queue `8` is strongly supported as `Video Queue`, but the exact runtime table write has not been found.
- Engine/video MMIO has first behavioral names, but register semantics are not complete.

