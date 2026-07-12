# HP 1020 USB Bulk Parser Draft

This is a mechanically inert, non-printing open-firmware draft for the HP
LaserJet 1020 Plus USB receive and ZjStream framing boundary.

It implements only enough USB behavior to:

- answer standard endpoint-0 descriptor reads
- arm the stock-mapped bulk OUT receive descriptor and buffer
- count completed receive data
- recognize bounded ZjStream chunk framing and discard payload bytes
- expose counters in the USB product string

It has no engine, video, laser, fuser, motor, paper-feed, raster decode, page
work, or mechanical output path. That boundary is checked by the offline build,
but actual execution on hardware remains unproven until a guarded test succeeds.
The entry point raises the Xtensa interrupt level before enabling USB service;
bulk completion is handled only by the explicit status-register polling loop.

## Counter Marker

The product descriptor has this exact zero state after successful startup:

```text
HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000
```

The hexadecimal counters are:

- `B`: bytes received through completed bulk OUT descriptors
- `D`: completed bulk OUT receive descriptors
- `C`: completely received chunks in the controlled `0x00..0x06` scope
- `E`: invalid descriptor length or malformed ZjStream framing errors
- `U`: completely framed chunk types outside the controlled scope

Reading the product descriptor does not increment those bulk counters.

## Offline Build

Run:

```sh
scripts/build-open-firmware-usb-bulk-parser-draft.sh
```

The build assembles and wraps the custom `.dl`, regenerates the host parser
model, and runs the layout, safety, USB allowlist, MMIO, endpoint-0, memory,
source, status-descriptor, and configuration-descriptor checks. It does not
enumerate or contact USB.

The generated upload is:

```text
analysis/open-firmware-probes/usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.dl
```

## Guarded Harness

The hardware harness is dry-run by default:

```sh
scripts/run-usb-bulk-parser-draft-hardware-test.sh --dry-run
```

Dry-run mode rebuilds the draft and validates the only allowed test payload.
It does not enumerate USB, read a USB descriptor, invoke the CUPS USB backend,
upload firmware, or send data.

A real custom upload requires both `--upload` and the exact upload opt-in. It
also requires an explicit direct `usb://` URI:

```sh
HP1020_ALLOW_USB_BULK_PARSER_UPLOAD=1 \
  scripts/run-usb-bulk-parser-draft-hardware-test.sh \
  --upload \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...'
```

The optional data step has an independent flag and environment guard:

```sh
HP1020_ALLOW_USB_BULK_PARSER_UPLOAD=1 \
HP1020_ALLOW_USB_BULK_PARSER_DATA=1 \
  scripts/run-usb-bulk-parser-draft-hardware-test.sh \
  --upload \
  --send-probe-data \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...'
```

The harness never accepts `hp1020queue://localhost`, does not read `DEVICE_URI`
from the environment, and never sends the bundled proprietary firmware. It
uploads only the custom `.dl`; the separately guarded payload is sent only
after the exact zero-counter product marker is read back.

## Inert Payload

The fixed payload is exactly 36 bytes:

1. ASCII `JZJZ`
2. one big-endian 16-byte `START_DOC` header: size `16`, type `0`, item count
   `0`, reserved `0`, signature `0x5a5a`
3. one big-endian 16-byte `END_DOC` header: size `16`, type `1`, item count `0`,
   reserved `0`, signature `0x5a5a`

It contains no `START_PAGE`, `END_PAGE`, JBIG, image, raster, or other payload.
Its SHA-256 is:

```text
935c947d40c020007ecf88534956defbd9e1764bde63708e025a2897a597978d
```

If hardware receives it as one short bulk transfer, the exact expected product
string is:

```text
HP1020 B=00000024 D=00000001 C=00000002 E=00000000 U=00000000
```

This result proves USB bulk receive and inert framing only. It neither issues a
page nor proves any print-path behavior.

## Recovery

The working queue, installed proprietary runtime, and printer files are not
modified. After any custom upload attempt, power-cycle the printer before
normal printing or another firmware test. The printer loses the custom firmware
on power loss and returns to the existing proprietary preload workflow.
