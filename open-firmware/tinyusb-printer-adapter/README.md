# TinyUSB printer/document adapter

Focused execution passes **132 sanitized host and 132 big-endian QEMU scenarios**.
The independent fixture compares exact pixels, USB reply proposals and final
receive/output storage while checking borrowed buffers after every operation.
Reports: `analysis/usb-path/tinyusb-printer/validation.{json,md}`. This is a
synthetic DCD experiment; no physical controller or USB operation is implemented.
Full integration is being validated separately. Target component state/fixed
memory is 128588 bytes, excluding stack, code, TinyUSB core, ID and test captures.

`hp1020_tusb_adapter.c/.h` compose the pinned, separately patched TinyUSB device
core with the existing printer class, four-slot receive queue and page decoder.
New code is GPL-2.0-or-later. TinyUSB retains its MIT license. No upstream class
code is copied, and no new dependency, RTOS, allocator, descriptor implementation,
MMIO, output device or controller is introduced.

## First profile and integration

The application initializes a stationary document and printer class, then one
caller-owned adapter before `tusb_init`. It returns/copies `*driver()` from
`usbd_app_driver_get_cb`, and delegates its patched
`usbd_app_control_route_cb` to `route()`. The application supplies descriptors,
DCD, immutable IEEE-1284 ID, optional explicit status snapshot and the existing
output consumer. Address and configuration remain TinyUSB/DCD responsibilities;
class reset does not write them.

This profile accepts a full-speed printer interface 7/1/2, alternate zero, one
64-byte bulk OUT endpoint followed by one 64-byte bulk IN endpoint. Bulk OUT
reservations are a caller-selected multiple of 64, at most 1024 bytes. Bulk IN is
opened for the bidirectional profile but has no payload producer in this profile.
The document starts stopped. A newly established configuration starts one
internal recovery after its ordinary status packet is accepted for submission.
Three explicit promises are required before input can resume; no wire SOFT_RESET
or fabricated class request is needed. Every nonzero configuration selection,
including the current value, drains and reinitializes the binding as required by
USB2.0. Repeated configuration0 and generic polling create no recovery.
Real SOFT_RESET remains supported.
The synthetic 1024-byte reservation profile does not prove that one HP descriptor
can receive that amount; the physical port must separately establish controller
mode, transfer capacity and DMA/cache behavior.

Call `service()` for protocol events, `arm_out()` to submit at most one OUT,
and `pump()` separately to consume completed slots. Four READY slots therefore
produce backpressure without requiring an artificial decoder wait. The adapter
does not rearm from TinyUSB callbacks. Existing output progress remains a
synchronous consumer contract; an asynchronous output scheduler is not supplied.

Normal document input remains open across validated END_PAGE/END_DOC boundaries.
END_PAGE drains the page with its retained geometry. END_DOC can produce one
optional notification containing original receive generation, document ID and
encoded-page range. This does not stop receiving or advance generation.
`close_input()`/`finish()` are explicit shutdown operations; a missing END_DOC
still fails even if all page pixels have drained. Neither short transfers nor
ZLPs close a document. `continuous-printer/validation` separately checks exact
notification traces and pixels, failures, retained slots and fresh recovery.

## Identity and ownership contract

All operations are serialized, nonreentrant and use nonoverlapping stationary
objects. Interrupt ingress is marshalled outside the module. The only permitted
synchronous reentry is the DCD's `bind_submission()` call from inside
`dcd_edpt_xfer`, before accepting a buffer. It receives a checked, nonwrapping
cookie copied by value beside the actual DCD transfer. If binding fails, the DCD
must not start that transfer. All other callbacks arrive after the initiating
call returns. A DCD that binds but then returns false still owes explicit
settlement; the adapter retains the owner and fences the reservation.

The cookie contains submission identity, original generation and endpoint. EP0
uses a control epoch; OUT uses a separate transport binding epoch and its exact
receive reservation sequence. Neither a benign SETUP nor the current document
state may retag a late OUT event. A transport-wide fault supplies its original
binding epoch/generation even when no transfer is live. Old identities are stale;
exhaustion is terminal and retains owned storage.

The controller delivers `complete(cookie,result,length)` only after that exact
transfer's accesses ended and data is CPU-visible. `cancelled(cookie)` has the
same ownership promise; `request_cancel` merely asks and never settles storage.
Recognized invalid lengths/results fence and retain ownership. The callback that
requests cancellation must queue work and must not reenter the adapter.

Completion admission immediately stops the document on an unexpected current
failure, before READY data can be pumped. Successful OUT data is not committed
until `service()` sends the event through actual TinyUSB dispatch and the class
callback receives the retained original cookie from a side ledger. Expected
ABORTED completions pass through TinyUSB to clear its BUSY state without erasing
a current reset's promises. Duplicate and old events cannot match a later reuse.

Every SETUP/reset/completion enters through this adapter. Do not independently
call TinyUSB's `dcd_event_setup_received`, `dcd_event_bus_reset`,
`dcd_event_xfer_complete` or `tud_task_ext`. Direct endpoint submissions, receive
restart, document restart and class reply submission would bypass these gates.
Suspend/resume/unplug integration and arbitrary composite-driver traffic are not
part of this first profile. Deinitialization also requires settling all owners;
its class callback is not a cancellation implementation.

## Control and recovery

The adapter retains original eight-byte SETUP wire data; it never recasts the
host-endian TinyUSB request struct as bytes. A new SETUP immediately invalidates
old EP0 permission, including when a standard request supersedes a deferred class
reset. Old DCD ownership must settle before TinyUSB can reuse its shared control
buffer or the class's retained response bytes. A controller must likewise settle
old EP0 accesses before writing new SETUP storage. Successful ACK or explicit old
packet settlement plus replacement releases the exact class response identity.

A valid canonical/legacy SOFT_RESET stops input at admission, before EP0 can be
dispatched. Configuration changes, SET_INTERFACE for this interface and bulk
endpoint halt/toggle-changing requests also fence at admission. This follows the
pinned core's actual dispatch fields, including fields it ignores, so malformed
requests cannot bypass ownership checks. Configuration dispatch and endpoint
state changes wait for settled old bulk callbacks before TinyUSB erases mapping
or BUSY state. Replacing a deferred destructive SETUP preserves the stop fence.
Repeated configuration0 while already unconfigured does not fence. A pending bus reset cannot be
replaced by a SETUP; the caller retains and retries that later event.

`pending_reset()` returns the exact class ticket: independent recovery identity
and original receive generation. Automatic and real-reset attempts supersede
each other; only real reset retains a host request identity for its ACK. Supply its three parts
independently through `ack_reset()`:

- RECEIVE: every old OUT write and callback has permanently settled, including
  caller/controller queues. An empty ledger is necessary but insufficient.
- OUTPUT: every old published/accepted output and callback has settled. This
  separate promise cannot be inferred from input cancellation.
- TRANSPORT: all old bulk IN events/ownership are settled; bulk IN/OUT stalls,
  data toggles and default state are reset, with endpoints unarmed. TinyUSB's
  bulk BUSY/STALLED state must also be clear. The caller/controller performs that
  work; the adapter never clears bits to manufacture the promise.

`finish_reset()` rechecks settled ownership and core endpoint state, then asks
the class to restart the whole document. It submits an ACK only when that reset
still owns the current control epoch and real request identity. Automatic recovery
creates no class reply. A superseding standard SETUP suppresses
the reply but may allow the still-current reset recovery to complete. No output
or input storage is reset sooner, and no packet is automatically armed.

Status remains an explicit caller snapshot. Unknown status uses the class's
spec-permitted `0x18` fallback with `status_fallback` metadata. It does not prove
selected/no-error physical state. The stock firmware's separate fixed-zero
GET_PORT_STATUS observation does not change that policy.

## Normalized receive seam

`hp1020_usb_receive_complete_data(receive,ticket,length)` retains exact-ticket,
stop, bounded count and READY checks without fabricating HP descriptor bits.
The old descriptor-policy API retains its original error/owner/RX/L checks and
passes only a validated count to the shared operation. Its separate regression
passes 75 host/75 QEMU cases. The normalized API promises only that reservation's
settled CPU-visible data; it does not certify physical quiescence or drain every
callback. Failed submission leaves its reservation fenced until explicit recovery.

## Admission and submission failures

This profile rejects every control OUT request with nonzero wLength before
TinyUSB dispatch, after old EP0 ownership settles. It has no supported control
OUT data operation. This prevents malformed standard GET_STATUS/GET_CONFIGURATION
from retaining the core's stack-local reply pointers as receive destinations.
Normal OUT bulk transfers remain supported. Endpoint halt admission normalizes
reserved endpoint-address bits exactly as the pinned core does, so an alias
cannot change endpoint state while an old buffer is held.

A core-managed initial EP0 submission records BUSY at binding. If the core then
clears BUSY on rejection or marks the endpoint stalled, the adapter fences the
original generation, invalidates old recovery promises and requests cancellation.
It retains the exact owner until explicit settlement. The unfixed source returned
OK with that owner unfenced; a separate preserved capture reproduces the failure.
Sixteen new profiles cover active input, promised recovery, normal/unsupported
requests and direct-DCD SET_ADDRESS. That direct-DCD operation has no core BUSY
transition and remains the DCD's responsibility. Rejection before binding has no
retained owner and cannot be distinguished here from an unsupported request.

After a successful current EP0 DATA packet, another DATA/STATUS submission is
required. Missing follow-on ownership, or bound ownership with cleared TinyUSB
BUSY after submission failure, fences the new submission generation. Retained
pointers still require cancellation. A successfully completed old-generation
packet can initiate a new-generation submission after recovery; those identities
must not be conflated. Sixteen follow-on rejection scenarios cover DATA/STATUS,
before/after binding, standard/class requests and this cross-generation edge.

## References and validation limits

The pinned upstream is TinyUSB 0.21.0 commit
`dae3f9a366bfcddbf9dcf1b48d7500286a849539`. Exact original bytes/licensing are in
`vendor/tinyusb-0.21.0/PROVENANCE.json`; separately materialized changes are in
`open-firmware/tinyusb-device/patches/manifest.json` and
`protocol-compatibility.patch` (SHA256
`62edce457c5f3a4d7be7db18a9aea36be0e59477985252df53d23a2d2261a5cb`). The adapter
depends on that patch's private class routing and failed-EP0 latch.

Pinned primary code boundaries:

- [Device core](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/device/usbd.c): SETUP/transfer dispatch,
  configuration_reset, endpoint claim/BUSY handling and class callbacks.
- [Private device API](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/device/usbd_pvt.h): custom driver and endpoint interfaces.
- [DCD API](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/device/dcd.h): actual event bridge and controller obligations.
- [USB Printer Class 1.1](https://www.usb.org/sites/default/files/usbprint11a021811.pdf): class request contracts. Existing exact spec provenance and class semantics remain in
  `open-firmware/usb-printer-class/README.md`.

The current matrix covers mixed page geometry, consecutive/empty documents,
fragmented/short/ZLP transfers, four-slot backpressure, stale cookies, benign
control requests with live OUT, retained EP0/bulk across reset, deferred
configuration changes and replacement, halt aliases, submission/completion
failures, malformed control OUT and payload errors. Every accepted completion
is synthetic. Output failure/identity saturation have component-level evidence;
not every combination is repeated through this adapter. Continuous documents
have a separate 34-case host/target experiment. Synchronous output, supplied
quiescence and absence of a DCD port remain material limitations.

## Retained packet faults

`hp1020_tusb_adapter_packet_fault` accepts only the exact original still-owned
cookie in its current control/transport domain and receive generation. It fences
input and requests cancellation without freeing storage or fabricating a
completion. A real late EP0 SUCCESS retires faulted ownership without issuing a
follow-on packet or ACK. Superseded or older-generation faults cannot affect new
work. Bulk settlement still clears the real core BUSY state while input is fenced.

Separate `packet-fault-validation.{json,md}` evidence under the adapter evidence
directory checks retained ownership and late completion. Settlement is supplied;
faults and cancellation requests never prove it.

## Typed standard-request notifications

The ordered SETUP bridge also accepts typed controller configuration/interface
notifications, with original sequence identity separate from reconstructed
TinyUSB input bytes. No-buffer automatic-status ownership is retained through
an explicit one-shot grant and later settled cancellation; granting never calls
the stack's completion callback or asserts host ACK. Physical mode, request
validation, currentness and programming are separate supplied facts. The
`udc-offload-test/README.md` fixture documents the58 paired-case boundary.

A failed raw or typed endpoint-open attempt retains a programming-cleanup ticket.
Later requests/reset cannot erase the ticket or start another open. Raw sequence0
is explicit provenance, alongside the original control/transport epochs. Only
an exact externally completed cleanup with no retained owners clears dirty state;
it neither restarts a document nor supplies a recovery promise.

Ordinary raw SET_INTERFACE uses the USB-permitted sole-default-interface STALL
policy. Rejection preserves healthy bulk input and any pre-existing fault/reset,
while waiting for old EP0 ownership to settle and suppressing its reply. The
separate typed SI path still requires the controller facts and original status
ownership above. See the composed fixture's62-case execution and preserved
pre-policy observations; no physical USB compatibility is established.
