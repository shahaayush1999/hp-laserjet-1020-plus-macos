# Current handoff

Updated: 2026-09-06. **The open replacement cannot print yet.**
The working HP-based macOS printing setup is untouched. Current aim: evaluate
independent offline reverse engineering; the owner consumes progress through chat.

## Implemented and verified offline

- Four corrected assembly probes: idle, USB snapshot, endpoint-0 marker and inert
  bulk/ZjStream framing. None of their corrected builds has live execution proof.
- Bounded C parser and page/band planner, including execution of compiled BE/call0
  Xtensa code in synthetic RAM. Reproducible compiler/assembler, sanitizers,
  instruction interpreters and MMIO/unknown-opcode gates support these components.
- Original parser/libc, status decisions, JobMgr scheduling, allocator and selected
  MMIO-free render paths execute against independent oracles. Original completion,
  release and datastore bookkeeping now run with injected FIFO completion events;
  cooperative parser/JobMgr schedules exercise repeated documents and cleanup.
- Both checkpoint suites pass; detailed counts and boundaries remain beside each
  component. `scripts/validate.sh` runs the offline-only aggregate validation.

## Corrections agents must not regress

- BE bit-branch numbering was reversed in the interpreter; libc and control-payload
  regressions now catch this. Stock compiler annotations define valid instruction
  starts and recover locations missed by linear disassembly.
- Earlier probes contained LE instructions in BE ELF. Rebuilt; the old quiet idle
  upload proves nothing. Use the repaired, pinned toolchain.
- Stock helper `0x1001b668` performs unsigned floor division.
- START_PAGE directly fills active work: VIDEO_Y/RET/ECONOMODE are `+0x26/+0x30/+0x32`;
  `+0x22` is VIDEO_BPP and `+0x12` is NBIE. Default A4 window is 1200 bytes.
- Endpoint-0 pointer clobbers are fixed. Original render changes list pointers
  before returning busy; the former ring-model ordering was wrong.
- Logical-clip metadata declares 156 bytes for 180 bytes of items. The narrow
  planner rejects it and BPP4. Custom raster instruction effects remain unknown.

## Next action and limits

**Offline only; no hardware test is authorized.**
Continue from `scripts/validate-hp1020-stock-lifecycle.py`. Queuing an empty
non-head document can free an earlier unfinished document in two reproducible
host schedules. Eager completion avoids it. The original parser mutex wrapper
does not wait for job-list drain, but outer transport admission remains unverified.
Trace that admission before calling this a device bug; alternatively pursue
independent ISA execution with a second engine. Do not make this conditional
counterexample a blocker for the narrow replacement.

Completion events and consumed raster slots are explicit host inputs. Passing
lifetime checks does not establish DMA, printing, IRQ timing or recovery.
Nonfinal raster markers retain allocation bytes; tested compressed render paths
ignore them, while the known flag consumer is the alternate raw path.

Live questions remain corrected boot/endpoint-0 execution, repeated bulk receive,
custom raster ISA or measured bypass, video/cache ownership and physical engine
timing/recovery. Detailed questions and evidence requirements are in
`analysis/open-firmware-model/next-evidence.md`. The guarded non-printing USB ladder
is available for a future specifically authorized test, not a current prerequisite.

## Resume

Use `analysis/README.md` to locate relevant evidence and recover scratch tools.
Keep this handoff current, commit coherent changes, push private `main`, verify sync.
