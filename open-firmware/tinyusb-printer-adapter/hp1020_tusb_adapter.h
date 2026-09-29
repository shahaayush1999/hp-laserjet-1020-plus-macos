/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_TUSB_ADAPTER_H
#define HP1020_TUSB_ADAPTER_H

#include <stdint.h>
#include "tusb.h"
#include "device/usbd_pvt.h"
#include "hp1020_usb_printer.h"

/* Bounded experimental component. One stationary caller-owned instance, one serialized
 * context, patched/pinned TinyUSB, no allocator/RTOS/controller/MMIO supplied.
 * This adapter owns class, receive and document admission while attached.
 * Descriptors, DCD implementation and output consumer remain caller-owned. */
enum hp1020_tusb_result {
    HP1020_TUSB_OK = 0, HP1020_TUSB_WAIT, HP1020_TUSB_STALE,
    HP1020_TUSB_INVALID, HP1020_TUSB_LIMIT, HP1020_TUSB_ERROR
};

/* Copied by value at submission and retained beside the actual DCD transfer.
 * No field may be reconstructed from current state when a late event arrives.
 * EP0 epoch is a control identity; bulk epoch is a transport binding identity.
 * sequence is the original receive reservation, or zero for EP0. */
struct hp1020_tusb_cookie {
    uint32_t id, epoch, generation, sequence;
    uint8_t endpoint;
};

struct hp1020_tusb_config {
    uint8_t rhport, ep_out, ep_in;
    uint16_t out_capacity; /* 64-byte multiple, 64..HP1020_RX_CAPACITY. */
};
struct hp1020_tusb_ops {
    /* Request only: does not settle ownership. Do not reenter the adapter.
     * Queue cancellation work, then separately deliver cancelled()/complete(). */
    void (*request_cancel)(void *context, struct hp1020_tusb_cookie);
    void *context;
};

enum hp1020_tusb_owner_state {
    HP1020_TUSB_OWNER_NONE = 0, HP1020_TUSB_OWNER_DCD,
    HP1020_TUSB_OWNER_PENDING
};
struct hp1020_tusb_owner {
    struct hp1020_tusb_cookie cookie;
    uint8_t *buffer;
    uint32_t actual;
    uint16_t length;
    uint8_t state, result, cancel_requested, expected_cancel;
    /* Captured before the DCD returns. Direct-DCD SET_ADDRESS status does
     * not pass through usbd_edpt_xfer and has no core BUSY transition. */
    uint8_t core_busy_at_bind;
    /* An admitted packet fault keeps DCD ownership until real settlement and
     * permanently suppresses protocol progress from this EP0 packet. */
    uint8_t packet_fault;
};

/* Public for allocation and read-only diagnostics; fields are adapter-owned.
 * Three records: EP0 OUT, EP0 IN and one bulk OUT. Completed receive slots stay
 * in the existing four-slot receive core; service never consumes their bytes. */
struct hp1020_tusb_adapter {
    struct hp1020_usb_printer *printer;
    struct hp1020_tusb_config config;
    struct hp1020_tusb_ops ops;
    struct hp1020_tusb_owner owners[3];
    struct hp1020_tusb_owner delivering;
    struct hp1020_rx_ticket prepared_ticket;
    uint8_t *prepared_buffer;
    struct hp1020_printer_response response;
    struct hp1020_printer_status pending_status, active_status;
    tusb_control_request_t class_request;
    uint8_t pending_setup[8], active_setup[8];
    uint32_t last_submission_id, control_epoch, active_control_epoch;
    uint32_t transport_epoch, active_transport_epoch, deferred_epoch;
    uint32_t binding_pending_epoch, reset_transport_epoch;
    uint32_t class_request_id, response_epoch;
    enum hp1020_rx_result last_receive_result;
    enum hp1020_printer_result last_class_result;
    uint8_t initialized, exhausted, busy, stack_active;
    uint8_t opened, fenced, input_closed, prepared, configuration_value;
    uint8_t pending_kind, pending_speed, pending_destructive;
    uint8_t deferred, response_owned, delivering_live, delivered;
};

/* Bind before tusb_init. First-use only, never a recovery mechanism. The
 * document starts fenced. A newly successful configuration binding begins a
 * class-owned recovery with three external promises; no wire SOFT_RESET is
 * required for first input. Real SOFT_RESET also remains supported. Neither
 * path supplies physical quiescence, clears retained storage or auto-arms OUT.
 * Full-speed interface 7/1/2, alternate zero, two bulk endpoints, MPS 64 only.
 * Application usbd_app_driver_get_cb returns/copies *driver(); application's
 * usbd_app_control_route_cb delegates to route(). Other descriptors stay out. */
enum hp1020_tusb_result hp1020_tusb_adapter_init(struct hp1020_tusb_adapter *,
    struct hp1020_usb_printer *, const struct hp1020_tusb_config *,
    const struct hp1020_tusb_ops *);
const usbd_class_driver_t *hp1020_tusb_adapter_driver(void);
bool hp1020_tusb_adapter_route(uint8_t rhport,
    const tusb_control_request_t *, uint8_t *interface_number);

/* Every actual SETUP must enter here before reaching TinyUSB. Copy exactly
 * eight wire bytes, never a host-endian tusb_control_request_t. A new SETUP
 * invalidates old reply permission immediately; destructive admission also
 * stops bulk/document input BEFORE waiting for retained EP0 packets. Request
 * replacement preserves the stop fence. A pending bus reset is not replaceable.
 * Hardware must have settled old EP0 writes before writing new SETUP storage.
 * Receipt does not itself prove cancellation of any borrowed data buffer. */
enum hp1020_tusb_result hp1020_tusb_adapter_setup(struct hp1020_tusb_adapter *,
    const uint8_t *raw, uint32_t length, const struct hp1020_printer_status *);
enum hp1020_tusb_result hp1020_tusb_adapter_bus_reset(struct hp1020_tusb_adapter *,
    tusb_speed_t speed);

/* Sole permitted synchronous reentry: dcd_edpt_xfer calls bind_submission
 * BEFORE accepting any buffer. Retain returned cookie by value. false/error
 * means do not start a transfer. A DCD that accepted the cookie but returns
 * false must still settle that cookie explicitly; the reservation stays fenced.
 * No direct dcd_event_setup_received/bus_reset/xfer_complete outside service(). */
enum hp1020_tusb_result hp1020_tusb_adapter_bind_submission(
    struct hp1020_tusb_adapter *, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, struct hp1020_tusb_cookie *);

/* Serialized ingress AFTER the initiating TinyUSB call returns. Completion
 * promises that this transfer's writes/reads ended and data is CPU-visible;
 * it does not promise that every old-generation callback has been drained.
 * cancelled is an explicit settled cancellation, not a cancellation request.
 * Both preserve the cookie through the actual TinyUSB callback. Duplicates and
 * old identities are stale. Recognized invalid events fence without release. */
enum hp1020_tusb_result hp1020_tusb_adapter_complete(struct hp1020_tusb_adapter *,
    struct hp1020_tusb_cookie, xfer_result_t result, uint32_t length);
enum hp1020_tusb_result hp1020_tusb_adapter_cancelled(struct hp1020_tusb_adapter *,
    struct hp1020_tusb_cookie);
/* Unsettled packet fault, after the initiating TinyUSB call returns. Requires
 * the exact original DCD-owned cookie and its current identity domain/receive
 * generation. EP0 epochs are control identities; bulk epochs are transport
 * identities. A zero reason is a validated no-op. Nonzero faults fence input
 * and pending recovery, request cancellation, and retain every borrowed byte.
 * Repeats are idempotent. No completion/event/ACK is manufactured. A later real
 * EP0 settlement retires the owner without advancing the faulted request, even
 * if that late result is SUCCESS; fresh SETUP restores protocol permission.
 * STALE (including superseded/older-generation or already settled ownership)
 * has no side effects and never grants settlement. WAIT needs retry; LIMIT is
 * terminal fencing, still requiring explicit settlement of retained owners. */
enum hp1020_tusb_result hp1020_tusb_adapter_packet_fault(struct hp1020_tusb_adapter *,
    struct hp1020_tusb_cookie, uint32_t reason);
enum hp1020_tusb_result hp1020_tusb_adapter_fault(struct hp1020_tusb_adapter *,
    uint32_t transport_epoch, uint32_t generation, uint32_t reason);

/* service handles protocol events and settled ownership. A newly opened,
 * successfully configured endpoint binding begins exactly one internal class
 * recovery, without a fabricated SETUP or reply. Idempotent configuration,
 * generic mounted/fenced polling and superseded deconfiguration do not start
 * recovery. No decoding or automatic rearming occurs. arm_out submits at most
 * one transfer; pumping is separate so four completed slots apply backpressure. */
enum hp1020_tusb_result hp1020_tusb_adapter_service(struct hp1020_tusb_adapter *);
enum hp1020_tusb_result hp1020_tusb_adapter_arm_out(struct hp1020_tusb_adapter *);
enum hp1020_rx_result hp1020_tusb_adapter_pump(struct hp1020_tusb_adapter *);

/* Explicit stream shutdown. A short packet or ZLP is never EOF. close stops
 * admission without stopping pumping; finish waits for all reservations and
 * callbacks. Ordinary END_DOC boundaries already drain completed pages and
 * notify the document consumer without closing the stream or supplying EOF. */
enum hp1020_tusb_result hp1020_tusb_adapter_close_input(struct hp1020_tusb_adapter *);
enum hp1020_rx_result hp1020_tusb_adapter_finish(struct hp1020_tusb_adapter *);

/* Three separately supplied current recovery promises, checked by independent
 * recovery ID, receive generation and the adapter's original transport epoch.
 * pending_reset covers real SOFT_RESET and automatic configuration recovery;
 * finishing the latter never submits an EP0 packet. RECEIVE requires every
 * old write AND callback settled; empty software ownership is only a necessary
 * check. TRANSPORT additionally covers unimplemented bulk-IN/stalls/toggles and
 * requires TinyUSB bulk busy/stall state to be explicitly cleared. OUTPUT is
 * independent. Neither a timeout nor cancellation request supplies a promise.
 * A superseding SETUP may suppress the ACK while recovery still succeeds. */
enum hp1020_printer_result hp1020_tusb_adapter_pending_reset(
    const struct hp1020_tusb_adapter *, struct hp1020_printer_reset_ticket *);
enum hp1020_printer_result hp1020_tusb_adapter_ack_reset(struct hp1020_tusb_adapter *,
    struct hp1020_printer_reset_ticket, enum hp1020_printer_reset_part);
enum hp1020_printer_result hp1020_tusb_adapter_finish_reset(struct hp1020_tusb_adapter *,
    struct hp1020_printer_reset_ticket);

#endif
