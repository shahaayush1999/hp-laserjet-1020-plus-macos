# Minimal Idle Probe Hardware Test Plan

This is the first custom-firmware hardware test, if we choose to run it.

It is not a print test. It uploads only the open idle probe and sends no document bytes.

## Goal

Answer one question:

```text
Does the printer accept and branch into our uploaded non-HP Xtensa payload?
```

## Expected Outcomes

Good outcome:

- the USB backend accepts/sends the bytes
- the printer does not move paper
- the printer does not heat, feed, or make engine noise
- the device disappears, stalls, or changes USB state until power-cycle

Useful failure:

- upload is rejected quickly
- USB backend reports a transfer error
- printer needs a power-cycle to recover

Stop condition:

- any paper-feed, motor, scanner/laser, or fuser behavior
- repeated mechanical noise
- anything other than idle USB-level behavior

## Safety Boundary

The current probe:

- has zero safety-scan hits
- contains no known video/engine/fuser MMIO addresses
- points the 75-entry system-interface table to a local trap loop
- points early runtime-vector placeholders to local trap/state placeholders
- does not contain print parser or ZjStream handling

The realistic recovery expectation is still power-cycle recovery.

## Command Shape

Dry run:

```sh
scripts/run-idle-probe-hardware-test.sh --dry-run
```

Real upload, only when the printer is connected and freshly power-cycled:

```sh
HP1020_ALLOW_CUSTOM_FIRMWARE_UPLOAD=1 \
  scripts/run-idle-probe-hardware-test.sh \
  --upload \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...' \
  --i-understand-this-uploads-custom-firmware
```

Do not run this through the normal print queue. Do not use Chrome/Preview. Do not send a PDF.
