# Agent Notes

This repo documents and packages the working HP LaserJet 1020 Plus macOS workaround on Aayush's machine.

## What This Is

The HP LaserJet 1020 Plus is a host-based USB printer. On modern macOS, the built-in HP/PCL drivers are not enough. The printer needs:

- `sihp1020.dl` firmware sent after power-on
- PDF/PostScript converted through `foo2zjs-wrapper`
- final ZjStream bytes sent over the macOS CUPS USB backend

The normal CUPS filter path was blocked by macOS sandboxing when trying to run Homebrew Ghostscript/GNU sed. The solution here keeps the visible printer queue normal, but moves the actual conversion/send work into a root LaunchDaemon outside the CUPS sandbox.

## Installed Shape

Queue:

- `HP_LaserJet_1020_Plus`
- device URI: `hp1020queue://localhost`

Privileged files:

- `/usr/libexec/cups/backend/hp1020queue`
- `/usr/libexec/cups/filter/hp1020passthrough`
- `/Library/Printers/hp1020/hp1020-root-spool-worker`
- `/Library/Printers/hp1020/HP-LaserJet_1020-Plus-hp1020zjs.ppd`
- `/Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist`
- `/private/var/spool/cups/tmp/hp1020queue`

User files:

- `/Users/aayush/bin/hp1020-print`
- `/Users/aayush/.local/share/hp1020/foo2zjs`
- `/Users/aayush/.local/share/hp1020/foo2zjs-wrapper`
- `/Users/aayush/.local/share/hp1020/foo2zjs-pstops`
- `/Users/aayush/.local/share/hp1020/sihp1020.dl`

Logs:

- `/Library/Printers/hp1020/spool-worker.log`
- `/Library/Printers/hp1020/launchd.out.log`
- `/Library/Printers/hp1020/launchd.err.log`

Bundled source/assets:

- `assets/runtime/` has the known-good runtime currently used on the machine.
- `assets/firmware-source/` has the firmware artifacts produced while getting the printer working.
- `vendor/foo2zjs-source/` has the source snapshot used to build the runtime.
- `MANIFEST.md` has dependency versions and checksums.
- `REDISTRIBUTION.md` explains the public/private redistribution posture.

## Normal Debug Loop

1. `scripts/diagnose.sh`
2. Check `lpinfo -v` includes `usb://Hewlett-Packard/HP%20LaserJet%201020?serial=S43VYTP`.
3. Check `lpstat -p HP_LaserJet_1020_Plus -l`.
4. Tail `/Library/Printers/hp1020/spool-worker.log`.
5. If USB is missing/offline, ask the user to power-cycle and replug USB before changing code.

## Important Behavior

- Jobs may vanish from Print Center quickly because CUPS only hands them to the worker. The worker log is the source of truth after handoff.
- The printer loses firmware on power cycle. `hp1020-print` sends firmware before each document.
- The macOS USB backend sometimes waits after data is sent. The script has timeouts so the worker does not wedge forever.
- If the queue is paused, run `cupsenable HP_LaserJet_1020_Plus` and inspect logs before retrying repeatedly.

## Reinstall / Cleanup

Use:

- `scripts/install.sh`
- `scripts/uninstall.sh`

Use `scripts/rebuild-runtime-from-vendor.sh` only if you need to rebuild the foo2zjs runtime. The normal install path does not require rebuilding.

Do not manually delete random CUPS files unless the uninstall script fails and you know which installed path you are removing.
