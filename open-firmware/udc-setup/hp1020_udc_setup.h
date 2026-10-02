/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_SETUP_H
#define HP1020_UDC_SETUP_H

#include <stdint.h>
#include "hp1020_tusb_adapter.h"

#define HP1020_UDC_SETUP_RECORD_BYTES 16u

/* RAM-only ingress, one stationary instance and one serialized context. No
 * DCD/IRQ entry point, live-DMA read, rearm, acknowledgement or ownership
 * settlement is implemented. The adapter remains the protocol identity owner.
 * All raw SETUP, reconstructed SC/SI and bus-reset admissions for this adapter
 * must use this bridge. Reconstructed notifications never replace raw capture. */
enum hp1020_udc_setup_result {
    HP1020_UDC_SETUP_OK = 0, HP1020_UDC_SETUP_WAIT, HP1020_UDC_SETUP_STALE,
    HP1020_UDC_SETUP_INVALID, HP1020_UDC_SETUP_FAULT,
    HP1020_UDC_SETUP_ADAPTER_ERROR, HP1020_UDC_SETUP_LIMIT
};

enum hp1020_udc_setup_pending {
    HP1020_UDC_SETUP_PENDING_NONE = 0, HP1020_UDC_SETUP_PENDING_CAPTURE,
    HP1020_UDC_SETUP_PENDING_RESET, HP1020_UDC_SETUP_PENDING_OFFLOAD
};
enum hp1020_udc_setup_terminal {
    HP1020_UDC_SETUP_LIMIT_NONE = 0, HP1020_UDC_SETUP_LIMIT_SEQUENCE,
    HP1020_UDC_SETUP_LIMIT_ADAPTER
};
enum hp1020_udc_setup_progress_permission {
    HP1020_UDC_SETUP_ALLOW_SERVICE = 1u,
    HP1020_UDC_SETUP_ALLOW_ARM = 2u,
    HP1020_UDC_SETUP_ALLOW_PUMP = 4u
};

/* The caller assigns sequence ONCE, at original ingress, from a shared strictly
 * increasing, nonzero, nonwrapping order for SETUP and bus-reset observations.
 * Preserve it across deferral, copies and record-address reuse. The bridge does
 * not allocate identities. Identical request bytes with a NEW sequence are a
 * new request; a duplicate or older sequence is stale. Sequence must not restart
 * after USB reset. UINT32_MAX is a reserved terminal LIMIT observation, never a
 * protocol admission. Gaps are permitted only when the caller has retained order
 * and has not lost a relevant SETUP/reset event. No normal EP0 cookie substitutes
 * for this unsolicited event identity.
 *
 * record is an immutable copy of ONE SETUP record: BE status at +0, reserved
 * word at +4, eight unchanged USB wire bytes at +8. It is not a normal data
 * descriptor. record_dma identifies the configured dedicated SETUP allocation;
 * numeric equality cannot establish actual mapping or snapshot provenance.
 * endpoint_fault is a separate supplied fault, not a complete EPSTS value.
 * printer_status is the original optional status snapshot, copied by value;
 * the existing class owns its validation/fallback policy. */
struct hp1020_udc_setup_observation {
    uint32_t sequence, record_dma, endpoint_fault;
    uint8_t record[HP1020_UDC_SETUP_RECORD_BYTES];
    struct hp1020_printer_status printer_status;
};

/* Exactly 0 or 1; a missing fact makes dispatch WAIT with its capture retained.
 * format_be_wire means the descriptor status is BE and bytes +8..+15 are the
 * original USB wire bytes. cpu_visible/stable assert a complete, coherent copy
 * from this record with no concurrent overwrite during acquisition. No bit in
 * the descriptor proves these facts, SETUP-vs-OUT status identity, or cancellation
 * of an unrelated old IN/OUT packet. The input object itself must be readable,
 * stationary and immutable for the duration of offer(). Facts describe that
 * retained snapshot; asserting them later must not silently reread live bytes. */
struct hp1020_udc_setup_capture_facts {
    uint8_t format_be_wire, cpu_visible, stable;
};

/* External promises about the originally retained SC/SI observation. All are
 * exact 0/1. dynamic_csr means hardware owns standard status but is holding it
 * for the software CSR_DONE grant. coherent_current includes the sample's
 * association with this original event, no lost request/reset, and stable
 * CFG/INTF/ALT acquisition; the bridge cannot infer these from pending bits.
 * request_validated covers original fields that four-bit DEVSTS cannot retain.
 * Unknown facts retain the event and block ordinary progress. Unsupported
 * values in this initial bounded profile also stay held, without a fabricated
 * STALL or status grant, until an actual reset supersedes them. */
struct hp1020_udc_offload_facts {
    uint8_t dynamic_csr, coherent_current, request_validated, ep0_stalls_cleared;
};
/* csr_programmed includes completed affected-endpoint default, DATA0 toggle
 * and halt reset for every nonzero configuration selection (even the same
 * value) or interface reselection. It is not proved by opening software
 * endpoints. A retained core bulk halt makes the grant wait; a newly armed
 * packet after recovery need not be cancelled merely because it is BUSY. */
struct hp1020_udc_auto_status_facts {
    uint8_t csr_programmed, status_gate_current;
};

/* Public only for allocation/read-only diagnostics. Exactly one retained
 * capture; no queue or transfer-cookie allocator. Captured bytes are left
 * unchanged after admission or a reset barrier. The adapter's existing pending
 * slot then owns admitted wire bytes. All fields below are component-owned. */
struct hp1020_udc_setup {
    struct hp1020_tusb_adapter *adapter;
    struct hp1020_udc_setup_observation capture;
    struct hp1020_tusb_offload offload;
    uint32_t record_dma, last_sequence, last_reset_sequence, pending_sequence;
    uint32_t adapter_control_epoch, reset_control_epoch, last_admitted_sequence;
    enum hp1020_tusb_result last_adapter_result;
    uint8_t initialized, busy, pending_kind, terminal;
};

/* First use only, with a freshly initialized adapter before any control event
 * or submission. One aligned, nonzero, nonwrapping 16-byte DMA label is supplied;
 * no physical allocation, mapping, alias detection or record initialization is
 * performed. Real object validity/nonaliasing remain caller obligations. Never
 * reinitialize to escape sequence exhaustion or outstanding controller owners. */
enum hp1020_udc_setup_result hp1020_udc_setup_init(struct hp1020_udc_setup *,
    struct hp1020_tusb_adapter *, uint32_t record_dma);

/* Copy one known SETUP observation into the free capture slot. It may still
 * need supplied format/visibility/stability facts before dispatch. This does
 * NOT admit the USB request to TinyUSB/adapter, clear EP0 stalls, rearm SETUP
 * storage, or settle any transfer. The immutable record remains unvalidated.
 * Rejected observations stay caller-owned and unchanged. If a capture is held,
 * a newer event returns WAIT: retain it externally, do not overwrite or reorder.
 * An unadmitted reset retry also blocks later captures, while its earlier events
 * are stale. A valid-source UINT32_MAX observation is copied but enters local
 * terminal LIMIT without any adapter call.
 *
 * Once a new SETUP is known, prioritize its admission before ordinary protocol
 * service/pumping. Unknown facts or FAULT are not permission to continue an old
 * reply. Exact-cookie settlement and service needed to drain an ALREADY pending
 * bus reset remain allowed. Enforce progress() in the integration owner. */
enum hp1020_udc_setup_result hp1020_udc_setup_offer(struct hp1020_udc_setup *,
    const struct hp1020_udc_setup_observation *);

/* Admit only the originally retained sequence. ep0_stalls_cleared is a separate
 * supplied fact (0/1), not an action or conclusion of this bridge. WAIT retains
 * the immutable record and status, including when adapter bus reset is pending.
 * Owner != 2 waits; RX != 0 or a supplied endpoint fault returns FAULT and keeps
 * the capture held. Unused status bits and reserved word remain opaque.
 * OK means adapter_setup copied the eight raw bytes and invalidated old reply
 * permission; later adapter service still waits for original packet settlement.
 * Every request_cancel callback merely queues work. Drain it after this function
 * returns through the existing EP0/OUT components with original packet cookies.
 * The caller must NOT clear stalls or report cancellation just because OK was
 * returned. Source SETUP-record reuse remains a separate controller operation. */
enum hp1020_udc_setup_result hp1020_udc_setup_dispatch(struct hp1020_udc_setup *,
    uint32_t sequence, struct hp1020_udc_setup_capture_facts,
    uint8_t ep0_stalls_cleared);

/* Separate immutable typed ingress in the same single pending-event slot and
 * external sequence order. No raw record bytes/DMA label are invented or
 * changed. offer_offload freezes the sample before validation; dispatch alone
 * may construct a canonical notification through the adapter. Values outside
 * config0/1, interface0/alt0 remain held/FAULT; a later actual reset is required
 * by this bounded profile. This is not a general controller rejection policy. */
enum hp1020_udc_setup_result hp1020_udc_setup_offer_offload(struct hp1020_udc_setup *,
    const struct hp1020_tusb_offload *);
enum hp1020_udc_setup_result hp1020_udc_setup_dispatch_offload(struct hp1020_udc_setup *,
    uint32_t original_sequence, struct hp1020_udc_offload_facts);

/* One CSR_DONE permission proposal for this exact no-buffer status owner.
 * Requires full progress permission and the latest original admitted ingress;
 * even a newer offered-but-unadmitted event blocks an old grant. Neither facts
 * nor success supply DMA/USB completion or any reset promise. status_gate_current
 * independently asserts the physical status gate still belongs to this event.
 * The serialized caller must consume the returned permission immediately,
 * before any newer ingress; it may not queue/reuse it after an intervening
 * request/reset. Explicit original-cookie settled cancellation is independent.
 * grant is caller-owned valid nonaliasing output and stays unchanged on error. */
enum hp1020_udc_setup_result hp1020_udc_setup_take_auto_status(struct hp1020_udc_setup *,
    uint32_t original_sequence, struct hp1020_tusb_cookie,
    struct hp1020_udc_auto_status_facts, struct hp1020_tusb_auto_status_grant *);

/* Independently supplied completed cleanup of one failed programming attempt.
 * This is allowed while a newer observation is held: it emits no reply and
 * creates no forward-progress permission. Exact original ticket, zero retained
 * owners and the adapter's stop fence remain necessary. Never infer the fact
 * from a new SETUP, reset interrupt, empty software queue or elapsed time. */
enum hp1020_udc_setup_result hp1020_udc_setup_ack_programming_cleanup(
    struct hp1020_udc_setup *, struct hp1020_tusb_programming_ticket,
    uint8_t controller_programming_clean);

/* Ordered admission of an actual supplied bus-reset observation. Same external
 * ingress sequence space as SETUP; the bridge never creates a reset event.
 * Calls only adapter_bus_reset. On OK, commit a sequence barrier and abandon a
 * pending older capture WITHOUT clearing its bytes. Older/replayed captures are
 * now stale; later captures can wait for the adapter's pending reset to drain.
 * Before calling the adapter, retain the exact reset sequence in the SINGLE
 * pending-event tag, replacing any older pending-capture tag but preserving its
 * bytes. WAIT keeps that reset retry and blocks later offer/dispatch. Only the
 * same reset sequence retries; a newer reset waits externally. Only OK clears
 * the retry tag. LIMIT/error retain it and fail closed. Full-speed is the only
 * accepted speed, so no second speed state is needed. No DMA/default-state/
 * recovery promise is supplied. Packet owners keep original adapter cookies. */
enum hp1020_udc_setup_result hp1020_udc_setup_bus_reset(struct hp1020_udc_setup *,
    uint32_t sequence, tusb_speed_t speed);

/* Read-only bounded scheduling permission, not a physical-state promise.
 * Normally SERVICE|ARM|PUMP. A retained capture, reset retry, terminal condition
 * or adapter epoch mismatch blocks normal forward progress. SERVICE alone is
 * allowed solely to drain an ALREADY admitted bus reset: its recorded actual
 * adapter control epoch is current but not active yet. No private adapter
 * pending-kind enum is inspected. Exact-cookie complete/cancelled/fault ingress
 * and draining queued cancellation requests remain allowed independently.
 *
 * Integration MUST check this before adapter service/arm_out/pump. Require all
 * three bits before adapter close_input/finish/finish_reset, manual EP0 or OUT
 * descriptor publication, or other output-driving operations. finish_reset can
 * restart input and submit a deferred control ACK; it is forward progress, not
 * merely a supplied reset promise. Exact-cookie settlement and ack_reset(part)
 * remain allowed independently. A local sequence LIMIT cannot physically stop the controller
 * or fence the adapter by itself; do not claim it does. This predicate and
 * explicit settlement are required until a new, fully settled firmware lifetime.
 * Calls rejected before offer captures anything remain the caller's event. */
uint32_t hp1020_udc_setup_progress(const struct hp1020_udc_setup *);

#endif
