# Private macOS installer

This packages the working HP-firmware/foo2zjs printing path for another Apple
Silicon Mac. It is independent of the open firmware research. Building and
validating it do not install anything, start services, enumerate USB or print.

The single file to copy is
`dist/HP-LaserJet-1020-Plus/HP-LaserJet-1020-Plus-1.0.0-Apple-Silicon.dmg`.
Opening it shows `Install HP LaserJet 1020 Plus.pkg`,
`Remove HP LaserJet 1020 Plus.pkg` and the short `Start Here.txt` instructions.
No internet, Homebrew, Python, Xcode or source checkout is needed on the
recipient's Mac. It installs once on each Mac and can then run with the disk
image ejected. Removal uses the included remover, not deletion of the download.

## Build and check

On an Apple Silicon build Mac with Python 3 and Xcode command-line tools:

```sh
python3 scripts/build-macos-package.py
python3 scripts/validate-macos-package.py
```

The builder verifies pinned GhostPDL 10.07.0 and GNU sed 4.10 source archives,
builds Ghostscript and GNU sed against macOS system libraries, and builds
foo2zjs with the preserved full JBIG encoder in `vendor/foo2zjs-source`.
It does not use the experimental open decoder or research toolchains.
Ghostscript contains its initialization files, fonts and color profiles in ROM;
OCR, fontconfig, X11 and CUPS integration are disabled. PDF/PostScript rendering
and the PBM output used by the existing wrapper remain enabled.

All executables target arm64/macOS 11.0; the builder verifies their deployment
target, dependencies and ad-hoc signatures. That minimum is a build requirement,
not evidence of tests on every macOS release. The installer also requires the
system CUPS USB backend. Full installation and physical output on the recipient
Mac still need verification. Do not run this installer on Aayush's working setup
as an offline test.

`--sources DIR`, `--work DIR` and `--output DIR` select disposable build locations.
`--reuse-runtime` is allowed only when the saved build recipe and every binary
hash/signature still match. It does not skip packaging or validation. Pin hashes
originate from the preserved Homebrew formulae used by the working setup; every
download is verified before extraction. Sources and build scripts accompany the
installed files under `/Library/Printers/hp1020/Sources`. Extract
`hp1020-package-source.tar.gz` into an empty directory, then run its builder with
`--sources` pointing to the directory containing the two dependency archives.
Build logs remain under the selected work directory.

The builder creates a compressed HFS+ disk image containing only the two packages
and recipient instructions. The validator checks its integrity, mounts it read-only
without opening Installer, compares the contents with the checked packages and
instructions byte for byte, and detaches it. It does not inspect physical disks.
The standalone packages remain in the output folder for agent diagnostics.

The output's `build-info.json` records input and executable hashes;
`validation.json` records only executed offline checks, package hashes and the
disk image hash. `SHA256SUMS` covers both packages and the disk image.
The validator also preserves `packaging/macos/validation-report.json` in Git;
this generated report is excluded from the source archive to avoid self-hashing.
Generated packages are ignored by Git. Rebuild them from the committed recipe.

Offline validation includes four two-page conversions (PDF/PostScript,
A4/Letter, one/two copies), actual package expansion and byte/ownership checks,
disk image contents, and isolated installation/removal/job-flow fixtures.
The September 27 baseline ran on macOS 27. For a common renderer, compressed image chunks match the original
foo2zjs runtime exactly. Comparing the bundled renderer with the installed
Homebrew Ghostscript 10.07.0 found 195 changed gray samples on the first page of
each sample format, all at single-pixel text edges; the second pages were exact.
Decoded geometry is 4800 × 6824 in these A4 fixtures. The validator checks every
decoded sample, requires all differences to lie on text edges, and preserves the
counts/bounds. The different FreeType builds are a possible cause, not an isolated
proof. No claim of byte-identical rendering across arbitrary documents is made.
These are offline checks, not installation or physical printing evidence.

## Installation and ownership

The standard macOS Installer requests administrator permission and installs:

- All runtime binaries and the original firmware under `/Library/Printers/hp1020`.
- The private CUPS backend and passthrough filter under `/usr/libexec/cups`.
- One root LaunchDaemon and the `HP_LaserJet_1020_Plus` printer queue.
- Root-owned job directories under `/private/var/spool/cups/tmp/hp1020queue`.

There are no user-home references, Homebrew paths, fixed printer serial numbers,
firmware uploads or USB discovery in install/remove scripts. Only an actual
submitted job reaches the system USB backend. Discovery requires exactly one
matching HP 1020/1020 Plus. The original HP firmware is preloaded for each job,
as in the established working setup.

The package refuses to overwrite the older manually installed setup or an
unrelated queue with the same name. Reinstalling this package requires an idle
queue. It never changes the default printer, shares a queue, or changes global
CUPS logging. Its remover recognizes only the packaged installation marker.

The backend runs as root (mode 0700, per CUPS backend documentation), writes a
complete job into a private incoming directory and atomically publishes it.
The worker claims it before sending. Completed document files are removed;
failed or interrupted jobs are retained privately and never automatically
reprinted. Print Center reports handoff, not observed paper delivery. A USB
timeout is recorded as uncertain rather than asserted to be successful printing.
The worker log is `/Library/Printers/hp1020/spool-worker.log`.

A4, Letter and copy counts are forwarded. Other printer features have not been
added. The existing conversion wrapper receives only the established HP 1020
flags. Its packaged copy adds Bash pipeline-failure propagation, quotes the
input filename and returns success explicitly after successful cleanup. The
original wrapper/runtime, manual installer and installed printing setup are
preserved unchanged.

## Distribution

This is a private family handoff with the original HP firmware, not an official
HP product or a public release. Corresponding source and GPL/AGPL license texts
are included in the installer. Retain the source archives and third-party notices.
See the repository's existing `NOTICE.md` and `REDISTRIBUTION.md`.

The package is unsigned and not notarized. It may need the per-file Open Anyway
approval described in [Apple's guidance](https://support.apple.com/102445).
Do not disable Gatekeeper. A publicly distributed installer would additionally
need the appropriate Developer ID signing/notarization workflow and a separate
review of firmware distribution terms.

Apple references: [package distribution](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution),
[CUPS backend permissions](https://apple.github.io/cups/doc/man-backend.html).
