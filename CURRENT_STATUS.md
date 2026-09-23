# Current handoff

Updated: 2026-09-23. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. No printer contact, upload,
installed-printing change or print-driving hardware path occurred.

## Current verified state

- The full sequential validation passed **100 consistency checks** and both suites.
  Log: `/tmp/hp1020-full-raw-parser-20260923.log`; child logs `hp1020-validation.khHDMA`.
  Reports and their source/fixture hashes match the tested current files.
- The open JBIG decoder produces packed image bands: 176 focused cases,
  21 original/normalized-header comparisons, 32 separately classified mutations
  and 66 QEMU cases. Complete-file integration passes 57 host and 35 QEMU cases.
- The bounded stream bridge passes **65 host and 43 QEMU cases**. A detailed
  page with 10,112,256 decoded bytes and 161 BID chunks passes with reused input
  storage. Target state and fixed buffers total **91,028 bytes**, excluding
  code/stack/caller packets/test capture. Host comparisons cover every output
  byte; larger target outputs use a prefix plus complete hash and counts.
- Legacy retained parsing still rejects 129/257 BID partitions; the new stream
  mode accepts the same image bytes. Its synchronous consumer has no asynchronous
  queue/retry protocol. Output remains provisional until finish succeeds.
- The raw-buffer contract passes **68 separate fragments and two controls**.
  Deliberately unprefixed pointers yield before-buffer free requests in two
  conditional fixtures, not stock faults. This older test observes free requests;
  the following test executes actual allocation and cleanup.
- New raw-producer/admission checks pass **52 interpreter/QEMU comparisons**
  and **eight conditional release cases** with the original allocator and queue.
  JobMgr initializes references, and only descriptor selector 0 reaches this
  raw list. A supplied 16-byte prefix permits original cleanup after one raw
  completion; a second reference retains ownership with an adjusted cursor.
  These results are included in the full sequential validation above.
- Actual chunk-12 parsing passes **10 admission cases and two metadata-only
  controls** in both engines. Original queued messages create the owner hierarchy.
  The image pointer equals the allocator return and the raw IRQ flag stays zero
  at the checked boundaries. This is a separate producer from the standalone
  helper. No consumer or completed page lifecycle is added by these checks.

## Preserved evidence and limits

Use `analysis/README.md` for recovery and the image/raw-contract sections of
`analysis/open-firmware-model/next-evidence.md` for detailed evidence and scope.
Pinned GPL sources, the reproduced upstream pointer finding and matching source
snapshots remain preserved. Software image cases are not stock page lifecycles.

Existing stock evidence stays separate: 26 completed empty-document lifecycles,
six conditional null reads, 28 bounded retirement cases and 36 native page
lifecycles with supplied FIFO consumption/completion. The 42 bypass cases are
fragment selections/stops. All 36 page fixtures preserve datastore 32 before/after,
not over every boot/engine write. The historical 64-chunk budget stop is retained.

## Next action and restrictions

Resolve the input buffer prefix, cursor, metadata and timing before an adapter.
The standalone producer's actual caller remains unproven. The distinct chunk-12
path executes through admission without adding a prefix; its band dimensions
are populated but later work dimensions are zero. Next test actual BIH delivery
with independent page/band metadata, then trace pointer/mode changes before the
excluded hardware boundary.
Keep source-kind dispatch, raw IRQ mode and engine output selection distinct.
Do not repeat the completed selector matrix or resolved empty-document
cancellation/END_DOC ordering.
Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10.

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
No research process remains running at this checkpoint. Engine-ready packing, cache
visibility, physical throughput, boot, printing and power-cycle recovery remain
unproven. Passing software tests do not establish physical output.
