/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_OUT_H
#define HP1020_UDC_OUT_H

#include <stdint.h>
#include "hp1020_tusb_adapter.h"

#define HP1020_UDC_OUT_PACKET_BYTES 64u
#define HP1020_UDC_OUT_DESCRIPTOR_BYTES 16u

/* One serialized context, stationary nonoverlapping objects, one
 * original adapter binding. No IRQ, MMIO, cache operation, allocation, queue,
 * address translation or DMA cancellation implementation is supplied. */
enum hp1020_udc_out_result {
    HP1020_UDC_OUT_OK = 0, HP1020_UDC_OUT_WAIT, HP1020_UDC_OUT_STALE,
    HP1020_UDC_OUT_INVALID, HP1020_UDC_OUT_FAULT, HP1020_UDC_OUT_ADAPTER_ERROR
};

/* Caller asserts this CPU span and DMA span refer to the same stationary
 * writable RAM. Numeric bounds/alignment are checked, actual mapping/aliases
 * and allocation validity are not discoverable here. No pointer-to-DMA cast. */
struct hp1020_udc_out_span {
    uint8_t *cpu;
    uint32_t dma, bytes;
};

struct hp1020_udc_out_memory {
    _Alignas(16) uint8_t descriptor[HP1020_UDC_OUT_DESCRIPTOR_BYTES];
};

/* Supplied facts, each exactly 0 or 1. Unknown facts leave storage retained.
 * mode_packet64_be means DMA packet mode, MPS 64 and BE descriptor access are
 * established externally. descriptor_visible covers complete descriptor
 * publication; buffer_dma_ready includes required receive-buffer cache work.
 * These are assertions by the caller, not facts inferred from register images. */
struct hp1020_udc_out_publish_facts {
    uint8_t mode_packet64_be, descriptor_visible, buffer_dma_ready;
};

/* Taking a proposal conservatively exposes the descriptor and buffer. Backend
 * rejection does not undo that state. It still owes explicit settlement. The
 * proposal authorizes only this binding and must never be cached for retry
 * after cancellation. It is not a register write or transfer acknowledgement. */
struct hp1020_udc_out_submission {
    struct hp1020_tusb_cookie cookie;
    const uint8_t *descriptor_cpu;
    uint8_t *buffer_cpu;
    uint32_t descriptor_dma, buffer_dma;
    uint16_t capacity;
    uint8_t endpoint;
};

/* Immutable event snapshot. The caller captured the cookie from the original
 * submission BEFORE descriptor reuse; it must never infer identity from the
 * current endpoint, generation or recycled descriptor address. endpoint_fault
 * is an independently supplied nonzero fault (including BNA/HE), not the full
 * endpoint status register. A wake/TDC indication alone is not completion. */
struct hp1020_udc_out_observation {
    struct hp1020_tusb_cookie cookie;
    uint8_t descriptor[HP1020_UDC_OUT_DESCRIPTOR_BYTES];
    uint32_t endpoint_fault;
};

struct hp1020_udc_out_completion_facts {
    uint8_t descriptor_cpu_visible, transfer_settled, payload_cpu_visible;
};

enum hp1020_udc_out_phase {
    HP1020_UDC_OUT_FREE = 0, HP1020_UDC_OUT_PREPARED, HP1020_UDC_OUT_EXPOSED
};

/* Public for allocation/diagnostics; fields are component-owned. Holding one
 * descriptor is separate from the existing four-slot input queue. No new
 * generation or sequence is allocated. Descriptor bytes are not zeroed when
 * ownership retires. Payload ownership then remains with the adapter/queue. */
struct hp1020_udc_out {
    struct hp1020_tusb_adapter *adapter;
    struct hp1020_udc_out_span descriptor, buffer;
    struct hp1020_tusb_cookie cookie;
    enum hp1020_tusb_result last_adapter_result;
    uint32_t fault_reason;
    uint8_t initialized, busy, phase, cancel_requested, fault_reported;
};

/* First use only, never a recovery path. The adapter must already be initialized
 * with ep_out=1 and out_capacity=64. Each provided span must be real, stationary,
 * owned RAM, and neither span may alias any adapter/document or control state.
 * Supplied input/output structs must not overlap retained descriptor/payload,
 * component state or one another. This nonalias contract also covers aliases
 * that cannot be detected by comparing numeric CPU or DMA addresses. */
enum hp1020_udc_out_result hp1020_udc_out_init(struct hp1020_udc_out *,
    struct hp1020_tusb_adapter *, struct hp1020_udc_out_span descriptor);

/* Called only from the real DCD's dcd_edpt_xfer callback for bulk OUT1.
 * Validate spans before the sole allowed adapter reentry, bind_submission().
 * On OK the record holds its original cookie and freshly encoded bytes. On
 * rejection no publication occurred; adapter reservation recovery remains the
 * adapter's responsibility. This is not a DCD implementation. */
enum hp1020_udc_out_result hp1020_udc_out_prepare(struct hp1020_udc_out *,
    uint8_t endpoint, struct hp1020_udc_out_span buffer, uint16_t requested,
    struct hp1020_tusb_cookie *cookie);

enum hp1020_udc_out_result hp1020_udc_out_take_submission(struct hp1020_udc_out *,
    struct hp1020_tusb_cookie, struct hp1020_udc_out_publish_facts,
    struct hp1020_udc_out_submission *);

/* Call after the initiating TinyUSB call returns. Other owners mean WAIT;
 * RX==0/L==1/count<=64 and unchanged descriptor body are conservative policy.
 * Completion requires the independent settled and CPU-visible facts as well.
 * On OK only descriptor transport ownership retires; actual TinyUSB dispatch
 * and queue consumption still require adapter service/pump. Zero count is not
 * EOF. Faults retain every borrowed byte. Retry ADAPTER_ERROR/WAIT before
 * pumping queued input, so an outstanding fault is not ignored. */
enum hp1020_udc_out_result hp1020_udc_out_observe(struct hp1020_udc_out *,
    const struct hp1020_udc_out_observation *,
    struct hp1020_udc_out_completion_facts);

/* Queued cancellation work calls request_cancel after adapter callbacks have
 * returned. It fences future publication without changing descriptor/payload.
 * No callback or stop acknowledgement is generated by request_cancel itself. */
enum hp1020_udc_out_result hp1020_udc_out_request_cancel(struct hp1020_udc_out *,
    struct hp1020_tusb_cookie);

/* transfer_settled is an explicit external promise: old descriptor/buffer
 * accesses cannot recur and pending events retain their original identities.
 * It is not inferred from owner bits, NAK, a timeout or a bus reset. Requires a
 * cancellation request or observed fault. This does not supply any class reset
 * RECEIVE/TRANSPORT/OUTPUT promise, default endpoint state, or global quiescence. */
enum hp1020_udc_out_result hp1020_udc_out_cancelled(struct hp1020_udc_out *,
    struct hp1020_tusb_cookie, uint8_t transfer_settled);

#endif
