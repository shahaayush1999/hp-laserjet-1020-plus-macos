# Current handoff

Updated: 2026-09-28. **The separate open firmware replacement cannot print yet.**
The owner-authorized native HP-based Mac driver is now installed. No printer
enumeration, query, firmware upload or physical print occurred during this work.

## Installed Mac driver

The driver uses Apple's native document/raster renderer, the unchanged foo2zjs
encoder, and a per-job native CUPS backend. CUPS owns copies, queueing and job
lifetime. Installation removed the private queue/worker, launch daemon, old
bridge filters/backend and per-user runtime. No Homebrew runtime is required.
Clone/install/uninstall remains the user flow; do not restore apps/packages/ZIPs.

Final runs passed **35 printing checks, 14 setup checks, three source-derived
sandbox checks and five actual macOS scheduler lifecycle checks**. Reports own
exact tested hashes. The actual scheduler test used a uniquely named temporary
queue and a compiled simulator with no USB access. It verified four complete
copies, five queued documents, paper recovery, cancellation followed by another
job, and failure held without replay. `_lp` execution, generated profiles and a
positive/negative filesystem control confirmed sandbox enforcement. Fixtures and
the temporary queue were removed; source-derived tests remain distinct evidence.

The real system check caught a cancellation hang: the helper survived a forced
stop while the backend blocked waiting. Cleanup now closes input after the reset
request, checks signal failure and bounds all waits. An unclosed transport asks
CUPS to stop the queue. Final Clang analysis has no diagnostics with the unused-
errno checker excluded. The status parser's existing ASan/UBSan result predates
this cleanup-only fix; parser code is unchanged. Do not claim hardware behavior.

Installed signatures, ownership and bytes were checked against a fresh build.
The native queue accepts jobs, defaults to collated sets and is empty/idle. The
obsolete `Sandboxing off` configuration line was removed with backup and a
successful configuration check; the system test had already demonstrated an
active sandbox. No scheduler restart was needed. Recovery backup:
`/private/tmp/hp1020-native-migration-backup-20260928/` (root-only; `paths.json`).
The earlier backup recorded in Git history remains intact. MANIFEST owns binary
hashes, evidence details and recovery instructions; README owns user setup.

Actual system evidence: `/private/tmp/hp1020-system-install-20260928-2/` and
`assets/macos-system-validation.json`. Source-derived sandbox evidence:
`/private/tmp/hp1020-sandbox-3wymtojl/stage/`. Other final logs:
`/private/tmp/hp1020-printing-native-final-20260928.log` and
`/private/tmp/hp1020-setup-native-final-20260928.log`.

For future system checks use `scripts/validate-macos-system.py`. macOS 27.0
ignored the isolated scheduler's alternate file settings; that attempt failed
at queue creation before any test job. The older isolated runner now fails
closed when the settings are ignored and is not a validated lifecycle path.
Do not repeat it on this Mac. Read MANIFEST for the precise failed-run evidence.

Next support step is observation of real printing only when explicitly requested
with the printer connected and freshly power-cycled. Copies/status/recovery on
this device and a fresh Mac remain unverified. Do not ask the owner to test every
edge case. Ordinary app printing uses PDF; legacy PS/EPS needs export to PDF in
a supporting app. Preserve original assets, licenses and the separate research.

## Separate firmware research baseline

September 23 full sequential validation passed **100 consistency checks** and
both suites. Log `/tmp/hp1020-full-raw-parser-bih-20260923.log`, child logs
`hp1020-validation.9CdiDF`. Support changes do not relabel that baseline.

Image decoding, bounded stream integration and original raw-producer/admission
work are retained with exact evidence in `analysis/README.md` and
`analysis/open-firmware-model/next-evidence.md`. Most recent raw chunk-12 evidence:
22 admission cases and two metadata controls in both engines; separate BIH and
page/band metadata explain work dimensions, but raw IRQ mode remains zero and
cursor/prefix ownership remain unresolved. Next trace those changes before the
excluded hardware boundary; do not repeat resolved selector/cancellation work.

Preserve distinctions: 26 completed empty-document lifecycles, six conditional
null reads, 28 bounded retirement cases, 36 native page lifecycles with supplied
FIFO consumption/completion, and 42 fragment/bypass cases. Software image tests
are not extra stock page lifecycles. Physical printing, boot/engine behavior and
power-cycle recovery remain unproven. No research processes are running.
