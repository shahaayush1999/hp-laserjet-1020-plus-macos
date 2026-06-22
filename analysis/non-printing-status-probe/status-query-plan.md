# HP 1020 Non-Printing Status Query Plan

This is the next useful hardware discriminator after the open idle upload.

## Plain-English Purpose

The last custom upload was intentionally quiet. That was good for safety, but
quiet does not prove whether our open code actually ran.

This probe asks the printer a tiny text question over USB and records whether
anything answers. It does not print, feed paper, warm the engine, or send raster
data.

## What It Tests

There are three useful cases:

| Setup | Expected Result | Meaning |
|---|---|---|
| Stock HP firmware loaded, then `@PJL ECHO ...` | Back-channel bytes contain a PJL reply or status text | The capture path works; HP firmware is alive enough to parse PJL |
| Open idle probe uploaded, then same PJL query | Usually no PJL reply | Confirms the open probe is not accidentally running HP's PJL stack |
| Open idle probe uploaded, then host still sees USB identity | Device stayed electrically recoverable | Good safety result, but still not proof of `_start` execution |

The high-value comparison is stock firmware response versus open idle response
using the same query harness.

## Script

Use:

```sh
scripts/query-hp1020-pjl-status.sh
```

The exact non-printing payloads and expected response markers are generated in:

```text
analysis/non-printing-status-probe/pjl-status-contract.md
```

Default mode is dry-run. It writes the exact PJL payload into:

```text
analysis/non-printing-status-probe/runs/<timestamp>-<query>/
```

The real send is guarded:

```sh
HP1020_ALLOW_NONPRINTING_USB_QUERY=1 \
  scripts/query-hp1020-pjl-status.sh \
  --send \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=S43VYTP' \
  --preload-stock-firmware \
  --query echo
```

That sends the bundled stock firmware first, then sends only:

```text
<ESC>%-12345X@PJL ECHO HP1020_STATUS_PROBE<CR><LF>
<ESC>%-12345X
```

The script captures:

- `query-stderr.txt` - CUPS USB backend log
- `backchannel.bin` - raw CUPS back-channel fd 3 bytes
- `backchannel.hex` - hex dump when bytes exist
- `backchannel-printable.txt` - printable view when bytes exist

## Safe Boundary

This is safer than a print test:

- no normal CUPS queue
- no PDF or PostScript conversion
- no ZjStream raster data
- no engine/video MMIO from our side
- no paper required

It can still leave the printer in a temporary confused state if queried after a
custom firmware upload. A power cycle should clear that state.

## Next Hardware Sequence

When the printer is available:

1. Power-cycle printer.
2. Run stock firmware calibration with `--preload-stock-firmware --query echo`.
3. Save whether `backchannel.bin` contains the echo/status response.
4. Power-cycle printer.
5. Upload the open idle probe with `scripts/run-idle-probe-hardware-test.sh`.
6. Run the same `query echo` without stock preload.
7. Compare response/no-response and USB identity.

## Interpretation

If stock firmware responds and open idle does not, then the script gives us a
working non-mechanical discriminator. The next custom firmware target should be
a USB-only marker response, not any printing logic.

If stock firmware does not respond either, then the blocker is host-side
back-channel capture, not firmware behavior. In that case the next step is to
instrument the USB path more directly instead of reading fd 3.
