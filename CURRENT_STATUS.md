# Current handoff

Updated: 2026-09-27. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. No printer contact, upload,
installed-printing change or print-driving hardware path occurred.

Support deliverable built: one self-contained `.dmg` for the working HP-based
setup on Aayush's dad's Apple Silicon Mac. It contains plainly named Install and
Remove packages and short instructions. `packaging/macos/README.md` owns this work;
`scripts/build-macos-package.py` builds it under `dist/HP-LaserJet-1020-Plus/`.
Eleven offline package check groups pass, including opening the image read-only,
matching its exact contents, sample conversion and mocked installation/removal.
The generated report is preserved beside the recipe; latest logs are
`/tmp/hp1020-dmg-build.log` and `/tmp/hp1020-dmg-validation.log`.
Installation and physical printing on the recipient Mac remain untested.
The original manual installer/runtime are unchanged. The recipient needs no
repository, Homebrew or commands, but the owner has rejected this handoff's
removal experience: he should not have to retain the downloaded disk image.
Do not present a copyable installer as satisfying his requested app lifecycle.
The open choice is a permanent installed app with its own Uninstall control
versus removal by dragging the app to Trash. No app has been implemented.
The existing CUPS files, queue and daemon live outside an app and require explicit
cleanup. Bundled services alone would not remove those CUPS components; the
installed SDK also requires notarization for SMAppService LaunchDaemons, which
does not fit the owner's rejected paid-signing route. Preserve the current
validated package while resolving this design; do not silently substitute a
workflow requiring users to open documents in a dedicated printing app.
The firmware research baseline below remains the September 23 checkpoint.

## Current verified state

- Full sequential validation passed **100 consistency checks** and both suites.
  Log: `/tmp/hp1020-full-raw-parser-bih-20260923.log`; child logs `hp1020-validation.9CdiDF`.
  All current report source and fixture hashes match the tested files.
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
- Original raw-producer/admission checks pass **52 interpreter/QEMU comparisons**
  and **eight conditional release cases** with the original allocator and queue.
  JobMgr initializes references, and only descriptor selector 0 reaches this
  raw list. A supplied 16-byte prefix permits original cleanup after one raw
  completion; a second reference retains ownership with an adjusted cursor.
  These results are included in the full sequential validation above.
- Actual chunk-12 parsing passes **22 admission cases and two metadata-only
  controls** in both engines. Original queued messages create the owner hierarchy.
  The image pointer equals the allocator return and the raw IRQ flag stays zero
  at the checked boundaries. This is a separate producer from the standalone
  helper. Separate BIH delivery fills later work dimensions only with page bitmap
  setting 1; two mixed-metadata cases combine those dimensions with source kind 1.
  The raw IRQ flag and unadvanced cursor remain unresolved. No consumer or
  completed page lifecycle is added. These cases are included in the full run.

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
path executes through admission without adding a prefix. Actual BIH delivery and
independent page/band metadata now resolve the work-dimension copy, while raw IRQ
mode stays zero. Next trace pointer/mode changes before the excluded hardware
boundary; do not assume the mixed-metadata fixtures are physically supported.
Keep source-kind dispatch, raw IRQ mode and engine output selection distinct.
Do not repeat the completed selector matrix or resolved empty-document
cancellation/END_DOC ordering.
Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10.

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
No research process remains running. Engine-ready packing, cache
visibility, physical throughput, boot, printing and power-cycle recovery remain
unproven. Passing software tests do not establish physical output.
