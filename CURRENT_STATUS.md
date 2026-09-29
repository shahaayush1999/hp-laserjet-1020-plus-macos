# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity by
reusing open components and verifying hardware contracts. AGENTS.md owns scope.

## Current offline work

The latest full run passes **124 consistency checks and both sequential suites**.
Log `/tmp/hp1020-full-ep0-boundary-20260929.log`; child
`hp1020-validation.JolOPF`. Tools work; pinned recovery is in `analysis/README.md`.
This includes continuous documents, automatic recovery,132 adapter/34 continuous
and34 RAM-only OUT cases per host/QEMU. The prior failed stream-size gate and
reproduced standard-reply failure remain archived separately.

New work included in that completed aggregate:

- Original EP0 construction:66 profiles per engine (36 construction,12 pointer,
  16 pre-MMIO,2 excluded-length controls),18 excluded PCs. All mutable RAM,
  registers and ordered accesses agree. Supplied mid-function cuts; no original
  ENTRY, copy/cache helper, completion or peripheral access.
- Exact-cookie retained faults:20 host/20 QEMU. Faults retain borrowed bytes and
  suppress a late successful ACK/follow-on. Superseded/old-generation faults
  cannot stop newer input. Target adapter state remains128536 bytes.
- Separate EP0 IN staging/OUT status descriptors:50 host/50 QEMU; real TinyUSB
  packet splitting/DATA ZLP/status, exact wire/pixels/events, immutable snapshots,
  malformed facts, stale cookies and recovery. Component/allocation overhead296
  bytes;92 sources/six fixtures. Bulk remains normalized in this experiment.

Exact first failed and passed captures/sources are archived beside their reports.
Packet-fault first run reached all cases but stopped at an audit-listing hash
check; the capture generator was corrected. EP0 first run passed50 host then
stopped before target build due to unadapted draft paths; only builder integration
changed. Neither failed run is relabelled as a completed success.

## Next action

Commit/push this validated checkpoint, then integrate the unexecuted SETUP bridge
from `/tmp/hp1020-setup-ingress-next-20260929/` and composed fixture from
`/tmp/hp1020-udc-composed-draft-20260929/`. The lead's unexecuted34-profile validator
is `/tmp/hp1020-udc-composed-validation.py`. Independent reviews added held-request
gates for old reset ACKs and delayed publication, exact reset-WAIT retry, and
terminal controller-settlement versus pending-adapter distinctions. No new
draft is validated yet. Execute focused checks sequentially, preserve failures,
then add its aggregate gate and rerun the full suite before the next checkpoint.
Do not repeat completed70-case stock SETUP analysis. The next bounded stock
candidate is its unexecuted post-dispatch retirement/rearm tail; a separate agent
is drafting it under `/tmp`. Ordering, hardware stall clearing and old-buffer
settlement remain separate supplied facts. Details are in `next-evidence.md`.

Keep separate:26 completed empty-document lifecycles, six conditional original
null reads,28 retirement cases,36 native page lifecycles with supplied completion,
and42 fragment/bypass cases. USB/component checks add zero physical USB or native
page lifecycles. Copies remain metadata; output is synchronous. Boot, actual
USB/cache/engine behavior, physical status/printing and power-cycle recovery are
unproved. No physical DCD exists. Do not repeat cancellation/END_DOC research.

## Installed Mac driver (separate, preserve)

The owner-authorized HP-based native Mac driver is installed. It uses Apple's
renderer, unchanged foo2zjs and a per-job CUPS backend. CUPS owns copies, queueing
and job lifetime. Clone/install/uninstall remains the user flow; no apps/packages/
ZIPs or Homebrew runtime are required. README owns setup; MANIFEST owns validation,
installed-byte checks and recovery. Do not restore the obsolete private worker,
daemon or per-user runtime.

Support checks passed 35 printing, 14 setup, three source-derived sandbox and
five actual macOS scheduler lifecycle cases using a simulated transport. This
is not physical printing proof. Evidence: `assets/macos-system-validation.json`
and `/private/tmp/hp1020-system-install-20260928-2/`. Root-only migration backup:
`/private/tmp/hp1020-native-migration-backup-20260928/` (`paths.json`). The native
queue was empty/idle and installed signatures/ownership/bytes matched the build.
Actual copies, status/recovery and fresh-Mac installation remain unverified.
For explicitly authorized system checks use `scripts/validate-macos-system.py`;
the older isolated scheduler ignores alternate settings on this Mac and fails
closed. No USB query, firmware upload or physical print occurred during this work.
