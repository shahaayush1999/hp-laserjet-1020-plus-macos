# HP LaserJet 1020 Plus on macOS

This repo packages the working local macOS setup for an HP LaserJet 1020 Plus.

The printer is old and host-based. It needs two things macOS does not provide out of the box:

- firmware upload after power-on
- conversion from PDF/PostScript into the printer's ZjStream format

The setup makes the printer appear as a normal macOS printer named `HP_LaserJet_1020_Plus`, while a small background worker handles the firmware/conversion/USB send path.

## Current Working Flow

```text
Chrome / Preview / app print dialog
  -> macOS CUPS printer queue: HP_LaserJet_1020_Plus
  -> CUPS filter: hp1020passthrough
  -> CUPS backend: hp1020queue
  -> handoff folder: /private/var/spool/cups/tmp/hp1020queue
  -> LaunchDaemon worker: /Library/Printers/hp1020/hp1020-root-spool-worker
  -> user print script: ~/bin/hp1020-print
  -> foo2zjs-wrapper + firmware + macOS USB backend
  -> HP LaserJet 1020
```

This is a compatibility workaround, not an official HP driver. It is intentionally explicit and removable.

## Install

Requirements:

- macOS with CUPS
- Homebrew Ghostscript and GNU sed. The installer will try to install these automatically if Homebrew is available:

```sh
brew install ghostscript gnu-sed
```

Then run:

```sh
./scripts/install.sh
```

The install script prompts once for macOS administrator permission and installs the privileged CUPS/LaunchDaemon pieces in one batch.

## Test

```sh
./scripts/print-test.sh
```

You can also print normally from Chrome, Preview, etc. Select `HP_LaserJet_1020_Plus`.

## Diagnose

Basic checks without admin prompt:

```sh
./scripts/diagnose.sh
```

Protected spool details with one admin prompt:

```sh
./scripts/diagnose.sh --admin
```

Useful signals:

- `lpinfo -v` should show `usb://Hewlett-Packard/HP%20LaserJet%201020?serial=S43VYTP`.
- `lpstat -p HP_LaserJet_1020_Plus -l` should show the queue as enabled/idle when not printing.
- `/Library/Printers/hp1020/spool-worker.log` should show firmware bytes and document bytes sent.

If the queue accepts a job but no paper moves, first unplug/replug USB and run `diagnose.sh`.

## Uninstall / Cleanup

```sh
./scripts/uninstall.sh
```

This removes:

- CUPS printer queue `HP_LaserJet_1020_Plus`
- CUPS backend `/usr/libexec/cups/backend/hp1020queue`
- CUPS filter `/usr/libexec/cups/filter/hp1020passthrough`
- PPD files for the queue
- LaunchDaemon `/Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist`
- helper folder `/Library/Printers/hp1020`
- handoff spool folder `/private/var/spool/cups/tmp/hp1020queue`
- user print script `~/bin/hp1020-print`
- user runtime folder `~/.local/share/hp1020`

## Repo Contents

- `assets/runtime/`: working local foo2zjs runtime files and `sihp1020.dl` firmware
- `assets/firmware-source/`: firmware artifacts used while getting this working
- `vendor/foo2zjs-source/`: source snapshot used to build the bundled foo2zjs runtime
- `MANIFEST.md`: dependency versions, bundle sizes, and SHA-256 checksums
- `files/cups/backend/hp1020queue`: CUPS backend that hands jobs to the worker spool
- `files/cups/filter/hp1020passthrough`: CUPS filter that preserves the original PDF/PS
- `files/ppd/`: PPD used by the macOS queue
- `templates/`: rendered by the installer with the current user home and USB device URI
- `scripts/install.sh`: install/reinstall
- `scripts/uninstall.sh`: remove everything installed by this repo
- `scripts/diagnose.sh`: state/log inspection
- `scripts/print-test.sh`: one-page test print
- `scripts/rebuild-runtime-from-vendor.sh`: rebuilds `assets/runtime/` from `vendor/foo2zjs-source/`
- `scripts/query-hp1020-pjl-status.sh`: guarded non-printing PJL/status query harness for firmware analysis
- `REDISTRIBUTION.md`: practical notes on private vs public redistribution risk
- `OPEN_SOURCE_OPTIONS.md`: explains existing open source options and why firmware loading is unavoidable

## Rebuild Runtime

The normal installer uses the bundled known-good runtime. If a future agent wants to rebuild it:

```sh
brew install ghostscript gnu-sed jbigkit
./scripts/rebuild-runtime-from-vendor.sh
```

## Licensing Note

The foo2zjs code is GPLv2; see `assets/licenses/foo2zjs-COPYING`.

The HP firmware blob `assets/runtime/sihp1020.dl` and firmware artifacts under `assets/firmware-source/` are included so this personal repo is self-contained. Do not publish this repo publicly without reviewing the firmware redistribution terms. A private repo or local handoff repo is the safer default.
