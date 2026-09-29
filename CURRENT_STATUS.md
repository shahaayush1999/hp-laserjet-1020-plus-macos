# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity by
reusing open components and verifying hardware contracts. AGENTS.md owns scope.

## Latest firmware evidence

The reusable TinyUSB adapter now connects synthetic bulk reception to the open
class/receive/JBIG/output path. **98 sanitized host/98 QEMU cases pass**, checking
independent exact pixels, USB reply proposals, retained buffers, stale events,
reset/configuration recovery and malformed controls. Target state/fixed memory
is 128488 bytes, excluding code, stack, TinyUSB and fixture captures. This is a
synthetic DCD, not a real controller port. Initial wire SOFT_RESET, three external
recovery promises, synchronous output and explicit input close remain supplied.
Reports and earlier failed/passed source snapshots: `analysis/usb-path/tinyusb-printer/`.

The normalized receive API preserves the original raw-descriptor wrapper; its
75 host/75 QEMU regression passes. The separate printer-class composition retains
73/73. Unchanged pinned TinyUSB retains its 52/52 baseline with 14 protocol
observations and 32 BE status-byte mismatches; the two-file patched core passes
160/160. Vendor originals stay unchanged. Every current source hash matches.

Original SETUP ingress passes 70 interpreter/QEMU cases, six pre-MMIO rejection
controls per engine and 14 excluded-code controls. It distinguishes SUBPTR from
ordinary OUT0 DESPTR and verifies stock field swaps before dispatch. Six older
generators and the authored contract now distinguish these representations,
register roles and task wake hints from successful transfer completion. All
hardware allowlists and original write permissions remain unchanged.
Original pause/restore retains 46 conditional cases; it does not prove DMA stop.

Latest **full sequential validation passes 118 consistency checks and both suites**.
Log: `/tmp/hp1020-full-reusable-printer-20260929.log`; child
`hp1020-validation.quvweZ`. Reports were regenerated normally; no hashes were
patched to claim untested source. No printer contact or installed-driver changes.
GCC, binutils and QEMU currently work; pinned recovery is in `analysis/README.md`.

## Next work

Review/commit/push this validated checkpoint, then apply and execute the separate
unapplied `/tmp/hp1020-continuous-streaming.patch`, automatic-recovery patches and
independent oracle/test drafts. They add validated END_PAGE/END_DOC observations
without closing ordinary input and recovery after a new configuration without
fabricating a host reset. They are **not implemented or tested in the 98 cases**.
A failed initial configuration acknowledgement must stay fenced and retain any
bound EP0 owner. Preserve source snapshots before investigating failures.

`scripts/validate-hp1020-usb-idle-receive.py` is a saved **unexecuted draft**.
Its bounded next experiment checks original background RDE-enable intent with
three private RAM literal redirects and supplied interrupt/delay services. It
cannot establish physical quiescence. Run it sequentially, never alongside
another validator. Detailed evidence/plans: `analysis/open-firmware-model/next-evidence.md`.

Keep separate: 26 completed empty-document lifecycles, six conditional original
null reads, 28 retirement cases, 36 native page lifecycles with supplied completion,
and 42 fragment/bypass cases. New USB/control/adapter checks add zero native page
lifecycles and zero USB transfers. Copies remain metadata. Boot, actual USB,
engine timing/cache, physical status/printing and power-cycle recovery are unproved.

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
