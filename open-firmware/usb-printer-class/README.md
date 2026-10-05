# Bounded USB printer-class request layer

**Offline software component, 2026-09-29.** The composed implementation passes
82 sanitized host and 82 independent QEMU cases. It adds no USB controller,
enumeration, endpoint submission, MMIO or printer operation. Its external reset
and response-lifetime acknowledgements are supplied promises, not hardware proof.

The narrow purpose is to handle the three standard USB printer-class requests
without losing the existing document ownership and recovery gates. USB addressing,
configuration, descriptors, control-transfer framing and actual endpoint work stay
with a future transport adapter. There is no allocator, RTOS or new bulk-data
queue. The independent implementation is GPL-2.0-or-later like the component it
uses; upstream sources below were inspected as references, not copied wholesale.

## Wire requests

`hp1020_usb_printer_setup` accepts exactly eight raw setup bytes. The three
16-bit setup fields are explicitly decoded little-endian, independent of CPU
byte order. Each invocation that obtains an identity supersedes the older control
reply, even if the new request is rejected with a pending STALL.

| Request | Exact accepted fields | Response |
|---|---|---|
| GET_DEVICE_ID | type `0xa1`, request `0`, configured zero-based configuration index, index `(interface << 8) \| alternate`, any 16-bit maximum length | Immutable IEEE1284 ID prefix/data, clipped to the requested length |
| GET_PORT_STATUS | type `0xa1`, request `1`, value `0`, index equal to the interface number, length `1` | One supplied status byte: bit 5 paper empty, bit 4 selected, bit 3 **not** error; all other bits zero |
| SOFT_RESET | type `0x21` or legacy `0x23`, request `2`, value `0`, index equal to the interface number, length `0` | No status ACK until the complete reset contract below is satisfied |

The caller supplies one supported configuration index/interface/alternate.
This does not advertise or emulate other interfaces or alternate settings.
GET_DEVICE_ID's index is not the ordinary low-byte interface encoding used by
the other requests. The ID's first two bytes are a big-endian total length that
includes those bytes. Initialization requires that prefix to match the supplied
storage length. The class does not construct or invent a device ID.

Status is a caller-supplied snapshot, copied at SETUP time. A NULL or explicitly
unknown snapshot uses the specification's permitted benign value `0x18` and
sets `status_fallback` in the response. That fallback is not sensor evidence,
physical readiness or print completion. A known value with reserved bits set is
rejected. There is no attempt to infer status from decoder progress.

The separate original-byte experiment in `analysis/usb-path/port-status.md`
prepares a fixed zero byte, unchanged by unrelated status-state fixtures, before
the excluded control sender. Copying that value would not provide paper sensing.
Neither that experiment nor this component establishes actual USB wire status.

## Reset and ownership

A valid reset immediately calls `hp1020_usb_receive_stop` on the supplied
document. Input and output data remain owned. Its reset ticket contains both the
independent recovery identity and the receive generation. Real SOFT_RESET also
retains separate request linkage, used only to authorize its eventual ACK. Repeating a valid reset
creates a fresh ticket and discards all local acknowledgements, even while the
document remains in the same generation. Prior document acknowledgement flags
cannot bypass the new local gates.

The adapter must supply three separate promises, using exactly one enum part
per `hp1020_usb_printer_ack_reset` call:

1. `HP1020_PRINTER_RECEIVE_QUIESCED`: no old OUT write or callback can ever touch
   retained memory. This includes events waiting in the transport/stack queue.
   It forwards the existing receive quiescence acknowledgement.
2. `HP1020_PRINTER_OUTPUT_QUIESCED`: every previously published/accepted output
   slot and callback is settled. It forwards the existing output acknowledgement.
3. `HP1020_PRINTER_TRANSPORT_RESET`: old bulk-IN buffers/events are settled and
   the bulk IN/OUT pipe defaults, stalls and data toggles have actually been
   reset. Endpoints remain unarmed. Address, configuration and EP0 ownership are
   unchanged. This is an additional externally supplied promise, not simulated
   controller work performed by this class.

Only `hp1020_usb_printer_finish_reset` can restart the composed document. It
requires all three current promises and calls the existing document restart,
which advances the receive generation. It makes an ACK available only if this
reset is still the latest SETUP. A newer unrelated request invalidates the old
reply but leaves the document's stop fence and reset work intact. Completing
that older reset can recover the document without issuing a stale EP0 reply.

Current-generation faults invalidate pending reset promises and keep the
document stopped. A new real reset or actual transport recovery boundary is required for recovery. Old-generation
faults and old reset tickets cannot alter current work. The adapter must preserve
the original submission identity; assigning today's generation to a late event
would defeat these checks. It must route current transport faults through this
layer before allowing more bulk input or output.

Request identities, recovery identities and receive generations never wrap. Exhaustion leaves the
document stopped and allows no new reply or restart. Reinitialization is for
first use only, not a recovery escape. No caller may independently restart the
embedded receive component or document while attached to this class.

`hp1020_usb_printer_begin_transport_recovery` is reserved for a real transport
boundary such as newly configured endpoints. It allocates an independent recovery
identity, invalidates all earlier promises and old reply permission, and stops
input. It does not invent a SETUP, advance the request counter or release borrowed
EP0 bytes. All three promises remain mandatory; completion creates no class ACK.
An attached adapter owns these calls and must not retry merely because input is
stopped. Nine additional cases check missing promises, distinct identities,
retained EP0, real/automatic supersession, faults and independent exhaustion.

## EP0 response lifetime

`hp1020_usb_printer_take_response` returns a response once and records its EP0
ownership. It does not submit anything. The adapter must serialize response
submission with new SETUP/error handling and must not submit a response after
its control request has been superseded. Cancelling an already submitted EP0
response remains adapter work.

The ID bytes must remain immutable for the entire class lifetime and every
outstanding transfer. The status byte is stored in the class. Later SETUPs only
change separate staging fields; they cannot overwrite that active status byte.
No subsequent response is issued until `hp1020_usb_printer_ep0_quiesced` receives
the exact prior response identity. That acknowledgement means all old EP0 reads
and callbacks are permanently finished or cancelled, not merely that software
wants to reuse the buffer. It is distinct from all three reset promises.

The class, document, configuration/ID storage, response metadata and API outputs
must be stationary and nonoverlapping. Keep each returned response's metadata
and packet storage alive until EP0 quiescence. A zero-length GET_DEVICE_ID reply
is represented as DATA with length zero; the USB stack supplies the appropriate
control framing/status. Bulk short packets and zero-length packets remain data
transport events, never document EOF.

## Pinned primary references and reuse decision

The USB-IF source is
[USB Device Class Definition for Printing Devices, §§4.2.1–4.2.3](https://www.usb.org/sites/default/files/usbprint11a021811.pdf).
The table defines the three requests, and the v1.1 correction explicitly asks
device implementations to accommodate the old `0x23` SOFT_RESET recipient.
The PDF was read from that official URL; it is not vendored here, and no local
file SHA256 is claimed.

TinyUSB release **0.21.0** points to commit
**`dae3f9a366bfcddbf9dcf1b48d7500286a849539`**. Its release notes add the printer
device class in June 2026. Exact inspected source paths at that commit:

- [src/class/printer/printer_device.c](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/class/printer/printer_device.c): reset calls a void application callback and immediately submits status; completion ignores the transfer result and rearms reception; FIFO flush also requests another receive.
- [src/class/printer/printer_device.h](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/class/printer/printer_device.h): ID storage must outlive its transfer; prefix includes its own two bytes.
- [src/device/usbd.c](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/device/usbd.c): legacy recipient `0x23` reaches unsupported-recipient handling; high-byte GET_DEVICE_ID routing is special-cased for its built-in printer callback.
- [src/device/dcd.h](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/device/dcd.h): controller close/stall operations own cancellation; transfer events carry endpoint/result/length without our submission generation or ticket.
- [src/osal/osal_none.h](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/src/osal/osal_none.h): a bare-metal integration is possible without an RTOS.
- [LICENSE](https://github.com/hathach/tinyusb/blob/dae3f9a366bfcddbf9dcf1b48d7500286a849539/LICENSE): MIT; retain notices if any upstream implementation is later copied.

Its generic enumeration/EP0 code is reused separately by
`open-firmware/tinyusb-printer-adapter/`, with a synthetic DCD for execution checks. Vendoring the printer class unchanged would bypass the current
ownership contract; a custom class also needs explicit routing for legacy reset
and, if used, nonzero printer-interface GET_DEVICE_ID requests. This class alone supplies
no controller port; the separate composition still does not implement HP hardware.

An independent alternative inspected was Eclipse USBX **v6.5.1.202602_rel**,
commit **`359977dd98d797fa3c93d0dda71cdbb29820fdc1`**, also MIT:

- [common/usbx_device_classes/inc/ux_device_class_printer.h](https://github.com/eclipse-threadx/usbx/blob/359977dd98d797fa3c93d0dda71cdbb29820fdc1/common/usbx_device_classes/inc/ux_device_class_printer.h) has a real printer device class, standalone state machines and optional application-owned buffers.
- [common/usbx_device_classes/src/ux_device_class_printer_soft_reset.c](https://github.com/eclipse-threadx/usbx/blob/359977dd98d797fa3c93d0dda71cdbb29820fdc1/common/usbx_device_classes/src/ux_device_class_printer_soft_reset.c) aborts OUT and optional IN requests.
- [common/core/src/ux_device_stack_transfer_all_request_abort.c](https://github.com/eclipse-threadx/usbx/blob/359977dd98d797fa3c93d0dda71cdbb29820fdc1/common/core/src/ux_device_stack_transfer_all_request_abort.c) explicitly leaves endpoint toggle state unchanged.
- [common/core/src/ux_device_stack_transfer_abort.c](https://github.com/eclipse-threadx/usbx/blob/359977dd98d797fa3c93d0dda71cdbb29820fdc1/common/core/src/ux_device_stack_transfer_abort.c) delegates pending-transfer abort to the DCD and has no asynchronous hardware-quiescence acknowledgement.

USBX therefore supplies another protocol reference, not a shortcut through the
controller or output gates. No upstream files are vendored in this directory;
the immutable commit identities are the source pins, not invented content hashes.

## Executed scope

`python3 scripts/validate-hp1020-usb-printer.py --target` builds this composition
under host address/undefined-behavior sanitizers and the pinned BE/call0 compiler.
The target ELF uses synthetic RAM, with the unchanged conservative instruction
audit. Report: `analysis/usb-path/printer-class/validation.json/.md`.

The original 73 cases cover ID length clipping across 255/256 bytes, nonzero interface and
configuration-index encoding, all defined status-bit combinations, unknown status,
reserved bits and malformed fields; canonical/legacy reset and all six orders of
the three promises; repeated resets, newer SETUPs, faults and identity exhaustion.
An independent fixture owns each EP0 response until its exact acknowledgement;
later requests cannot hide premature ownership loss or overwrite its status byte.

Actual composed decoding leaves 148800 bytes of a 9600-bit-wide source image
accepted before the reset boundary. All six promise orders and both initial fills
preserve held input/output until restart, then decode an unrelated 32-bit-wide
page exactly. A late old completion arrives after physical receive slot zero is
reused and cannot complete the new data. Generation exhaustion also retains
accepted output. Full independent JBIG decoding supplies the pixel oracle; both
engines compare every observed state, all retained storage and control reply bytes.

Target component state/fixed memory is 128256 bytes, excluding code, stack,
immutable device-ID storage and test captures. Current report source hashes
identify the tested implementation. Device feedback and physical reset remain
external to this software fixture.
