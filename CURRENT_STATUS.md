# Open Firmware Current Status

## Objective

Replace only the HP LaserJet 1020 Plus device firmware needed to print
host-generated ZjStream. Keep the working macOS/foo2zjs path intact. Scanner,
network, multi-model, and unrelated firmware features are out of scope.

## Current State

- Normal macOS printing works using bundled HP firmware plus the repo's CUPS
  and LaunchDaemon glue. Do not modify that installed path during research.
- The stock 2005 Old-Xtensa ELF has been structurally analyzed. USB receive,
  ZjStream parsing, raster handoff, video transfer, and engine-control paths
  are mapped to varying confidence levels under `analysis/`.
- `open-firmware/usb-bulk-parser-draft/` is a buildable, mechanically inert
  open firmware probe. It implements endpoint-0 status counters, USB bulk OUT
  receive/re-arm, and incremental ZjStream framing for chunk types `0x00..0x06`.
- Offline validation passes: 11/11 generated streams, 33/33 boundary cases,
  425/425 assertions, reproducible artifacts, and zero forbidden mechanical,
  engine, video, fuser, motor, laser, or paper-feed MMIO accesses.
- The probe has never been uploaded. Real custom-code execution, endpoint-0,
  bulk completion length, acknowledgement, and repeated re-arm remain unproven.
- A separate portable C semantic parser retains page metadata and compressed
  raster records in bounded RAM. It is native-tested, not linked into a probe.
  Raster/video output and engine control remain unimplemented.

## Latest Offline Audit (2026-09-05)

- Fixed a toolchain ISA-overlay mismatch: earlier probes contained LE instructions
  in BE ELF files. All four probes are rebuilt; earlier uploads cannot prove execution.
- Added byte fixtures and complete stock-helper reassembly to every probe build.
- Refuted ceiling division at `0x1001b668`: complete decoding and 169,890
  differential instruction executions establish unsigned floor division.
- The assembled parser now passes all 44 generated/boundary cases in an
  independent RAM-only interpreter: 1,178,483 instructions; zero MMIO accesses.
- Fixed endpoint-0 descriptor/state pointer clobbers in both USB probes;
  104 assembled control-IN RAM tests verify exact payloads and transfer records.
- Resolved the missing low work fields: START_PAGE calls the item builder
  directly on active work. VIDEO_Y/RET/ECONOMODE source +0x26/+0x30/+0x32.
- Corrected +0x22 to VIDEO_BPP (NBIE is +0x12); default A4 window is 1200,
  not 2400 bytes. All dependent reports and consistency checks are updated.
- Portable semantic C passes 512 ASan/UBSan cases across 11 generated streams.
- Verified four raster callback arguments and isolated their custom instructions;
  their transformations/side effects remain unknown. Probe instruction gates
  now reject unknown/custom code from entry and all six vector roots.
- Identified logical-clip metadata length mismatch (180 actual / 156 declared).
- RAM-only C page planner passes 1398 cases and 5,394,344 band partitions;
  rejects BPP4 and inconsistent metadata. A4: 1706 bands, four rows each.
- Both validation suites, 72 consistency checks and reproducibility pass.
  A clean freestanding C cross-compiler build is in progress outside the repo.

## Main Unknowns

1. Whether boot-ROM USB initialization is sufficient for the standalone probe.
2. Whether real bulk descriptor completion and length encoding match the static
   model.
3. Custom instruction semantics inside stock raster-processing callbacks.
4. Exact safe video-transfer and mechanical engine sequencing for a first page.

## Productive Offline Work

- Independently audit the recovered contracts against stock ELF instructions.
- Build and validate target C output for the portable semantic components.
- Lift or model remaining video helpers and engine state transitions.
- Extend the tested portable semantic component and host-side transfer planning.
- Build executable host models for video descriptors and engine state machines.
- Extend static safety gates before any printing-capable firmware is created.

Continue offline until remaining uncertainty is a precise hardware-only
question. Do not turn static hypotheses into claimed facts.

## Hardware Checkpoint

The highest-value live test is the guarded, non-printing two-stage test in
`analysis/open-firmware-probes/usb-bulk-parser-draft/hardware-test-plan.md`:

1. Fresh power cycle, upload the inert probe, expect zero counter descriptor.
2. Fresh power cycle, send only 36-byte START_DOC/END_DOC input, expect
   `B=24 D=1 C=2 E=0 U=0`.

Do not contact the printer unless the user explicitly says it is connected,
freshly power-cycled, and ready.

## Verification

```sh
scripts/validate-hp1020-offline-analysis.sh
scripts/validate-open-firmware-probes.sh
scripts/check-open-firmware-usb-bulk-parser-reproducibility.sh
```

Start with this file, then `AGENTS.md`, `analysis/README.md`, and the generated
reports referenced above. Commit and push coherent progress to private `main`.
