# HP 1020 PJL Back-Channel Map

This maps the firmware evidence behind the non-printing status probe.

## Why PJL Is The Right Next Probe

The stock firmware contains a real PJL parser and response path. The useful
part is that this path talks over USB back-channel and does not require paper,
raster transfer, fuser, scanner motor, or laser/video hardware.

That gives us a safer yes/no discriminator than another print test:

- stock HP firmware loaded should answer some PJL/status queries
- the current open idle probe should not answer PJL unless our code really
  implements that path
- no mechanical movement is expected in either case

## Host-Side Capture

CUPS defines back-channel fd 3:

```text
CUPS_BC_FD = 3
```

The macOS USB backend already logs back-channel reads during normal HP firmware
and print sends:

```text
DEBUG: Read 23 bytes of back-channel data...
DEBUG: Read 44 bytes of back-channel data...
DEBUG: Read 59 bytes of back-channel data...
```

`scripts/query-hp1020-pjl-status.sh` opens fd 3 to `backchannel.bin`, so data
the backend relays through `cupsBackChannelWrite` can be captured as raw bytes.

## Firmware-Side Evidence

Known functions:

| Address | Label | Role |
|---:|---|---|
| `0x1000d2a8` | `hp1020_pjl_command_dispatch_candidate` | matches incoming PJL command text |
| `0x1000cdb0` | `hp1020_pjl_echo_matcher` | consumes the rest of `@PJL ECHO ...` |
| `0x1000cd44` | `hp1020_pjl_response_send_candidate` | sends a response through a vtable-style write callback |
| `0x1000bd04` | `hp1020_pjl_info_capabilities_builder` | builds capability text for INFO-style responses |
| `0x1000b3f8` | `hp1020_pjl_ustatus_result_builder` | builds USTATUS result strings |
| `0x1000b2a8` | `hp1020_pjl_status_notify_builder_candidate` | builds USTATUS notification strings |

Important strings:

| Address | String |
|---:|---|
| `0x10004728` | `@PJL ECHO ` |
| `0x10004098` | `USTATUS` |
| `0x10004168` | `CODE=` |
| `0x10004170` | `DISPLAY="` |
| `0x10004350` | `USTATUS [4 ENUMERATED]` |
| `0x1001bf70` | `Hewlett-Packard` |
| `0x1001bf8c` | `HP LaserJet 1020` |

## Best First Query

Use `@PJL ECHO HP1020_STATUS_PROBE`.

The exact payload bytes and fallback query contracts are generated in
`analysis/non-printing-status-probe/pjl-status-contract.md`.

Reason:

- it has an explicit firmware string reference
- it should exercise parser/response plumbing without changing printer state
- it creates a unique token that is easy to find in captured bytes

The `INFO STATUS` and `USTATUS DEVICE = ON` payloads remain useful fallbacks
because `foo2zjs` already sends related commands in normal job prologues.

## Expected Hardware Outcomes

| Result | Interpretation |
|---|---|
| Stock firmware preload plus ECHO returns bytes containing the token | Host capture and stock PJL response path both work |
| Stock firmware preload returns only CUPS logs, no fd 3 bytes | Need lower-level USB capture; fd 3 is not enough in direct-backend mode |
| Open idle upload plus ECHO returns no bytes while USB identity remains visible | Good non-mechanical contrast; open idle is not the HP PJL stack |
| Open idle upload plus ECHO returns bytes containing our token | Unexpected; either stock firmware is still running or the upload did not replace it |
| Any paper feed/motor/fuser behavior | Stop this path and power-cycle; this probe should not cause mechanical activity |

## What This Does Not Prove

No-response after open idle still does not prove `_start` executed. It only
narrows the next problem. To prove open-code execution, the next target must be
a tiny USB-only marker implemented by our firmware, or another observable that
does not touch engine/video hardware.
