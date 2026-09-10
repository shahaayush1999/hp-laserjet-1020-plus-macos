# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. No printer contact, upload,
installed-printing change or print-driving hardware path occurred.

## Progress and validation

- Current sources pass **97 consistency checks** in the full offline suite.
  A bounded open JBIG decoder now connects the existing semantic parser/planner
  to packed image bands from complete ZjStream files.
- Current focused decoder checks pass: 176 cases, 21 original/normalized-header
  comparisons, 32 separately classified mutations and 66 QEMU cases. The host
  compares every image byte; larger target pages compare a prefix and full hash.
- Complete-file checks pass: 57 host cases (39 accepted, others expected errors)
  and 35 QEMU cases, including multiple pages/documents and 6/13/64 BID splits.
  These are **open software image cases**, not additional stock lifecycles.
- Full sequential validation passed in `/tmp/hp1020-full-stream.log` (child logs
  `hp1020-validation.0D3y3e`). The original native/probe checks also pass.
  Reports and recorded source/fixture hashes match the tested current files.
- The decoder uses 11,512 bytes for A4 state, two history rows and a four-row
  output band, excluding code/stack/input/test storage. The complete-file bridge
  still retains compressed input in the existing parser arena.
- Bounded stream checks pass **65 host and 43 QEMU cases**. A deterministic
  detailed page (10,112,256 decoded bytes, 161 BID chunks) passes with reused
  input/chunk storage. The target stream state and fixed buffers total 91,028
  bytes, excluding code/stack/caller packets/test capture. Legacy retained mode
  still rejects 129/257 BID partitions; streaming accepts the same image bytes.
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
Next pursue the raw-output contract, keeping source-kind dispatch, raw IRQ mode
and engine output selection distinct. The next bounded fragments are specified
in next-evidence; an unexecuted scratch draft is `/tmp/hp1020-raw-contract-draft.py`.
It adds producer selection and conditional raw retirement/cleanup to the planned
dispatch/flag experiment. Its claims still require execution. No research process
remains running after the full validation. Boot, physical printing and power-cycle
recovery remain unproven. Passing software tests are not physical output.
