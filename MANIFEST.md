# Runtime and verification records

## Native macOS printing path

The September 28 redesign uses macOS's CUPS raster-driver interface:
`application/pdf → cgpdftoraster → rastertohp1020 → hp1020 backend → Apple USB backend`.
Native Mac image/text filters feed the same PDF path. There is no private queue,
launch daemon, Python worker, shell conversion pipeline or Homebrew runtime.
CUPS owns scheduling, job lifetime, serialization and cancellation.

`scripts/rebuild-runtime-from-vendor.sh OUTPUT_DIRECTORY` builds two arm64
binaries using Apple's compiler and system libraries. `rastertohp1020` links the
unchanged foo2zjs/JBIG source objects; only the original command's main symbol is
renamed at compilation. It supplies one checked monochrome PBM page at a time to
the original encoder functions. This does not install the experimental firmware
or substitute a new compression implementation. Original runtime files under
`assets/runtime/`, vendor sources, firmware and licenses remain unchanged.

The raster PPD requests packed, black-is-one, 1200×600 input. `cupsManualCopies`
and `cupsMaxCopies: 1` make Apple's renderer expand all copies. The encoder and
USB backend each use one copy. Queue defaults request complete collated sets.
A4 uses the existing encoder wrapper's 9920×7016 full-sheet geometry; Letter uses
10200×6600. Both keep the original 192×96 pixel crop on each side. The PPD's
fractional dimensions therefore yield 9536×6824 and 9816×6408 imageable rasters.
The adapter validates dimensions, colors, depth, copy count and resolution; it
does not silently rescale or reinterpret incompatible raster data.

The raster filter resides in `/Library/Printers/hp1020/runtime/`, along with the
stock firmware. Its PPD names the absolute filter path. The executable backend
is `/usr/libexec/cups/backend/hp1020`, installed with permissions that let CUPS
run it as `_lp`. The queue's `hp1020:` URI retains the selected Apple's `usb:`
address. The backend performs no discovery; the installer obtains or accepts
that exact address. A small compatibility shell command only submits via `lp`.

Before opening the transport, the backend captures and validates the complete
encoded document, including chunk/item bounds, page boundaries and END_DOC.
Failed rendering cannot send a partial document. CUPS temporary files are
unlinked immediately after creation and retain no additional document archive.
A 1 GiB encoded-job bound prevents unbounded extra spool use. One native USB
backend child carries standard fd-3 back-channel and fd-4 side-channel traffic.
No root renderer or independent service runs in the background.

A fresh device ID must identify the HP 1020. Nonempty FWVER controls stock
firmware loading; after a cold load, a new connection must confirm FWVER before
the document is sent. Original PJL status requests are preserved. Only JOB/EOJ
names change to a random token. Known paper, cover, jam and toner feedback is
translated into standard CUPS reasons. Physical completion requires the matching
job name and exact page count. Missing feedback is explicitly unconfirmed.
Malformed, stale and unknown messages cannot clear known attention conditions.
Apple's constant ONLINE GET_STATE response is not used to infer paper status.

Before connection, jobs wait for reconnection and remain cancellable. Connected
ID, transfer, close and progress timeouts bound failures; known paper/cover/jam
conditions can wait for intervention. Failed transfer exits with CUPS HOLD, so
uncertain output is not automatically replayed. Cancellation requests the
standard USB soft reset, then closes the input pipe so Apple's backend can exit
normally. Apple's reset handler drains queued input before resetting. Every
cleanup wait is bounded; a failed forced termination cannot enter a blocking
wait. If the transport cannot close, the backend requests that CUPS stop the
queue instead of overlapping another connection. CUPS owns the process group.
Device buffer-reset effectiveness still needs physical verification.

## Installation and migration

The user flow remains clone, install script and uninstall script. No app,
package installer or downloadable runtime bundle is introduced. All elevated
inputs are staged first: Apple's privileged AppleScript helper cannot read the
user's protected Documents repository. Replacement runs in a child shell; the
parent's rollback trap catches even fatal zsh expansion failures. Backups cover
the old runtime, legacy filters/backend/daemon, actual queue PPD and new backend.
Rollback restores the prior URI, PPD, enabled state and acceptance.

Pending CUPS work and visible/hidden legacy worker jobs block migration. Native
binary signatures/execution and installed PPD references are checked before the
queue is enabled. Only then are legacy components retired. Old package ownership
records are honored: pre-existing or newly shared Homebrew packages are kept;
cleanup failures preserve the record for retry. Failed queue removal retains the
driver files. Neither script changes the system CUPS sandbox configuration.

Direct PostScript is no longer advertised. A native CGPSConverter feasibility
probe returned success with **zero output bytes** in the ordinary environment
and failure in CUPS's environment. This is not a working conversion. The draft
was removed; current macOS lacks that old conversion capability. Legacy PS/EPS
must be exported to PDF using a supporting app. Normal Mac app printing already
uses PDF. The test-page script uses native text conversion.

## Validation and current deployment

Run offline suites **sequentially**, using Python from Apple's Command Line Tools
or an existing Python installation (Python is a test tool, not a driver dependency):

```sh
python3 scripts/validate-macos-printing.py
python3 scripts/validate-macos-setup.py
```

The printing suite exercises real native renderers and encoder output, including
copies, order, ranges, odd/even pages, layout and paper. Separate processes
simulate USB responses over the actual fd-3/fd-4 interface. Tests cover firmware
readiness, paper-out, disconnection/reconnection, cancellation, missing status,
malformed/truncated documents and unsupported settings. System libcups supplies
an independent side-channel codec. Pixel placement and original encoder chunks
are compared independently. Setup tests isolate every administration, queue and
package operation, including inaccessible source files, fatal shell errors,
legacy migration, package ownership and failed-update restoration.

`assets/macos-printing-validation.json` and
`assets/macos-setup-validation.json` contain generated results and exact source
hashes. Do not patch hashes manually. Final sequential runs passed **35 native
printing checks and 14 setup checks**, including failures at the final queue
enable/accept gates. All hashes match. After I/O/remapping fixes, Clang static
analysis reports no diagnostics with the unused-errno checker disabled; the
actual status parser also passes AddressSanitizer/UndefinedBehaviorSanitizer.

On macOS 27.0 (26A428), the attempted isolated scheduler printed `-s ignored.`
and did not apply the alternate backend/log paths. Queue creation failed before
any test job was submitted. `scripts/validate-macos-scheduler.py` now refuses to
start a scheduler when that diagnostic or missing private log reveals that its
settings were not applied. Its isolated execution remains unvalidated; its
ordinary-user `prepare` function also builds fixtures for the other suites.

`scripts/validate-macos-system.py --prepare /private/tmp/hp1020-NAME` prepares the
replacement system test. Run that directory's `run.py --exercise` as administrator
through macOS's password dialog. It adds a uniquely named temporary queue and
native backend to the installed scheduler. That backend can execute **only its
compiled fd-only simulator**, never Apple's USB backend. It does not discover
devices or change an existing queue or global CUPS settings. Test files and the
temporary queue are removed even on failure; raw evidence stays in staging.

The actual scheduler passed **five lifecycle checks**: four collated three-page
copies, five queued documents with one active transport, paper recovery and
ordered completion, cancellation with no surviving helper before the next job,
and transfer failure held without replay. The processes ran as `_lp` (UID 26).
The scheduler's generated profiles were captured. A harmless fixture writable
by an ordinary `_lp` process was denied by the CUPS sandbox, establishing that
the policy was actually applied. The generated result is
`assets/macos-system-validation.json`; its `raw_evidence` directory preserves
the exact source map, generated profiles, queue snapshots and encoded fixtures.

The first system run caught a real cancellation defect missed by the earlier
source-derived sandbox check: the native child stayed alive while the backend
blocked in `wait4` after a force-stop attempt. A same-UID stop outside the CUPS
sandbox succeeded. The fix closes input after reset, checks forced-termination
failure and bounds every wait. The final system run confirms cancellation and
subsequent job progress without administrator process cleanup. The failed run
and stack trace remain under `/private/tmp/hp1020-system-install-20260928-1/`.

Separately, `scripts/validate-macos-sandbox.py` passed **three checks** on the final
sources. It compiles the exact `cupsdCreateProfile` and quoting functions from
hash-pinned Apple CUPS source with strict, root-mode policy generation and no test
root exemption. It applies separate filter/backend profiles to actual native
conversion and a native fake transport. Four three-page copies produce twelve
pages; the mock confirms completion. A harmless repository-file read is denied
as a negative control. These processes run as the current user, not `_lp` or an
actual scheduler. Keep that evidence separate from the actual system test above.

The generated report is `assets/macos-sandbox-validation.json`; raw profiles,
logs, compiler input and output are retained at its `raw_evidence` path. Recovery:

```sh
curl --fail --location https://raw.githubusercontent.com/apple/cups/master/scheduler/process.c -o /tmp/hp1020-cups-process.c
python3 scripts/validate-macos-sandbox.py /tmp/hp1020-cups-process.c
```

The validator requires SHA-256
`0074e1403f3e3c1c5e789af10ab3b75a72a0a13b188446e84e2054bd322295b7`;
a changed download fails instead of silently changing the tested policy. If it
moves, recover the matching revision from Apple's history. The invoking shell
must permit `sandbox-exec`; no administrator password is required for this test.
Run it after the other suites, never concurrently.

Original `assets/firmware-source/sihp1020.img` bytes were also checked directly:
`Hewlett-Packard`, `HP LaserJet 1020` and the MFG/MDL/FWVER format string are present.
This supports the expected loaded-firmware identity, not a new boot-ROM/device
observation. No live identity request occurred.

After all four suites passed sequentially, the owner-authorized installation
succeeded using the saved USB URI without discovery. The old worker, daemon,
bridge backend/filters and per-user runtime were removed. The queue uses the
native backend, accepts jobs, defaults to collated sets and is idle with no
pending jobs. Code signatures and root ownership were checked; installed
binaries and stock firmware exactly match a fresh production build, and the
installed driver PPD matches its source. The actual queue PPD's native filter
reference and host-copy attributes were checked after installation. No real
print job, device query or firmware upload occurred.

The obsolete `Sandboxing off` line was removed with backup and a successful
default `cupsd -t` check. No service restart was needed: the preceding actual
system test had already demonstrated sandbox enforcement despite that legacy
line. Its historical effective behavior is not inferred. The old installation
and configuration are preserved in the root-only recovery directory
`/private/tmp/hp1020-native-migration-backup-20260928/` (`paths.json` maps backups).
The earlier recovery backup listed in Git history is also retained.

Final installed SHA-256 values, also saved beside the comparison build at
`/private/tmp/hp1020-native-installed-build-20260928/installed-hashes.json`:

| Component | SHA-256 |
| --- | --- |
| rastertohp1020 | c41248b039f6719025f7112daeb54f653bd2a03cd228ff1fa403ba089943e134 |
| hp1020 backend | ce381c3afcb38e5ab2939d4e79a61369e7d462684a05bc316917aa736d7e0f6b |
| sihp1020.dl | 133b21fe0cb24bfe53e2eff2f00a82cce4beb970749049661ade7a6801f22663 |

Do not describe simulated device feedback as hardware, queue UI, fresh-Mac or
physical-output proof. All reported hashes belong to their actual executed
sources; never update a report's hashes by hand after editing.

The separate September 23 firmware-research baseline remains unchanged; use
`analysis/README.md` for its hashes and recovery instructions.

## Primary integration references

- [CUPS raster API](https://openprinting.github.io/cups/doc/api-raster.html)
- [CUPS filter status/channels](https://openprinting.github.io/cups/doc/api-filter.html)
- [Backend arguments/results](https://www.cups.org/doc/man-backend.html)
- [PPD attributes](https://www.cups.org/doc/spec-ppd.html)
- [Apple USB backend](https://github.com/apple/cups/blob/master/backend/usb-darwin.c)
- [Apple scheduler profiles/process groups](https://github.com/apple/cups/blob/master/scheduler/process.c)
- [HP PJL reference](https://h10032.www1.hp.com/ctg/Manual/bpl13208.pdf)
- [Apple PS/EPS support change](https://support.apple.com/en-ie/108775)
- Preserved `hplj10xx_gui.tcl`, `hplj1000`, `foo2zjs.c` and its wrapper.

For standalone filter experiments always pass `cupsfilter -p PPD`; `-d` only
sets a printer name and does not load its PPD. Omitting `-p` previously exposed
an error-reporting crash in the system utility. [Apple's source](https://github.com/apple/cups/blob/master/scheduler/cupsfilter.c)
confirms the argument distinction.
