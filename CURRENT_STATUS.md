# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
Offline research is active. The working HP-based macOS setup is untouched;
no printer contact or installed-printing changes occurred.

## Progress and validation

- Pinned GCC recovery succeeded, including verified source, target headers and
  libgcc. Current native sources passed 26 completed empty-document lifecycles
  and six separately verified conditional null reads. All 28 retirement cases
  pass, including the formerly unexecuted constructor-result assertion.
- The full offline suite then passed sequentially: **91 consistency checks**.
  Reports now contain actual current-source hashes. Historical tested source
  snapshots and original failure captures remain preserved.
- The first native page experiment now passes six focused software lifecycles:
  one page, three pages in one document, and three one-page documents, both RAM
  fills. Original allocation, queues, scheduling, retirement reference stores,
  counters and reclamation execute. A synthetic consumer supplies successful
  FIFO consumption and completion; this is not physical printing evidence.
- Initial page failures were draft errors: invalid immediate comparison and a
  free-pointer assertion that confused an embedded descriptor with its containing
  node. Original cleanup bytes confirm the node is freed. The corrected focused
  validator preserves full pool and ownership checks; pages are not yet wired
  into the aggregate.

## Exact next work

Continue the native handoff in `analysis/open-firmware-model/next-evidence.md`.
Add a bounded, explicitly delivered two-tick interval after retirement and before
message 17. Observe whether original JobMgr cleans retired raster nodes before
page completion, preserving zero-tick controls and original code/RAM gates.
Then validate focused changes and the full suite sequentially before integrating
the expanded page evidence. No automatic interrupt or elapsed-time claim follows.

## Restrictions and corrections

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
The original cancellation/END_DOC ordering is resolved; do not repeat it.
Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10. Stock annotations
own instruction boundaries. Boot, automatic IRQs, caches, custom raster code,
DMA/engine ownership, physical printing and power-cycle recovery remain unproven.
