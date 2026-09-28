# Current handoff

Updated: 2026-09-28. **The open replacement cannot print yet.**
Current work is maintenance of the separate HP-based macOS printing setup.
No printer enumeration, query, firmware upload or physical test occurred.

**Support fixes implemented and installed on the owner’s Mac:** the PPD now uses Apple's
native copy/layout filters. Complete collated and uncollated document sets,
page selection/order/layout and A4/Letter are verified through real native
filters, Ghostscript and encoder output. The backend stays connected to a
serialized `_lp` worker for progress, cancellation and failures. Known PJL
feedback drives paper/cover/jam reasons; matching job name/page count is required
for confirmed completion. Missing feedback is explicitly unconfirmed. Failed
transfers/restarted work are held without automatic replay. Firmware is loaded
only when FWVER is absent and must be verified before sending a document.
Cancellation requests the standard USB reset, kills descendants, and cleans up.
New jobs have no extra document archive; crash leftovers are removed on restart.

Sequential support validation passed **38 printing checks and 17 setup checks**.
Exact tested hashes/scope are in `assets/macos-printing-validation.json` and
`assets/macos-setup-validation.json`; all match. The latter includes protected
repository access and fatal shell failures after a real update exposed those
problems. The original setup was restored and checked, then the staged-input
installer succeeded. Installed source/firmware/license bytes match; both native
binaries verify; the service runs as `_lp`; the queue is enabled, accepting and
idle with collated sets as default. The old per-user helper/runtime is retired.
An additional offline run through the installed native filter chain and encoder
produced four ordered two-page sets (eight output pages, encoder copies one).
No print job was submitted. See `MANIFEST.md` for the deployment/test details.

The offline suites simulate USB, Homebrew and administration. Real installation
and idle startup are separately verified; actual CUPS scheduler/UI, device
feedback, buffer reset, fresh-Mac installation and physical output remain
unverified. Next support evidence: one explicitly authorized, freshly power-cycled
printer test for copies and paper/queue feedback. Do not ask the owner to manually
exercise every edge case or claim live alerts are proven. The first-attempt
recovery backup remains at `/private/var/folders/zz/zyxvpxvq6csfxvn_n0000000000000/T/hp1020-rollback.XXXXXXXX.CbLay5meYi`.

Use **git clone + `scripts/install.sh` + `scripts/uninstall.sh`**, with Homebrew
for Ghostscript/GNU sed/Python. Do not reintroduce apps, packages or ZIP handoffs.
Ownership survives reinstall; cleanup preserves pre-existing/shared packages and
retains failed-cleanup records for retry. Failed replacement restores prior
files/queue PPD and requires service readiness before enabling the updated queue.
`README.md` is user setup; `MANIFEST.md` owns support implementation/test detail.
Original runtime/vendor assets and the September 23 research baseline are intact.

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

Firmware research remains offline: no USB enumeration/contact, queries, uploads,
installed-printing changes or print-driving MMIO. The authorized support update
above is separate from research. Unknown custom instructions are not inert.
No research process remains running. Engine-ready packing, cache
visibility, physical throughput, boot, printing and power-cycle recovery remain
unproven. Passing software tests do not establish physical output.
