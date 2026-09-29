# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity by
reusing open components and verifying the hardware boundary. AGENTS.md owns scope.

## Latest firmware evidence

The new `open-firmware/usb-printer-class/` composes standard ID/status/reset
requests with the existing receive, parser, JBIG and software output pipeline.
**73 sanitized host and 73 QEMU cases pass.** Recovery preserves accepted page
output, rejects late events even after a buffer is reused, and produces a fresh
exact-pixel document. Repeated resets, newer requests, response-buffer lifetime,
faults and exhausted identities are checked. Three external reset promises and
separate EP0 quiescence remain supplied; there is no actual USB controller port.
Status is supplied or explicitly unknown fallback, never inferred from progress.

Target state/fixed memory is 128216 bytes, excluding code, stack, immutable ID
and test captures. Report: `analysis/usb-path/printer-class/validation.json/.md`;
log `/tmp/hp1020-usb-printer-target-20260929-2.log`. The first target audit rejected
a test-only remainder helper. The fixture was corrected without relaxing the
audit; prior exact sources, host report, target ELF and logs are preserved in
that report directory's `source-snapshots/`. No report hashes were patched.

Original-byte experiments now pass 20 class-reset and 12 output-format cases
in interpreter/QEMU, stopping before peripheral access. Reset clears registration
and software lists with supplied frees; that does not prove DMA cancellation.
Format tables differ between selectors 0 and default 2 despite both using one
output lane. Pixel polarity/sample meaning and physical acceptance remain open.
The earlier output address/count experiment retains 30 passing cases. A further
28 original port-status cases prepare a fixed zero byte before transmission;
that path is not a source of measured paper/engine status.

Full sequential validation passed **113 consistency checks and both suites** in
`/tmp/hp1020-full-printer-class-20260929.log` (child `hp1020-validation.tBubz6`).
All focused and full runs finished and source hashes match. The previous pushed
checkpoint is `9eb8ee3` (109 checks); this expanded checkpoint is ready to save.
New TinyUSB protocol-fixture work and `vendor/tinyusb-0.21.0/` are unexecuted and
excluded from this run; preserve that separation at the next checkpoint.

Next execute the unchanged TinyUSB generic protocol core on host and BE target,
record compatibility findings, then address the demonstrated gaps. Continue toward
the unresolved controller/boot and physical output contracts, without rebuilding resolved
internal scheduling models. Detailed questions, captures and evidence categories:
`analysis/open-firmware-model/next-evidence.md`; topic map and disposable-tool
recovery: `analysis/README.md`. GCC, binutils and QEMU currently work.

Keep separate: 26 completed empty-document lifecycles, six conditional original
null reads, 28 retirement cases, 36 native page lifecycles with supplied completion,
and 42 fragment/bypass cases. New control/receive software and hardware-boundary
fragments add **zero native page lifecycles and zero USB transfers**. Existing
receive component retains 75 host/75 QEMU cases, image output 45/45, stream 66/44.
Copies remain metadata. Boot, actual USB, engine timing/cache, printing and
power-cycle recovery remain unproved.

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
