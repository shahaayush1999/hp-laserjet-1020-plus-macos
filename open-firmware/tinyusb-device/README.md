# Synthetic TinyUSB device baseline

**Unexecuted draft.** This fixture composes the unmodified pinned TinyUSB generic
device/EP0 core with the existing printer-class/document component. It supplies
a synthetic DCD that records packet submissions. There is no MCU port, actual
USB, controller access, enumeration on a host OS, physical reset or printing.
No bulk transfers or page decoding are exercised by this first experiment.

Upstream sources/provenance are in `vendor/tinyusb-0.21.0/`. The configuration
selects `OPT_MCU_NONE`, full speed, OS_NONE, EP0 size 64 and no built-in classes.
Only `tusb.c`, `device/usbd.c` and `common/tusb_fifo.c` are compiled upstream.
The application registers its own printer driver and a separate rejecting dummy
driver. Standard USB requests continue through the original generic core.

The fixture's descriptor bytes are deliberately explicit USB wire arrays. The
18-byte device descriptor is `1201000200000040feca0040000100000001` (synthetic
VID/PID, one configuration, EP0 size 64). A configuration begins with
`[9,2,total,0,interface+1,1,0,0xe0,50]`; every interface below the printer receives
`[9,4,n,0,0,0xff,0,0,0]`, and the printer receives
`[9,4,interface,0,2,7,1,2,0]`. Its two endpoint descriptors are
`07050102400000` and `07058102400000`. Configuration lengths are 32 and 59 for
printer interface 0 and 3 respectively. Flags advertise self-power and remote
wakeup. Optional string zero is `04030904`; other string indices are unsupported.
The ID is `01 90` followed by 398 cycling ASCII letters A through Z, or `01 80`
followed by 382 letters. The 384-byte profile checks the required terminating
zero-length DATA packet only when the host asks for more than 384 bytes.

## Boundaries and observations

Each DCD submission retains its exact pointer, length, epoch and unique token.
The fixture saves the bytes independently and rechecks them before/after events,
including before another submission. Completion/cancellation must match the
original token. A newer SETUP advances an independent control epoch immediately,
but waits for separately held EP0 packet reads to settle before entering TinyUSB.
Old-epoch completions settle their original owner and are then rejected before
they can alter the current upstream control state. Every forwarded event drains
the stack queue before another event enters it. This explicit serialization is
part of the experiment, not a proof that a future interrupt-driven DCD provides it.

The class accepts the preserved eight raw SETUP bytes. TinyUSB's decoded request
fields are compared with those bytes, never copied back as if they were still
little-endian wire storage. An independently held class response survives until
the matching ACK or until explicit packet cancellation makes it safe to retire.

SOFT_RESET records the actual class reset ticket, returns true from SETUP without
submitting status, and waits for the three supplied promises. A later standard
SETUP invalidates that deferred submission permission even though the generic
core does not forward it to the class. Finishing the older document reset can
advance its generation but cannot submit status for the newer control request.
Bus reset and valid SOFT_RESET fence data immediately on admission, even if old
EP0 ownership delays protocol dispatch; they invalidate earlier reset promises.
Bus reset/deconfiguration fences the document through its fault API; it does not
manufacture quiescence or restart. A subsequent explicit class reset is required
for this narrow fixture's document recovery. Reset acknowledgements remain
synthetic promises, and `fixture_reset` destroys a previous test world rather
than demonstrating production recovery.

The baseline intentionally preserves upstream limitations. Legacy `0x23` reset
and nonzero-interface GET_DEVICE_ID have no routing fix. A separate dummy driver
prevents accidental success through interface zero. Native two-byte GET_STATUS
and device-state bitfields receive no endian correction. Current non-success
EP0 completion results are forwarded unchanged, so the upstream core's result
handling remains observable. This deliberate negative control is not the proposed
safe adapter: a production adapter must fence faults before such an event can
advance the generic control state.
Submitting an IN packet is only a captured proposal: cancelled packet bytes also
appear in the transcript and do not represent bytes received by a real host.

## Event interface

Exports are `hp1020_tusb_fixture_reset(fill, printer_interface, id_length)` and
`hp1020_tusb_fixture_step(op,a,b,c,d)`, returning OK=0, WAIT=1, STALE=2, INVALID=3,
LIMIT=4 or FAIL=5. Interface is 0 or 3; ID length is 384 or 400. Arrays are
`hp1020_tusb_fixture_input[1024]`, `capture[32768]` and `stats[64]`, all with the
same `hp1020_tusb_fixture_` prefix. Input is poisoned after each step.

| Op | Inputs | Meaning |
|---|---|---|
| 0 | a=8, b=status known 0/1, c=status byte, d=0; raw SETUP in input | Queue a new SETUP; WAIT while old EP0 storage is still held |
| 1 | a=endpoint, b=original token, c=reported length, d=TinyUSB result | Complete exact owned packet; OUT bytes come from input |
| 2 | a=endpoint, b=original token, c=d=0 | Explicitly cancel/settle exact owned packet |
| 3 | a=0 (full speed), b=c=d=0 | Synthetic bus reset, delayed until old packet ownership settles |
| 4 | all zero | Attempt pending dispatch |
| 5 | a=one reset promise 1/2/4; b=c=d=0 | Acknowledge the cached original class reset ticket |
| 6 | all zero | Finish that reset; submit ACK only if its control epoch remains current |

Capture concatenates every submitted IN packet's bytes. ZLPs contribute zero
bytes but remain visible in submission counters and token/length fields. Endpoint
mask bit is `2*endpoint_number + direction` (OUT=0, IN=1). A successful CANCEL or
an old completion can immediately dispatch a waiting SETUP and submit a new packet.
Only one ingress event is queued: a SETUP may replace another pending SETUP, while
a new SETUP is rejected as INVALID until a pending bus reset has dispatched. It
cannot silently erase that reset or claim a general interrupt-queue implementation.

| Stats indices | Contents |
|---|---|
| 0–4 | result, initialization result, control epoch, pending kind (0/1/2 = none/SETUP/bus-reset), active epoch |
| 5–12 | submissions, completions, cancellations, stale events, owned endpoint mask, stall mask, ownership violations, document-memory guards intact |
| 13–19 | capture length, capture FNV-1a, last submitted endpoint, length, token, epoch, packet FNV-1a |
| 20–25 | active EP0 OUT token/length/epoch, then EP0 IN token/length/epoch (zeros when unowned) |
| 26–31 | printer class SETUP/DATA/ACK callbacks, dummy callbacks, last class result, last class request ID |
| 32–39 | class EP0 live/id, reset active/parts, receive generation/stopped/quiescent, output quiescent |
| 40–45 | deferred epoch/pending, suppressed deferred submissions, finished resets, cached reset request/generation |
| 46–51 | mounted, synthetic address, pending address, driver reset callbacks, open endpoint mask, stack events pending |
| 52–55 | active raw wLength, last class reply kind/length, component state plus fixed-buffer sizeof |
| 56–60 | last printer class SETUP callback's decoded type, request, value, index, length |
| 61–63 | document-memory FNV-1a, independently owned class reply flag, last completion result |

The host runner takes `fill interface id_length capture_path`, prints initial stats as one
JSON line, then repeatedly reads a 24-byte big-endian header containing
`op,a,b,c,d,data_length` followed by exactly that many input bytes. It prints and
flushes a stats line per event. EOF writes the capture. The caller should retain
tokens from earlier observations and replay those exact resolved events on the
target, with an independently specified expected wire transcript. Index 55 may
differ between host and target. Upstream compatibility failures must be recorded
separately from fixture ownership failures; do not normalize expected bytes.
