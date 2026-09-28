# Current handoff

Updated: 2026-09-28. **The open replacement cannot print yet.**
The HP-based macOS setup prints, but has the support gaps below. It is untouched.
No printer contact, upload, installed-printing change or print-driving hardware
path occurred.

**Current support issue (September 28):** requested copies are lost; jobs leave
the macOS queue without waiting for the worker; no paper-out alert is provided.
Read-only inspection confirmed this in the installed backend, passthrough filter,
worker and per-user helper. A temporary, relocated copy of the installed backend
produced one identical document and no copy metadata for both 1 and 4 requested
copies, returning success without running a worker. Repository sources retain
the same defects: backend arguments 4/5 are discarded, the worker receives only
a filename, and the helper sends one copy. No fix or live test has occurred.
Next support work: preserve copy counts through the handoff and produce complete
document sets; keep CUPS attached through processing/transfer with failure and
cancellation handling. Do not mistake transfer completion for physical printing.
Paper-out/physical completion needs verified device feedback; existing PJL probe
plans are not proof of working alerts. Printer contact still needs authorization.
The 12 setup checks below cover conversion/install/cleanup, not print-dialog copy
propagation or queue/status behavior; direct encoder `-n2` cases did not cover it.

Support decision: the owner reversed the self-contained bundle experiment.
Use **git clone + `scripts/install.sh` + `scripts/uninstall.sh`**, with Homebrew
handling downloads. Do not reintroduce apps, packages, ZIP handoffs or bundled
Ghostscript/GNU sed. The installer bootstraps official Homebrew if absent,
installs missing dependencies, compiles the small foo2zjs encoder for the host,
and sets up the existing queue/worker approach. Package ownership persists in
`~/.local/state/hp1020/`; removal handles added dependencies and a newly created,
unused Homebrew installation, preserving pre-existing/shared packages. Interrupted
or failed cleanup keeps its record for retry. Run as the same normal Mac user.
Twelve focused offline checks passed; exact hashes and scope are in
`assets/macos-setup-validation.json`. Four conversion cases match all original
encoder chunks. Homebrew, administration and USB calls were mocked. No fresh-Mac
installation or physical print test occurred. Original `assets/runtime/`, vendor
sources and firmware research remain unchanged; the research baseline is still
September 23. README uses a shallow clone so obsolete archives in Git history
are not fetched. The removed bundle and reports remain recoverable in Git.

Repository visibility changed to public on September 27 at the owner's explicit
request and verified through GitHub without authentication. Existing third-party
assets and redistribution notices remain; visibility is not a license review.

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
