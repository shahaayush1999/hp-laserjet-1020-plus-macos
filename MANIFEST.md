# Runtime and verification records

The installer obtains `ghostscript`, `gnu-sed` and the canonical `python@3.14`
formula through Homebrew. It compiles foo2zjs from `vendor/foo2zjs-source/` and
`files/macos/hp1020-usb-run.c`, then copies the original `sihp1020.dl` from
`assets/runtime/`. Reference runtime files, vendor sources and licenses remain
unchanged. No replacement firmware is installed.

The runtime lives in `/Library/Printers/hp1020/`. Package ownership is recorded
under `~/.local/state/hp1020/`; removal preserves pre-existing/shared packages and
retains failed-cleanup records for retry. No global Homebrew `autoremove` is run.
Python uses its canonical formula name for ownership and its explicit interpreter
path; Homebrew aliases are not ownership identities.

`scripts/rebuild-runtime-from-vendor.sh OUTPUT_DIRECTORY` builds the native
runtime without installation or printer contact. Its wrapper changes quote
filenames and propagate conversion failures. Ghostscript/GNU sed are not built
or bundled by this script.

## September 28 printing corrections

The previous backend discarded CUPS copy/options arguments, returned success
before the worker ran, and had no feedback or cancellation connection. The old
PPD bypassed Apple's page-selection/copy filters. The old worker also removed
another worker's directory lock, retained document archives, and loaded firmware
before every job. Previous direct encoder `-n2` checks did not exercise these
behaviours. Read-only inspection confirmed the same defects in the old installed
setup; historical reports are not proof that these paths worked.

The revised PPD routes PDF/PostScript through Apple's native PostScript and
`pstops` filters before the marked passthrough output. `cupsManualCopies` plus
`cupsMaxCopies` allows host-rendered collated sets and uncollated PostScript
`NumCopies`. The queue defaults to complete collated document sets. Encoder and
USB copies stay one to avoid multiplying prepared pages again. A4/Letter options
reach the encoder; unsupported paper or duplex settings fail before USB.

The zsh CUPS backend atomically publishes a private document, NUL-separated
ticket and reply FIFO. It remains attached until the Python worker replies;
heartbeats, INFO/STATE messages, holds and cancellation reach CUPS. A missing
worker holds after 60 seconds. Worker restarts hold already-started jobs rather
than replaying uncertain output. An OS file lock serializes workers and jobs.
Native conversions run in cancellable process groups with isolated scratch paths.
The compatibility command now submits through the same CUPS queue.

The service runs as `_lp`, including conversion and the system USB backend.
Homebrew programs are never executed as root by the service. The C launcher maps
the required descriptors to CUPS fd 3/4. Apple's USB backend provides device ID,
back-channel bytes and side-channel reset; its GET_STATE response is a constant
ONLINE and is deliberately not used to infer paper status. FWVER in a fresh
device ID controls stock firmware loading. A timeout/disconnection during loading
is not success: the next connection must report FWVER before a document is sent.
Firmware is no longer loaded unconditionally before each document.

The original encoder's PJL status requests are retained; only JOB/EOJ names are
changed to a unique per-job token. Bounded response parsing maps known paper,
cover, jam and toner codes to CUPS reasons. Completion requires matching job name
and page count. Unrelated/malformed responses do not clear known errors or finish
a job. Missing correlated feedback produces an explicit unconfirmed-completion
warning. Transfer failures hold without automatic retry. Disconnection before
transfer leaves work queued for reconnection. Cancellation requests the native
USB soft-reset interface, then terminates the entire process group, including a
backend that ignores SIGTERM. Actual device buffer reset remains unverified.

New jobs retain no extra document archive. Temporary copies are removed on
completion/failure/cancellation and after worker restart; the worker log rotates.
Updates check pending CUPS and legacy worker jobs, back up replaced components,
and require a live service readiness marker before enabling the queue. Failed
replacement restores prior files. Failed queue removal retains the runtime and
dependency record for retry.

The first real update attempt exposed a macOS privacy boundary: the elevated
helper could not read the repository in Documents. A fatal zsh glob also skipped
its own EXIT trap. The previous queue files/service were restored from the saved
backup and verified before retry. Installation now stages every input as the
normal user and performs replacement in a child shell so the parent can roll
back fatal expansion failures. The setup suite reproduces an inaccessible source
directory and the fatal expansion case, including restoration of the actual
queue PPD and previous acceptance state.

Sources for the integration contract are the CUPS [backend arguments and result
codes](https://www.cups.org/doc/man-backend.html), [filter status and channel
API](https://openprinting.github.io/cups/doc/api-filter.html), [PPD attributes](https://www.cups.org/doc/spec-ppd.html),
Apple's [USB backend](https://github.com/apple/cups/blob/master/backend/usb-darwin.c)
and [pstops](https://github.com/apple/cups/blob/master/filter/pstops.c), the
[HP PJL reference](https://h10032.www1.hp.com/ctg/Manual/bpl13208.pdf), and preserved
`hplj10xx_gui.tcl`, `hplj1000` and `foo2zjs.c`. These contracts and simulations do
not establish this printer's real responses or physical completion.

## Reproduce offline checks

Run sequentially on an Apple Silicon Mac with Ghostscript/GNU sed installed:

```sh
python3 scripts/validate-macos-printing.py
python3 scripts/validate-macos-setup.py
```

The printing validator exercises real macOS PDF/PostScript filters, Ghostscript,
encoder, backend, worker and fd launcher. It compares page hashes/order and
ZjStream copy/paper fields, exercises collated/uncollated copies, selection/layout,
five jobs, cancellation, stalls, disconnection, firmware readiness, malformed
status, worker loss and restart. A separate fixture uses the system CUPS library
as the independent fd-4 codec. All USB processes and responses are simulated;
worker timeouts are accelerated except the actual 60-second missing-worker check.

The setup validator compares four conversions against every original encoder
chunk and exercises isolated Homebrew/admin/CUPS fixtures, ownership, retries,
rollback and service readiness. No actual package, launchd or queue changes occur.
Reports `assets/macos-printing-validation.json` and
`assets/macos-setup-validation.json` retain exact tested source hashes and scope.
Never update these hashes manually. Native CUPS scheduler/GUI, actual device
feedback, soft reset, fresh-Mac installation and physical printing are outside
these offline checks. New changes require rerunning the affected validator.

Latest complete sequential support run: **38 printing checks and 17 setup
checks**, all matching their recorded source hashes. The separate firmware
research baseline was not rerun or relabeled by this support work.

Separately, the corrected installer completed on the owner's Apple Silicon Mac
on September 28 using its saved URI, without USB discovery or a submitted job.
Installed backend/filter/PPD/service, stock firmware and license bytes matched
the repository, both native binary signatures verified, and launchd/`ps` showed
the service running as `_lp`. The enabled, accepting queue was idle, its default
was complete collated sets, and the service had no child process. The earlier
per-user helper/runtime was retired. Existing Homebrew dependencies were reused.

An additional generated two-page PDF passed through the installed PPD and actual
`cgpdftops → pstops → hp1020passthrough` chain with four copies, then the installed
encoder. Output page hashes proved four complete ordered sets (eight pages),
DMCOPIES one and A4 metadata, entirely into temporary files. For this check use:

```sh
cupsfilter -p /Library/Printers/hp1020/HP-LaserJet_1020-Plus-hp1020zjs.ppd -e \
  -m printer/HP_LaserJet_1020_Plus -n 4 -o Collate=True fixture.pdf
```

`-d` alone does not supply a PPD: this Mac's utility crashed in its error-reporting
path when the PPD was omitted; Apple's [source](https://github.com/apple/cups/blob/master/scheduler/cupsfilter.c)
confirms `-d` only sets the name. The corrected invocation passed. These deployment observations are not
added to the offline reports as hardware or fresh-install successes.

Firmware research retains its separate hashes and recovery instructions in
`analysis/README.md`. Abandoned app/package/bundle machinery stays removed;
Git retains that history. End users only need the clone/install/uninstall flow.
