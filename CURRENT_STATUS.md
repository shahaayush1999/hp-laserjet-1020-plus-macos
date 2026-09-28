# Current handoff

Updated: 2026-09-28. **The open firmware replacement cannot print yet.** Offline
research is active. Do not enumerate/contact the printer, upload firmware,
execute print-driving hardware paths or change the installed printing setup.

## Latest firmware evidence

The actual chunk-12 parser now continues through original JobMgr endings,
PrintMgr/media matching, engine acknowledgement and VideoThread RAM preparation.
**Eight preparation continuations and four missing-dimension controls** agree in
the interpreter and independent QEMU, alongside the retained **22 admissions and
two metadata-only controls**. No late source-prefix adjustment or raw-mode
activation occurs: preparation retains the source allocation cursor and clears
the raw IRQ selection bit. Missing dimensions stop before division.

The original video constructor prefix now allocates both output buffers, clears
idle state, creates its semaphore and registers handlers in RAM, stopping before
peripheral setup. All prepared slot spans fit their actual allocated buffers.
**Two idle release/reuse cases and four pre-retry capacity controls** also agree
between engines. Output buffers still hold initialization bytes; source pixels
have not entered them. Ready/media values, task-entry cuts and pool capacity
remain explicit fixtures. These are **zero additional native page lifecycles**.

Full sequential `scripts/validate.sh` passed **102 consistency checks and both
suites**, including native pipeline/retirement/page regressions. Log:
`/tmp/hp1020-full-raw-handoff-20260928.log`; child logs `hp1020-validation.a6RCMj`.
Current source hashes match the generated evidence. Raw validators now reject
mid-run source changes instead of recording new hashes for old execution.
The first continuation's report-range error was corrected at the generator's
instruction boundary; no original execution failure or manual report edit was
reclassified as a pass. No research process remains running at this checkpoint.

GCC 14.3.0, target headers and libgcc were recovered using the pinned build script,
checksum and encoding/profile gates. Log `/tmp/hp1020-gcc-recovery-20260928.log`.
Sandbox DNS required network permission for the same pinned source download.
Tool recovery is in `analysis/README.md`; reports are
`analysis/hardware-boundary/raw-parser.json/.md`. Detailed evidence and next steps
are in the September 28 serialized-handoff section of
`analysis/open-firmware-model/next-evidence.md`.

The follow-up stock-byte inspection located separate buffer claim, fill-publication
and output-release stages: a claimed descriptor does not establish ready pixels.
The next handoff records their precise RAM-only cuts and consumer delay. This
is instruction-derived planning, not another executed lifecycle. Next connect
software-decoded bands through those stages with exact byte checks, including
ring wrap and partial final bands. Keep readiness/consumption explicit and
peripheral prefixes excluded. Do not
force raw IRQ mode or repeat resolved metadata, selector or cancellation matrices.
Physical packing, live configuration, repeat submission, boot/engine behavior
and power-cycle recovery remain unproven.

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
