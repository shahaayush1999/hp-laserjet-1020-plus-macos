/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_USB_PRINTER_H
#define HP1020_USB_PRINTER_H

#include <stdint.h>
#include "hp1020_usb_document.h"

/* Experimental RAM-only component. No controller, enumeration, MMIO or physical reset exists.
 * All calls use one serialized context and stationary, nonoverlapping objects.
 * This layer is the exclusive owner of document restart while attached.
 * Initialization is for first use only, never a way to clear a fence or limit. */
enum hp1020_printer_result {
    HP1020_PRINTER_OK = 0,
    HP1020_PRINTER_WAIT,
    HP1020_PRINTER_STALE,
    HP1020_PRINTER_INVALID,
    HP1020_PRINTER_LIMIT,
    HP1020_PRINTER_DOCUMENT_ERROR
};

enum hp1020_printer_reply_kind {
    HP1020_PRINTER_DATA = 1,
    HP1020_PRINTER_ACK,
    HP1020_PRINTER_STALL
};

enum hp1020_printer_reset_part {
    HP1020_PRINTER_RECEIVE_QUIESCED = 1,
    HP1020_PRINTER_OUTPUT_QUIESCED = 2,
    HP1020_PRINTER_TRANSPORT_RESET = 4
};

struct hp1020_printer_config {
    /* Storage includes its two-byte big-endian length prefix. The prefix must
     * equal device_id_length. The bytes remain immutable for the entire class
     * lifetime and every outstanding EP0 transfer, including cancelled ones. */
    const uint8_t *device_id;
    uint16_t device_id_length;
    uint8_t interface_number;
    uint8_t alternate_setting;
    uint8_t configuration_index; /* Zero-based index, not bConfigurationValue. */
};

struct hp1020_printer_status {
    uint8_t value; /* Only bits 5 (empty), 4 (selected), 3 (NOT error) are valid. */
    uint8_t known; /* Exactly 0 or 1. NULL/unknown uses explicit 0x18 fallback. */
};

struct hp1020_printer_reset_ticket {
    /* Independent nonzero identity for a recovery attempt, not a host request. */
    uint32_t recovery_id;
    uint32_t generation;
};

struct hp1020_printer_response {
    uint32_t request_id;
    const uint8_t *data; /* DATA only; NULL for ACK/STALL. */
    uint16_t length;
    uint8_t kind; /* enum hp1020_printer_reply_kind */
    uint8_t status_fallback; /* 1 only for an unknown GET_PORT_STATUS snapshot. */
};

struct hp1020_usb_printer {
    struct hp1020_usb_document *document;
    struct hp1020_printer_config config;
    struct hp1020_printer_reset_ticket reset;
    uint32_t last_request_id;
    uint32_t current_request_id;
    uint32_t ep0_request_id;
    uint32_t last_recovery_id;
    uint32_t reset_request_id; /* Real SOFT_RESET reply linkage; zero for automatic recovery. */
    uint16_t requested_length;
    uint8_t initialized;
    uint8_t exhausted;
    uint8_t current_action; /* Private implementation tag, not a wire value. */
    uint8_t current_issued;
    uint8_t reset_active;
    uint8_t reset_parts;
    uint8_t ep0_live;
    uint8_t staged_status;
    uint8_t staged_fallback;
    uint8_t response_status; /* Never overwritten until ep0_quiesced. */
};

enum hp1020_printer_result hp1020_usb_printer_init(
    struct hp1020_usb_printer *, struct hp1020_usb_document *,
    const struct hp1020_printer_config *);

/* Exactly eight setup bytes in USB wire order. Every accepted API invocation
 * gets a fresh identity and supersedes the previous control reply, including a
 * malformed/unsupported SETUP that will be stalled. The active EP0 packet bytes
 * remain immutable until their own identity is acknowledged quiescent.
 * Valid reset (0x21 or legacy 0x23, request 2) stops the document immediately.
 * It does not clear data, restart, acknowledge EP0 or alter USB configuration.
 * status is sampled only for GET_PORT_STATUS; NULL means unknown fallback.
 * INVALID denotes a rejected request with a STALL response pending. LIMIT is
 * terminal identity exhaustion: the document remains fenced, no reply is issued.
 * request_id is optional; a zero output denotes that no identity was available. */
enum hp1020_printer_result hp1020_usb_printer_setup(
    struct hp1020_usb_printer *, const uint8_t *setup, uint32_t length,
    const struct hp1020_printer_status *status, uint32_t *request_id);

/* Begin recovery for a real transport boundary such as a new configuration.
 * This allocates an independent recovery identity and stops the document. It
 * invalidates old reset promises and reply permission without fabricating a
 * host request, advancing last_request_id or releasing owned EP0 storage.
 * All three external promises are still required. Completion never creates a
 * class ACK. The adapter is the exclusive caller while attached; merely being
 * fenced/mounted is not permission to begin or repeatedly retry recovery.
 * ticket is required and receives zero on failure. Identity exhaustion is
 * terminal for both explicit and automatic recovery; initialization is no reset. */
enum hp1020_printer_result hp1020_usb_printer_begin_transport_recovery(
    struct hp1020_usb_printer *, struct hp1020_printer_reset_ticket *ticket);

/* An unrelated later SETUP does not cancel the ongoing document stop. Repeated
 * wire resets and transport recovery attempts allocate independent recovery IDs
 * and invalidate every prior promise, even when generation has not changed. */
enum hp1020_printer_result hp1020_usb_printer_pending_reset(
    const struct hp1020_usb_printer *, struct hp1020_printer_reset_ticket *);

/* Supply exactly one part per call, for this recovery identity AND generation.
 * RECEIVE: all old OUT writes and callbacks are permanently settled, including
 * events waiting in an adapter/stack queue. Never attach today's generation to
 * a late event. This forwards the existing receive_quiesced promise.
 * OUTPUT: all old published/accepted output and callbacks are settled. This
 * forwards the existing document_output_quiesced promise.
 * TRANSPORT: old bulk-IN ownership/events are settled; bulk IN/OUT stalls and
 * data toggles/default pipe state are reset; endpoints remain unarmed. Address,
 * configuration and EP0 ownership stay unchanged. None of these facts can be
 * inferred from this software. A hardware adapter must establish them.
 * Late/mismatched tickets return STALE without modifying current work. */
enum hp1020_printer_result hp1020_usb_printer_ack_reset(
    struct hp1020_usb_printer *, struct hp1020_printer_reset_ticket,
    enum hp1020_printer_reset_part);

/* Requires all three current promises, then restarts the composed document.
 * No receive-only restart is permitted. ACK becomes available only for a real
 * SOFT_RESET that is still the current SETUP. Transport recovery has no reply
 * linkage and never creates a class response; no current request is fabricated.
 * This does not arm hardware. A failed restart leaves the document stopped and
 * requires a new valid reset attempt (identity/generation exhaustion is terminal). */
enum hp1020_printer_result hp1020_usb_printer_finish_reset(
    struct hp1020_usb_printer *, struct hp1020_printer_reset_ticket);

/* Each SETUP response may be taken once. WAIT means reset is incomplete, a reply
 * was already taken, or an earlier EP0 response is still owned. A DATA response
 * of length zero is legal for GET_DEVICE_ID with wLength zero; the USB stack
 * supplies control-transfer framing/status. No packet framing is emulated here.
 * After OK, retain the response metadata and data pointer unchanged until the
 * transport has finished or cancelled that exact EP0 request and settled all
 * old reads/callbacks, then call ep0_quiesced with its original identity.
 * A new SETUP invalidates old permission to submit a reply. The adapter must
 * serialize SETUP handling and submission; never submit a superseded response. */
enum hp1020_printer_result hp1020_usb_printer_take_response(
    struct hp1020_usb_printer *, struct hp1020_printer_response *);
enum hp1020_printer_result hp1020_usb_printer_ep0_quiesced(
    struct hp1020_usb_printer *, uint32_t response_request_id);

/* Endpoint/transport fault scoped to its original receive generation. A current
 * nonzero fault stops the document and invalidates reset promises/reply. It does
 * not release EP0/input/output memory. A new wire reset or actual transport
 * recovery boundary with three fresh promises is needed to recover.
 * Old-generation faults are STALE. Zero is a no-op, never a resume operation. */
enum hp1020_printer_result hp1020_usb_printer_fault(
    struct hp1020_usb_printer *, uint32_t generation, uint32_t fault);

#endif
