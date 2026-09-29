# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity in
verified stages, reusing open components; HP's internal architecture is not the
implementation target. AGENTS.md owns the scope and authority.

## Latest firmware evidence

A strong **classic Synopsys USB device-controller family match** now has a
concrete open-source reference: pinned Linux v6.12 controller code, preserved
with license and provenance. The audit checks 24 literal/layout correspondences
and 18 original instruction anchors. Twelve original descriptor-construction
cases and 51 ownership/count fragments agree between independent QEMU and the
bounded interpreter. The only submission address is redirected to RAM; two
unredirected controls stop before MMIO. No USB controller behavior is emulated.

This is a family inference, not an AMD chip identification, working port or
live USB proof. The status fragment admits ownership completion even with other
status bits set; do not treat that alone as a valid transfer. The reference can
now guide a small controller adapter beneath a generic USB/printer-class layer.
Wrapper/PHY setup, byte order, cache/aliases and real reset/abort remain open.
Evidence: `analysis/usb-path/controller-family.json/.md`. Focused log:
`/tmp/hp1020-usb-controller-family-status-20260929.log`. Detailed handoff and the
initial mask-oracle correction/snapshots are in `next-evidence.md` below.

Full sequential validation passed **107 consistency checks and both suites**,
in `/tmp/hp1020-full-usb-family-20260929.log`, child logs
`hp1020-validation.atqz2B`. No research process remains running. Tested source
hashes match; the stock ELF and pinned upstream bytes are unchanged. Reports
were regenerated, never patched. The preceding document checkpoint is `35e3f07`
(106 checks and both suites, `/tmp/hp1020-full-page-reuse-20260929.log`).

That document checkpoint removed streaming's 16-page limit without increasing
component memory. **45 host/45 QEMU output cases** (31 successes, 14 expected
rejections) and **66 host/44 QEMU stream cases** cover 65 mixed-size pages,
65 consecutive documents, delayed output, final bands and checked count overflow.
Whole-file inspection keeps its separate 16-page bound. State/fixed memory is
123968 bytes, excluding code, stack, caller packets and captures. Copies remain
metadata; no copy replay, physical output or real cancellation is implemented.

Next use the pinned controller source and original bytes to resolve receive-error
and reset/abort ownership before a bounded software receive adapter. Preserve
queued output until its external consumer is quiescent; clearing C state is not
cancellation. Detailed questions: `analysis/open-firmware-model/next-evidence.md`.
Tool recovery and the source map: `analysis/README.md`.

Preserve separate evidence categories: 26 completed empty-document lifecycles,
six conditional original null reads, 28 retirement cases, 36 native page
lifecycles with supplied completion, and 42 fragment/bypass cases. The new
software streams and USB fragments add **zero native page lifecycles**. The
replacement still lacks demonstrated boot, USB, pixel packing, engine control,
timing/cache, physical printing and power-cycle recovery. Do not repeat resolved
selector/cancellation investigations or modify the working Mac setup.

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
