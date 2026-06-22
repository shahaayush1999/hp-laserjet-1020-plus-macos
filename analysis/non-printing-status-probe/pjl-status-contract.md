# HP 1020 Non-Printing PJL/Status Contract

This is an offline contract for the tiny PJL/status payloads used to compare stock HP firmware against future open firmware.
It does not contact the printer.

## Safety Scope

- no PDF
- no PostScript
- no ZjStream raster
- no engine/video command from host
- no paper required

- first recommended query: `echo`

## Payloads

| Query | Bytes | Purpose | Stock response markers | Open minimal response |
|---|---:|---|---|---|
| `echo` | `49` | lowest-risk parser/response proof with a unique token | `HP1020_STATUS_PROBE` | return the same token through the USB back-channel |
| `info-status` | `36` | exercise stock status response builders | `CODE=`, `DISPLAY=` | defer until a tiny CODE/DISPLAY builder exists |
| `info-id` | `32` | read identity/model text without printing | `HP LaserJet 1020`, `Hewlett-Packard` | return a conservative model string only after USB response path is proven |
| `ustatus-device` | `44` | enable device status notifications for later stock calibration | `USTATUS`, `CODE=`, `DISPLAY=`, `ONLINE=` | not a first open-firmware target; stateful notifications can wait |

## Exact Payload Text

### `echo`

```text
<ESC>%-12345X@PJL ECHO HP1020_STATUS_PROBE<CR><LF>
<ESC>%-12345X
```

### `info-status`

```text
<ESC>%-12345X@PJL INFO STATUS<CR><LF>
<ESC>%-12345X
```

### `info-id`

```text
<ESC>%-12345X@PJL INFO ID<CR><LF>
<ESC>%-12345X
```

### `ustatus-device`

```text
<ESC>%-12345X@PJL USTATUS DEVICE = ON<CR><LF>
<ESC>%-12345X
```

## Practical Meaning

The first useful stock calibration is `echo`: it has a unique token and should not change printer state.
For open firmware, implementing only the echo response would be enough to prove USB/PJL back-channel execution without touching the print engine.

