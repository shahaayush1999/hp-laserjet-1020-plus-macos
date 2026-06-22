# USB Marker Draft Hardware Test Plan

This is a later-stage custom firmware test plan for the USB marker draft.

It is not a print test. It uploads only the open USB marker draft and sends no
PDF, PostScript, ZjStream, engine, video, motor, fuser, or paper-feed data.

## Goal

Answer one narrow question:

```text
Can open firmware use only the mapped USB endpoint-0 registers to expose a
different product-string descriptor such as HP1020 OPEN MARKER?
```

## Current Offline Evidence

The draft currently passes these static gates:

- HP-shaped boot-probe layout profile
- general safety scan: no engine/video/function failures
- USB probe contract: only mapped `0xb300....` USB registers
- USB MMIO access scan: mapped USB reads/writes only
- endpoint-0 sequence scan: USB writes match the extracted stock endpoint-0 contract
- memory boundary scan: candidate setup-buffer reads, stock response-state writes, one staging-buffer copy loop, and four descriptor-ring writes, with no hidden fail hits
- marker length-flow check: clipped host `wLength` is preserved into the endpoint-0 response-length write
- behavior model: product-string requests select Sequence A or B based on USB gates, response length is clipped to `min(wLength, 38)`, and one stock-shaped control-IN descriptor is submitted
- data-stage model: marker bytes are copied into the stock staging buffer at `0x90022bd0`, one descriptor is built at `0x900226f0`, and the transfer is kicked through the stock endpoint-0 registers
- completion/interrupt model: stock firmware uses event flags object `0x10021318`; control-IN waits bit `0x1`, while the USB task consumes a separate `0x10000` lane signal

The draft still has an important unresolved assumption:

```text
setup packet base 0x90021348, response state base 0x100212d4, staging buffer
0x90022bd0, descriptor ring 0x900226f0, and the 0xb3000014/0xb3000000
control-IN kick are valid after custom firmware upload without the full stock
USB runtime. The current marker draft does not yet implement the stock
event-flag wait/rearm path.
```

That assumption is exactly what hardware must prove or disprove.

## Expected Outcomes

Good outcome:

- upload completes or times out only after bytes are sent
- printer stays mechanically quiet
- a host descriptor read can observe `HP1020 OPEN MARKER`

Useful failure:

- upload succeeds but host still sees the stock descriptor
- upload succeeds but the device disappears until power cycle
- CUPS USB backend reports a USB transfer error

Stop condition:

- any paper-feed, motor, scanner/laser, or fuser behavior
- repeated mechanical noise
- anything beyond USB-level behavior

## Recovery

Power-cycle the printer. The HP 1020 loses uploaded firmware on power loss, so
this should clear the test state.

## Test Order

Do not start with this marker draft. The safer order is:

1. Confirm normal stock firmware preload still works.
2. Confirm the open idle probe still uploads quietly.
3. Optionally run the read-only USB register snapshot probe.
4. Only then consider this write-capable USB marker draft.

This plan exists so the write-capable step is ready when needed, not because it
should be run automatically.

## Script

Dry run:

```sh
scripts/run-usb-marker-draft-hardware-test.sh --dry-run
```

Real upload, only after the safer stock/idle/read-only checks:

```sh
HP1020_ALLOW_USB_MARKER_DRAFT_UPLOAD=1 \
  scripts/run-usb-marker-draft-hardware-test.sh \
  --upload \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...' \
  --i-understand-this-uploads-usb-marker-draft
```

Do not run this through the normal print queue. Do not use Chrome/Preview. Do
not send a PDF.

Host-side USB identity capture before and after upload:

```sh
scripts/capture-hp1020-usb-identity.sh
```

The capture script only reads macOS device listings. It does not send bytes to
the printer.

The preferred wrapper is:

```sh
HP1020_ALLOW_OPEN_FIRMWARE_LADDER_UPLOAD=1 \
  scripts/run-open-firmware-usb-test-ladder.sh \
  --upload \
  --stage marker \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...' \
  --i-understand-this-uploads-open-firmware
```

That wrapper records `identity-before`, uploads exactly one stage, records
`identity-after`, and writes a summary with the observed marker-string count.
