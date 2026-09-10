# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
Offline research is active. The working HP-based macOS setup is untouched;
no printer contact or installed-printing changes occurred.

## Progress and validation

- Pinned GCC recovery succeeded, including verified source, target headers and
  libgcc. Current native sources passed 26 completed empty-document lifecycles
  and six separately verified conditional null reads. All 28 retirement cases
  pass, including the formerly unexecuted constructor-result assertion.
- The full offline suite then passed sequentially: **92 consistency checks**, including the integrated timed-page matrix.
  Reports now contain actual current-source hashes. Historical tested source
  snapshots and original failure captures remain preserved.
- The first native page experiment first passed six focused software lifecycles:
  one page, three pages in one document, and three one-page documents, both RAM
  fills. Original allocation, queues, scheduling, retirement reference stores,
  counters and reclamation execute. A synthetic consumer supplies successful
  FIFO consumption and completion; this is not physical printing evidence.
- Initial page failures were draft errors: invalid immediate comparison and a
  free-pointer assertion that confused an embedded descriptor with its containing
  node. Original cleanup bytes confirm the node is freed. The corrected focused
  validator preserves full pool and ownership checks.
- The expanded page matrix passes 18 focused lifecycles. Two explicit ticks
  allow original JobMgr to clean retired data before supplied completion.
  Consuming the event first prevents early cleanup with the same ticks. The
  newly reached RAM-only helper is byte-audited; no peripheral path was added.
  Aggregate integration now passes the full offline suite.

## Exact next work

Continue the native handoff in `analysis/open-firmware-model/next-evidence.md`.
Timed-page integration is fully validated. Now test pages split into
six, thirteen and 64 raster chunks with the same three timing/event controls.
The scratch launcher is running sequentially after full validation. Preserve the unchanged bounded
execution and hardware exclusions; investigate failures before expanding scope.

## Restrictions and corrections

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
The original cancellation/END_DOC ordering is resolved; do not repeat it.
Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10. Stock annotations
own instruction boundaries. Boot, automatic IRQs, caches, custom raster code,
DMA/engine ownership, physical printing and power-cycle recovery remain unproven.
