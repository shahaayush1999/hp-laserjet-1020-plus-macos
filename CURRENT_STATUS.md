# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity in
verified stages, reusing open components; HP's internal architecture is not the
implementation target. AGENTS.md owns the scope and authority.

## Latest firmware evidence

The bounded ZjStream parser and JBIG decoder now feed the independent C output
ring through `hp1020_image_output`. **39 sanitized host and 39 QEMU cases** pass:
28 successful software streams and 11 expected rejections. Different page sizes,
consecutive documents, delayed completion, final partial bands and reused input
preserve all tested pixels and all output storage bytes. Late syntax errors,
consumer failures and a consumer returning success without progress cannot
become successful completion. Failed output retains ownership until explicitly
quiesced/abandoned by the caller. Copies are forwarded metadata, not replayed.

Focused log: `/tmp/hp1020-image-output-target-20260929-permitted.log`. Target
state/fixed storage is 123968 bytes, excluding code, stack, input packets and test
captures. Reports: `analysis/open-firmware-model/image-core/output-validation.json/.md`.
This is a serialized RAM experiment with supplied output acceptance/completion,
not a native printer lifecycle or physical output. Its prerequisite decoder/ring
and bounded original ownership evidence remain separate reports.

Full sequential validation passed **106 consistency checks and both suites**, log
`/tmp/hp1020-full-image-output-20260929.log`, child logs `hp1020-validation.3BfPNL`.
All current tested source hashes match. No validation process remains running.
No reports or source hashes have been patched by hand.

Next remove streaming mode's 16-page metadata limit by reusing the current page
record, while retaining whole-file inspection's explicit bound. A private,
**unexecuted** draft is at `/tmp/hp1020-stream-page-reuse-20260929/`; apply/review it
after this validated source checkpoint is committed and pushed.
It includes longer mixed-page/document cases and checked counter overflows.
Do not run validation suites concurrently or modify their tested sources mid-run.

USB/runtime reuse decisions and detailed evidence live in
`analysis/open-firmware-model/next-evidence.md`. JBIG-KIT is used already. TinyUSB
has a printer-class implementation, but a compatible controller port remains
unestablished; ThreadX also needs a core/toolchain fit assessment. Boot, USB,
physical pixel packing, output timing/cache, engine control and real recovery
remain unproven. Do not repeat resolved selector/cancellation investigations.

Preserve existing evidence categories: 26 completed empty-document lifecycles,
six conditional null reads, 28 retirement cases, 36 native page lifecycles with
supplied consumption/completion, and 42 fragment/bypass cases. New software
streams add **zero native page lifecycles**. Disposable compiler/tool recovery
is in `analysis/README.md`; QEMU's private debugger socket needs sandbox permission.

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
