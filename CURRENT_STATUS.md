# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity by
reusing open components and verifying hardware contracts. AGENTS.md owns scope.

## Current offline work

The current checkpoint passes **121 consistency checks and both sequential
validation suites**, including native pipeline, retirement and page checks. Log:
`/tmp/hp1020-full-udc-boundary-20260929.log`; child `hp1020-validation.csAmPs`.
The preceding completed/pushed baseline is `67672b9` (118 checks). GCC, binutils
and QEMU work; pinned recovery is in `analysis/README.md`.

Continuous-document/recovery source passes **132/132 host/QEMU adapter,
34/34 continuous, 82/82 class, 45/45 output and 75/75 receive** cases. Valid
page/document boundaries drain software output and notify without closing input;
configuration starts recovery without a fake host reset. Three settlement
promises remain external. The initial standard-reply failure was reproduced and
fixed; exact failed/passed sources and captures are preserved. Protocol baselines
retain 52/52 and 160/160. A prior aggregate stopped at an obsolete stream-size
expectation; the checker now matches measured91032 bytes, with no report-hash
edits. That stopped attempt is archived separately.

The RAM-only OUT descriptor bridge passes **34 sanitized host/34 QEMU scenarios**
through actual TinyUSB dispatch to exact pixels/document events. Both directions
of disagreement between a saved completion and live bytes are checked. Source
closure97; component/descriptor overhead80 bytes beyond adapter128536.
`open-firmware/udc-out/` retains the original adapter cookie with no new queue.
Mode, CPU/DMA mapping, cache ordering, immutable observations and settlement are
supplied; descriptor bits do not prove them. No physical DCD exists.

Original idle receive retains58 conditional cases/62 invocations per engine,
six pre-MMIO rejection controls per engine and15 excluded controls. Its supplied
services show delayed receive-enable intent, not a proven stock race or DMA stop.
SETUP ingress70 and pause/restore46 remain separate. The legacy control-IN pointer
model now distinguishes active unchanged pointers from initialization ADD; it
establishes no physical address alias.

## Next action

Commit/push this validated checkpoint, then integrate and execute the reviewed
EP0 drafts sequentially: original construction cuts, exact-cookie adapter fault
handling and separate IN0/OUT0 descriptor/staging boundaries. Drafts are under
`/tmp/hp1020-ep0-construction-draft-20260929.py`,
`/tmp/hp1020-ep0-adapter-draft-20260929/`,
`/tmp/hp1020-udc-ep0-draft-20260929/` and
`/tmp/hp1020-udc-ep0-validation.py`; none has executed. First close the fixture's
retirement-time original-buffer check gap and consume the executed original
report as the new component's byte oracle. EP0 cookie epochs are control epochs,
not bulk transport epochs. Never run validators concurrently or alter tested
source closures during execution. Detailed evidence/unresolved questions live in
`analysis/open-firmware-model/next-evidence.md`.

Keep separate:26 completed empty-document lifecycles, six conditional original
null reads,28 retirement cases,36 native page lifecycles with supplied completion,
and42 fragment/bypass cases. New USB/component checks add zero physical USB or
native page lifecycles. Copies remain metadata; output is synchronous. Boot,
actual USB/cache/engine behavior, physical status/printing and power-cycle
recovery remain unproved. Do not repeat cancellation/END_DOC ordering research.

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
