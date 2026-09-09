# Current handoff

Updated: 2026-09-09. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. The owner requested a full handoff
to another thread; research is paused, not exhausted. No research/QEMU processes
remained active at the handoff check. No printer contact occurred.

## Verified baseline

- Nine coherent research checkpoints were committed and pushed this session,
  ending at `e7bef56`. Both full offline suites passed there, with 89 consistency
  checks. See the topic map in `analysis/README.md`, not every historical report.
- Original parser/libc/arithmetic, work construction, selected render paths,
  completion/release, stream admission, cancellation and status publication have
  bounded execution evidence. Page completion remains an explicit fixture input.
- Original register windows, context switching, priority scheduling, blocking
  queues and synchronization execute in QEMU. Original timed waits pass 44 cases;
  software ticks are supplied explicitly and automatic CPU interrupts disabled.
- Original memory allocation/free passes 93 independent-engine cases. Original
  StatusMgr passes 30 scheduled cases with original queues, locks, pool and startup
  waits; no runtime host services. That committed experiment still uses prior
  JobMgr replay and explicit migration of notice storage.
- Corrected inert USB/boot probes and bounded C parser/planner exist, but their
  corrected device execution and physical printing remain unproven.

## Immediate unfinished work

Three draft scripts are saved in the handoff snapshot, outside the aggregate:
`hp1020_qemu_pipeline.py`, `validate-hp1020-native-pipeline.py`, and
`hp1020_qemu_retire.py`, all under `scripts/`.

The new pipeline runs original parser, JobMgr and StatusMgr concurrently with
original allocation throughout. Only input bytes come from the host; no replay
or heap migration. Several empty-document cases pass all ownership/counter/queue
oracles, including 13 documents with unequal priorities. **Its proposed 24-case
validator does not pass:** equal priorities `(5,5,5)` reach a guarded null read at
`0x1000e9f4` for 11–13 documents (10 passes). Thirteen fails with both RAM fills.
No `pipeline.json`/`.md` success report has been generated. Do not integrate it or
claim all combinations pass until the failure is traced and recorded accurately.

**Next:** read the in-progress section in
`analysis/open-firmware-model/next-evidence.md`. Trace original cancellation,
END_DOC and self-acknowledgement ordering at the fault, then preserve a minimal
conditional regression. After that, validate the drafted no-next-DMA retirement
tail before using it in a native page-completion fixture. That draft has never
been executed; the intended page extension has not been implemented.

## Restrictions and durable corrections

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert. The
owner wants sustained autonomous offline work and short plain-language updates;
notes are agent memory. Do not invent percentages or equate passing tests with
physical completion. AGENTS.md retains these preferences and authorities.

Queue IDs are engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10. Earlier
engine/PrintMgr mappings were reversed. Datastore entry locks are 28-byte binary
semaphores; entry 25 is the numeric status event. Stock annotations define valid
instruction starts; linear disassembly can be wrong. Prior probes had LE bytes
inside BE ELF, and interpreter BE bit numbering was corrected. The old quiet
upload proves nothing. Preserve the other recorded conditional cancellation and
empty-document findings; none is an observed printer fault.

Real boot, automatic IRQ/timer delivery, caches, custom raster instructions,
DMA/engine ownership, printing and recovery remain unproven. Missing hardware is
not a current reason to end productive offline research. Resume from the precise
unfinished experiments, not from an invented final hardware-only blocker list.
