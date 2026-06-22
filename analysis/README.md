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
30. `printer-test-readiness-report.md` - controlled sample and next connected-printer test commands
31. `jobmgr-producer-boundary-report.md` - earlier JobMgr producer scan, now superseded for `0x29`
32. `pjl-status-code-reference.md` - external HP PJL status-code mapping for generated `CODE=` values
33. `dispatch-mmio-report.md` - dispatch tables and MMIO use sites
34. `mmio-semantics-report.md` - first behavioral names for hardware registers
35. `firmware-layout-report.md` - offline upload/image/ELF structural validator output
36. `symbols/apply-labels-report.md` - replay report for portable Ghidra labels
37. `toolchain-probe-report.md` - local build-tool availability for replacement firmware work
38. `prototype-roadmap.md` - practical prototype options and safety gates
39. `open-firmware-model-report.md` - executable offline model of the normal ZjStream-to-work-object path
40. `hardware-boundary/hardware-boundary.md` - concrete safe/unsafe MMIO boundary for custom firmware work
41. `hardware-boundary/video-register-projection.md` - projection from modeled work fields to first unsafe video registers
42. `non-printing-usb-probe-spec.md` - narrow custom-firmware boot/USB probe target and hard safety gate
43. `hardware-boundary/safety-scanner-known-unsafe-report.md` - validation that the safety scanner flags known unsafe firmware paths
44. `toolchain-probe/xtensa-toolchain-checkpoint.md` - crosstool-NG/Xtensa binutils checkpoint
45. `open-firmware-probes/minimal-idle/summary.md` - generated open idle firmware probe and static validation
46. `boot-handoff/boot-handoff.md` - stock-vs-open boot/upload handoff comparison
47. `open-firmware-probes/minimal-idle/hardware-test-result-2026-06-15.md` - first connected-printer idle-probe upload result
48. `non-printing-status-probe/status-query-plan.md` - guarded PJL/back-channel query plan for the next non-mechanical hardware discriminator
49. `non-printing-status-probe/pjl-backchannel-map.md` - firmware and CUPS evidence behind the PJL/status query path
50. `usb-path/usb-marker-boundary.md` - why a future USB marker probe is plausible but not the next safe upload
51. `usb-path/usb-descriptor-extraction.md` - generated extraction of stock USB device/config descriptors and identity strings
52. `usb-path/usb-descriptor-response-model.md` - byte-level GET_DESCRIPTOR response model for stock descriptors and a future open marker string
53. `usb-path/endpoint0-machinery.md` - stock endpoint-0 transfer/queue/register machinery and remaining USB marker blocker
54. `usb-path/usb-mmio-map.md` - generated map of `0xb300....` USB controller reads/writes used by stock endpoint-0 handling
55. `open-firmware-probes/minimal-idle/usb-contract-scan.md` - strict USB-only probe contract scan for the current idle candidate
56. `toolchain-probe/binutils-exec-status.md` - old corrupt crosstool-NG prefix and recovered manual binutils path
57. `toolchain-probe/manual-binutils-rebuild.md` - reproducible manual Xtensa binutils recovery path
58. `toolchain-probe/binutils-smoke/report.md` - runnable Xtensa assembler/linker smoke test using the recovered manual prefix
59. `open-firmware-probes/usb-register-snapshot/summary.md` - generated open-code USB register snapshot probe and static validation
60. `usb-path/open-endpoint0-model.md` - pure host-side endpoint-0 GET_DESCRIPTOR decision model for a future open USB marker
61. `open-firmware-probes/usb-register-snapshot/usb-mmio-access-scan.md` - disassembly-level proof that the USB snapshot probe reads mapped USB registers and writes none
62. `usb-path/endpoint0-handshake-contract.md` - static endpoint-0 setup/status gates and USB controller programming sequences
63. `open-firmware-probes/usb-marker-draft/summary.md` - generated write-capable USB-only endpoint-0 marker draft and static validation
64. `open-firmware-probes/usb-marker-draft/hardware-test-plan.md` - guarded future hardware test plan for the marker draft
65. `open-firmware-probes/usb-register-snapshot/hardware-test-plan.md` - guarded future hardware test plan for the read-only USB snapshot probe
66. `open-firmware-probes/usb-marker-draft/memory-boundary-scan.md` - explicit setup-buffer reads and stock response-state writes in the marker draft
67. `open-firmware-probes/usb-marker-draft/marker-descriptor-check.md` - embedded marker descriptor bytes, length, and hardware alias verification
68. `open-firmware-probes/usb-marker-draft/marker-length-flow-check.md` - source-level guard that clipped host length reaches endpoint-0
69. `open-firmware-probes/usb-marker-draft/behavior-model.md` - host-side model of marker setup/gate decisions and response-length clipping
70. `open-firmware-probes/hardware-test-ladder.md` - staged non-printing hardware test order and one-stage harness usage
71. `open-firmware-model/model-invariants.md` - regenerated invariant check for the ZjStream print-path model across all generated cases
72. `status-path/status-code-correlation.md` - conservative engine-event-to-PJL-CODE correlation model
73. `non-printing-status-probe/pjl-status-contract.md` - exact non-printing PJL/status payload contract and expected response markers
74. `offline-consistency/offline-consistency.md` - cross-report consistency gate for the current offline conclusions
75. `usb-path/usb-setup-source.md` - static split between the likely setup-packet RAM buffer and USB event pointer
76. `usb-path/control-in-data-stage.md` - stock endpoint-0 control-IN transfer descriptor and kick model
77. `usb-path/control-completion-event.md` - stock endpoint-0 completion event-flag model
78. `usb-path/usb-interrupt-events.md` - USB interrupt task event-lane and completion-bit model
79. `open-firmware-model/minimal-print-scope.md` - generated minimum scope for a printing-only open replacement, including platform boundary and remaining blockers
80. `hardware-boundary/first-page-hardware-sequence.md` - generated ordered first-page sequence from parser handoff into engine/video/refill hardware
81. `hardware-boundary/video-engine-register-semantics.md` - generated register-role model for engine handshake, video setup, video transfer, and raw-band feed
82. `hardware-boundary/video-prepare-modes.md` - generated branch/table model for `0xb100` video prepare timing and mode setup
83. `hardware-boundary/engine-command-status.md` - generated command/status model for the stock `0xb050` engine register pair, status reads, side-effect commands, and event decisions
84. `hardware-boundary/engine-status-decisions.md` - generated executable branch model for `hp1020_engine_status_poll_candidate` scenarios and side effects
85. `hardware-boundary/video-engine-feedback.md` - generated model of VideoThread completion/reset messages back into engine/status flow
86. `hardware-boundary/video-transfer-ring.md` - generated model of video transfer ring ownership, channel A/B descriptors, and band-done refill behavior
87. `hardware-boundary/video-irq-decisions.md` - generated executable branch model for video block IRQ/status bits and reset-dispatch cases
88. `hardware-boundary/video-band-queue.md` - generated model of the `0x10013f34` video descriptor queue/list helper, raw-band A/B register feed, and `+0xdc/+0xe0` loop gate
89. `hardware-boundary/video-mode-flag.md` - generated model of work object `+0x74` to video state `+0xfc` and the IRQ refill fork between descriptor-queue and raw linked-list paths
90. `hardware-boundary/video-refill-topology.md` - generated synthesis of the normal descriptor-queue refill path versus the alternate raw linked-list refresh path
91. `hardware-boundary/video-prepare-projection.md` - generated projection from current host print variants into the 600dpi `0xb100` video-prepare setup scenarios
92. `hardware-boundary/engine-print-topology.md` - generated synthesis of engine startup/preflight, page work acceptance, status recovery, and completion/deferred-work flow
93. `open-firmware-model/raster-field-semantics.md` - generated host-to-raster field semantics for BIH/BID values that reach the video hardware boundary
94. `hardware-boundary/video-dataflow-contract.md` - generated normal first-page dataflow contract from host raster fields into render/refill hardware formulas
95. `hardware-boundary/video-chunk-sizing.md` - generated model for stride-derived `+0xcc` chunk sizing and raw-band flag helper behavior
96. `hardware-boundary/video-helper-disassembly.md` - generated instruction-level status report for helper `0x1001b668` and the current old-Xtensa decoder limit
97. `hardware-boundary/video-queue-payload-chain.md` - generated pointer-chain report showing VideoThread prepare receives the `0x94` video/page work object
98. `hardware-boundary/video-remaining-units.md` - generated model for the `+0xd0/+0xd4` remaining-unit candidate source and unresolved active work `+0x26` source

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
- `hardware-boundary/`
- `identity/`
- `jobmgr-producer-boundary/`
- `labeled/`
- `message-map/`
- `message-producers/`
- `open-firmware-model/`
- `open-firmware-probes/`
- `object-creation/`
- `printmgr-fallout/`
- `queue-send-census/`
- `queue-routing/`
- `queue-table-init/`
- `samples/generated/`
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
- The recovered manual Xtensa binutils prefix at `/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf` can assemble/link/inspect `elf32-xtensa-be`; full GCC/newlib is still not needed for the current assembly probes.
- `open-firmware/minimal-idle/` now builds an open-code, non-printing idle firmware probe with HP-style `.elf`, date-prefixed `.img`, and PJL/ACL `.dl` outputs.
- `analysis/open-firmware-probes/minimal-idle/summary.md` records the current generated probe. It passes the boot-probe layout profile and safety scan, and it has trap-safe system-interface/runtime-vector placeholders.
- `open-firmware/usb-register-snapshot/` now builds an open-code, non-printing USB register snapshot probe. It only reads mapped USB `0xb300....` registers into RAM and then idles; it has no host-visible output yet and has not been uploaded.
- `open-firmware/usb-marker-draft/` now builds an open-code, USB-only marker draft. It recognizes a product-string `GET_DESCRIPTOR` setup shape and writes only the extracted stock endpoint-0 USB register sequences. It has not been uploaded.
- `scripts/validate-open-firmware-probes.sh` rebuilds all open firmware probes and runs the offline layout/scanner/dry-run harness validation stack.
- `analysis/boot-handoff/boot-handoff.md` compares the stock HP firmware and open idle probe. The core packaging/shape question is mostly answered; the next decisive question is whether hardware accepts and branches into the open payload.
- `analysis/open-firmware-probes/minimal-idle/hardware-test-result-2026-06-15.md` records the first hardware upload: USB backend sent all `121931` bytes, printer stayed green/quiet with no paper movement, and macOS still saw the HP USB identity. This is a good safety result but not proof that `_start` executed.
- `scripts/query-hp1020-pjl-status.sh` is the next guarded hardware probe. It sends tiny non-printing PJL/status payloads through the direct USB backend, captures CUPS back-channel fd 3 bytes, and writes `backchannel-analysis.md` so stock/open responses can be classified without eyeballing hex.
- The firmware uses ThreadX-style RTOS objects with magic values such as `QUEU` and `THRD`.
- Queue send-by-ID reads from runtime table `0x1002c918`.
- Queue `8` is strongly supported as `Video Queue`, but the exact runtime table write has not been found.
- Message numbers are queue-relative; use `analysis/message-map/queue-message-map.tsv` as the current `(queue, message)` dictionary.
- Engine message `0x17` carries a second-word event/status code; use `analysis/engine-events/engine-0x17-events.tsv` as the current code map.
- `analysis/engine-status-poll-report.md` maps the branch conditions that choose event words such as `0xe6100a01`, `0xf6000300`, and `0xe6000d03`.
- The exact engine dispatch table maps `0x17` to the default return/no-op block; `0x17` is produced and received but not consumed as a normal engine command.
- PJL-visible words such as `PAPERLESS`, `FUSER`, `TONEREXP`, and `JAMRECOVERY` are entries in a status command table at `0x10003c8c`, not direct engine dispatch cases.
- `0x10010838` is the current bridge from internal status words to StatusMgr/PJL-visible notifications; `0x1000a2a4` converts status words into PJL `CODE=` values.
- `analysis/status-path/status-code-correlation.md` records the important boundary that engine queue `0x17` event words are correlated with, but not identical to, final PJL `CODE=` values.
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
- `analysis/open-firmware-model-report.md` adds a runnable offline model: `scripts/model-hp1020-print-path.py` parses the controlled ZjStream sample into document/page/work/raster objects and stops at the video/engine MMIO boundary.
- `analysis/open-firmware-model/variant-matrix.md` runs that model against A4, letter, legal, resolution, copy-count, draft/economode, source, media, and logical-clip variants to show which fields are host-controlled.
- `analysis/open-firmware-model/model-invariants.md` verifies the modeled chunk sequence, JobMgr message sequence, BIH-to-work-field propagation, raster list linkage, and safe-stop boundary across the base sample and all generated variants.
- `analysis/open-firmware-model/minimal-print-scope.md` synthesizes the narrow replacement target: reuse host-side ZjStream generation, implement only the firmware receive/parser/raster/engine path needed for printing, and ignore unrelated HP features.
- `analysis/open-firmware-model/raster-field-semantics.md` maps the important host-to-firmware fields for the narrow print path: JBIG BIH `XD/YD/L0/options` become work `+0x84/+0x88/+0x8c/+0x90`, BID byte counts become payload `+0x48/+0x54`, and the raster list at work `+0x50` is what the video path later consumes.
- `analysis/hardware-boundary/hardware-boundary.md` converts the hardware side into a do-not-touch map: USB `0xb300` is the only plausible early custom-firmware target; video/engine families `0xb100`, `0xb200`, `0xb204`, `0xb208`, `0xb050`, and `0xb020` are unsafe for a first custom probe.
- `analysis/hardware-boundary/video-register-projection.md` projects modeled work fields onto the first unsafe video writes, proving host-controlled BIH fields would reach `0xb2000008`, `0xb200000c`, `0xb2000024`, and `0xb2000000` if the firmware crossed the safe stop boundary.
- `analysis/hardware-boundary/first-page-hardware-sequence.md` orders the post-parser page path: engine accepts work, PrintMgr sends Video Queue `0x0b`, video prepare projects the normal 600dpi state, render arms `0xb204/0xb208` and `0xb200`, normal descriptor-queue refill (`0x10014244 -> 0x10013f34`) feeds raw-band/channel-B registers, then video completion wakes engine. The alternate raw-refresh helper remains mapped separately.
- `analysis/hardware-boundary/video-engine-register-semantics.md` extracts literal-cell-to-register mappings from the stock ELF and decompiled functions. It names the current dangerous roles: `0xb050` engine command/status, `0xb100` video setup/raw-band feed, `0xb200` transfer descriptors/control, and `0xb204`/`0xb208` paired transfer channels.
- `analysis/hardware-boundary/video-prepare-modes.md` narrows the `0xb100` setup path: it records mode-dependent writes for `0xb1000020/0x24`, `0xb1000120/0x24`, `0xb100001c/0x11c`, and the `0xb1000400..0x0430` timing table blocks.
- `analysis/hardware-boundary/engine-command-status.md` narrows the `0xb050` engine path: stock status reads use command IDs `1`, `0x20`, `2`, `0x16`, and `0x13`; side-effect/start commands include `0x501a`, `0x5043`, `0x3a13`, and `0x6012`; selected event words are stored at engine state `+0x60` and sent as queue `1` message `0x17`.
- `analysis/hardware-boundary/engine-status-decisions.md` turns the nested engine poller into an executable scenario model. It covers the `0x14000a04` ready rewrite, `0x501a`/`0x5043` side effects, `0x13` and `0x16` substatus branches, and previous-event extra emit behavior.
- `analysis/hardware-boundary/video-engine-feedback.md` maps the video-to-engine feedback loop: normal VideoThread completion sends engine queue message `0x10`; reset/flush can send `0x25`; reset dispatch can send `0x11`, requeue deferred work as `0x0b`, or emit video reset event words through engine message `0x17`.
- `analysis/hardware-boundary/video-transfer-ring.md` maps the video transfer ring around producer index `+0x98`, consumer/full check `+0x94`, IRQ done index `+0xd8`, descriptor base `0x1002efe0`, channel A registers `0xb2040004/0008`, and channel B registers `0xb2080004/0008`.
- `analysis/hardware-boundary/video-irq-decisions.md` turns video block status bits into branch outcomes: `0x20` is the refill path, while `0x02`, `0x08`, `0x10`, and idle `0x01` lead to reset-dispatch cases `0`, `3`, `4`, and `7` respectively.
- `analysis/hardware-boundary/video-band-queue.md` maps the queue/list helper that advances video state `+0xdc`, stops before colliding with `+0xe0` unless the descriptor final flag permits one more queue step, and writes raw-band A/B pointer and flag registers at `0xb1000008/000c` and `0xb1000108/010c`.
- `analysis/hardware-boundary/video-mode-flag.md` maps the mode fork: work object byte `+0x74` is copied into the sign bit of video state `+0xfc`; zero selects the descriptor queue/list refill path, while nonzero selects the raw linked-list refresh path.
- `analysis/hardware-boundary/video-refill-topology.md` stitches the current video refill evidence together: the stronger normal-print hypothesis is the descriptor queue/list refill path, while the raw linked-list refresh path is real but still lacks a proven normal print-path producer.
- `analysis/hardware-boundary/video-prepare-projection.md` narrows the current generated host print cases against the `0xb100` setup path: all generated variants are 600x600/NBIE=1 and project into a small two-output 600dpi setup family when datastore `0x20` and work `+0x36` take the normal zero path.
- `analysis/hardware-boundary/engine-print-topology.md` organizes the mechanical engine side into startup/preflight, page work acceptance, status/recovery polling, and completion/deferred-work stages. It preserves the important stock commands `0x6012`, `0x3a13`, `0x501a`, and `0x5043`.
- `analysis/hardware-boundary/video-dataflow-contract.md` pins the normal `a4_default` first-page values through the video boundary: work `+0x84/+0x88/+0x8c/+0x90 = 9600/6824/128/0x5c`, BID bytes `6364`, prepare stride/window `1200/2400`, render channel-A length `6364`, and helper channel-B length formula `min(4, +0xd0) * 1200`.
- `analysis/hardware-boundary/video-chunk-sizing.md` tightens that helper formula: `+0xb8` is `((work +0x84 + 31) & ~31) >> 3`, `+0xcc` is projected as `ceil_div(8192, stride) & ~3`, so `a4_default` uses stride `1200` and max chunk units `4`. The divide helper `0x1001b668` is still named cautiously because Ghidra truncates the divide path.
- `analysis/hardware-boundary/video-helper-disassembly.md` records the exact bytes and decoder evidence for helper `0x1001b668`: Ghidra confirms denominator `0 -> 0` and denominator `1 -> numerator`, but hits a pcode constructor failure at `0x1001b685`; local Xtensa objdump also emits custom/old-instruction-looking markers, so denominator `>=2` stays a bounded ceil-div hypothesis.
- `analysis/hardware-boundary/video-queue-payload-chain.md` traces the queue word handed to VideoThread through JobMgr, Engine, PrintMgr, and VideoThread. Current conclusion: prepare receives the `0x94` video/page work object, not the raw page-parameter block.
- `analysis/hardware-boundary/video-remaining-units.md` traces the remaining-unit candidate and corrects the old source claim: `ZJI_VIDEO_Y` reaches page-param `+0x26`, and video prepare reads argument `+0x26`, but the active work object `+0x26` source is still unsourced in static decompilation. If a hidden alias/copy still exists, `a4_default` first channel-B refill length would be `4800`.
- `analysis/non-printing-usb-probe-spec.md` defines the only custom-firmware experiment that is currently defensible: boot/USB identity only, no video/engine MMIO.
- `analysis/non-printing-status-probe/pjl-status-contract.md` defines the exact tiny PJL/status payloads to use when calibrating stock back-channel responses or future open USB/PJL echo behavior.
- `analysis/offline-consistency/offline-consistency.md` now cross-checks the main offline conclusions against generated reports: engine `0x17` dispatch, status-code correlation, print-path model invariants, hardware boundary, PJL query contract, and USB marker draft safety.
- `analysis/usb-path/usb-marker-boundary.md` maps the stock USB string-descriptor marker path and records the current decision not to build/upload that marker yet; the open firmware would first need USB control-endpoint and descriptor-transfer plumbing.
- `analysis/usb-path/usb-descriptor-extraction.md` statically extracts two HP device descriptors, high/full-speed USB printer configurations, and identity string pointer runs from the stock ELF. The device descriptors match vendor `0x03f0` and product `0x2b17`.
- `analysis/usb-path/usb-descriptor-response-model.md` turns those descriptors into exact byte strings for standard USB `GET_DESCRIPTOR` responses. This defines the payload contract for a future USB-only open marker, but not the endpoint-0 hardware plumbing.
- `analysis/usb-path/open-endpoint0-model.md` converts those descriptor bytes into a pure setup-packet response model. It answers what bytes to return for standard `GET_DESCRIPTOR` requests, including a future open marker string, while explicitly excluding USB controller MMIO.
- `analysis/usb-path/usb-setup-source.md` narrows the setup-packet source: the stock descriptor branch reads setup-like fields from `0x90021348 + offset`, while `0xb3000214` looks like a separate event/envelope pointer.
- `analysis/usb-path/control-in-data-stage.md` models how the stock firmware sends endpoint-0 response bytes: staging buffer `0x90022bd0`, descriptor ring `0x900226f0`, `0x08000000` final-descriptor flag, `0xb3000014` submit register, and `0xb3000000 |= 0x108` kick.
- `analysis/usb-path/control-completion-event.md` models the next stock layer: the control-IN sender waits on event flag bit `0x1` at `0x10021318`, while USB2Thread waits on bit `0x10000`; this is the current boundary for replacing ThreadX with a tiny open polling/event loop.
- `analysis/usb-path/usb-interrupt-events.md` maps the producer side of those event flags: interrupt task `0x10008208`, two 16-lane event banks, lane stride `0x20`, and per-lane `0x400` completion status.
- `analysis/usb-path/endpoint0-machinery.md` maps the stock endpoint-0 flow: interrupt 4, USB event flags, `0x58`-byte transfer records, `0x10`-byte transfer descriptors, and `0xb300` control bits. The current standalone USB-marker blocker is endpoint-0 machinery, not descriptor payload bytes.
- `analysis/usb-path/endpoint0-handshake-contract.md` extracts the immediate hardware-facing contract from those blocks: likely setup packet base `0x90021348`, event pointer register `0xb3000214`, response state slots, and two stock USB controller programming sequences.
- `analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.md` verifies that the current marker draft's USB writes match the extracted endpoint-0 contract; this is the strictest offline gate before any future write-capable hardware test.
- `analysis/usb-path/usb-mmio-map.md` turns the endpoint-0 register evidence into a concrete checklist: setup/status gates `0xb3000400/0408`, descriptor/control registers `0xb3000504/0508/050c/0510`, ack/kick registers, and likely setup/event pointer `0xb3000214`.
- `scripts/check-hp1020-usb-probe-contract.py` is the stricter scanner for future USB-only candidates: engine/video MMIO fails, and USB MMIO must be one of the mapped endpoint-0 registers.
- `scripts/check-hp1020-usb-mmio-accesses.py` classifies candidate disassembly into USB MMIO reads and writes. The current USB snapshot probe reports 14 mapped reads and 0 writes.
- `scripts/check-hp1020-memory-boundary.py` classifies non-MMIO memory references in open probes. The USB marker draft intentionally reads a candidate setup packet buffer and writes stock USB response-state slots.
- `scripts/check-hp1020-marker-descriptor.py` verifies the marker string descriptor and the 0x90000000 hardware alias pointer used by the USB marker draft.
- `scripts/check-hp1020-marker-length-flow.py` verifies the marker draft preserves the clipped host `wLength` register into the endpoint-0 response-length write.
- `scripts/model-hp1020-usb-marker-draft.py` models the USB marker draft's setup/gate behavior and verifies response length clipping at the decision level.
- `scripts/model-hp1020-usb-setup-source.py` regenerates the setup-source report that separates the direct setup RAM candidate from the USB event pointer.
- `scripts/model-hp1020-control-in-data-stage.py` regenerates the stock endpoint-0 control-IN descriptor/kick model and self-tests key response sizes.
- `scripts/model-hp1020-control-completion.py` regenerates the stock endpoint-0 completion event-flag model and verifies the evidence snippets.
- `scripts/model-hp1020-usb-interrupt-events.py` regenerates the USB interrupt event-lane model and verifies the evidence snippets.
- `scripts/model-hp1020-video-engine-register-semantics.py` regenerates the dangerous video/engine register-role model from the stock ELF and decompiled source.
- `scripts/model-hp1020-video-prepare-modes.py` regenerates the branch/table model for the `0xb100` video prepare setup path.
- `scripts/model-hp1020-engine-command-status.py` regenerates the `0xb050` engine command/status model, including stock command IDs, state offsets, and event decisions.
- `scripts/model-hp1020-engine-status-decisions.py` regenerates the executable engine poller branch/scenario model from the command/status report and decompiled source.
- `scripts/model-hp1020-video-engine-feedback.py` regenerates the video-to-engine completion/reset feedback model.
- `scripts/model-hp1020-video-transfer-ring.py` regenerates the video transfer ring ownership and descriptor refill model.
- `scripts/model-hp1020-video-irq-decisions.py` regenerates the executable video block IRQ/status decision model.
- `scripts/model-hp1020-video-band-queue.py` regenerates the video descriptor queue/list and raw-band register-feed model.
- `scripts/model-hp1020-video-mode-flag.py` regenerates the work-object mode flag and IRQ refill-fork model.
- `scripts/model-hp1020-video-refill-topology.py` regenerates the synthesis report connecting mode flag, IRQ decision, transfer-ring, and band-queue models.
- `scripts/model-hp1020-video-prepare-projection.py` regenerates the projection from generated print-path variants into `0xb100` video-prepare setup scenarios.
- `scripts/model-hp1020-engine-print-topology.py` regenerates the engine-side print topology synthesis from command/status and status-decision reports.
- `scripts/model-hp1020-first-page-hardware-sequence.py` regenerates the ordered first-page hardware sequence from the current print-path and hardware-boundary reports.
- `scripts/model-hp1020-raster-field-semantics.py` regenerates the host-to-raster field semantics report from the generated print-path model variants and video-boundary reports.
- `scripts/model-hp1020-video-dataflow-contract.py` regenerates the normal first-page video dataflow contract from raster fields, prepare projection, transfer-ring, and refill models.
- `scripts/model-hp1020-video-chunk-sizing.py` regenerates the stride-derived chunk sizing and raw-band flag helper model.
- `scripts/model-hp1020-video-helper-disassembly.py` regenerates the helper disassembly limit report for `0x1001b668`.
- `scripts/model-hp1020-video-queue-payload-chain.py` regenerates the VideoThread work-object pointer-chain report.
- `scripts/model-hp1020-video-remaining-units.py` regenerates the remaining-unit candidate source report and keeps the unresolved copy/alias gap explicit.
- `scripts/model-hp1020-minimal-print-scope.py` regenerates the current minimum printing-only replacement scope from the generated print-path, USB, and hardware-boundary reports.
- `scripts/analyze-hp1020-pjl-status-capture.py` classifies PJL/status back-channel captures against the generated contract, including expected-marker, no-response, and unexpected-byte outcomes.
- `scripts/run-usb-marker-draft-hardware-test.sh` is the guarded dry-run/default harness for the marker draft. It re-runs the static gates before any upload and requires `HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD=1`.
- `scripts/run-open-firmware-usb-test-ladder.sh` wraps the staged hardware path. Dry-run validates all probes offline; upload mode runs one selected non-printing stage with before/after USB identity capture.
- `scripts/run-usb-snapshot-probe-hardware-test.sh` is the guarded dry-run/default harness for the read-only USB snapshot probe. It re-runs the static gates before any upload and requires `HP1020_ALLOW_USB_SNAPSHOT_UPLOAD=1`.
- `scripts/validate-hp1020-offline-analysis.sh` regenerates the print-path matrix, model invariants, video-register projection, hardware-boundary model, and open endpoint-0 model without touching the printer.
- `scripts/capture-hp1020-usb-identity.sh` captures host-side USB identity evidence without sending bytes. Use it before/after marker tests to compare stock identity, disappearance, or `HP1020 OPEN MARKER`.
- `scripts/check-hp1020-safety-boundary.py` is a pre-upload safety scanner for future candidate source/disassembly; it fails on known unsafe video/engine functions and MMIO families.
- `analysis/toolchain-probe/binutils-exec-status.md` records that the old `/tmp/hp1020-ctng-mnt/.../xtensa-fsf-elf-*` tools are present but corrupt, and that `scripts/build-xtensa-binutils-manual.sh` recovers a runnable assembly-only prefix.
- `analysis/printer-test-readiness-report.md` records the controlled connected-printer test path using `analysis/samples/minimal-page.ps` and `scripts/run-printer-readiness-test.sh --send`; that test has printed successfully once on hardware.
- `analysis/jobmgr-producer-boundary-report.md` is now superseded for message `0x29`; it remains useful as the pre-parser checkpoint showing why the producer was missed by broad queue-send scans.
- The status-state object is currently mapped through pointer `0x100063d8 -> 0x1002adb4`, with current status at offset `0x08`, transition status at `0x10`, and source/reason at `0x14`.
- HP's PJL reference anchors firmware-generated `410xx` codes as foreground paper-loading status codes; see `analysis/pjl-status-code-reference.md`.
- Engine/video MMIO has first behavioral names, but register semantics are not complete.
