/* SPDX-License-Identifier: GPL-2.0-or-later
 * One RAM-only composed DCD. No MMIO, IRQ or device access.
 */
#include "hp1020_udc_out.h"
#include "hp1020_udc_setup.h"

static bool composed_bulk_xfer(uint8_t, uint8_t, uint8_t *, uint16_t, bool);
#define HP1020_EP0_DCD_XFER composed_ep0_xfer
#define HP1020_EP0_SET_ADDRESS composed_ep0_set_address
#define HP1020_EP0_FIXTURE_RESET composed_ep0_reset
#define HP1020_EP0_FIXTURE_STEP composed_ep0_step
#define HP1020_EP0_BULK_XFER composed_bulk_xfer
#include "udc-ep0-test/fixture.c"
#undef HP1020_EP0_DCD_XFER
#undef HP1020_EP0_SET_ADDRESS
#undef HP1020_EP0_FIXTURE_RESET
#undef HP1020_EP0_FIXTURE_STEP
#undef HP1020_EP0_BULK_XFER

#define COMPOSED_OUT_DMA UINT32_C(0x579bdf10)
#define COMPOSED_RX_DMA UINT32_C(0x24681340)
#define COMPOSED_RX_STEP UINT32_C(0x1000)
#define COMPOSED_SETUP_DMA UINT32_C(0x79bdf130)
#define COMPOSED_SNAPSHOTS 8u

uint32_t hp1020_composed_out_stats[48], hp1020_composed_setup_stats[40];
static _Alignas(16) struct hp1020_udc_out composed_out;
static _Alignas(16) struct hp1020_udc_setup composed_setup;
static struct {
    _Alignas(16) uint8_t before[16], descriptor[16], after[16];
} composed_out_memory;
static struct {
    _Alignas(16) uint8_t before[16], record[16], after[16];
} composed_setup_memory;
_Static_assert(sizeof(composed_out_memory) == 48, "portable OUT descriptor capture");
_Static_assert(sizeof(composed_setup_memory) == 48, "portable live SETUP capture");
static uint8_t composed_out_shadow[16], composed_published_bytes[16];
static uint8_t composed_setup_shadow[16];
static struct hp1020_udc_out_submission composed_publication;
static struct hp1020_udc_out_observation composed_saved[COMPOSED_SNAPSHOTS];
static uint8_t composed_saved_valid[COMPOSED_SNAPSHOTS];
static struct hp1020_udc_setup_observation composed_capture_shadow;
static struct {
    uint32_t result, violations, preparations, publications, completions;
    uint32_t cancellations, stale, cancel_marks, steps, last_slot;
    uint32_t observed_id, observed_status, observed_fault, observed_facts;
    uint8_t automatic;
    struct hp1020_udc_out_publish_facts publish;
} composed_out_state;
static struct {
    uint32_t result, violations, writes, offers, copies, dispatches, admissions;
    uint32_t resets, resets_ok, blocked, blocked_service, blocked_arm, steps;
} composed_setup_state;

static void composed_put32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v;
}
static void composed_out_violation(void) {
    composed_out_state.violations++; state.violations++;
}
static void composed_setup_violation(void) {
    composed_setup_state.violations++; state.violations++;
}
static int composed_guard(const uint8_t *before, const uint8_t *after) {
    for (uint32_t i = 0; i < 16; i++)
        if (before[i] != state.fill || after[i] != state.fill) return 0;
    return 1;
}
static int composed_observation_same(const struct hp1020_udc_setup_observation *a,
    const struct hp1020_udc_setup_observation *b) {
    return a->sequence == b->sequence && a->record_dma == b->record_dma &&
        a->endpoint_fault == b->endpoint_fault && !memcmp(a->record, b->record, 16) &&
        a->printer_status.value == b->printer_status.value &&
        a->printer_status.known == b->printer_status.known;
}
static int composed_capture_same(void) {
    return composed_observation_same(&composed_setup.capture, &composed_capture_shadow);
}
static void composed_check(void) {
    check_owned(); ep0_check();
    if (!composed_guard(composed_out_memory.before, composed_out_memory.after) ||
        memcmp(composed_out_shadow, composed_out_memory.descriptor, 16))
        composed_out_violation();
    if (!composed_guard(composed_setup_memory.before, composed_setup_memory.after) ||
        memcmp(composed_setup_shadow, composed_setup_memory.record, 16) ||
        !composed_capture_same()) composed_setup_violation();
}
static int composed_dma_spans(void) {
    /* Distinct CPU objects are stationary. Independently enforce the supplied
     * numeric cross-component mapping; individual components cannot see peers. */
    const uint32_t spans[][2] = {
        {OUT_DESCRIPTOR_DMA, 16}, {IN_DESCRIPTOR_DMA, 16},
        {OUT_PACKET_DMA, 64}, {IN_PACKET_DMA, 64},
        {COMPOSED_OUT_DMA, 16}, {COMPOSED_SETUP_DMA, 16},
        {COMPOSED_RX_DMA, 64}, {COMPOSED_RX_DMA + COMPOSED_RX_STEP, 64},
        {COMPOSED_RX_DMA + 2*COMPOSED_RX_STEP, 64},
        {COMPOSED_RX_DMA + 3*COMPOSED_RX_STEP, 64}
    };
    for (uint32_t i = 0; i < sizeof(spans)/sizeof(spans[0]); i++) {
        if (!spans[i][0] || (spans[i][0] & 15u) ||
            spans[i][0] > UINT32_MAX - (spans[i][1] - 1u)) return 0;
        for (uint32_t j = 0; j < i; j++)
            if (spans[i][0] <= spans[j][0] + spans[j][1] - 1u &&
                spans[j][0] <= spans[i][0] + spans[i][1] - 1u) return 0;
    }
    return HP1020_RX_SLOTS == 4;
}
static int composed_out_current(struct hp1020_tusb_cookie cookie) {
    return cookie.id && cookie.endpoint == 1 &&
        composed_out.phase != HP1020_UDC_OUT_FREE && same_cookie(composed_out.cookie, cookie);
}
static void composed_snapshot(void) {
    uint32_t *o = hp1020_composed_out_stats;
    memset(o, 0, sizeof(hp1020_composed_out_stats));
    o[0] = composed_out_state.result; o[1] = composed_out.initialized;
    o[2] = composed_out.phase; o[3] = composed_out.cancel_requested;
    o[4] = composed_out.fault_reported; o[5] = composed_out.fault_reason;
    o[6] = composed_out.last_adapter_result; o[7] = composed_out_state.violations;
    o[8] = (uint32_t)composed_guard(composed_out_memory.before, composed_out_memory.after);
    o[9] = !memcmp(composed_out_shadow, composed_out_memory.descriptor, 16);
    o[10] = composed_out_state.preparations; o[11] = composed_out_state.publications;
    o[12] = composed_out_state.completions; o[13] = composed_out_state.cancellations;
    o[14] = composed_out_state.stale; o[15] = composed_out_state.cancel_marks;
    ep0_cookie_words(o + 16, composed_out.cookie);
    o[21] = composed_out.descriptor.dma; o[22] = composed_out.buffer.dma;
    o[23] = composed_out.buffer.bytes;
    ep0_cookie_words(o + 28, composed_publication.cookie);
    for (uint32_t i = 0; i < 4; i++) {
        o[24+i] = ep0_be32(composed_out_memory.descriptor + 4*i);
        o[33+i] = ep0_be32(composed_published_bytes + 4*i);
    }
    o[37] = composed_publication.descriptor_dma; o[38] = composed_publication.buffer_dma;
    o[39] = composed_publication.capacity;
    o[40] = composed_out_state.observed_id; o[41] = composed_out_state.observed_status;
    o[42] = composed_out_state.observed_fault; o[43] = composed_out_state.observed_facts;
    /* Original adapter states, independent of component phases/live flags:
     * OUT0 low byte, IN0 middle byte, bulk OUT high byte. */
    o[44] = (uint32_t)adapter.owners[0].state |
        ((uint32_t)adapter.owners[1].state << 8) |
        ((uint32_t)adapter.owners[2].state << 16);
    o[45] = ((uint32_t)composed_out_state.automatic << 24) |
        ((uint32_t)composed_out_state.publish.mode_packet64_be << 16) |
        ((uint32_t)composed_out_state.publish.descriptor_visible << 8) |
        composed_out_state.publish.buffer_dma_ready;
    o[46] = composed_out_state.steps; o[47] = composed_out_state.last_slot;
    o = hp1020_composed_setup_stats;
    memset(o, 0, sizeof(hp1020_composed_setup_stats));
    o[0] = composed_setup_state.result; o[1] = composed_setup.initialized;
    o[2] = composed_setup.pending_kind; o[3] = composed_setup.pending_sequence;
    o[4] = composed_setup.last_sequence; o[5] = composed_setup.last_reset_sequence;
    o[6] = composed_setup.last_admitted_sequence; o[7] = composed_setup.adapter_control_epoch;
    o[8] = composed_setup.reset_control_epoch; o[9] = composed_setup.last_adapter_result;
    o[10] = composed_setup.terminal; o[11] = hp1020_udc_setup_progress(&composed_setup);
    o[12] = composed_setup_state.violations;
    o[13] = (uint32_t)composed_guard(composed_setup_memory.before, composed_setup_memory.after);
    o[14] = (uint32_t)!memcmp(composed_setup_shadow, composed_setup_memory.record, 16) |
        ((uint32_t)composed_capture_same() << 1);
    o[15] = composed_setup_state.writes; o[16] = composed_setup_state.offers;
    o[17] = composed_setup_state.copies; o[18] = composed_setup_state.dispatches;
    o[19] = composed_setup_state.admissions; o[20] = composed_setup_state.resets;
    o[21] = composed_setup_state.resets_ok; o[22] = composed_setup.capture.sequence;
    o[23] = composed_setup.capture.record_dma; o[24] = composed_setup.capture.endpoint_fault;
    o[25] = ((uint32_t)composed_setup.capture.printer_status.value << 8) |
        composed_setup.capture.printer_status.known;
    o[26] = COMPOSED_SETUP_DMA; o[27] = composed_setup_state.blocked;
    for (uint32_t i = 0; i < 4; i++) {
        o[28+i] = ep0_be32(composed_setup_memory.record + 4*i);
        o[32+i] = ep0_be32(composed_setup.capture.record + 4*i);
    }
    o[36] = composed_setup_state.steps; o[37] = composed_setup_state.blocked_service;
    o[38] = composed_setup_state.blocked_arm; o[39] = cancel_mask();
}

static enum hp1020_udc_out_result composed_publish(struct hp1020_tusb_cookie cookie,
    uint32_t flags, uint32_t mutation) {
    if (flags > UINT32_C(0xffffff) || mutation > 5) return HP1020_UDC_OUT_INVALID;
    cookie = ep0_mutate(cookie, mutation);
    const struct hp1020_udc_out_publish_facts facts = {
        (uint8_t)(flags >> 16), (uint8_t)(flags >> 8), (uint8_t)flags
    };
    struct hp1020_udc_out_submission next;
    const enum hp1020_udc_out_result r = hp1020_udc_out_take_submission(&composed_out, cookie, facts, &next);
    composed_out_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK) {
        composed_publication = next; composed_out_state.publications++;
        if (!packets[2].live || next.buffer_cpu != packets[2].buffer ||
            next.descriptor_cpu != composed_out_memory.descriptor || next.endpoint != 1 ||
            next.capacity != 64 || !same_cookie(next.cookie, packets[2].cookie) ||
            next.descriptor_dma != COMPOSED_OUT_DMA || composed_out_state.last_slot >= HP1020_RX_SLOTS ||
            next.buffer_dma != COMPOSED_RX_DMA + COMPOSED_RX_STEP*composed_out_state.last_slot)
            composed_out_violation();
        else memcpy(composed_published_bytes, next.descriptor_cpu, 16);
    } else if (r == HP1020_UDC_OUT_STALE) composed_out_state.stale++;
    return r;
}
static bool composed_bulk_xfer(uint8_t rhport, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, bool in_isr) {
    (void)in_isr; composed_check();
    if (rhport || endpoint != 1 || !buffer || length != 64 || packets[2].live ||
        !(state.open_mask & endpoint_bit(endpoint))) { composed_out_violation(); return false; }
    uint32_t slot = UINT32_MAX;
    for (uint32_t i = 0; i < HP1020_RX_SLOTS; i++)
        if (buffer == memory.data.receive.data[i]) slot = i;
    if (slot == UINT32_MAX) { composed_out_violation(); return false; }
    composed_out_state.last_slot = slot;
    const uint32_t failure = state.fail_submission; state.fail_submission = 0;
    if (failure == 1) return false;
    uint8_t before[64]; memcpy(before, buffer, sizeof(before));
    const struct hp1020_udc_out_span span = {buffer, COMPOSED_RX_DMA + COMPOSED_RX_STEP*slot, 64};
    struct hp1020_tusb_cookie cookie;
    enum hp1020_udc_out_result r = hp1020_udc_out_prepare(&composed_out, endpoint, span, length, &cookie);
    composed_out_state.result = (uint32_t)r;
    if (r != HP1020_UDC_OUT_OK) return false;
    /* Independent allowed bytes, not a copy of the implementation's result. */
    composed_put32(composed_out_shadow, UINT32_C(0x08000000));
    composed_put32(composed_out_shadow + 4, 0);
    composed_put32(composed_out_shadow + 8, span.dma);
    composed_put32(composed_out_shadow + 12, 0);
    composed_out_state.preparations++;
    struct packet *p = &packets[2];
    p->cookie = cookie; p->buffer = buffer; p->length = length;
    p->live = 1; p->cancel_requested = 0; memcpy(p->shadow, before, sizeof(before));
    state.submissions++; state.last_id = cookie.id; state.last_ep = endpoint; state.last_length = length;
    if (!cookie.id || cookie.id >= 4096) { composed_out_violation(); return false; }
    history[cookie.id] = cookie;
    if (composed_out.buffer.cpu != buffer || composed_out.buffer.dma != span.dma ||
        cookie.endpoint != endpoint || adapter.owners[2].buffer != buffer ||
        adapter.owners[2].length != length || adapter.owners[2].state != HP1020_TUSB_OWNER_DCD ||
        !same_cookie(adapter.owners[2].cookie, cookie)) composed_out_violation();
    composed_check();
    if (composed_out_state.automatic) {
        const struct hp1020_udc_out_publish_facts f = composed_out_state.publish;
        r = composed_publish(cookie, ((uint32_t)f.mode_packet64_be << 16) |
            ((uint32_t)f.descriptor_visible << 8) | f.buffer_dma_ready, 0);
        if (r != HP1020_UDC_OUT_OK && r != HP1020_UDC_OUT_WAIT) return false;
    }
    return failure != 2;
}
/* The only symbols seen by the separately compiled reusable USB stack. */
bool dcd_edpt_xfer(uint8_t rhport, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, bool in_isr) {
    return composed_ep0_xfer(rhport, endpoint, buffer, length, in_isr);
}
void dcd_set_address(uint8_t rhport, uint8_t address) {
    composed_ep0_set_address(rhport, address);
}
static enum hp1020_udc_out_result composed_cancel_request(struct hp1020_tusb_cookie cookie,
    uint32_t mutation) {
    if (mutation > 5) return HP1020_UDC_OUT_INVALID;
    cookie = ep0_mutate(cookie, mutation);
    const uint8_t previous = composed_out.cancel_requested;
    const enum hp1020_udc_out_result r = hp1020_udc_out_request_cancel(&composed_out, cookie);
    composed_out_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK && !previous) composed_out_state.cancel_marks++;
    if (r == HP1020_UDC_OUT_STALE) composed_out_state.stale++;
    return r;
}
static void composed_cancel_work(void) {
    /* Requests are queued by the base callback. Never imply DMA settlement. */
    ep0_drain_cancel_requests();
    if (packets[2].live && packets[2].cancel_requested &&
        composed_out_current(packets[2].cookie) && !composed_out.cancel_requested) {
        const uint32_t saved_result = composed_out_state.result;
        if (composed_cancel_request(packets[2].cookie, 0) != HP1020_UDC_OUT_OK)
            composed_out_violation();
        composed_out_state.result = saved_result;
    }
}
static enum hp1020_udc_out_result composed_observe(struct hp1020_udc_out_observation observation,
    uint32_t flags, uint32_t mutation) {
    if (flags > UINT32_C(0xffffff) || mutation > 5) return HP1020_UDC_OUT_INVALID;
    observation.cookie = ep0_mutate(observation.cookie, mutation);
    composed_out_state.observed_id = observation.cookie.id;
    composed_out_state.observed_status = ep0_be32(observation.descriptor);
    composed_out_state.observed_fault = observation.endpoint_fault;
    composed_out_state.observed_facts = flags;
    const struct hp1020_udc_out_completion_facts facts = {
        (uint8_t)(flags >> 16), (uint8_t)(flags >> 8), (uint8_t)flags
    };
    const enum hp1020_udc_out_result r = hp1020_udc_out_observe(&composed_out, &observation, facts);
    composed_check(); /* Preserve original-buffer checks THROUGH retirement. */
    composed_out_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK) {
        if (!packets[2].live || !same_cookie(packets[2].cookie, observation.cookie))
            composed_out_violation();
        packets[2].live = 0; state.completions++; composed_out_state.completions++;
    } else if (r == HP1020_UDC_OUT_STALE) { state.stale++; composed_out_state.stale++; }
    return r;
}
static enum hp1020_udc_out_result composed_cancelled(struct hp1020_tusb_cookie cookie,
    uint32_t settled, uint32_t mutation) {
    if (settled > 255 || mutation > 5) return HP1020_UDC_OUT_INVALID;
    cookie = ep0_mutate(cookie, mutation);
    const enum hp1020_udc_out_result r = hp1020_udc_out_cancelled(&composed_out, cookie, (uint8_t)settled);
    composed_check();
    composed_out_state.result = (uint32_t)r;
    if (r == HP1020_UDC_OUT_OK) {
        if (!packets[2].live || !same_cookie(packets[2].cookie, cookie)) composed_out_violation();
        packets[2].live = 0; state.cancellations++; composed_out_state.cancellations++;
    } else if (r == HP1020_UDC_OUT_STALE) { state.stale++; composed_out_state.stale++; }
    return r;
}

uint32_t hp1020_bulk_fixture_reset(uint32_t fill, uint32_t capacity,
    uint32_t interface_number, uint32_t fail_at) {
    /* Fresh process/ELF only, never a reset escape from outstanding owners. */
    memset(&composed_out_state, 0, sizeof(composed_out_state));
    memset(&composed_setup_state, 0, sizeof(composed_setup_state));
    memset(&composed_out, 0, sizeof(composed_out));
    memset(&composed_setup, 0, sizeof(composed_setup));
    memset(&composed_publication, 0, sizeof(composed_publication));
    memset(&composed_capture_shadow, 0, sizeof(composed_capture_shadow));
    memset(composed_published_bytes, 0, sizeof(composed_published_bytes));
    memset(composed_saved_valid, 0, sizeof(composed_saved_valid));
    memset(&composed_out_memory, (int)(fill & 255u), sizeof(composed_out_memory));
    memset(&composed_setup_memory, (int)(fill & 255u), sizeof(composed_setup_memory));
    memset(composed_out_shadow, (int)(fill & 255u), sizeof(composed_out_shadow));
    memset(composed_setup_shadow, (int)(fill & 255u), sizeof(composed_setup_shadow));
    composed_out_state.last_slot = UINT32_MAX; composed_out_state.automatic = 1;
    composed_out_state.publish = (struct hp1020_udc_out_publish_facts){1, 1, 1};
    uint32_t r = composed_dma_spans() ? HP1020_TUSB_OK : HP1020_TUSB_INVALID;
    if (!r) r = composed_ep0_reset(fill, capacity, interface_number, fail_at);
    if (!r) {
        const struct hp1020_udc_out_span span = {composed_out_memory.descriptor, COMPOSED_OUT_DMA, 16};
        r = (uint32_t)hp1020_udc_out_init(&composed_out, &adapter, span);
    }
    composed_out_state.result = r;
    if (!r) r = (uint32_t)hp1020_udc_setup_init(&composed_setup, &adapter, COMPOSED_SETUP_DMA);
    composed_setup_state.result = r; state.initialized = r;
    composed_check(); snapshot(r); ep0_snapshot(); composed_snapshot(); return r;
}

uint32_t hp1020_bulk_fixture_step(uint32_t op, uint32_t a, uint32_t b, uint32_t c, uint32_t d) {
    uint32_t r = HP1020_TUSB_INVALID;
    struct hp1020_tusb_cookie cookie = {0};
    const int have_cookie = ep0_history(a, &cookie);
    composed_check();
    if (op < 60) {
        const uint32_t permission = hp1020_udc_setup_progress(&composed_setup);
        const uint32_t needed = op == 1 ? HP1020_UDC_SETUP_ALLOW_SERVICE :
            op == 6 ? HP1020_UDC_SETUP_ALLOW_ARM :
            op == 7 ? HP1020_UDC_SETUP_ALLOW_PUMP :
            (op == 8 || op == 9 || op == 12 || op == 41) ?
                HP1020_UDC_SETUP_ALLOW_SERVICE | HP1020_UDC_SETUP_ALLOW_ARM |
                    HP1020_UDC_SETUP_ALLOW_PUMP : 0;
        if (op == 0 || op == 2 || op == 3 || op == 4 || op == 5) {
            /* No normalized SETUP/reset or completion/cancellation/data bypass. */
        } else if (needed && (permission & needed) != needed) {
            r = op == 9 ? HP1020_RX_WAIT : HP1020_TUSB_WAIT;
            composed_setup_state.blocked++;
            if (op == 1) composed_setup_state.blocked_service++;
            if (op == 6) composed_setup_state.blocked_arm++;
        } else r = composed_ep0_step(op, a, b, c, d);
    } else {
        memcpy(&protected_memory, &memory.data, sizeof(memory.data));
        if (op < 80) {
            composed_out_state.steps++;
            if (op == 60 && a <= 1 && b <= UINT32_C(0xffffff)) {
                composed_out_state.automatic = (uint8_t)a;
                composed_out_state.publish = (struct hp1020_udc_out_publish_facts){
                    (uint8_t)(b >> 16), (uint8_t)(b >> 8), (uint8_t)b};
                r = HP1020_UDC_OUT_OK;
            } else if (op == 61 && hp1020_udc_setup_progress(&composed_setup) != 7u) {
                r = HP1020_UDC_OUT_WAIT; composed_setup_state.blocked++;
            } else if (op == 61 && have_cookie) r = (uint32_t)composed_publish(cookie, b, d);
            else if (op == 62 && have_cookie) {
                struct hp1020_udc_out_observation observation;
                observation.cookie = cookie; observation.endpoint_fault = c;
                memcpy(observation.descriptor, hp1020_bulk_fixture_input, 16);
                r = (uint32_t)composed_observe(observation, b, d);
            } else if (op == 63 && have_cookie) r = (uint32_t)composed_cancel_request(cookie, d);
            else if (op == 64 && have_cookie) r = (uint32_t)composed_cancelled(cookie, b, d);
            else if (op == 65 && have_cookie && composed_out_current(cookie) &&
                composed_out.phase == HP1020_UDC_OUT_EXPOSED &&
                packets[2].live && same_cookie(packets[2].cookie, cookie)) {
                const uint32_t capacity = b == 0 ? 16 : b == 1 ? 64 : 0;
                if (capacity && c <= capacity && d <= capacity - c) {
                    uint8_t *target = b ? packets[2].buffer : composed_out_memory.descriptor;
                    uint8_t *shadow = b ? packets[2].shadow : composed_out_shadow;
                    memcpy(target + c, hp1020_bulk_fixture_input, d);
                    memcpy(shadow + c, hp1020_bulk_fixture_input, d);
                    if (b) {
                        /* Only this exact synthetic DMA window may change. */
                        memcpy(protected_memory.receive.data[composed_out_state.last_slot] + c,
                            hp1020_bulk_fixture_input, d); state.dcd_writes++;
                    }
                    r = HP1020_UDC_OUT_OK;
                }
            } else if (op == 66 && have_cookie && composed_out_current(cookie) &&
                composed_out.phase == HP1020_UDC_OUT_EXPOSED && b < COMPOSED_SNAPSHOTS) {
                composed_saved[b].cookie = cookie; composed_saved[b].endpoint_fault = 0;
                memcpy(composed_saved[b].descriptor, composed_out_memory.descriptor, 16);
                composed_saved_valid[b] = 1; r = HP1020_UDC_OUT_OK;
            } else if (op == 67 && a < COMPOSED_SNAPSHOTS && composed_saved_valid[a]) {
                struct hp1020_udc_out_observation observation = composed_saved[a];
                observation.endpoint_fault = c; r = (uint32_t)composed_observe(observation, b, d);
            }
            composed_out_state.result = r;
        } else {
            composed_setup_state.steps++;
            if (op == 80) {
                memcpy(composed_setup_memory.record, hp1020_bulk_fixture_input, 16);
                memcpy(composed_setup_shadow, hp1020_bulk_fixture_input, 16);
                composed_setup_state.writes++; r = HP1020_UDC_SETUP_OK;
            } else if (op == 81 && d <= UINT32_C(0xffff)) {
                struct hp1020_udc_setup_observation observation;
                memset(&observation, 0, sizeof(observation));
                observation.sequence = a; observation.record_dma = b; observation.endpoint_fault = c;
                observation.printer_status.value = (uint8_t)(d >> 8);
                observation.printer_status.known = (uint8_t)d;
                memcpy(observation.record, composed_setup_memory.record, 16);
                const struct hp1020_udc_setup_observation expected = observation;
                const uint8_t previous_terminal = composed_setup.terminal;
                composed_setup_state.offers++;
                r = (uint32_t)hp1020_udc_setup_offer(&composed_setup, &observation);
                /* An independently saved input, including original status; do
                 * not build the allowed shadow by rereading component output. */
                if (r == HP1020_UDC_SETUP_OK || (r == HP1020_UDC_SETUP_LIMIT &&
                    !previous_terminal && a == UINT32_MAX)) {
                    composed_capture_shadow = expected; composed_setup_state.copies++;
                }
                if (!composed_observation_same(&observation, &expected)) composed_setup_violation();
            } else if (op == 82 && b <= UINT32_C(0xffffff) && c <= 255) {
                const struct hp1020_udc_setup_capture_facts facts = {
                    (uint8_t)(b >> 16), (uint8_t)(b >> 8), (uint8_t)b};
                /* This is the explicitly supplied external clear fact, not an
                 * action inferred from a successful adapter/bridge return. */
                if (c == 1) state.stall_mask &= ~3u;
                composed_setup_state.dispatches++;
                r = (uint32_t)hp1020_udc_setup_dispatch(&composed_setup, a, facts, (uint8_t)c);
                if (r == HP1020_UDC_SETUP_OK) composed_setup_state.admissions++;
            } else if (op == 83 && c <= 1) {
                const uint8_t previous_busy = adapter.busy;
                if (c) adapter.busy = 1; /* Test-only serialized rejection. */
                composed_setup_state.resets++;
                r = (uint32_t)hp1020_udc_setup_bus_reset(&composed_setup, a, (tusb_speed_t)b);
                adapter.busy = previous_busy;
                if (r == HP1020_UDC_SETUP_OK) composed_setup_state.resets_ok++;
            }
            composed_setup_state.result = r;
        }
        if (memcmp(&protected_memory, &memory.data, sizeof(memory.data))) {
            if (op < 80) composed_out_violation(); else composed_setup_violation();
        }
    }
    memset(hp1020_bulk_fixture_input, state.fill ^ 255, sizeof(hp1020_bulk_fixture_input));
    composed_cancel_work(); composed_check(); snapshot(r); ep0_snapshot(); composed_snapshot(); return r;
}
uint8_t *hp1020_composed_fixture_out_storage(void) { return (uint8_t *)(void *)&composed_out_memory; }
uint8_t *hp1020_composed_fixture_setup_storage(void) { return (uint8_t *)(void *)&composed_setup_memory; }
uint32_t hp1020_composed_fixture_out_storage_bytes(void) { return (uint32_t)sizeof(composed_out_memory); }
uint32_t hp1020_composed_fixture_setup_storage_bytes(void) { return (uint32_t)sizeof(composed_setup_memory); }
uint32_t hp1020_composed_fixture_out_component_bytes(void) {
    return (uint32_t)(sizeof(struct hp1020_udc_out) + sizeof(struct hp1020_udc_out_memory));
}
uint32_t hp1020_composed_fixture_setup_component_bytes(void) {
    return (uint32_t)(sizeof(struct hp1020_udc_setup) + HP1020_UDC_SETUP_RECORD_BYTES);
}
