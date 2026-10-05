/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_IN_H
#define HP1020_UDC_IN_H
#include "hp1020_tusb_adapter.h"

/* One IN1 normal descriptor and separate 64-byte staging allocation. No MMIO,
 * cache implementation, IRQ handling or automatic publication is supplied. */
enum hp1020_udc_in_result {
    HP1020_UDC_IN_OK, HP1020_UDC_IN_WAIT, HP1020_UDC_IN_STALE,
    HP1020_UDC_IN_INVALID, HP1020_UDC_IN_FAULT, HP1020_UDC_IN_ADAPTER_ERROR
};
enum hp1020_udc_in_phase { HP1020_UDC_IN_FREE, HP1020_UDC_IN_PREPARED, HP1020_UDC_IN_EXPOSED };
struct hp1020_udc_in_span { uint8_t *cpu; uint32_t dma, bytes; };
struct hp1020_udc_in_memory {
    _Alignas(16) uint8_t descriptor[16];
    _Alignas(16) uint8_t packet[64];
};
struct hp1020_udc_in {
    struct hp1020_tusb_adapter *adapter;
    struct hp1020_udc_in_span descriptor, packet;
    struct hp1020_tusb_cookie cookie;
    const uint8_t *original;
    enum hp1020_tusb_result last_adapter_result;
    uint32_t fault_reason;
    uint16_t length;
    uint8_t phase, initialized, busy, cancel_requested, fault_reported;
};
struct hp1020_udc_in_submission {
    struct hp1020_tusb_cookie cookie;
    struct hp1020_udc_in_span descriptor, packet;
    const uint8_t *original;
    uint16_t length;
};
struct hp1020_udc_in_observation {
    struct hp1020_tusb_cookie cookie; /* Captured before address reuse. */
    uint8_t descriptor[16];
    uint32_t endpoint_fault; /* Supplied fault reason, never a raw IRQ word. */
};
struct hp1020_udc_in_publish_facts {
    uint8_t mode_packet64_be, descriptor_visible, packet_visible;
};
struct hp1020_udc_in_completion_facts {
    uint8_t descriptor_visible, memory_settled, actual_known;
    uint32_t actual;
};

/* Zero-initialized first-use state, stationary allocations and one serialized
 * context. Arguments/results must not alias state or borrowed storage. Explicit
 * aligned CPU/DMA spans are exactly 16 and 64 bytes and must be real distinct
 * mappings; numeric checks cannot establish that fact. Init changes no
 * descriptor/staging bytes. */
enum hp1020_udc_in_result hp1020_udc_in_init(struct hp1020_udc_in *,
    struct hp1020_tusb_adapter *, struct hp1020_udc_in_span descriptor,
    struct hp1020_udc_in_span packet);
/* Only inside the actual DCD IN1 submission. Bind the adapter's exact original
 * pointer, then copy to staging and construct one last-marked BE descriptor.
 * A staging copy does not release the original; the caller collects its adapter
 * result normally. NULL/0 requests an explicit ZLP; this is replacement policy,
 * not a claim that the original HP queue transmits zero-length records. */
enum hp1020_udc_in_result hp1020_udc_in_prepare(struct hp1020_udc_in *,
    uint8_t endpoint, uint8_t *source, uint16_t length, struct hp1020_tusb_cookie *);
/* A RAM proposal only, requiring independently supplied visibility/mode facts.
 * Taking a proposal exposes both entire allocations until real settlement.
 * Caller must serialize register publication with cancellation/reset and must
 * discard old proposals. This component cannot revoke copies held elsewhere. */
enum hp1020_udc_in_result hp1020_udc_in_take_submission(struct hp1020_udc_in *,
    struct hp1020_tusb_cookie, struct hp1020_udc_in_publish_facts,
    struct hp1020_udc_in_submission *);
/* DMA_DONE/TDC alone is insufficient without the mode/visibility contract.
 * memory_settled promises all external accesses to descriptor, staging and the
 * original source permanently ended. The exact DMA count is separately supplied,
 * never inferred from descriptor low bits. FIFO retry bytes may remain inside
 * the controller. This releases memory, not FIFO capacity or host receipt;
 * publication/reset must establish those separately. Faults retain all bytes. */
enum hp1020_udc_in_result hp1020_udc_in_observe(struct hp1020_udc_in *,
    const struct hp1020_udc_in_observation *, struct hp1020_udc_in_completion_facts);
/* Forward the adapter's queued cancellation request outside its callback. No
 * descriptor mutation, settlement or controller-wide reset promise is implied. */
enum hp1020_udc_in_result hp1020_udc_in_request_cancel(struct hp1020_udc_in *,
    struct hp1020_tusb_cookie);
enum hp1020_udc_in_result hp1020_udc_in_cancelled(struct hp1020_udc_in *,
    struct hp1020_tusb_cookie, uint8_t transfer_settled);
#endif
