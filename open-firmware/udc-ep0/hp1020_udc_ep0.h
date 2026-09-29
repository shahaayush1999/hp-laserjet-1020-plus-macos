/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_EP0_H
#define HP1020_UDC_EP0_H

#include <stdint.h>
#include "hp1020_tusb_adapter.h"

#define HP1020_UDC_EP0_PACKET_BYTES 64u
#define HP1020_UDC_EP0_DESCRIPTOR_BYTES 16u

enum hp1020_udc_ep0_result {
    HP1020_UDC_EP0_OK = 0, HP1020_UDC_EP0_WAIT, HP1020_UDC_EP0_STALE,
    HP1020_UDC_EP0_INVALID, HP1020_UDC_EP0_FAULT, HP1020_UDC_EP0_ADAPTER_ERROR
};
enum hp1020_udc_ep0_phase {
    HP1020_UDC_EP0_FREE = 0, HP1020_UDC_EP0_PREPARED, HP1020_UDC_EP0_EXPOSED
};

/* Explicit mapping supplied by the caller. Numeric alignment/wrap/overlap is
 * checked; real allocation, aliasing and DMA reachability remain assertions.
 * No CPU-pointer cast, guessed alias bit or address translation is performed. */
struct hp1020_udc_ep0_span { uint8_t *cpu; uint32_t dma, bytes; };
struct hp1020_udc_ep0_spans {
    struct hp1020_udc_ep0_span out_descriptor, in_descriptor;
    struct hp1020_udc_ep0_span out_sink, in_staging;
};
struct hp1020_udc_ep0_memory {
    _Alignas(16) uint8_t out_descriptor[HP1020_UDC_EP0_DESCRIPTOR_BYTES];
    _Alignas(16) uint8_t in_descriptor[HP1020_UDC_EP0_DESCRIPTOR_BYTES];
    _Alignas(16) uint8_t out_sink[HP1020_UDC_EP0_PACKET_BYTES];
    _Alignas(16) uint8_t in_staging[HP1020_UDC_EP0_PACKET_BYTES];
};

/* Supplied booleans, each exactly0 or1. The mode means packet64 and BE normal
 * descriptors, independently established outside this RAM-only component.
 * packet_dma_ready covers IN staging visibility or OUT sink cache preparation.
 * No cache operation, publication barrier or peripheral instruction is supplied. */
struct hp1020_udc_ep0_publish_facts {
    uint8_t mode_packet64_be, descriptor_visible, packet_dma_ready;
};

/* A proposal borrows the descriptor and full64-byte DMA allocation until this
 * cookie settles. original_buffer is the EXACT pointer bound to the adapter,
 * possibly NULL for a ZLP; packet_cpu is the distinct staging/sink allocation.
 * Requested bytes may be0 while allocation_bytes always remains64. */
struct hp1020_udc_ep0_submission {
    struct hp1020_tusb_cookie cookie;
    const uint8_t *original_buffer;
    const uint8_t *descriptor_cpu;
    uint8_t *packet_cpu;
    uint32_t descriptor_dma, packet_dma;
    uint16_t requested, allocation_bytes;
    uint8_t endpoint;
};

/* Copy bytes and the ORIGINAL cookie before descriptor address reuse. Never
 * recover an event identity from the current endpoint or recycled address.
 * endpoint_fault is a nonzero independently supplied fault, including BNA/HE,
 * not an unfiltered EPSTS word or a TDC/wake hint. This is not a SETUP record. */
struct hp1020_udc_ep0_observation {
    struct hp1020_tusb_cookie cookie;
    uint8_t descriptor[HP1020_UDC_EP0_DESCRIPTOR_BYTES];
    uint32_t endpoint_fault;
};
struct hp1020_udc_ep0_completion_facts {
    uint8_t descriptor_cpu_visible, transfer_settled, packet_cpu_visible;
    uint8_t in_actual_known;
    uint32_t in_actual;
};

/* Both slots are component-owned: index0 OUT0, index1 IN0. No additional queue
 * or transfer identity is created. Public layout is for stationary allocation
 * and read-only diagnostics, never caller mutation or runtime reinitialization. */
struct hp1020_udc_ep0_slot {
    struct hp1020_udc_ep0_span descriptor, packet;
    struct hp1020_tusb_cookie cookie;
    const uint8_t *original_buffer;
    enum hp1020_tusb_result last_adapter_result;
    uint32_t fault_reason;
    uint16_t requested;
    uint8_t phase, cancel_requested, fault_reported;
};
struct hp1020_udc_ep0 {
    struct hp1020_tusb_adapter *adapter;
    struct hp1020_udc_ep0_slot slots[2];
    uint8_t initialized, busy;
};

/* First-use only. All objects are real stationary nonoverlapping allocations;
 * API argument/output structs must not alias component/adapter state, borrowed
 * original packets or the four DMA spans. Every call is serialized. Existing
 * adapter callbacks queue cancellation work without reentering this component.
 * The component changes no descriptor or packet byte during init. */
enum hp1020_udc_ep0_result hp1020_udc_ep0_init(struct hp1020_udc_ep0 *,
    struct hp1020_tusb_adapter *, const struct hp1020_udc_ep0_spans *);

/* Actual dcd_edpt_xfer callback only. IN0 endpoint0x80 permits requested0..64;
 * OUT0 endpoint0 permits requested0 only. Zero length requires original NULL,
 * as emitted by pinned TinyUSB. No control OUT data or other endpoint is
 * supported. TinyUSB alone distinguishes DATA ZLP from STATUS ZLP.
 * Validate before bind_submission; bind the exact original pointer/cookie.
 * After successful binding copy only requested IN bytes, then encode one normal
 * descriptor. The original packet remains borrowed despite that staging copy. */
enum hp1020_udc_ep0_result hp1020_udc_ep0_prepare(struct hp1020_udc_ep0 *,
    uint8_t endpoint, uint8_t *original_buffer, uint16_t requested,
    struct hp1020_tusb_cookie *);

/* Returns RAM-only proposal after supplied facts; no MMIO. Returning one
 * conservatively exposes storage even when a later backend rejects it. The
 * caller serializes publication/cancellation and fences delayed use of an old
 * proposal. This function cannot revoke a proposal held elsewhere. */
enum hp1020_udc_ep0_result hp1020_udc_ep0_take_submission(struct hp1020_udc_ep0 *,
    struct hp1020_tusb_cookie, struct hp1020_udc_ep0_publish_facts,
    struct hp1020_udc_ep0_submission *);

/* Event ingress only after the initiating TinyUSB call returns. Owner2,
 * TX/RX0,L1,unchanged body are strict replacement policy. OUT0 count must be0.
 * For IN0 the descriptor's low16 bits are NOT interpreted as actual length:
 * require separately supplied in_actual_known and in_actual==requested.
 * Both directions also need descriptor/packet visibility and transfer settlement.
 * in_actual fields are ignored for OUT0 except boolean-shape validation.
 * Faults retain all bytes and use the cookie-scoped packet_fault adapter API.
 * WAIT/error fault delivery must be retried before service/pumping other work. */
enum hp1020_udc_ep0_result hp1020_udc_ep0_observe(struct hp1020_udc_ep0 *,
    const struct hp1020_udc_ep0_observation *, struct hp1020_udc_ep0_completion_facts);

/* Request merely prevents future publication. It never releases storage,
 * generates an ACK, clears stalls/toggles, commits an address or resets USB. */
enum hp1020_udc_ep0_result hp1020_udc_ep0_request_cancel(struct hp1020_udc_ep0 *,
    struct hp1020_tusb_cookie);
/* Explicit supplied promise that accesses to descriptor, owned staging/sink
 * and original packet have settled. Pending events must retain old cookies.
 * A successful adapter cancellation retires metadata without clearing bytes.
 * This supplies no controller-wide or class-reset quiescence promise. */
enum hp1020_udc_ep0_result hp1020_udc_ep0_cancelled(struct hp1020_udc_ep0 *,
    struct hp1020_tusb_cookie, uint8_t transfer_settled);

#endif
