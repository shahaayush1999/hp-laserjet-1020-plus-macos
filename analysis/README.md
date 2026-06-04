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
21. `queue-send-census-report.md` - global queue-send census and PrintMgr `0x2d` producer check
22. `printmgr-inputs-report.md` - proven PrintMgr queue inputs and handler targets
23. `job-object-flow-report.md` - JobMgr/PrintMgr list nodes and work-object handoff
24. `job-record-fields-report.md` - first field map for job and child/page records
25. `video-handoff-report.md` - PrintMgr to Video Queue `0x0b` payload and video state slots
26. `video-work-object-report.md` - `0x94` video/page work object lifecycle and fields
27. `zjs-parser-boundary/zjs-parser-boundary.md` - USB/ZjStream parser entry and chunk switch table
28. `jobmgr-raster-message-flow-report.md` - parser-to-JobMgr raster flow for `0x29`/`0x2a`/`0x2b`
29. `video-raster-consumer-report.md` - video-side consumer for `work +0x50` raster list nodes
30. `jobmgr-producer-boundary-report.md` - earlier JobMgr producer scan, now superseded for `0x29`
31. `pjl-status-code-reference.md` - external HP PJL status-code mapping for generated `CODE=` values
32. `dispatch-mmio-report.md` - dispatch tables and MMIO use sites
33. `mmio-semantics-report.md` - first behavioral names for hardware registers
34. `firmware-layout-report.md` - offline upload/image/ELF structural validator output
35. `symbols/apply-labels-report.md` - replay report for portable Ghidra labels
36. `toolchain-probe-report.md` - local build-tool availability for replacement firmware work
37. `prototype-roadmap.md` - practical prototype options and safety gates

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
- `jobmgr-producer-boundary/`
- `labeled/`
- `message-map/`
- `message-producers/`
- `object-creation/`
- `printmgr-fallout/`
- `queue-send-census/`
- `queue-routing/`
- `queue-table-init/`
- `status-masks/`
- `status-path/`
- `symbols/`
- `toolchain-probe/`
- `tasks/`
- `usb-path/`
- `video-work-object/`
- `zjs-parser-boundary/`

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
- PrintMgr has its own real `0x2d` dispatch case, but the queue-send census found `0` direct static sends of `queue 0, message 0x2d`.
- The only proven queue-send `0x2d` producer remains the data-store writer at `0x10010fd0`, where the queue id is read from each subscriber record.
- Proven PrintMgr queue-0 inputs are now summarized in `analysis/printmgr-inputs-report.md`; `0x4a` is sent to queue 0 but falls outside the PrintMgr dispatch range and is treated as a wake/retry/no-op style message.
- Job/work records now have a first flow map in `analysis/job-object-flow-report.md`; JobMgr creates records, PrintMgr moves list nodes from pending to active, and PrintMgr `0x11` returns active work to JobMgr.
- `analysis/job-record-fields-report.md` maps the first useful offsets in the `0x78`-byte job record and `0x50`-byte child/page record.
- `analysis/video-handoff-report.md` maps the PrintMgr-to-video handoff: `queue 8, message 0x0b` carries the work pointer in payload word 4, and the video thread stores it in video state slots `+0x60`/`+0x64`.
- `analysis/video-work-object-report.md` maps that pointer as a `0x94`-byte video/page work object. It is created by `0x1000f228`, populated by `0x100104c8`, stored in a child/page slot, and later consumed by Engine/PrintMgr/Video.
- `analysis/zjs-parser-boundary/zjs-parser-boundary.md` identifies `0x10009d34` as the ZjStream parser entry wired from the USB2Thread descriptor and maps chunk types `0..12`.
- `analysis/jobmgr-raster-message-flow-report.md` closes the parser-to-JobMgr raster path: `ZJT_JBIG_BIH -> JobMgr 0x29 -> 0x10023e28 -> work +0x84/+0x88/+0x8c/+0x90`, and `ZJT_JBIG_BID -> JobMgr 0x2a -> work +0x50` raster list.
- `analysis/video-raster-consumer-report.md` maps the video consumer side: `work +0x50` list nodes carry payload `+0x54` raster buffer pointers and `+0x48` byte-count/transfer-length candidates into VideoThread/raw-band hardware setup.
- `analysis/jobmgr-producer-boundary-report.md` is now superseded for message `0x29`; it remains useful as the pre-parser checkpoint showing why the producer was missed by broad queue-send scans.
- The status-state object is currently mapped through pointer `0x100063d8 -> 0x1002adb4`, with current status at offset `0x08`, transition status at `0x10`, and source/reason at `0x14`.
- HP's PJL reference anchors firmware-generated `410xx` codes as foreground paper-loading status codes; see `analysis/pjl-status-code-reference.md`.
- Engine/video MMIO has first behavioral names, but register semantics are not complete.
