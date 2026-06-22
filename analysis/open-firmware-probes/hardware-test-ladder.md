# HP 1020 Open Firmware Hardware Test Ladder

This is the guarded order for non-printing open-firmware tests. Each real stage
requires a fresh printer power cycle first. None of these stages sends a PDF,
PostScript, ZjStream page, fuser command, motor command, or raster/video stream.

## Stages

1. Stock identity/status calibration
   - Confirm macOS sees the direct `usb://Hewlett-Packard/...` backend URI.
   - Optionally run the non-printing PJL/status query against stock firmware.

2. Idle probe
   - Uploads open firmware that parks immediately.
   - Expected result: no paper movement, no sounds, no identity improvement.
   - Already tested once: backend sent bytes and printer stayed green/quiet.

3. USB register snapshot probe
   - Uploads open firmware that reads mapped USB registers into RAM and idles.
   - Expected result: no paper movement; this mainly checks that USB reads are not disruptive.

4. USB marker draft
   - Uploads open firmware that tries to answer a product-string request with `HP1020 OPEN MARKER`.
   - Expected result if successful: host-side USB identity may expose the marker string.
   - Expected result if incomplete: no visible change, possible temporary USB silence until power cycle.

## One-Stage Harness

Dry-run all gates:

```sh
scripts/run-open-firmware-usb-test-ladder.sh --dry-run
```

Real run for one selected stage:

```sh
HP1020_ALLOW_OPEN_FIRMWARE_LADDER_UPLOAD=1 \
  scripts/run-open-firmware-usb-test-ladder.sh \
  --upload \
  --stage marker \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...' \
  --i-understand-this-uploads-open-firmware
```

The harness captures USB identity before and after the selected stage under:

```text
analysis/open-firmware-probes/hardware-test-runs/
```

Power-cycle the printer before normal printing or before another custom firmware
stage.
