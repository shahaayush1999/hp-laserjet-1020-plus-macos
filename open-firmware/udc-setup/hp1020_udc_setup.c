/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_udc_setup.h"
#include <string.h>

static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
        ((uint32_t)p[2] << 8) | p[3];
}
static bool cpu_span_valid(const void *p, uintptr_t bytes) {
    return p && bytes && (uintptr_t)p <= UINTPTR_MAX - (bytes - 1);
}
static bool cpu_overlap(const void *a, uintptr_t an, const void *b, uintptr_t bn) {
    return (uintptr_t)a <= (uintptr_t)b + bn - 1 &&
        (uintptr_t)b <= (uintptr_t)a + an - 1;
}
static enum hp1020_udc_setup_result enter(struct hp1020_udc_setup *s) {
    if (!s || !s->initialized || !s->adapter) return HP1020_UDC_SETUP_INVALID;
    if (s->busy) return HP1020_UDC_SETUP_WAIT;
    if (s->terminal) return HP1020_UDC_SETUP_LIMIT;
    /* Detect accidental direct SETUP/reset admission around this bridge. Other
     * adapter operations do not allocate control epochs. Never rewrite an
     * original capture identity to make it match current adapter state. */
    if (s->adapter->control_epoch != s->adapter_control_epoch)
        return HP1020_UDC_SETUP_ADAPTER_ERROR;
    s->busy = 1;
    return HP1020_UDC_SETUP_OK;
}
static enum hp1020_udc_setup_result leave(struct hp1020_udc_setup *s,
    enum hp1020_udc_setup_result result) {
    s->busy = 0;
    return result;
}
static enum hp1020_udc_setup_result adapter_result(struct hp1020_udc_setup *s,
    enum hp1020_tusb_result result) {
    s->last_adapter_result = result;
    if (result == HP1020_TUSB_OK) {
        s->adapter_control_epoch = s->adapter->control_epoch;
        return HP1020_UDC_SETUP_OK;
    }
    if (result == HP1020_TUSB_WAIT) return HP1020_UDC_SETUP_WAIT;
    if (result == HP1020_TUSB_LIMIT) {
        /* A terminal adapter may have advanced control identity before another
         * identity exhausted. Retain the capture and all actual packet owners. */
        s->adapter_control_epoch = s->adapter->control_epoch;
        s->terminal = HP1020_UDC_SETUP_LIMIT_ADAPTER;
        return HP1020_UDC_SETUP_LIMIT;
    }
    return HP1020_UDC_SETUP_ADAPTER_ERROR;
}

enum hp1020_udc_setup_result hp1020_udc_setup_init(struct hp1020_udc_setup *s,
    struct hp1020_tusb_adapter *adapter, uint32_t record_dma) {
    if (!cpu_span_valid(s, sizeof(*s)) || !cpu_span_valid(adapter, sizeof(*adapter)) ||
        cpu_overlap(s, sizeof(*s), adapter, sizeof(*adapter)) ||
        !adapter->initialized || adapter->busy || adapter->exhausted ||
        adapter->control_epoch || adapter->last_submission_id ||
        !record_dma || (record_dma & 15u) || record_dma > UINT32_MAX - 15u)
        return HP1020_UDC_SETUP_INVALID;
    memset(s, 0, sizeof(*s));
    s->adapter = adapter;
    s->record_dma = record_dma;
    s->adapter_control_epoch = adapter->control_epoch;
    s->initialized = 1;
    return HP1020_UDC_SETUP_OK;
}

enum hp1020_udc_setup_result hp1020_udc_setup_offer(struct hp1020_udc_setup *s,
    const struct hp1020_udc_setup_observation *observation) {
    enum hp1020_udc_setup_result r = enter(s);
    if (r) return r;
    if (!cpu_span_valid(observation, sizeof(*observation)) ||
        cpu_overlap(observation, sizeof(*observation), s, sizeof(*s)) ||
        cpu_overlap(observation, sizeof(*observation), s->adapter, sizeof(*s->adapter)) ||
        !observation->sequence) return leave(s, HP1020_UDC_SETUP_INVALID);
    if (observation->sequence <= s->last_sequence)
        return leave(s, HP1020_UDC_SETUP_STALE);
    if (s->pending_kind == HP1020_UDC_SETUP_PENDING_RESET) {
        if (observation->sequence <= s->pending_sequence)
            return leave(s, HP1020_UDC_SETUP_STALE);
        return leave(s, HP1020_UDC_SETUP_WAIT);
    }
    if (s->pending_kind != HP1020_UDC_SETUP_PENDING_NONE)
        return leave(s, HP1020_UDC_SETUP_WAIT);
    if (observation->record_dma != s->record_dma)
        return leave(s, HP1020_UDC_SETUP_INVALID);
    /* Freeze the entire supplied observation before any later facts/admission.
     * This is a private readable snapshot, never a live-DMA acquisition. */
    s->capture = *observation;
    s->last_sequence = observation->sequence;
    s->pending_sequence = observation->sequence;
    s->pending_kind = HP1020_UDC_SETUP_PENDING_CAPTURE;
    if (observation->sequence == UINT32_MAX) {
        s->terminal = HP1020_UDC_SETUP_LIMIT_SEQUENCE;
        return leave(s, HP1020_UDC_SETUP_LIMIT);
    }
    return leave(s, HP1020_UDC_SETUP_OK);
}

enum hp1020_udc_setup_result hp1020_udc_setup_dispatch(struct hp1020_udc_setup *s,
    uint32_t sequence, struct hp1020_udc_setup_capture_facts facts,
    uint8_t ep0_stalls_cleared) {
    enum hp1020_udc_setup_result r = enter(s);
    if (r) return r;
    if (s->pending_kind == HP1020_UDC_SETUP_PENDING_RESET)
        return leave(s, HP1020_UDC_SETUP_WAIT);
    if (s->pending_kind != HP1020_UDC_SETUP_PENDING_CAPTURE || !sequence ||
        sequence != s->pending_sequence || sequence != s->capture.sequence)
        return leave(s, HP1020_UDC_SETUP_STALE);
    if (facts.format_be_wire > 1 || facts.cpu_visible > 1 || facts.stable > 1 ||
        ep0_stalls_cleared > 1) return leave(s, HP1020_UDC_SETUP_INVALID);
    if (!facts.format_be_wire || !facts.cpu_visible || !facts.stable || !ep0_stalls_cleared)
        return leave(s, HP1020_UDC_SETUP_WAIT);
    if (s->capture.endpoint_fault) return leave(s, HP1020_UDC_SETUP_FAULT);
    const uint32_t status = be32(s->capture.record);
    if ((status >> 30) != 2) return leave(s, HP1020_UDC_SETUP_WAIT);
    if (status & UINT32_C(0x30000000)) return leave(s, HP1020_UDC_SETUP_FAULT);
    /* Do not reinterpret reserved/wire bytes as normal-descriptor pointer,
     * count or L fields. TinyUSB performs its own wire-field conversion. */
    r = adapter_result(s, hp1020_tusb_adapter_setup(s->adapter,
        s->capture.record + 8, 8, &s->capture.printer_status));
    if (r == HP1020_UDC_SETUP_OK) {
        s->last_admitted_sequence = sequence;
        s->pending_kind = HP1020_UDC_SETUP_PENDING_NONE;
        s->pending_sequence = 0;
    }
    return leave(s, r);
}

enum hp1020_udc_setup_result hp1020_udc_setup_bus_reset(struct hp1020_udc_setup *s,
    uint32_t sequence, tusb_speed_t speed) {
    enum hp1020_udc_setup_result r = enter(s);
    if (r) return r;
    if (!sequence || speed != TUSB_SPEED_FULL) return leave(s, HP1020_UDC_SETUP_INVALID);
    if (s->pending_kind == HP1020_UDC_SETUP_PENDING_RESET) {
        if (sequence < s->pending_sequence) return leave(s, HP1020_UDC_SETUP_STALE);
        if (sequence != s->pending_sequence) return leave(s, HP1020_UDC_SETUP_WAIT);
    } else {
        if (sequence <= s->last_sequence) return leave(s, HP1020_UDC_SETUP_STALE);
        /* The actual reset is now the one pending event. Preserve any older
         * capture bytes, but never allow them or a later event to bypass retry. */
        s->pending_kind = HP1020_UDC_SETUP_PENDING_RESET;
        s->pending_sequence = sequence;
    }
    if (sequence == UINT32_MAX) {
        s->terminal = HP1020_UDC_SETUP_LIMIT_SEQUENCE;
        return leave(s, HP1020_UDC_SETUP_LIMIT);
    }
    r = adapter_result(s, hp1020_tusb_adapter_bus_reset(s->adapter, speed));
    if (r == HP1020_UDC_SETUP_OK) {
        s->last_sequence = sequence;
        s->last_reset_sequence = sequence;
        s->reset_control_epoch = s->adapter_control_epoch;
        s->pending_kind = HP1020_UDC_SETUP_PENDING_NONE;
        s->pending_sequence = 0;
    }
    return leave(s, r);
}

uint32_t hp1020_udc_setup_progress(const struct hp1020_udc_setup *s) {
    if (!s || !s->initialized || !s->adapter || s->busy || s->adapter->busy ||
        s->adapter->exhausted || s->adapter->control_epoch != s->adapter_control_epoch ||
        s->pending_kind == HP1020_UDC_SETUP_PENDING_RESET) return 0;
    /* Successful reset admission advanced the existing control epoch. It is
     * active only after adapter service drained owners and delivered that reset.
     * A subsequent accepted SETUP has a different epoch and cannot match here. */
    if (s->reset_control_epoch && s->adapter_control_epoch == s->reset_control_epoch &&
        s->adapter->active_control_epoch != s->reset_control_epoch)
        return HP1020_UDC_SETUP_ALLOW_SERVICE;
    if (s->terminal || s->pending_kind != HP1020_UDC_SETUP_PENDING_NONE) return 0;
    return HP1020_UDC_SETUP_ALLOW_SERVICE | HP1020_UDC_SETUP_ALLOW_ARM |
        HP1020_UDC_SETUP_ALLOW_PUMP;
}
