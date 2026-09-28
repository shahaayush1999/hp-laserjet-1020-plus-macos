# Current handoff

Updated: 2026-09-28. **The open replacement cannot print yet.** Current work is
an owner-authorized redesign of the separate HP-based macOS driver. No printer
enumeration, query, upload or physical test has occurred during this redesign.

## Native Mac driver — in progress

The owner requested a conventional driver and delegated implementation. The
repository now uses Apple's native PDF/raster rendering, a small C raster
adapter linked to the unchanged foo2zjs encoder, and a per-job CUPS backend.
CUPS owns the queue and job lifetime. The private spool/FIFO, Python worker,
launch daemon, descriptor launcher and Homebrew runtime requirements are removed.
Clone/install/uninstall remains the user flow; do not restore apps/packages/ZIPs.

Native tests verify copies/order, selected pages, layout, A4/Letter and original
encoder chunks. Known PDF marks confirm page placement. Separate fake transports
exercise status, paper wait, cancellation/reset, cold firmware readiness,
failures and holds. System libcups independently checks the channel encoding.
No software check establishes real printer feedback or physical output.

Final sequential runs passed **35 native printing checks, 14 setup checks and
three source-derived sandbox checks**. All generated source hashes match.
Static analysis found and prompted fixes to I/O/descriptor error paths; the
post-fix analysis has no diagnostics with the unused-errno checker excluded.
The actual status parser also passed AddressSanitizer/UBSan. Generated reports
own tested hashes; never edit them manually. `MANIFEST.md` owns the details.

The installed setup is still the earlier validated worker-based revision
(b53fcbd). **The native redesign has not been installed.** A staged actual CUPS
scheduler test requires administrator execution because Apple's cupsd binary
is root-executable only. The macOS password prompt was unanswered and cancelled;
`sudo -n` also reports that a password is required. No permission auto-review
rejection occurred. Obtain the owner's physical approval in macOS's dialog,
never a password in chat. Finish all other validation/review first.

The reproducible sandbox suite uses the exact profile-generation functions from
hash-pinned Apple CUPS source, with distinct filter/backend policies. Real Mac
rendering produced twelve pages for four three-page copies; the fake transport
completed the document, and a negative control denied reading a harmless user
file. This ran as the current user, **not `_lp` or actual cupsd**. Final evidence
is in `/private/tmp/hp1020-sandbox-1svgn82u/stage/`, with hashes recorded in
`assets/macos-sandbox-validation.json`. Recovery is in MANIFEST. Old experiments
in `/private/tmp/hp1020-native-driver-eval/` are superseded by this final run.

Next: when the owner is at the Mac, run the real isolated scheduler fixture and
deploy using macOS's administrator dialog. An asynchronous question asks whether
he is available for that physical action; no answer yet. Prepare a **fresh**
`/private/tmp/hp1020-NAME` using `scripts/validate-macos-scheduler.py --prepare`.
Existing staging directories contain direct test events and must not be reused.
The scheduler fixture is staged/compiled but **has not executed as administrator**;
investigate failures and do not count it as validated. It has only a compiled
fake transport, a private socket and temporary roots. Never use the installed
scheduler or real USB backend for this experiment.

Only after that check, update the installed driver with its saved USB URI to avoid
discovery. Restore normal CUPS sandbox settings with backup/config validation:
a legacy `Sandboxing off` line exists in `/private/etc/cups/cups-files.conf`, but
its effective behavior is unestablished. Installer scripts do not alter that
configuration. Verify installed bytes/signatures and an idle queue without
submitting jobs. Hardware tests still require a specific request and fresh power
cycle. Do not ask the owner to exercise every edge case manually.

Direct PS/EPS support was deliberately removed: macOS's old conversion API
returned success with zero bytes, then failed in the CUPS environment. The draft
was discarded. Normal apps already use PDF; legacy files must be exported to PDF
in a supporting app. The test-page script uses native text conversion. This
limitation and migration cleanup are documented in README. Preserve stock assets,
GPL source/licenses and the previous recovery backup listed in Git history.

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
