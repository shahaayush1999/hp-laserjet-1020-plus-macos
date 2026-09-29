/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_udc_ep0.h"
#include <string.h>

#define REASON_DESCRIPTOR_BODY UINT32_C(0x80000201)
#define REASON_DESCRIPTOR_STATUS UINT32_C(0x80000202)
#define REASON_IN_ACTUAL UINT32_C(0x80000203)

static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
        ((uint32_t)p[2] << 8) | p[3];
}
static void put_be32(uint8_t *p, uint32_t value) {
    p[0] = (uint8_t)(value >> 24); p[1] = (uint8_t)(value >> 16);
    p[2] = (uint8_t)(value >> 8); p[3] = (uint8_t)value;
}
static bool same_cookie(struct hp1020_tusb_cookie a, struct hp1020_tusb_cookie b) {
    return a.id == b.id && a.epoch == b.epoch && a.generation == b.generation &&
        a.sequence == b.sequence && a.endpoint == b.endpoint;
}
static bool cpu_span_valid(const void *p, uintptr_t bytes) {
    return p && bytes && (uintptr_t)p <= UINTPTR_MAX - (bytes - 1);
}
static bool cpu_overlap(const void *a, uintptr_t an, const void *b, uintptr_t bn) {
    return (uintptr_t)a <= (uintptr_t)b + bn - 1 &&
        (uintptr_t)b <= (uintptr_t)a + an - 1;
}
static bool span_valid(struct hp1020_udc_ep0_span span, uint32_t needed) {
    return span.bytes >= needed && cpu_span_valid(span.cpu, span.bytes) &&
        span.dma && span.dma <= UINT32_MAX - (span.bytes - 1) &&
        !((uintptr_t)span.cpu & 15u) && !(span.dma & 15u);
}
static bool dma_overlap(struct hp1020_udc_ep0_span a, uint32_t an,
    struct hp1020_udc_ep0_span b, uint32_t bn) {
    return a.dma <= b.dma + bn - 1 && b.dma <= a.dma + an - 1;
}
static enum hp1020_udc_ep0_result enter(struct hp1020_udc_ep0 *s) {
    if (!s || !s->initialized || !s->adapter) return HP1020_UDC_EP0_INVALID;
    if (s->busy) return HP1020_UDC_EP0_WAIT;
    s->busy = 1; return HP1020_UDC_EP0_OK;
}
static enum hp1020_udc_ep0_result leave(struct hp1020_udc_ep0 *s,
    enum hp1020_udc_ep0_result result) {
    s->busy = 0; return result;
}
static struct hp1020_udc_ep0_slot *slot_for(struct hp1020_udc_ep0 *s, uint8_t endpoint) {
    if (endpoint == 0) return &s->slots[0];
    if (endpoint == 0x80) return &s->slots[1];
    return NULL;
}
static struct hp1020_udc_ep0_slot *current(struct hp1020_udc_ep0 *s,
    struct hp1020_tusb_cookie cookie) {
    struct hp1020_udc_ep0_slot *p = slot_for(s, cookie.endpoint);
    if (!p || p->phase == HP1020_UDC_EP0_FREE || !cookie.id ||
        !same_cookie(p->cookie, cookie)) return NULL;
    return p;
}
static void retire(struct hp1020_udc_ep0_slot *p) {
    /* Descriptor and all64 packet bytes remain unchanged after retirement. */
    memset(&p->cookie, 0, sizeof(p->cookie));
    p->original_buffer = NULL; p->requested = 0;
    p->phase = HP1020_UDC_EP0_FREE; p->cancel_requested = 0;
    p->fault_reported = 0; p->fault_reason = 0;
}
static enum hp1020_udc_ep0_result report_fault(struct hp1020_udc_ep0 *s,
    struct hp1020_udc_ep0_slot *p) {
    p->cancel_requested = 1;
    if (p->fault_reported) return HP1020_UDC_EP0_FAULT;
    p->last_adapter_result = hp1020_tusb_adapter_packet_fault(s->adapter,
        p->cookie, p->fault_reason);
    if (p->last_adapter_result == HP1020_TUSB_WAIT) return HP1020_UDC_EP0_WAIT;
    if (p->last_adapter_result == HP1020_TUSB_OK ||
        p->last_adapter_result == HP1020_TUSB_STALE) {
        /* A superseded control packet must not fault a newer request. STALE
         * still grants no reuse: this exact local record stays retained. */
        p->fault_reported = 1; return HP1020_UDC_EP0_FAULT;
    }
    return HP1020_UDC_EP0_ADAPTER_ERROR;
}

enum hp1020_udc_ep0_result hp1020_udc_ep0_init(struct hp1020_udc_ep0 *s,
    struct hp1020_tusb_adapter *adapter, const struct hp1020_udc_ep0_spans *config) {
    if (!s || !adapter || !config || !cpu_span_valid(s, sizeof(*s)) ||
        !cpu_span_valid(adapter, sizeof(*adapter)) || !adapter->initialized ||
        cpu_overlap(s, sizeof(*s), adapter, sizeof(*adapter))) return HP1020_UDC_EP0_INVALID;
    const struct hp1020_udc_ep0_span spans[4] = {
        config->out_descriptor, config->in_descriptor, config->out_sink, config->in_staging
    };
    const uint32_t used[4] = {16, 16, 64, 64};
    for (uint32_t i = 0; i < 4; i++) {
        if (!span_valid(spans[i], used[i]) ||
            cpu_overlap(s, sizeof(*s), spans[i].cpu, used[i]) ||
            cpu_overlap(adapter, sizeof(*adapter), spans[i].cpu, used[i]))
            return HP1020_UDC_EP0_INVALID;
        for (uint32_t j = 0; j < i; j++)
            if (cpu_overlap(spans[i].cpu, used[i], spans[j].cpu, used[j]) ||
                dma_overlap(spans[i], used[i], spans[j], used[j])) return HP1020_UDC_EP0_INVALID;
    }
    memset(s, 0, sizeof(*s));
    s->adapter = adapter;
    for (uint32_t i = 0; i < 2; i++) {
        s->slots[i].descriptor = spans[i]; s->slots[i].packet = spans[i+2];
    }
    s->initialized = 1; return HP1020_UDC_EP0_OK;
}

enum hp1020_udc_ep0_result hp1020_udc_ep0_prepare(struct hp1020_udc_ep0 *s,
    uint8_t endpoint, uint8_t *original, uint16_t requested, struct hp1020_tusb_cookie *cookie) {
    enum hp1020_udc_ep0_result r = enter(s);
    if (r) return r;
    struct hp1020_udc_ep0_slot *p = slot_for(s, endpoint);
    if (!p || !cookie || requested > 64 || (!endpoint && requested) ||
        (!requested && original) || (requested && !cpu_span_valid(original, requested)))
        return leave(s, HP1020_UDC_EP0_INVALID);
    if (p->phase != HP1020_UDC_EP0_FREE) return leave(s, HP1020_UDC_EP0_WAIT);
    if (requested) {
        if (cpu_overlap(s, sizeof(*s), original, requested) ||
            cpu_overlap(s->adapter, sizeof(*s->adapter), original, requested))
            return leave(s, HP1020_UDC_EP0_INVALID);
        for (uint32_t i = 0; i < 2; i++)
            if (cpu_overlap(s->slots[i].descriptor.cpu, 16, original, requested) ||
                cpu_overlap(s->slots[i].packet.cpu, 64, original, requested))
                return leave(s, HP1020_UDC_EP0_INVALID);
    }
    struct hp1020_tusb_cookie bound = {0};
    p->last_adapter_result = hp1020_tusb_adapter_bind_submission(s->adapter,
        endpoint, original, requested, &bound);
    if (p->last_adapter_result != HP1020_TUSB_OK) return leave(s, HP1020_UDC_EP0_ADAPTER_ERROR);
    /* No fallible operation follows binding. Keep the ORIGINAL pointer alive
     * in the adapter; only the separate owned staging buffer reaches the DMA. */
    p->cookie = bound; p->original_buffer = original; p->requested = requested;
    p->phase = HP1020_UDC_EP0_PREPARED; p->cancel_requested = p->fault_reported = 0;
    p->fault_reason = 0;
    if (requested) memcpy(p->packet.cpu, original, requested);
    put_be32(p->descriptor.cpu + 4, 0);
    put_be32(p->descriptor.cpu + 8, p->packet.dma);
    put_be32(p->descriptor.cpu + 12, 0);
    put_be32(p->descriptor.cpu, UINT32_C(0x08000000) | requested);
    *cookie = bound;
    return leave(s, HP1020_UDC_EP0_OK);
}

enum hp1020_udc_ep0_result hp1020_udc_ep0_take_submission(struct hp1020_udc_ep0 *s,
    struct hp1020_tusb_cookie cookie, struct hp1020_udc_ep0_publish_facts facts,
    struct hp1020_udc_ep0_submission *submission) {
    enum hp1020_udc_ep0_result r = enter(s);
    if (r) return r;
    struct hp1020_udc_ep0_slot *p = current(s, cookie);
    if (!p) return leave(s, HP1020_UDC_EP0_STALE);
    if (!submission || facts.mode_packet64_be > 1 || facts.descriptor_visible > 1 ||
        facts.packet_dma_ready > 1) return leave(s, HP1020_UDC_EP0_INVALID);
    if (p->phase != HP1020_UDC_EP0_PREPARED || p->cancel_requested || p->fault_reason ||
        !facts.mode_packet64_be || !facts.descriptor_visible || !facts.packet_dma_ready)
        return leave(s, HP1020_UDC_EP0_WAIT);
    struct hp1020_udc_ep0_submission next = {0};
    next.cookie = p->cookie; next.original_buffer = p->original_buffer;
    next.descriptor_cpu = p->descriptor.cpu; next.packet_cpu = p->packet.cpu;
    next.descriptor_dma = p->descriptor.dma; next.packet_dma = p->packet.dma;
    next.requested = p->requested; next.allocation_bytes = 64;
    next.endpoint = p->cookie.endpoint;
    p->phase = HP1020_UDC_EP0_EXPOSED; *submission = next;
    return leave(s, HP1020_UDC_EP0_OK);
}

enum hp1020_udc_ep0_result hp1020_udc_ep0_observe(struct hp1020_udc_ep0 *s,
    const struct hp1020_udc_ep0_observation *observation, struct hp1020_udc_ep0_completion_facts facts) {
    enum hp1020_udc_ep0_result r = enter(s);
    if (r) return r;
    if (!observation) return leave(s, HP1020_UDC_EP0_INVALID);
    struct hp1020_udc_ep0_slot *p = current(s, observation->cookie);
    if (!p) return leave(s, HP1020_UDC_EP0_STALE);
    if (facts.descriptor_cpu_visible > 1 || facts.transfer_settled > 1 ||
        facts.packet_cpu_visible > 1 || facts.in_actual_known > 1)
        return leave(s, HP1020_UDC_EP0_INVALID);
    if (p->fault_reason) return leave(s, report_fault(s, p));
    if (observation->endpoint_fault) {
        p->fault_reason = observation->endpoint_fault; return leave(s, report_fault(s, p));
    }
    if (p->phase != HP1020_UDC_EP0_EXPOSED) return leave(s, HP1020_UDC_EP0_INVALID);
    if (!facts.descriptor_cpu_visible) return leave(s, HP1020_UDC_EP0_WAIT);
    const uint8_t *d = observation->descriptor;
    const uint32_t status = be32(d);
    if ((status >> 30) != 2) return leave(s, HP1020_UDC_EP0_WAIT);
    if (be32(d + 4) || be32(d + 8) != p->packet.dma || be32(d + 12)) {
        p->fault_reason = REASON_DESCRIPTOR_BODY; return leave(s, report_fault(s, p));
    }
    if ((status & UINT32_C(0x30000000)) || !(status & UINT32_C(0x08000000)) ||
        (!p->cookie.endpoint && (status & UINT32_C(0xffff)))) {
        p->fault_reason = REASON_DESCRIPTOR_STATUS; return leave(s, report_fault(s, p));
    }
    if (!facts.transfer_settled || !facts.packet_cpu_visible) return leave(s, HP1020_UDC_EP0_WAIT);
    if (p->cookie.endpoint) {
        if (!facts.in_actual_known) return leave(s, HP1020_UDC_EP0_WAIT);
        if (facts.in_actual != p->requested) {
            p->fault_reason = REASON_IN_ACTUAL; return leave(s, report_fault(s, p));
        }
    }
    p->last_adapter_result = hp1020_tusb_adapter_complete(s->adapter,
        p->cookie, XFER_RESULT_SUCCESS, p->requested);
    if (p->last_adapter_result == HP1020_TUSB_WAIT) return leave(s, HP1020_UDC_EP0_WAIT);
    if (p->last_adapter_result != HP1020_TUSB_OK) return leave(s, HP1020_UDC_EP0_ADAPTER_ERROR);
    retire(p); return leave(s, HP1020_UDC_EP0_OK);
}

enum hp1020_udc_ep0_result hp1020_udc_ep0_request_cancel(struct hp1020_udc_ep0 *s,
    struct hp1020_tusb_cookie cookie) {
    enum hp1020_udc_ep0_result r = enter(s);
    if (r) return r;
    struct hp1020_udc_ep0_slot *p = current(s, cookie);
    if (!p) return leave(s, HP1020_UDC_EP0_STALE);
    p->cancel_requested = 1; return leave(s, HP1020_UDC_EP0_OK);
}
enum hp1020_udc_ep0_result hp1020_udc_ep0_cancelled(struct hp1020_udc_ep0 *s,
    struct hp1020_tusb_cookie cookie, uint8_t transfer_settled) {
    enum hp1020_udc_ep0_result r = enter(s);
    if (r) return r;
    struct hp1020_udc_ep0_slot *p = current(s, cookie);
    if (!p) return leave(s, HP1020_UDC_EP0_STALE);
    if (transfer_settled > 1 || !p->cancel_requested) return leave(s, HP1020_UDC_EP0_INVALID);
    if (!transfer_settled) return leave(s, HP1020_UDC_EP0_WAIT);
    p->last_adapter_result = hp1020_tusb_adapter_cancelled(s->adapter, p->cookie);
    if (p->last_adapter_result == HP1020_TUSB_WAIT) return leave(s, HP1020_UDC_EP0_WAIT);
    if (p->last_adapter_result != HP1020_TUSB_OK) return leave(s, HP1020_UDC_EP0_ADAPTER_ERROR);
    retire(p); return leave(s, HP1020_UDC_EP0_OK);
}
