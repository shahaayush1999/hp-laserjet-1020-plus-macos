# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
The owner requested this saved handoff to start a new chat. Research is paused,
not exhausted. No research/QEMU/compiler-recovery process remains running.
The working HP-based macOS setup is untouched; no printer contact occurred.

## Progress and validation

- The last fully validated baseline remains `e7bef56`, with 89 consistency checks,
  inherited through the previous handoff `fe67c4f`. This new handoff is a research
  snapshot, not a fully validated replacement for that baseline.
- A focused original parser + JobMgr + StatusMgr native matrix completed:
  26 successful empty-document lifecycles and six separately verified conditional
  null reads. Original allocation, queues, locks and scheduling run throughout;
  the only runtime host service is input. No replay or heap migration occurs.
- The saved failure is traced: original cancellation queues its acknowledgement
  behind END_DOC; original END_DOC removes the last document before the ack
  attempts head+12. Both fills and original JobMgr/StatusMgr priority/time-slice
  settings preserve the fixed ten/eleven-document boundary with no ticks.
  This is conditional stock-software behavior, not an observed printer fault.
- The native no-next-transfer retirement tail passed 28 standalone cases,
  including two mutations stopped before the excluded next-transfer path.
  Original reference/event/return effects execute; consumption is supplied.
- After those focused passes, initialization was extracted into `prepare_pipeline`,
  failure hashes were added, and a negative constructor-result assertion was
  added to retirement. Those latest edits have syntax checks only. Existing
  reports retain their tested source hashes; exact old source snapshots are saved
  in `stock-execution/pipeline-boundary-capture.json`. Do not relabel them current.
- Full validation was attempted but stopped at missing target `stddef.h`.
  The disposable GCC executable survives, but target headers/libgcc and its
  source archive are absent. Pinned recovery stopped at sandbox DNS failure.
  Aggregate wiring/check additions remain provisional. Raw logs are preserved.

## Exact next work

Read the current native handoff in
`analysis/open-firmware-model/next-evidence.md`, including recovery instructions.
Restore GCC with the pinned `scripts/build-xtensa-gcc-manual.sh`, granting network
access for its checksum-verified source download. Rerun native pipeline and
retirement generators, then the full offline suite sequentially. QEMU needs its
private Unix debugger socket permitted; it requires no printer contact.

Then execute the saved **unexecuted** `scripts/hp1020_qemu_page_pipeline.py` draft:
start with one normal page, then both fills and three pages/documents. It adds a
synthetic deferred completion consumer to the three original tasks, uses the
bounded retirement tail and original completion queue, and checks FIFO ownership,
reference changes, counters and reclamation. It has only Python syntax checks;
no page assembly, execution, validator or report exists yet. The detailed handoff
records entry points, fixtures, expected boundaries and later controlled ticks.

## Restrictions and corrections

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
AGENTS.md retains the owner's autonomy and brief-update preferences.

Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10. Datastore locks
are 28-byte binary semaphores; entry 25 is the numeric status event. Stock
annotations define instruction starts. Earlier BE encoding/bit-numbering mistakes
are corrected; the old quiet upload proves nothing. Retain distinct earlier
cancellation and empty-document findings. Boot, automatic IRQs, caches, custom
raster instructions, DMA/engine ownership, printing and recovery remain unproven.
