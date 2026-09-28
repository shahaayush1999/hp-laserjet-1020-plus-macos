# Current handoff

Updated: 2026-09-28. **The open firmware replacement cannot print yet.** Offline
research continues. Do not enumerate/contact the printer, upload firmware,
execute print-driving hardware paths or change the installed printing setup.

## Latest firmware evidence

The open C decoder now connects directly to a bounded software output ring.
**36 sanitized host and 36 QEMU cases**, with 11 API rejection controls per
engine, pass. Every pixel and every guarded storage byte is compared. Six cases
per engine match the original bounded ownership trace exactly. Longer images
exercise repeated full-ring pauses, delayed completion and buffer reuse. There
is no host pixel-copy bridge between these C components. The simulated consumer
still supplies acceptance/completion; this is **zero new native page lifecycles**.

The preceding original-code experiment passed eight isolated transfers and two
continuous five-transfer sequences through actual original output allocations.
It distinguished claiming, filling, selecting and releasing a buffer, including
continuous wrap and a short final band. Source owners remain live after output
retirement. The raw IRQ flag stays zero; no source prefix is inserted/subtracted.
These serialized original stages and the new independent C ring are distinct.

Full sequential `scripts/validate.sh` passed **105 consistency checks and both
suites**, including native pipeline/retirement/page regressions. Log:
`/tmp/hp1020-full-image-ring-20260928.log`; child logs `hp1020-validation.WTCBMK`.
Current source hashes match the evidence. No validation process remains running
at this checkpoint. The previous 104-check checkpoint is committed at `7fe51be`.
The first host-only report and exact matching sources are preserved outside the
current evidence in `/tmp/hp1020-image-ring-host-first-20260928/`.

Reports: `analysis/hardware-boundary/software-ring.json/.md` and
`analysis/open-firmware-model/image-core/ring-validation.json/.md`. Existing
handoff details and the next experiment are in
`analysis/open-firmware-model/next-evidence.md`. The target component needs 30824
bytes of state/minimum buffers at A4 width, excluding code, stack, input and test
captures. It is neither a complete firmware RAM budget nor an upload image.

Next connect the existing bounded ZjStream band consumer to this software ring,
checking per-page draining and differently sized consecutive pages/documents with
reused input chunks. Keep late input rejection distinct from emitted rows.
Original owner integration, native scheduling, live configuration, physical
packing, engine behavior and power-cycle recovery remain unproven. Do not repeat
resolved metadata, selector or cancellation investigations.

Preserve earlier categories: 26 completed empty-document lifecycles, six
conditional null reads, 28 bounded retirement cases, 36 native page lifecycles
with supplied FIFO consumption/completion, and 42 fragment/bypass cases. Parser
admission/preparation, video allocation controls and software-image cases are
not extra native page lifecycles. Reports retain their actual tested hashes.

GCC 14.3.0, target headers and libgcc were recovered through the pinned build
script and checksum/encoding/profile gates. Log `/tmp/hp1020-gcc-recovery-20260928.log`;
sandbox DNS needed permission for that same pinned download. Disposable tool
recovery is in `analysis/README.md`.

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
