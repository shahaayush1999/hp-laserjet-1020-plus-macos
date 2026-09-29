/* SPDX-License-Identifier: GPL-2.0-or-later
 * Synthetic descriptor boundary only. No MMIO, IRQ, DMA or USB device access.
 * The shared fixture supplies genuine TinyUSB/class/document dispatch. Only
 * the bulk DCD submission and event ingress are replaced by this boundary.
 */
#include "hp1020_udc_out.h"

#define dcd_edpt_xfer hp1020_udc_base_dcd_edpt_xfer
#define hp1020_bulk_fixture_reset hp1020_udc_base_reset
#define hp1020_bulk_fixture_step hp1020_udc_base_step
#include "tinyusb-printer-test/fixture.c"
#undef dcd_edpt_xfer
#undef hp1020_bulk_fixture_reset
#undef hp1020_bulk_fixture_step

#define DESCRIPTOR_DMA UINT32_C(0x13579bd0)
#define BUFFER_DMA_BASE UINT32_C(0x24681340)
#define BUFFER_DMA_STEP UINT32_C(0x1000)
#define SNAPSHOTS 8u

uint32_t hp1020_udc_fixture_stats[48];
static _Alignas(16) struct hp1020_udc_out boundary;
static struct {
    _Alignas(16) uint8_t before[16];
    struct hp1020_udc_out_memory data;
    uint8_t after[16];
} descriptor_memory;
_Static_assert(sizeof(descriptor_memory) == 48, "portable descriptor capture");
static uint8_t descriptor_shadow[16], publication_bytes[16];
static struct hp1020_udc_out_submission publication;
static struct hp1020_udc_out_observation saved[SNAPSHOTS];
static uint8_t saved_valid[SNAPSHOTS];
static struct {
    uint32_t result, violations, preparations, publications, completions;
    uint32_t cancellations, stale, cancel_marks, steps, last_slot;
    uint32_t observed_id, observed_status, observed_fault, observed_facts;
    uint32_t inject, inject_dma, inject_bytes;
    uint8_t automatic;
    struct hp1020_udc_out_publish_facts publish;
} udc_state;

static uint32_t udc_be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
        ((uint32_t)p[2] << 8) | p[3];
}

static void udc_violation(void) {
    udc_state.violations++;
    state.violations++;
}

static int udc_canaries(void) {
    for (uint32_t i = 0; i < 16; i++)
        if (descriptor_memory.before[i] != state.fill ||
            descriptor_memory.after[i] != state.fill) return 0;
    return 1;
}

static void udc_check(void) {
    if (!udc_canaries() || memcmp(descriptor_shadow,
        descriptor_memory.data.descriptor, sizeof(descriptor_shadow))) udc_violation();
}

static int udc_history(uint32_t id, struct hp1020_tusb_cookie *cookie) {
    if (!id || id >= 4096 || history[id].id != id) return 0;
    *cookie = history[id];
    return 1;
}

static struct hp1020_tusb_cookie udc_mutate(struct hp1020_tusb_cookie c,
    uint32_t mutation) {
    if (mutation == 1) c.id ^= UINT32_C(0x80000000);
    else if (mutation == 2) c.epoch ^= UINT32_C(0x80000000);
    else if (mutation == 3) c.generation ^= UINT32_C(0x80000000);
    else if (mutation == 4) c.sequence ^= UINT32_C(0x80000000);
    else if (mutation == 5) c.endpoint ^= 0x80;
    return c;
}

static int udc_current(struct hp1020_tusb_cookie cookie) {
    return boundary.phase != HP1020_UDC_OUT_FREE && cookie.id &&
        same_cookie(boundary.cookie, cookie);
}

static void udc_cookie_words(uint32_t *out, struct hp1020_tusb_cookie c) {
    out[0] = c.id; out[1] = c.epoch; out[2] = c.generation;
    out[3] = c.sequence; out[4] = c.endpoint;
}

static void udc_snapshot(void) {
    uint32_t *out = hp1020_udc_fixture_stats;
    memset(out, 0, sizeof(hp1020_udc_fixture_stats));
    out[0] = udc_state.result; out[1] = boundary.initialized;
    out[2] = boundary.phase; out[3] = boundary.cancel_requested;
    out[4] = boundary.fault_reported; out[5] = boundary.fault_reason;
    out[6] = boundary.last_adapter_result; out[7] = udc_state.violations;
    out[8] = (uint32_t)udc_canaries();
    out[9] = memcmp(descriptor_shadow, descriptor_memory.data.descriptor, 16) == 0;
    out[10] = udc_state.preparations; out[11] = udc_state.publications;
    out[12] = udc_state.completions; out[13] = udc_state.cancellations;
    out[14] = udc_state.stale; out[15] = udc_state.cancel_marks;
    udc_cookie_words(out + 16, boundary.cookie);
    out[21] = boundary.descriptor.dma; out[22] = boundary.buffer.dma;
    out[23] = boundary.buffer.bytes;
    for (uint32_t i = 0; i < 4; i++) {
        out[24+i] = udc_be32(descriptor_memory.data.descriptor + 4*i);
        out[33+i] = udc_be32(publication_bytes + 4*i);
    }
    udc_cookie_words(out + 28, publication.cookie);
    out[37] = publication.descriptor_dma; out[38] = publication.buffer_dma;
    out[39] = publication.capacity;
    out[40] = udc_state.observed_id; out[41] = udc_state.observed_status;
    out[42] = udc_state.observed_fault; out[43] = udc_state.observed_facts;
    out[44] = udc_state.inject;
    out[45] = ((uint32_t)udc_state.automatic << 24) |
        ((uint32_t)udc_state.publish.mode_packet64_be << 16) |
        ((uint32_t)udc_state.publish.descriptor_visible << 8) |
        udc_state.publish.buffer_dma_ready;
    out[46] = udc_state.steps; out[47] = udc_state.last_slot;
}

static enum hp1020_udc_out_result udc_publish(struct hp1020_tusb_cookie cookie,
    struct hp1020_udc_out_publish_facts facts) {
    struct hp1020_udc_out_submission next;
    const enum hp1020_udc_out_result r = hp1020_udc_out_take_submission(
        &boundary, cookie, facts, &next);
    udc_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK) {
        publication = next;
        udc_state.publications++;
        /* Check native pointer identity independently before dereferencing a
         * returned pointer. Keep the observed proposal even when it is wrong;
         * do not normalize it into the fixture's expected publication. */
        if (!packets[2].live || next.buffer_cpu != packets[2].buffer ||
            next.descriptor_cpu != descriptor_memory.data.descriptor ||
            next.endpoint != 1 || next.capacity != 64 ||
            !same_cookie(next.cookie, packets[2].cookie)) udc_violation();
        else memcpy(publication_bytes, next.descriptor_cpu, 16);
    } else if (r == HP1020_UDC_OUT_STALE) udc_state.stale++;
    return r;
}

/* This wrapper is the real symbol called by separately compiled TinyUSB.
 * The renamed shared implementation still handles ordinary EP0 packets.
 */
bool dcd_edpt_xfer(uint8_t rhport, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, bool in_isr) {
    if (endpoint != 1)
        return hp1020_udc_base_dcd_edpt_xfer(rhport, endpoint, buffer, length, in_isr);
    (void)in_isr;
    check_owned(); udc_check();
    if (rhport || !buffer || length != 64 || packets[2].live ||
        !(state.open_mask & endpoint_bit(endpoint))) { udc_violation(); return false; }
    uint32_t slot = UINT32_MAX;
    for (uint32_t i = 0; i < HP1020_RX_SLOTS; i++)
        if (buffer == memory.data.receive.data[i]) slot = i;
    if (slot == UINT32_MAX) { udc_violation(); return false; }
    udc_state.last_slot = slot;
    const uint32_t injection = udc_state.inject;
    udc_state.inject = 0;
    const uint32_t failure = state.fail_submission;
    state.fail_submission = 0;
    if (failure == 1 || injection == 12) return false;
    struct hp1020_udc_out_span span = {
        buffer, BUFFER_DMA_BASE + BUFFER_DMA_STEP*slot, 64
    };
    uint16_t requested = length;
    uint8_t requested_endpoint = endpoint;
    if (injection == 1) span.cpu = NULL;
    else if (injection == 2) span.cpu++;
    else if (injection == 3) span.bytes = 63;
    else if (injection == 4) span.dma++;
    else if (injection == 5) span.dma = 0;
    else if (injection == 6) span.dma = UINT32_C(0xfffffff0);
    else if (injection == 7) span.cpu = descriptor_memory.data.descriptor;
    else if (injection == 8) span.dma = DESCRIPTOR_DMA;
    else if (injection == 9) span.cpu = (uint8_t *)(void *)&adapter;
    else if (injection == 10) requested = 63;
    else if (injection == 11) requested_endpoint = 0x81;
    else if (injection == 15) span.cpu = (uint8_t *)(void *)&boundary;
    else if (injection == 16) {
        span.dma = udc_state.inject_dma; span.bytes = udc_state.inject_bytes;
    } else if (injection == 17) span.cpu = (uint8_t *)(UINTPTR_MAX - 15);
    struct hp1020_tusb_cookie cookie;
    enum hp1020_udc_out_result r = hp1020_udc_out_prepare(&boundary,
        requested_endpoint, span, requested, &cookie);
    udc_state.result = (uint32_t)r;
    if (r != HP1020_UDC_OUT_OK) return false;
    memcpy(descriptor_shadow, descriptor_memory.data.descriptor, 16);
    udc_state.preparations++;
    /* Even a subsequent backend rejection retains this exact bound cookie. */
    struct packet *p = &packets[2];
    p->cookie = cookie; p->buffer = buffer; p->length = length;
    p->live = 1; p->cancel_requested = 0;
    memcpy(p->shadow, buffer, length);
    state.submissions++; state.last_id = cookie.id;
    state.last_ep = endpoint; state.last_length = length;
    if (!cookie.id || cookie.id >= 4096) { udc_violation(); return false; }
    history[cookie.id] = cookie;
    if (injection == 13) return false;
    if (udc_state.automatic) {
        r = udc_publish(cookie, udc_state.publish);
        /* WAIT means an accepted, retained DCD request awaiting supplied facts.
         * An invalid publication proposal instead fails the DCD submission. */
        if (r != HP1020_UDC_OUT_OK && r != HP1020_UDC_OUT_WAIT) return false;
    }
    return failure != 2 && injection != 14;
}

static enum hp1020_udc_out_result udc_cancel_request(struct hp1020_tusb_cookie cookie) {
    const uint8_t previous = boundary.cancel_requested;
    const enum hp1020_udc_out_result r = hp1020_udc_out_request_cancel(&boundary, cookie);
    udc_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK && !previous) udc_state.cancel_marks++;
    if (r == HP1020_UDC_OUT_STALE) udc_state.stale++;
    return r;
}

/* Adapter callbacks only queue cancellation in the base packet ledger. This
 * function runs after initiating adapter/component calls have fully returned.
 */
static void udc_drain_cancel_request(void) {
    if (packets[2].live && packets[2].cancel_requested &&
        udc_current(packets[2].cookie) && !boundary.cancel_requested) {
        const uint32_t previous_result = udc_state.result;
        if (udc_cancel_request(packets[2].cookie) != HP1020_UDC_OUT_OK) udc_violation();
        /* Expose the primary call's result, not this queued bookkeeping call. */
        udc_state.result = previous_result;
    }
}

static enum hp1020_udc_out_result udc_observe(
    struct hp1020_udc_out_observation observation, uint32_t facts,
    uint32_t mutation, uint8_t raw_facts) {
    if (facts > (raw_facts ? UINT32_C(0xffffff) : 7u) || mutation > 5)
        return HP1020_UDC_OUT_INVALID;
    observation.cookie = udc_mutate(observation.cookie, mutation);
    udc_state.observed_id = observation.cookie.id;
    udc_state.observed_status = udc_be32(observation.descriptor);
    udc_state.observed_fault = observation.endpoint_fault;
    udc_state.observed_facts = facts;
    const struct hp1020_udc_out_completion_facts supplied = {
        (uint8_t)(raw_facts ? ((facts >> 16) & 255) : (facts & 1)),
        (uint8_t)(raw_facts ? ((facts >> 8) & 255) : ((facts >> 1) & 1)),
        (uint8_t)(raw_facts ? (facts & 255) : ((facts >> 2) & 1))
    };
    const enum hp1020_udc_out_result r = hp1020_udc_out_observe(&boundary, &observation, supplied);
    udc_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK) {
        if (!packets[2].live || !same_cookie(packets[2].cookie, observation.cookie)) udc_violation();
        packets[2].live = 0; state.completions++; udc_state.completions++;
    } else if (r == HP1020_UDC_OUT_STALE) { state.stale++; udc_state.stale++; }
    return r;
}

static enum hp1020_udc_out_result udc_cancelled(struct hp1020_tusb_cookie cookie,
    uint32_t settled, uint32_t mutation) {
    if (settled > 255 || mutation > 5) return HP1020_UDC_OUT_INVALID;
    cookie = udc_mutate(cookie, mutation);
    const enum hp1020_udc_out_result r = hp1020_udc_out_cancelled(&boundary, cookie, (uint8_t)settled);
    udc_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK) {
        if (!packets[2].live || !same_cookie(packets[2].cookie, cookie)) udc_violation();
        packets[2].live = 0; state.cancellations++; udc_state.cancellations++;
    } else if (r == HP1020_UDC_OUT_STALE) { state.stale++; udc_state.stale++; }
    return r;
}

static enum hp1020_udc_out_result udc_probe_init(uint32_t kind, uint32_t dma, uint32_t bytes) {
    if (kind > 10) return HP1020_UDC_OUT_INVALID;
    _Alignas(16) struct hp1020_udc_out probe;
    memset(&probe, (int)state.fill, sizeof(probe));
    struct hp1020_udc_out_span span = {descriptor_memory.data.descriptor, DESCRIPTOR_DMA, 16};
    if (kind == 1) span.cpu = NULL;
    else if (kind == 2) span.cpu++;
    else if (kind == 3) span.bytes = 15;
    else if (kind == 4) span.dma++;
    else if (kind == 5) span.dma = 0;
    else if (kind == 6) { span.dma = UINT32_C(0xfffffff0); span.bytes = 32; }
    else if (kind == 7) span.cpu = (uint8_t *)(void *)&probe;
    else if (kind == 8) span.cpu = (uint8_t *)(void *)&adapter;
    else if (kind == 9) { span.dma = dma; span.bytes = bytes; }
    else if (kind == 10) span.cpu = (uint8_t *)(UINTPTR_MAX - 7);
    /* First use of a separate scratch record; no active record is reinitialized
     * and no descriptor byte is written by init, including the valid control. */
    return hp1020_udc_out_init(&probe, &adapter, span);
}

uint32_t hp1020_bulk_fixture_reset(uint32_t fill, uint32_t capacity,
    uint32_t interface_number, uint32_t fail_at) {
    /* A fresh process or ELF is mandatory, exactly as for the included fixture. */
    memset(&udc_state, 0, sizeof(udc_state));
    memset(&boundary, 0, sizeof(boundary));
    memset(&publication, 0, sizeof(publication));
    memset(publication_bytes, 0, sizeof(publication_bytes));
    memset(saved_valid, 0, sizeof(saved_valid));
    memset(&descriptor_memory, (int)(fill & 255), sizeof(descriptor_memory));
    memcpy(descriptor_shadow, descriptor_memory.data.descriptor, 16);
    udc_state.last_slot = UINT32_MAX;
    udc_state.automatic = 1;
    udc_state.publish = (struct hp1020_udc_out_publish_facts){1, 1, 1};
    uint32_t r = hp1020_udc_base_reset(fill, capacity, interface_number, fail_at);
    if (!r) {
        const struct hp1020_udc_out_span span = {descriptor_memory.data.descriptor, DESCRIPTOR_DMA, 16};
        r = (uint32_t)hp1020_udc_out_init(&boundary, &adapter, span);
    }
    udc_state.result = r; state.initialized = r;
    udc_check(); snapshot(r); udc_snapshot(); return r;
}

uint32_t hp1020_bulk_fixture_step(uint32_t op, uint32_t a, uint32_t b,
    uint32_t c, uint32_t d) {
    uint32_t r = HP1020_UDC_OUT_INVALID;
    struct hp1020_tusb_cookie cookie = {0};
    check_owned(); udc_check(); udc_state.steps++;
    const int have_cookie = udc_history(a, &cookie);
    const int bulk_cookie = have_cookie && cookie.endpoint == 1;
    if (op < 20 && !(op == 4 && bulk_cookie)) {
        /* Bulk completion must supply raw descriptor evidence via op22/28.
         * Writes cannot precede publication. Ordinary EP0 operations stay as-is. */
        if ((op == 2 && bulk_cookie) ||
            (op == 3 && bulk_cookie && (!udc_current(cookie) ||
             boundary.phase != HP1020_UDC_OUT_EXPOSED))) {
            memset(hp1020_bulk_fixture_input, state.fill ^ 255, sizeof(hp1020_bulk_fixture_input));
        } else r = hp1020_udc_base_step(op, a, b, c, d);
    } else {
        /* These operations may alter transport metadata but no document/input
         * or accepted output byte. Keep an exact, independent pre-call copy. */
        memcpy(&protected_memory, &memory.data, sizeof(memory.data));
        if (op == 4 && bulk_cookie) r = (uint32_t)udc_cancelled(cookie, 1, 0);
        else if (op == 20 && a <= 1 && b <= 255 && c <= 255 && d <= 255) {
            udc_state.automatic = (uint8_t)a;
            udc_state.publish = (struct hp1020_udc_out_publish_facts){(uint8_t)b, (uint8_t)c, (uint8_t)d};
            r = HP1020_UDC_OUT_OK;
        } else if (op == 21 && have_cookie && b <= 255 && c <= 255 && d <= 255) {
            const struct hp1020_udc_out_publish_facts facts = {(uint8_t)b, (uint8_t)c, (uint8_t)d};
            r = (uint32_t)udc_publish(cookie, facts);
        } else if ((op == 22 || op == 30) && have_cookie) {
            struct hp1020_udc_out_observation observation;
            observation.cookie = cookie; observation.endpoint_fault = c;
            memcpy(observation.descriptor, hp1020_bulk_fixture_input, 16);
            r = (uint32_t)udc_observe(observation, b, d, (uint8_t)(op == 30));
        } else if (op == 23 && have_cookie && d <= 5)
            r = (uint32_t)udc_cancel_request(udc_mutate(cookie, d));
        else if (op == 24 && have_cookie) r = (uint32_t)udc_cancelled(cookie, b, d);
        else if (op == 25 && a <= 17) {
            udc_state.inject = a; udc_state.inject_dma = b; udc_state.inject_bytes = c;
            r = HP1020_UDC_OUT_OK;
        } else if (op == 26 && have_cookie && udc_current(cookie) &&
            boundary.phase == HP1020_UDC_OUT_EXPOSED && b <= 16 && c <= 16-b) {
            memcpy(descriptor_memory.data.descriptor + b, hp1020_bulk_fixture_input, c);
            memcpy(descriptor_shadow + b, hp1020_bulk_fixture_input, c);
            r = HP1020_UDC_OUT_OK;
        } else if (op == 27 && have_cookie && udc_current(cookie) &&
            boundary.phase == HP1020_UDC_OUT_EXPOSED && b < SNAPSHOTS) {
            saved[b].cookie = cookie; saved[b].endpoint_fault = 0;
            memcpy(saved[b].descriptor, descriptor_memory.data.descriptor, 16);
            saved_valid[b] = 1; r = HP1020_UDC_OUT_OK;
        } else if (op == 28 && a < SNAPSHOTS && saved_valid[a]) {
            struct hp1020_udc_out_observation observation = saved[a];
            observation.endpoint_fault = c;
            r = (uint32_t)udc_observe(observation, b, d, 0);
        } else if (op == 29) r = (uint32_t)udc_probe_init(a, b, c);
        if (memcmp(&protected_memory, &memory.data, sizeof(memory.data))) udc_violation();
        memset(hp1020_bulk_fixture_input, state.fill ^ 255, sizeof(hp1020_bulk_fixture_input));
        udc_state.result = r;
    }
    udc_drain_cancel_request();
    /* Recheck all independent borrowed-buffer/output shadows after cancellation
     * bookkeeping too; no callback is permitted to settle or erase ownership. */
    udc_check(); snapshot(r); udc_snapshot(); return r;
}

uint8_t *hp1020_udc_fixture_descriptor_storage(void) {
    return (uint8_t *)(void *)&descriptor_memory;
}
uint32_t hp1020_udc_fixture_descriptor_storage_bytes(void) {
    return (uint32_t)sizeof(descriptor_memory);
}
uint32_t hp1020_udc_fixture_component_bytes(void) {
    return (uint32_t)(sizeof(struct hp1020_udc_out) + sizeof(struct hp1020_udc_out_memory));
}
