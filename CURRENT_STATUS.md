# Current handoff

Updated: 2026-09-09. **The open replacement cannot print yet.**
The working HP-based macOS printing setup is untouched. Current aim: evaluate
independent offline reverse engineering; the owner consumes progress through chat.

## Implemented and verified offline

- Four corrected assembly probes: idle, USB snapshot, endpoint-0 marker and inert
  bulk/ZjStream framing. None of their corrected builds has live execution proof.
- Bounded C parser and page/band planner, including execution of compiled BE/call0
  Xtensa code in synthetic RAM. Reproducible compiler/assembler, sanitizers,
  instruction interpreters and MMIO/unknown-opcode gates support these components.
  Independent QEMU agrees on the C target, original parser/libc/arithmetic,
  JobMgr cleanup and all six stock register-window handlers. Original PrintMgr
  stop sequencing, datastore notifications and final StatusMgr notice release
  also agree. Stop-prefix/tail and cancellation checks extend this, with explicit
  hardware stopping boundaries. Original status construction/publication, ONLINE
  subscriber delivery and circular event history now agree in both CPU engines.
  Original queues now carry completed notices through the original status task.
  FIFO wraparound and selected pending-suspension races also agree.
- Original parser/libc, status decisions, JobMgr scheduling, allocator and selected
  MMIO-free render paths execute against independent oracles. Original completion,
  release and datastore bookkeeping now run with injected FIFO completion events;
  cooperative parser/JobMgr schedules exercise repeated documents and cleanup.
  Original stream recognition, buffering and dispatch now run in those schedules.
- Latest aggregate passed both suites (84 consistency checks), including original
  original queues, pending-suspension races and the combined status task.
  Detailed scopes remain beside each component. `scripts/validate.sh` runs the
  offline-only aggregate validation.

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

- Stock constructor registration proves queue 0 is engine and queue 1 is PrintMgr.
  Earlier maps reversed these IDs, creating false missing-consumer conclusions
  for event 0x17 and datastore notification 0x2d. Use the registration audit.

## Next action and limits

**Offline only; no hardware test is authorized.**
Continue removing host boundaries where original RAM-only code can run, especially
scheduler/context-switch boundaries and cancellation scheduling. Original stop packets and the
post-reset RAM tail now agree in QEMU; engine acknowledgement precedes its
hardware-stop call. Conditional cancellation findings persist with that tail:
selector 2 retains a document; selector 4 after END_DOC reads through null.
Before END_DOC it instead retains a child record. Status publication now executes
for empty language-context tables; optional
external status callbacks remain outside the test. Actual stopping/ownership and
RTOS timing remain assumptions; these are not observed printer faults. Original stream admission now reproduces the delayed empty-document
cleanup failure without manually reinvoking the parser. Eager completion avoids
it; actual USB delivery, multi-language context and real scheduling remain
unverified. This conditional finding is not a narrow-replacement blocker.
QEMU independently reproduces the delayed-empty-document failure and runs the
stock window handlers under nested calls. It is not the printer CPU; real boot,
interrupt/cache state and custom raster instructions remain outside this proof.

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
