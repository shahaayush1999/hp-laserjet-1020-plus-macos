# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity by
reusing open components and verifying hardware contracts. AGENTS.md owns scope.

## Latest firmware evidence

The existing printer-class/document composition passes 73 host/73 QEMU cases:
ID/status/reset, retained responses/output, stale events, exact decoded pixels
and fresh document recovery. Target state/fixed memory is 128216 bytes, excluding
code, stack, immutable ID and test captures. Physical quiescence remains supplied.

TinyUSB's generic protocol core is now composed with that class. **52 unchanged
host/52 QEMU scenarios** retain 14 protocol observations and 32 BE status-byte
mismatches. A separate two-file patch fixes serialization, request routing, failed
EP0 progression and configuration context; **160 host/160 QEMU scenarios pass**
with exact wire proposals and recovery. Vendor originals remain pinned and
unchanged. This is a synthetic DCD/event fixture: no real controller, bulk payload
or page decoding passes through TinyUSB yet. Reports and byte-preserved earlier
sources/builds/captures: `analysis/usb-path/tinyusb-device/`. Focused log:
`/tmp/hp1020-tinyusb-patched-target-20260929.log`.

Original pause/restore passes 46 conditional cases in both engines. It requests
pause/resume and saves NAK state but does not establish DMA quiescence. Separate
original reset/status and output-format/pointer experiments remain bounded before
peripheral access. The old receive model's false thread-descriptor/name and
max-packet labels are corrected against 46 byte checks.

Full sequential validation passed **116 consistency checks and both suites**,
log `/tmp/hp1020-full-tinyusb-20260929.log` (child `hp1020-validation.qvzwiA`).
The C path emits SRC/MEMW; exact annotated stock bytes gate these standard
instructions in the shared auditor. Reports were regenerated and their current
source hashes match; no report hashes were patched manually. No printer contact.

Next connect protocol bulk reception to page decoding through a reusable adapter,
and execute the independent original SETUP-ingress draft sequentially. Explicit
transport/control identities, configuration admission, cancellation and input
closure require care. Local adapter/test and SETUP drafts are **unexecuted and
excluded from this checkpoint's validation**. Detailed questions/evidence:
`analysis/open-firmware-model/next-evidence.md`; topic map/tool recovery:
`analysis/README.md`. GCC, binutils and QEMU currently work.

Keep separate: 26 completed empty-document lifecycles, six conditional original
null reads, 28 retirement cases, 36 native page lifecycles with supplied completion,
and 42 fragment/bypass cases. New protocol/control fragments add **zero native
page lifecycles and zero USB transfers**. Receive retains 75 host/75 QEMU cases,
image output 45/45, stream 66/44. Copies remain metadata. Boot, actual USB, engine
timing/cache, physical status/printing and power-cycle recovery remain unproved.

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
