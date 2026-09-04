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
- Semantic print dispatch, raster/video output, and engine control are not
  implemented in open firmware.

## Main Unknowns

1. Whether boot-ROM USB initialization is sufficient for the standalone probe.
2. Whether real bulk descriptor completion and length encoding match the static
   model.
3. Video work sideband values, especially active-work `+0x26` and `+0x32`.
4. Exact safe video-transfer and mechanical engine sequencing for a first page.

## Productive Offline Work

- Independently audit the recovered contracts against stock ELF instructions.
- Improve function/field naming and resolve the active-work sideband sources.
- Lift or model remaining video helpers and engine state transitions.
- Implement and test semantic ZjStream object construction without MMIO output.
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
