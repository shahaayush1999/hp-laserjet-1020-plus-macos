# Current handoff

Updated: 2026-09-28. **The open firmware replacement cannot print yet.** Offline
research is active. Do not enumerate/contact the printer, upload firmware,
execute print-driving hardware paths or change the installed printing setup.

## Latest firmware evidence

Software-decoded pixels now enter actual original output-buffer allocations.
**Eight isolated transfers and two continuous five-transfer sequences** agree
byte for byte in the interpreter and independent QEMU. The continuous cases
fill the four slots, block reuse while owned, distinguish output acceptance
from completion, then wrap and reuse the released slot for a one-row final band.
All 17 selected rows match the decoder/original-decoder/source-pixel oracle.
Only intended bytes change; source owners and pool allocations remain intact.
These are **zero additional native page lifecycles**. The host still bridges
decoder output into parser input and supplies copies, readiness, completions and
their ordering. No physical transfer or automatic consumer is claimed.

The full sequential `scripts/validate.sh` passed **104 consistency checks and
both suites**, including all native pipeline/retirement/page regressions. Log:
`/tmp/hp1020-full-software-ring-20260928.log`, child logs `hp1020-validation.Rqozd4`.
Current source hashes match the evidence. No validation process remains running
at this checkpoint. The earlier 102-check baseline remains in `35ee3cc`; the
four-case delivery source snapshot is separate from the expanded result.

The retained parser/preparation evidence includes 22 admissions, two metadata
controls, eight preparation continuations and four missing-dimension stops.
Original video allocation also passes two idle release/reuse cases and four
pre-retry capacity controls. No late source-prefix adjustment or raw-mode
activation occurs. The delivery experiment uses the normal descriptor branch,
not the unrelated raw pointer-subtraction tail. Raw/delivery validators reject
source changes during execution. Peripheral/custom-code guards remain closed.

GCC 14.3.0, target headers and libgcc were recovered using the pinned build script,
checksum and encoding/profile gates. Log `/tmp/hp1020-gcc-recovery-20260928.log`.
Sandbox DNS required network permission for the same pinned source download.
Tool recovery is in `analysis/README.md`; reports are
`analysis/hardware-boundary/raw-parser.json/.md` and `software-ring.json/.md`.
Detailed evidence and next steps are in the September 28 handoff/delivery sections of
`analysis/open-firmware-model/next-evidence.md`.

Next remove the host copy bridge by connecting the bounded C decoder's band
pause/release contract to software output ownership in one compiled RAM fixture.
An unexecuted implementation/fixture draft is in
`/tmp/hp1020-ring-adapter-draft-20260928/`; it is not validated source or evidence.
Keep consumption explicit; completion of the last descriptor does not retire
the page/source owners. Stock input/output rings are distinct. Physical packing,
live configuration, repeated page submission, boot/engine behavior and power-cycle
recovery remain unproven. Do not repeat metadata, selector or cancellation matrices.

Preserve earlier categories: 26 completed empty-document lifecycles, six
conditional null reads, 28 bounded retirement cases, 36 native page lifecycles
with supplied FIFO consumption/completion, and 42 fragment/bypass cases.
Software image tests and serialized continuations are not extra stock lifecycles.

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
