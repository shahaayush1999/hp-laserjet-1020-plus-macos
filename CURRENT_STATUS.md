# Current handoff

Updated: 2026-09-05. Owner-facing answer: **the open replacement cannot print yet**.
The separate HP-firmware-based macOS printing setup already works and is untouched.
Aayush wants plain-language chat updates; these notes are for agents only.

## Implemented and verified offline

- Four assembly probes: idle, read-only USB snapshot, endpoint-0 marker, and inert
  USB bulk/ZjStream framing. None of the corrected builds has live execution proof.
- Bounded portable C page/raster parser and page/band planner. Actual compiled
  BE/call0 Xtensa C executes in synthetic host RAM; it is not a device boot image.
- Byte-verified assembler and conservative GCC 14.3.0 configuration, reproducible
  outputs, native sanitizers, instruction interpreters and MMIO/unknown-opcode gates.
- Latest research validation: both suites pass; 73 consistency checks, 512 native
  semantic cases, 1398 planner cases, 66 compiled-target cases. Detailed results
  live with the components, not in additional handoff summaries.

## Corrections agents must not regress

- Earlier probes put LE instructions inside BE ELF containers. All rebuilt;
  the old quiet idle upload does not prove execution. Use repaired manual binutils.
- Stock helper `0x1001b668` is unsigned floor division, not ceiling division.
- START_PAGE directly fills active work: VIDEO_Y/RET/ECONOMODE source
  `+0x26/+0x30/+0x32`. The old unresolved-field hypothesis is superseded.
- `+0x22` is VIDEO_BPP; NBIE is `+0x12`. Default A4 window is 1200 bytes.
- Endpoint-0 pointer clobbers are fixed and instruction-tested in host RAM.
- Logical-clip metadata declares 156 bytes for 180 bytes of items. The narrow
  planner rejects it and BPP4. Custom raster instruction effects remain unknown.

## Next action and blockers

Current mode: **offline only; no hardware test is authorized**.
The next useful device experiment is the guarded non-printing USB test in
`analysis/open-firmware-probes/usb-bulk-parser-draft/hardware-test-plan.md`,
subject to its prerequisites, a fresh power cycle and explicit user authorization.
Success must show the custom descriptor, then the fixed 36-byte transaction's
counters; stock identity or quiet LEDs are insufficient.

Remaining questions: corrected boot/endpoint-0 execution, repeated bulk receive,
custom raster ISA (or measured stock bypass), video channel/cache ownership,
and physical engine status/timing/recovery. Exact evidence requirements are in
`analysis/open-firmware-model/next-evidence.md`. A core-specific ISA definition
could still resolve the raster gap offline. Do not implement guessed hardware
behavior to make the replacement appear complete.

## Resume and verify

Use `analysis/README.md` for the relevant evidence and toolchain recovery.
`scripts/validate.sh` runs all offline checkpoint checks with separate logs.
Keep this handoff current, commit coherent changes and push private `main`.
