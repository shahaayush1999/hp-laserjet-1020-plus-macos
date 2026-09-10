# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. No printer contact, upload,
installed-printing change or print-driving hardware path occurred.

## Progress and validation

- Current sources pass **96 consistency checks** in the full offline suite.
  A bounded open JBIG decoder now connects the existing semantic parser/planner
  to packed image bands from complete ZjStream files.
- Current focused decoder checks pass: 176 cases, 21 original/normalized-header
  comparisons, 32 separately classified mutations and 66 QEMU cases. The host
  compares every image byte; larger target pages compare a prefix and full hash.
- Complete-file checks pass: 57 host cases (39 accepted, others expected errors)
  and 35 QEMU cases, including multiple pages/documents and 6/13/64 BID splits.
  These are **open software image cases**, not additional stock lifecycles.
- Full sequential validation passed in `/tmp/hp1020-full-image.log` (child logs
  `hp1020-validation.GAVU4h`). The original native/probe checks also pass.
  Reports and their recorded source/fixture hashes match the tested current files.
- The decoder uses 11,512 bytes for A4 state, two history rows and a four-row
  output band, excluding code/stack/input/test storage. The complete-file bridge
  still retains compressed input in the existing parser arena.
- A reproduced upstream absent-history pointer bug is fixed with a preserved
  source patch/failing capture. GPL source, license and content pins are retained.

## Current direction and preserved evidence

Use the open software image and raster-bypass sections in
`analysis/open-firmware-model/next-evidence.md`. The stock file-backed datastore
32 = 1 selects a raw buffer in bounded original execution, making software
image production a promising initial path. Engine-ready format, raw-buffer
ownership, cache visibility and timing remain unproven; no hardware path was added.

Existing stock evidence remains separate: 26 completed empty-document lifecycles,
six conditional null reads, 28 bounded retirement cases and 36 page lifecycles
with supplied FIFO consumption/completion. The 42 bypass cases are fragment
selections/stops, not lifecycles. All 36 stock page fixtures preserve datastore
32 before/after, not over every unexecuted boot/engine write. The historical
64-chunk budget stop and matching tested source history remain preserved.

## Restrictions and next action

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
The original empty-document cancellation/END_DOC ordering is resolved; do not
repeat it. Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10.
Next remove whole-page compressed retention through an optional chunk consumer
while preserving the legacy parser mode. Then pursue the raw-output contract,
keeping source-kind dispatch, raw IRQ mode and engine output selection distinct.
No research process is running at this checkpoint. Boot, physical printing and power-cycle
recovery remain unproven. Passing software tests are not physical output.
