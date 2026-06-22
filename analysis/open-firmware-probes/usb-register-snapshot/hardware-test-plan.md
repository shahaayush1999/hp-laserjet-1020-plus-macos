# USB Register Snapshot Hardware Test Plan

This is the intermediate custom firmware test between the pure idle probe and
the write-capable USB marker draft.

It is not a print test. It uploads only the open USB register snapshot probe and
sends no PDF, PostScript, ZjStream, engine, video, motor, fuser, or paper-feed
data.

## Goal

Answer one narrow question:

```text
Can open code safely read the mapped USB controller registers after upload and
remain mechanically quiet?
```

The snapshot currently is not host-readable. The useful hardware signal is
still safety/acceptance: upload bytes sent, printer stays quiet, power-cycle
recovers.

## Current Offline Evidence

The probe currently passes these static gates:

- HP-shaped boot-probe layout profile
- general safety scan: no engine/video/function failures
- USB probe contract: only mapped `0xb300....` USB registers
- USB MMIO access scan: 14 mapped USB reads, 0 USB writes

## Test Order

1. Confirm normal stock firmware preload still works.
2. Confirm the open idle probe still uploads quietly.
3. Run this read-only USB snapshot probe.
4. Only if all of the above are quiet/recoverable, consider the marker draft.

## Script

Dry run:

```sh
scripts/run-usb-snapshot-probe-hardware-test.sh --dry-run
```

Real upload, only when the printer is connected and freshly power-cycled:

```sh
HP1020_ALLOW_USB_SNAPSHOT_UPLOAD=1 \
  scripts/run-usb-snapshot-probe-hardware-test.sh \
  --upload \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...' \
  --i-understand-this-uploads-usb-snapshot-probe
```

Do not run this through the normal print queue. Do not use Chrome/Preview. Do
not send a PDF.
