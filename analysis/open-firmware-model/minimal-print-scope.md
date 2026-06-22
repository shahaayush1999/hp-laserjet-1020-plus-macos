# HP 1020 Minimal Printing-Only Replacement Scope

This is a generated offline scope report. It does not contact the printer.

## Goal

Print PDFs by reusing host-side ZjStream generation and implementing only the firmware path required to receive, parse, and print that stream.

## Simple Readout

For the narrow goal, we do not need to clone every HP firmware feature. We need:

1. USB upload and USB identity/control handling.
2. USB bulk receive of the host-generated ZjStream print file.
3. A small ZjStream parser for the chunk types foo2zjs actually emits.
4. Raster handoff into the video/raw-band hardware path.
5. Engine coordination for paper, fuser, motor, and page timing.

The first three are mostly software/protocol work. The last two are the hard hardware part.

## Platform Boundary

- `host_side`: PDF/PostScript to ZjStream conversion is host/platform packaging work.
- `device_side`: Open firmware would be platform-independent after bytes reach USB.
- `macos_repo_scope`: This repo's current production print path is macOS glue around HP firmware plus foo2zjs.

## Current Evidence

- parser entry: `0x10009d34`
- JobMgr queue: `3`
- work objects modeled: `1`
- raster nodes modeled: `1`
- print-model invariant failures: `0`
- required JobMgr messages missing: `none`
- endpoint-0 modeled data/stall cases: `24` / `4`
- control completion event object: `0x10021318`
- USB completion status bit candidate: `0x400`
- sideband access hits classified: `19`
- sideband risk split: `+0x26=critical`, `+0x32=mode_critical`, `+0x30=unknown_low_in_current_static_view`
- remaining-unit active-work source gap: `true`

## Component Scope

| Component | Status | Replacement need | Risk |
|---|---|---|---|
| Host PDF-to-ZjStream conversion | `available` | reuse existing GPL foo2zjs path; not firmware work | `low` |
| USB upload envelope | `available` | keep ACL/PJL upload wrapper for volatile firmware load | `low` |
| USB endpoint-0 descriptor/control path | `partially implemented` | live prove marker descriptor, then add tiny completion/rearm logic | `medium` |
| USB bulk receive to ZjStream parser | `mapped in stock firmware only` | open firmware must receive bulk bytes and feed the parser state machine | `medium` |
| ZjStream parser and JobMgr object model | `mapped` | implement only chunk types used by foo2zjs daily printing: START/END doc/page, JBIG_BIH/BID/END_JBIG, plus END_PLANE if emitted by a host variant | `medium` |
| JBIG compressed raster handling | `mapped to handoff boundary` | likely no full JBIG decode in firmware if hardware consumes the compressed stream like stock firmware | `high until hardware consumer semantics are proven` |
| Video sideband policy | `narrowed but unresolved` | decide deliberate values for work +0x26/+0x32 before any print-driving firmware; +0x26 gates channel-B refill and final accounting | `high` |
| Video/raw-band hardware feed | `danger boundary mapped, semantics incomplete` | reproduce page timing, raw-band pointers, channel enable/reset/wait sequence | `high` |
| Engine paper/fuser/motor coordination | `dispatch/status paths mapped, behavior incomplete` | coordinate mechanical state before and during video transfer | `high` |
| Scanner/fax/network/multi-product features | `out of scope` | none for Aayush's narrow goal | `none` |

## Main Blockers

| Blocker | Why | Next test/work |
|---|---|---|
| Live execution proof for open USB descriptor code | Without the marker descriptor appearing on the host, we do not yet know that custom code can control USB responses after upload. | Run the guarded marker stage when the printer is connected and power-cycled. |
| USB completion/rearm behavior | Stock firmware uses event flags at 0x10021318 fed by the USB interrupt task; the marker draft currently submits one descriptor and idles. | If marker fails, use the interrupt-lane model to build a bounded polling/rearm probe. |
| Video and engine hardware sequencing | The mapped print model reaches raster handoff, but real printing needs synchronized video transfer and mechanical engine control. | Do not test this until USB-only open code is proven; continue static mapping of video/engine semantics first. |
| Video sideband values for the first print path | Static analysis now shows +0x26 is critical for channel-B refill/final accounting, but its active-work source is still not proven. | After USB-only execution is proven, use a non-printing or tightly gated trace/probe to distinguish whether stock leaves +0x26 zero or seeds it from page height/runtime state. |

## Current Decision

Continue USB-only marker proof before any engine/video printing experiment.

