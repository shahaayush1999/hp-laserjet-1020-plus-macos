# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. No printer contact, upload,
installed-printing change or print-driving hardware path occurred.

## Progress and validation

- Pinned GCC recovery succeeded with the original checksum, instruction and
  compiler-profile gates. Target headers and libgcc are restored.
- Current sources pass the full offline suite: **93 consistency checks**.
  The original native matrix retains 26 completed empty-document lifecycles and
  six separately classified conditional null reads. All 28 retirement cases pass.
- Native pages now pass 36 completed software lifecycles: 18 ordinary page and
  document cases plus 18 split-raster cases (six, thirteen and 64 chunks), with
  both RAM fills and three timing/event controls. All are in the aggregate.
- A synthetic consumer supplies FIFO consumption and completion. Original parser,
  allocation, queues, scheduling, reference stores, counters and reclamation run.
  Two explicit ticks allow JobMgr to clean retired nodes before completion;
  consuming the cleanup event first prevents that early cleanup. Final ownership
  still passes in all controls. Automatic IRQs and physical consumption are absent.
- Initial page draft errors were corrected against original bytes: invalid
  immediate comparison, an embedded-descriptor/free-pointer mismatch, and a
  control-wrapper bit-index assertion. The newly reached timed cleanup helper
  is fully byte-audited RAM code; its peripheral exclusions remain intact.
- The first 64-chunk case stopped at the 200,000-step budget during final status
  bookkeeping. Its raw capture remains separate from completed lifecycles.
  Only 64-chunk fixtures now request an explicit 250,000 cap; they complete in
  200,315–201,736 instructions. The default remains 200,000.

## Next distinct offline work

Use the native handoff in `analysis/open-firmware-model/next-evidence.md` and
`analysis/README.md`. The page fixture still calls the original parser directly
once per document. Native integration of the already-audited stream admission
path is the next distinct question; inspect existing admission evidence first.
Active-work cancellation with a bounded software consumer is another unresolved
integration question. Neither is proven by the completed page matrices.

Latest full log: `/tmp/hp1020-full-fragments.log`; it names the child log directory.
Generated reports retain their actual tested source/fixture hashes. Historical
captures and snapshots remain preserved. No research process needs to be resumed.

## Restrictions and corrections

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
The original empty-document cancellation/END_DOC ordering is resolved; do not
repeat it. Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10.
Boot, automatic IRQs, caches, custom raster code, DMA/engine ownership, physical
printing and power-cycle recovery remain unproven. Passing tests are not output.
