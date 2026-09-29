# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity in
verified stages, reusing open components; HP's internal architecture is not the
implementation target. AGENTS.md owns the scope and authority.

## Latest firmware evidence

The bounded ZjStream parser and JBIG decoder feed the independent C output ring
through `hp1020_image_output`. Streaming now reuses one page metadata record;
65 mixed-size pages and 65 consecutive mixed-size documents preserve every tested
pixel and output-storage byte without increasing component memory. Whole-file
inspection retains its separate 16-page limit. Page/document/row/band overflow
fails before emission; old page geometry survives until its output drains.

Focused output validation passes **45 sanitized host and 45 QEMU cases**:
31 successful software streams and 14 expected rejections. Stream regression
passes **66 host and 44 QEMU cases**, including a detailed 10 MB source image.
Logs: `/tmp/hp1020-image-output-page-reuse-fixed-20260929.log` and
`/tmp/hp1020-image-stream-page-reuse-20260929.log`. State/fixed storage stays
123968 bytes, excluding code, stack, caller packets and test captures. Reports:
`analysis/open-firmware-model/image-core/output-validation.json/.md` and
`stream-validation.json/.md`. Copies remain forwarded metadata, not replayed.

Full sequential validation passed **106 consistency checks and both suites**
for the current sources, in `/tmp/hp1020-full-page-reuse-20260929.log`, child logs
`hp1020-validation.1RndJc`. All 309 image source/fixture/sample hash entries match.
No validation process remains running. Reports/hashes were regenerated, never
patched by hand. The earlier 39-case checkpoint is preserved at `02a858a`.

A compiler audit caught a null-page cold path in the initial metadata-reuse
build before target execution. Explicit order checks fixed it; the rejected
source/ELF/log snapshot is `/tmp/hp1020-page-reuse-null-trap-20260929/`.
This is separate from the six conditional null reads in original HP code.

Next pursue the promising classic Synopsys USB device-controller family match
against pinned
Linux v6.12 source and original instructions. Read-only upstream captures and an
**unexecuted** comparison/re-arm experiment draft are at
`/tmp/hp1020-usb-controller-reference-20260929/`; no controller port is established.
The old page-reuse draft is pre-fix history, not the latest source. Detailed
questions and evidence remain in `analysis/open-firmware-model/next-evidence.md`.

These are serialized RAM experiments with supplied output acceptance/completion,
not native printer lifecycles or physical output. Errors preserve outstanding
ownership; resetting C state does not cancel transfers. Boot, USB, physical pixel
packing, timing/cache, engine control and real recovery remain unproven. Preserve
26 completed empty-document lifecycles, six conditional null reads, 28 retirement
cases, 36 native page lifecycles with supplied completion, and 42 fragment/bypass
cases as separate categories. New software streams add **zero native lifecycles**.
Recovery is in `analysis/README.md`; QEMU's private debugger socket needs sandbox
permission. Do not repeat resolved selector/cancellation investigations.

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
