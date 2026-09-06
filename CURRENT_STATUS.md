# Current handoff

Updated: 2026-09-06. Owner-facing answer: **the open replacement cannot print yet**.
The separate HP-firmware-based macOS printing setup already works and is untouched.
Current aim: evaluate how far independent offline reverse engineering can go.
Aayush wants plain-language chat updates; these notes are for agents only.

## Implemented and verified offline

- Four assembly probes: idle, read-only USB snapshot, endpoint-0 marker, and inert
  USB bulk/ZjStream framing. None of the corrected builds has live execution proof.
- Bounded portable C page/raster parser and page/band planner. Actual compiled
  BE/call0 Xtensa C executes in synthetic host RAM; it is not a device boot image.
- Byte-verified assembler and conservative GCC 14.3.0 configuration, reproducible
  outputs, native sanitizers, instruction interpreters and MMIO/unknown-opcode gates.
- Latest research validation: both suites pass; 75 consistency checks, 512 native
  semantic cases, 1398 planner cases, 78 compiled-target cases. Detailed results
  live with the components, not in additional handoff summaries.

- Original stock parser/libc execution now has 9841 cases; page fields and raster
  records are compared against the sanitizer-built C replacement. Original status
  decisions are also checked over exhaustive single-status axes and mixed cases.
  Original JobMgr/list/page scheduling now executes too: 118 pipeline cases and
  36 allocator cases, plus 256 complete MMIO-free render paths. Hardware-facing
  consumer paths remain outside.
- Stock compiler annotations recover 623 instruction starts missed by linear
  decoding. All direct targets validate; stock execution now rejects other PCs.

## Corrections agents must not regress

- The target interpreter originally reversed BE bit-branch numbering. Fixed;
  original libc and 12 control-payload rejection regressions now detect that error.
- Earlier probes put LE instructions inside BE ELF containers. All rebuilt;
  the old quiet idle upload does not prove execution. Use repaired manual binutils.
- Stock helper `0x1001b668` is unsigned floor division, not ceiling division.
- START_PAGE directly fills active work: VIDEO_Y/RET/ECONOMODE source
  `+0x26/+0x30/+0x32`. The old unresolved-field hypothesis is superseded.
- `+0x22` is VIDEO_BPP; NBIE is `+0x12`. Default A4 window is 1200 bytes.
- Endpoint-0 pointer clobbers are fixed and instruction-tested in host RAM.
- Original render changes list pointers before returning busy; the old ring
  model incorrectly placed these stores after rejection.
- Logical-clip metadata declares 156 bytes for 180 bytes of items. The narrow
  planner rejects it and BPP4. Custom raster instruction effects remain unknown.

## Next action and blockers

Current mode: **offline only; no hardware test is authorized**.
Continue the evaluation from the original-byte execution harnesses in
`scripts/validate-hp1020-stock-execution.py` and `validate-hp1020-stock-status.py`.
Next: extend independent execution through software parts of compressed-input
completion/refill or validate ISA semantics with a second execution engine.
Nonfinal payload `+0x4c` retains allocation bytes; tested MMIO-free compressed
render paths ignore it. Its known flag consumer is the alternate raw path.
Do not turn that out-of-scope dependency into a first-printing blocker.
These challenge inferred models using unchanged stock instructions. Environment
substitutes and untested device behavior must stay explicit. The next live USB
experiment remains available in the existing guarded test plan, but is not the
current task or a prerequisite for further offline investigation.

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
