# Minimal Idle Probe Hardware Test Result - 2026-06-15

This records the first connected-printer upload of the open-code idle firmware probe.

## Test

- Date/time: `2026-06-15 22:21 IST`
- Printer: `HP LaserJet 1020`, serial `S43VYTP`
- Direct URI: `usb://Hewlett-Packard/HP%20LaserJet%201020?serial=S43VYTP`
- Uploaded file: `analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl`
- Bytes sent: `121931`
- USB backend exit status: `0`
- Print data sent: none
- Normal CUPS queue used: no

Pre-upload checks:

```text
PASS analysis/open-firmware-probes/minimal-idle/hp1020-idle-probe.dl
kind=dl_upload image_bytes=121880 elf_bytes=121872
entry=0x100167a8 machine=0xabc7 phnum=11 shnum=21
```

Safety scan:

```text
fail hits: 0
watch hits: 0
```

## Host-Side Result

The CUPS USB backend accepted and sent the whole upload:

```text
DEBUG: Sending print file, 121931 bytes...
DEBUG: Sent 121931 bytes...
USB backend exit status: 0
```

After upload, macOS still listed the printer:

```text
direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=S43VYTP
```

IORegistry still showed the same HP identity:

```text
USB Product Name: HP LaserJet 1020
USB Vendor Name: Hewlett-Packard
USB Serial Number: S43VYTP
idVendor: 1008
UsbDeviceSignature: f003172b000153343356595450000000070102
```

## Physical Observation

Aayush reported:

```text
Nothing happened, printer with green light, no blinking, no sounds or paper movement, just chillin
```

That is the desired safety outcome for this test.

## Interpretation

This proves:

- the host can send the open idle probe through the same USB upload path as firmware
- the upload did not trigger paper feed, motor, fuser, scanner/laser, or visible error behavior
- the printer remained recoverable-looking from the host side

This does not yet prove:

- that the printer boot ROM accepted the ELF as firmware
- that execution reached our `_start`
- that the trap-loop system-interface table was exercised

Most likely interpretations:

1. The printer accepted the byte stream but did not execute it.
2. The printer accepted and executed enough of the payload to idle/hang without changing visible USB identity.
3. The resident ACL/boot path ignored or rejected the payload without surfacing a host-side error.

## Next Discriminator

Do not repeat blind idle uploads. The next useful test should create an observable but non-mechanical signal:

- a status/back-channel query that distinguishes HP firmware from idle/no-response behavior, or
- a USB-only marker probe that changes descriptor/status behavior without touching engine/video MMIO.

Before normal printing, power-cycle the printer so the known HP firmware upload path starts from a clean state.
