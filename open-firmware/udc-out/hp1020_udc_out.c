/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_udc_out.h"
#include <string.h>

#define REASON_DESCRIPTOR_BODY UINT32_C(0x80000101)
#define REASON_DESCRIPTOR_STATUS UINT32_C(0x80000102)

static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
        ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void put_be32(uint8_t *p, uint32_t value) {
    p[0] = (uint8_t)(value >> 24);
    p[1] = (uint8_t)(value >> 16);
    p[2] = (uint8_t)(value >> 8);
    p[3] = (uint8_t)value;
}

static bool same_cookie(struct hp1020_tusb_cookie a, struct hp1020_tusb_cookie b) {
    return a.id == b.id && a.epoch == b.epoch && a.generation == b.generation &&
        a.sequence == b.sequence && a.endpoint == b.endpoint;
}

static bool cpu_span_valid(const void *p, uintptr_t bytes) {
    return p && bytes && (uintptr_t)p <= UINTPTR_MAX - (bytes - 1);
}

static bool cpu_overlap(const void *a, uintptr_t an, const void *b, uintptr_t bn) {
    /* Both ranges have already been checked for nonzero size and no wrap. */
    return (uintptr_t)a <= (uintptr_t)b + bn - 1 &&
        (uintptr_t)b <= (uintptr_t)a + an - 1;
}

static bool span_valid(struct hp1020_udc_out_span span, uint32_t needed) {
    return span.bytes >= needed && cpu_span_valid(span.cpu, span.bytes) &&
        span.dma && span.dma <= UINT32_MAX - (span.bytes - 1) &&
        !((uintptr_t)span.cpu & 15u) && !(span.dma & 15u);
}

static bool dma_overlap(struct hp1020_udc_out_span a, uint32_t an,
    struct hp1020_udc_out_span b, uint32_t bn) {
    return a.dma <= b.dma + bn - 1 && b.dma <= a.dma + an - 1;
}

static enum hp1020_udc_out_result enter(struct hp1020_udc_out *s) {
    if (!s || !s->initialized || !s->adapter) return HP1020_UDC_OUT_INVALID;
    if (s->busy) return HP1020_UDC_OUT_WAIT;
    s->busy = 1;
    return HP1020_UDC_OUT_OK;
}

static enum hp1020_udc_out_result leave(struct hp1020_udc_out *s,
    enum hp1020_udc_out_result result) {
    s->busy = 0;
    return result;
}

static bool current(const struct hp1020_udc_out *s, struct hp1020_tusb_cookie c) {
    return s->phase != HP1020_UDC_OUT_FREE && c.id && same_cookie(s->cookie, c);
}

static void retire(struct hp1020_udc_out *s) {
    /* Do not touch the descriptor or payload; the adapter owns completed data. */
    memset(&s->cookie, 0, sizeof(s->cookie));
    memset(&s->buffer, 0, sizeof(s->buffer));
    s->phase = HP1020_UDC_OUT_FREE;
    s->cancel_requested = 0;
    s->fault_reported = 0;
    s->fault_reason = 0;
}

static enum hp1020_udc_out_result report_fault(struct hp1020_udc_out *s) {
    s->cancel_requested = 1;
    if (s->fault_reported) return HP1020_UDC_OUT_FAULT;
    s->last_adapter_result = hp1020_tusb_adapter_fault(s->adapter,
        s->cookie.epoch, s->cookie.generation, s->fault_reason);
    if (s->last_adapter_result == HP1020_TUSB_WAIT) return HP1020_UDC_OUT_WAIT;
    if (s->last_adapter_result == HP1020_TUSB_OK ||
        s->last_adapter_result == HP1020_TUSB_STALE) {
        /* A stale fault must not alter a later generation. Retain the old
         * storage anyway until its own explicit cancellation settlement. */
        s->fault_reported = 1;
        return HP1020_UDC_OUT_FAULT;
    }
    return HP1020_UDC_OUT_ADAPTER_ERROR;
}

enum hp1020_udc_out_result hp1020_udc_out_init(struct hp1020_udc_out *s,
    struct hp1020_tusb_adapter *adapter, struct hp1020_udc_out_span descriptor) {
    if (!s || !adapter || !adapter->initialized || adapter->config.ep_out != 1 ||
        adapter->config.out_capacity != HP1020_UDC_OUT_PACKET_BYTES ||
        !cpu_span_valid(s, sizeof(*s)) || !cpu_span_valid(adapter, sizeof(*adapter)) ||
        !span_valid(descriptor, HP1020_UDC_OUT_DESCRIPTOR_BYTES) ||
        cpu_overlap(s, sizeof(*s), adapter, sizeof(*adapter)) ||
        cpu_overlap(s, sizeof(*s), descriptor.cpu, HP1020_UDC_OUT_DESCRIPTOR_BYTES) ||
        cpu_overlap(adapter, sizeof(*adapter), descriptor.cpu, HP1020_UDC_OUT_DESCRIPTOR_BYTES))
        return HP1020_UDC_OUT_INVALID;
    memset(s, 0, sizeof(*s));
    s->adapter = adapter;
    s->descriptor = descriptor;
    s->initialized = 1;
    return HP1020_UDC_OUT_OK;
}

enum hp1020_udc_out_result hp1020_udc_out_prepare(struct hp1020_udc_out *s,
    uint8_t endpoint, struct hp1020_udc_out_span buffer, uint16_t requested,
    struct hp1020_tusb_cookie *cookie) {
    enum hp1020_udc_out_result r = enter(s);
    if (r) return r;
    if (s->phase != HP1020_UDC_OUT_FREE) return leave(s, HP1020_UDC_OUT_WAIT);
    if (!cookie || endpoint != 1 || requested != HP1020_UDC_OUT_PACKET_BYTES ||
        !span_valid(buffer, HP1020_UDC_OUT_PACKET_BYTES) ||
        cpu_overlap(s, sizeof(*s), buffer.cpu, HP1020_UDC_OUT_PACKET_BYTES) ||
        cpu_overlap(s->adapter, sizeof(*s->adapter), buffer.cpu, HP1020_UDC_OUT_PACKET_BYTES) ||
        cpu_overlap(s->descriptor.cpu, HP1020_UDC_OUT_DESCRIPTOR_BYTES,
                    buffer.cpu, HP1020_UDC_OUT_PACKET_BYTES) ||
        dma_overlap(s->descriptor, HP1020_UDC_OUT_DESCRIPTOR_BYTES,
                    buffer, HP1020_UDC_OUT_PACKET_BYTES))
        return leave(s, HP1020_UDC_OUT_INVALID);
    struct hp1020_tusb_cookie bound = {0};
    s->last_adapter_result = hp1020_tusb_adapter_bind_submission(s->adapter,
        endpoint, buffer.cpu, requested, &bound);
    if (s->last_adapter_result != HP1020_TUSB_OK)
        return leave(s, HP1020_UDC_OUT_ADAPTER_ERROR);
    /* No fallible operation follows binding. No borrowed bytes were modified
     * before the adapter granted this exact cookie. All descriptor bytes are
     * complete before take_submission can expose them. */
    s->cookie = bound;
    s->buffer = buffer;
    s->phase = HP1020_UDC_OUT_PREPARED;
    s->cancel_requested = s->fault_reported = 0;
    s->fault_reason = 0;
    put_be32(s->descriptor.cpu + 4, 0);
    put_be32(s->descriptor.cpu + 8, buffer.dma);
    put_be32(s->descriptor.cpu + 12, 0);
    put_be32(s->descriptor.cpu, UINT32_C(0x08000000));
    *cookie = bound;
    return leave(s, HP1020_UDC_OUT_OK);
}

enum hp1020_udc_out_result hp1020_udc_out_take_submission(struct hp1020_udc_out *s,
    struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_publish_facts facts,
    struct hp1020_udc_out_submission *submission) {
    enum hp1020_udc_out_result r = enter(s);
    if (r) return r;
    if (!current(s, cookie)) return leave(s, HP1020_UDC_OUT_STALE);
    if (!submission || facts.mode_packet64_be > 1 || facts.descriptor_visible > 1 ||
        facts.buffer_dma_ready > 1) return leave(s, HP1020_UDC_OUT_INVALID);
    if (s->phase != HP1020_UDC_OUT_PREPARED || s->cancel_requested || s->fault_reason)
        return leave(s, HP1020_UDC_OUT_WAIT);
    if (!facts.mode_packet64_be || !facts.descriptor_visible || !facts.buffer_dma_ready)
        return leave(s, HP1020_UDC_OUT_WAIT);
    struct hp1020_udc_out_submission next = {0};
    next.cookie = s->cookie;
    next.descriptor_cpu = s->descriptor.cpu;
    next.buffer_cpu = s->buffer.cpu;
    next.descriptor_dma = s->descriptor.dma;
    next.buffer_dma = s->buffer.dma;
    next.capacity = HP1020_UDC_OUT_PACKET_BYTES;
    next.endpoint = 1;
    s->phase = HP1020_UDC_OUT_EXPOSED;
    *submission = next;
    return leave(s, HP1020_UDC_OUT_OK);
}

enum hp1020_udc_out_result hp1020_udc_out_observe(struct hp1020_udc_out *s,
    const struct hp1020_udc_out_observation *observation,
    struct hp1020_udc_out_completion_facts facts) {
    enum hp1020_udc_out_result r = enter(s);
    if (r) return r;
    if (!observation) return leave(s, HP1020_UDC_OUT_INVALID);
    if (!current(s, observation->cookie)) return leave(s, HP1020_UDC_OUT_STALE);
    if (facts.descriptor_cpu_visible > 1 || facts.transfer_settled > 1 ||
        facts.payload_cpu_visible > 1) return leave(s, HP1020_UDC_OUT_INVALID);
    if (s->fault_reason) return leave(s, report_fault(s));
    if (observation->endpoint_fault) {
        s->fault_reason = observation->endpoint_fault;
        return leave(s, report_fault(s));
    }
    if (s->phase != HP1020_UDC_OUT_EXPOSED)
        return leave(s, HP1020_UDC_OUT_INVALID);
    if (!facts.descriptor_cpu_visible) return leave(s, HP1020_UDC_OUT_WAIT);
    const uint8_t *d = observation->descriptor;
    const uint32_t status = be32(d);
    if ((status >> 30) != 2) return leave(s, HP1020_UDC_OUT_WAIT);
    if (be32(d + 4) || be32(d + 8) != s->buffer.dma || be32(d + 12)) {
        s->fault_reason = REASON_DESCRIPTOR_BODY;
        return leave(s, report_fault(s));
    }
    const uint32_t count = status & UINT32_C(0xffff);
    if ((status & UINT32_C(0x30000000)) || !(status & UINT32_C(0x08000000)) ||
        count > HP1020_UDC_OUT_PACKET_BYTES) {
        s->fault_reason = REASON_DESCRIPTOR_STATUS;
        return leave(s, report_fault(s));
    }
    if (!facts.transfer_settled || !facts.payload_cpu_visible)
        return leave(s, HP1020_UDC_OUT_WAIT);
    s->last_adapter_result = hp1020_tusb_adapter_complete(s->adapter,
        s->cookie, XFER_RESULT_SUCCESS, count);
    if (s->last_adapter_result == HP1020_TUSB_WAIT)
        return leave(s, HP1020_UDC_OUT_WAIT);
    if (s->last_adapter_result != HP1020_TUSB_OK)
        return leave(s, HP1020_UDC_OUT_ADAPTER_ERROR);
    retire(s);
    return leave(s, HP1020_UDC_OUT_OK);
}

enum hp1020_udc_out_result hp1020_udc_out_request_cancel(struct hp1020_udc_out *s,
    struct hp1020_tusb_cookie cookie) {
    enum hp1020_udc_out_result r = enter(s);
    if (r) return r;
    if (!current(s, cookie)) return leave(s, HP1020_UDC_OUT_STALE);
    s->cancel_requested = 1;
    return leave(s, HP1020_UDC_OUT_OK);
}

enum hp1020_udc_out_result hp1020_udc_out_cancelled(struct hp1020_udc_out *s,
    struct hp1020_tusb_cookie cookie, uint8_t transfer_settled) {
    enum hp1020_udc_out_result r = enter(s);
    if (r) return r;
    if (!current(s, cookie)) return leave(s, HP1020_UDC_OUT_STALE);
    if (transfer_settled > 1) return leave(s, HP1020_UDC_OUT_INVALID);
    if (!s->cancel_requested) return leave(s, HP1020_UDC_OUT_INVALID);
    if (!transfer_settled) return leave(s, HP1020_UDC_OUT_WAIT);
    s->last_adapter_result = hp1020_tusb_adapter_cancelled(s->adapter, s->cookie);
    if (s->last_adapter_result == HP1020_TUSB_WAIT)
        return leave(s, HP1020_UDC_OUT_WAIT);
    if (s->last_adapter_result != HP1020_TUSB_OK)
        return leave(s, HP1020_UDC_OUT_ADAPTER_ERROR);
    retire(s);
    return leave(s, HP1020_UDC_OUT_OK);
}
