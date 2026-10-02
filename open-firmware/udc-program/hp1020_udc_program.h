/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_PROGRAM_H
#define HP1020_UDC_PROGRAM_H

#include <stdbool.h>
#include <stdint.h>
#include "hp1020_udc_setup.h"

/* Experimental recording-I/O component. No physical backend is supplied. Hooks use logical register
 * words and offsets, never a peripheral pointer or CPU-to-DMA cast. Every call
 * and hook is serialized/nonreentrant; a hook must not admit another ingress,
 * invoke the adapter, or defer a write for later execution. All objects and API
 * arguments are stationary, valid and mutually nonaliasing. First use only;
 * reinitialization is not recovery. */
enum hp1020_udc_program_result {
    HP1020_UDC_PROGRAM_OK = 0, HP1020_UDC_PROGRAM_WAIT,
    HP1020_UDC_PROGRAM_STALE, HP1020_UDC_PROGRAM_INVALID,
    HP1020_UDC_PROGRAM_FAULT, HP1020_UDC_PROGRAM_ADAPTER_ERROR
};

/* OK means the hook performed its documented ordered CPU operation. It does
 * NOT mean a posted peripheral write arrived, DATA0 was established, DMA ended
 * or USB acknowledged anything. NOT_PERFORMED and UNKNOWN are both failures;
 * neither grants permission to replay an already consumed CSR_DONE command.
 * A successful read writes one complete logical word to its output. */
enum hp1020_udc_program_io_result {
    HP1020_UDC_PROGRAM_IO_OK = 0,
    HP1020_UDC_PROGRAM_IO_NOT_PERFORMED,
    HP1020_UDC_PROGRAM_IO_UNKNOWN
};
struct hp1020_udc_program_io {
    enum hp1020_udc_program_io_result (*read32)(void *, uint32_t, uint32_t *);
    enum hp1020_udc_program_io_result (*write32)(void *, uint32_t, uint32_t);
    enum hp1020_udc_program_io_result (*order)(void *);
    void *context;
};

/* Explicit HP candidate slots, not Linux's OUT-bank index formula. The first
 * profile accepts OUT1 at +0x508 and IN1 at +0x50c only. in_fifo_words is an
 * externally allocated, nonoverlapping FIFO size in 32-bit words (at least16).
 * The allocation is READ/CHECK ONLY here; repeated configuration or interface
 * selection never changes FIFO size. No total FIFO geometry, EP0 allocation or
 * unused-CSR policy is inferred. */
struct hp1020_udc_program_layout {
    uint32_t out_ne_offset, in_ne_offset;
    uint16_t in_fifo_words;
};

/* Supplied facts, each exactly0/1. io_profile establishes the hook's logical
 * word ordering and the documented register/command semantics. mode_packet64_be
 * and dynamic_csr are independent capabilities, not inferred from stock boot.
 * affected_quiescent includes settled non-control DMA/FIFO/queued observations;
 * empty software owners alone do not establish it. in_snak_safe separately
 * establishes the documented IN-token/empty-TxFIFO point for an IN SNAK command;
 * DMA-done/source release alone cannot supply it. table_coherent includes all
 * unowned CSR entries/alternate settings. fifo_geometry justifies the allocation
 * above. No success in this unit generates any of these facts. */
struct hp1020_udc_program_facts {
    uint8_t io_profile, mode_packet64_be, dynamic_csr;
    uint8_t affected_quiescent, table_coherent, fifo_geometry, in_snak_safe;
};
struct hp1020_udc_program_init_facts {
    uint8_t noncontrol_initially_clean, table_coherent, fifo_geometry;
};

/* Separate from programming intent. affected_defaults includes completed
 * default/DATA0/halt state, even for repeated SC1 or SI0. It must not be derived
 * from successful writes/open callbacks. Physical gate currentness is supplied
 * independently from the bridge's software ingress order. devctl_stable covers
 * the entire read/order/grant/write interval, including HARDWARE changes (RDE
 * can auto-clear) as well as other software writers. Software serialization
 * alone cannot supply this fact; this first backend additionally reads RDE=0
 * and accepts an idle/stable register interval, not arbitrary concurrent RX.
 * A software bulk owner may legitimately exist while physical RDE is clear;
 * the adapter's broader grant permission does not prove this precondition. */
struct hp1020_udc_program_grant_facts {
    uint8_t io_profile, dynamic_csr, affected_defaults, status_gate_current, devctl_stable;
};

enum hp1020_udc_program_operation {
    HP1020_UDC_PROGRAM_READ = 1, HP1020_UDC_PROGRAM_WRITE,
    HP1020_UDC_PROGRAM_ORDER, HP1020_UDC_PROGRAM_FACT,
    HP1020_UDC_PROGRAM_REQUEST
};
struct hp1020_udc_program_failure {
    struct hp1020_tusb_programming_ticket ticket;
    uint32_t offset, attempted_value;
    uint8_t operation, io_result, grant_consumed;
};

/* Public only for stationary allocation/read-only diagnostics. These masks
 * record COMPLETED SOFTWARE COMMAND SEQUENCES, not physical endpoint state.
 * A partial failure invalidates their use as readiness proof. The bus trace
 * independently records every successful/uncertain write prefix. Existing
 * adapter tickets are copied; this object allocates no identity or owner. */
struct hp1020_udc_program {
    struct hp1020_udc_setup *ingress;
    struct hp1020_udc_program_io io;
    struct hp1020_udc_program_layout layout;
    struct hp1020_udc_program_failure failure;
    struct hp1020_tusb_programming_ticket selection;
    uint32_t service_control_epoch;
    enum hp1020_tusb_result last_adapter_result;
    enum hp1020_udc_setup_result last_bridge_result;
    uint8_t initialized, busy, servicing, failed;
    uint8_t completed_mask, selection_mask, binding_ready;
};

enum hp1020_udc_program_result hp1020_udc_program_init(
    struct hp1020_udc_program *, struct hp1020_udc_setup *,
    const struct hp1020_udc_program_io *, struct hp1020_udc_program_layout,
    struct hp1020_udc_program_init_facts);

/* Replace the application's normal adapter_service call with this wrapper.
 * It establishes the sole DCD open/close callback window and preserves bridge
 * scheduling. Newly failed void-close/programming callbacks return FAULT after
 * TinyUSB unwinds, even if the core would otherwise return OK. Once failed,
 * only SERVICE-only drainage of an ALREADY admitted actual reset is permitted.
 * New actual reset ingress and exact-cookie settlement remain independent;
 * a reset notification never clears the failure or pretends physical cleanup. */
enum hp1020_udc_program_result hp1020_udc_program_service(struct hp1020_udc_program *);

/* Read before every ordinary service/arm/pump/finish_reset/publication path.
 * Require all three existing bridge bits for finish/close_input/finish_reset
 * and manual descriptor publication. A failed backend blocks those paths;
 * exact-cookie settlement and external actual-reset admission remain allowed.
 * An unprogrammed typed SI cannot restart input after a newer raw request. */
uint32_t hp1020_udc_program_progress(const struct hp1020_udc_program *);

/* Call in EVERY DCD submission callback (including auto-status binding).
 * In particular a void close failure prevents the core's ensuing status bind.
 * This is explicitly MUTATING: a trusted active core callback attempting raw
 * SC0 status with retained open-command history or unsupported request fields
 * latches the exact original REQUEST failure before any owner is acquired.
 * An external/late query cannot create that failure from stale active bytes.
 * It does not replace ordinary progress/owner checks or validate a submission. */
bool hp1020_udc_program_submission_allowed(struct hp1020_udc_program *);

/* Actual dcd_edpt_open callback only; descriptor is exactly seven USB bytes.
 * Only bulk OUT1/IN1, MPS64, config1/interface0/alt0 are supported. Returning
 * anything but OK means false to TinyUSB. Unsupported fields from a genuine
 * active core callback latch REQUEST failure; inactive/external calls do not.
 * No descriptor is published, OUT NAK
 * is not cleared, and no FIFO flush/ACK/default-state promise is generated. */
enum hp1020_udc_program_result hp1020_udc_program_open(
    struct hp1020_udc_program *, uint8_t rhport, const uint8_t *descriptor,
    uint32_t length, struct hp1020_udc_program_facts);

/* Actual configuration-only dcd_edpt_close_all callback. The TinyUSB wrapper
 * may be void but MUST call this and keep its sticky failure; ignoring the
 * return cannot erase it. A genuine active callback with unsupported request
 * fields also latches REQUEST failure before I/O. Inactive/external calls do
 * not manufacture failure provenance. Does not support generic deinit/reset callbacks.
 * Masks only the two bulk IRQs, requests NAK and clears their old descriptor
 * pointers after independently supplied quiescence. None is settlement or
 * logical/NE disable proof. */
enum hp1020_udc_program_result hp1020_udc_program_close_all(
    struct hp1020_udc_program *, uint8_t rhport, struct hp1020_udc_program_facts);

/* After accepted typed SI0 or SC0 service, before recovery/grant. TinyUSB's SI
 * fallback does not call driver_open. SC0 may omit close_all when the core was
 * already cfg0 (including after an actual reset); software reset does not clear
 * this backend's programming history. Uses the SAME programming/disable code,
 * with the original current ticket and retained auto owner. Repeated SC0 with
 * no completed-open command history is an explicit no-op. Duplicate SI and
 * superseded calls perform no register write. */
enum hp1020_udc_program_result hp1020_udc_program_complete_selection(
    struct hp1020_udc_program *, struct hp1020_udc_program_facts);

/* Current identity/programming/facts check; read/order DEVCTL; consume exactly
 * one existing bridge permission; write CSR_DONE IMMEDIATELY; order. No grant
 * object escapes for deferred use. Failure after consumption, including a
 * definite NOT_PERFORMED write or a failed final barrier, is sticky and cannot
 * retry that grant. Retains the adapter's no-buffer owner, no completion/ACK.
 * Returning OK reports command issuance only, not physical status acceptance. */
enum hp1020_udc_program_result hp1020_udc_program_grant(
    struct hp1020_udc_program *, uint32_t original_sequence,
    struct hp1020_tusb_cookie, struct hp1020_udc_program_grant_facts);

enum hp1020_udc_program_result hp1020_udc_program_pending_cleanup(
    const struct hp1020_udc_program *, struct hp1020_udc_program_failure *);
/* Exact ORIGINAL failure ticket, even after later reset. Requires supplied
 * completed controller programming cleanup, stopped/unmounted software and no
 * retained DCD/PENDING/prepared/delivering/response ownership. Also clears a
 * matching existing adapter dirty ticket through its public API, when present.
 * Does not write registers, reopen a binding, retry a grant or supply any of
 * the three document recovery promises. A later failed attempt rejects this
 * old cleanup ticket. */
enum hp1020_udc_program_result hp1020_udc_program_ack_cleanup(
    struct hp1020_udc_program *, struct hp1020_tusb_programming_ticket,
    uint8_t controller_programming_clean);

#endif
