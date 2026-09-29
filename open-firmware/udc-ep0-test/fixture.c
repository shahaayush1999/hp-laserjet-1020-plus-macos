/* SPDX-License-Identifier: GPL-2.0-or-later
 * Synthetic EP0 normal descriptors. No MMIO, IRQ, controller or device access.
 * Bulk transfers remain the existing normalized synthetic lane, independently
 * of the separate bulk-descriptor experiment.
 */
#include "hp1020_udc_ep0.h"

#define dcd_edpt_xfer hp1020_ep0_base_dcd_edpt_xfer
#define dcd_set_address hp1020_ep0_base_dcd_set_address
#define hp1020_bulk_fixture_reset hp1020_ep0_base_reset
#define hp1020_bulk_fixture_step hp1020_ep0_base_step
#include "tinyusb-printer-test/fixture.c"
#undef dcd_edpt_xfer
#undef dcd_set_address
#undef hp1020_bulk_fixture_reset
#undef hp1020_bulk_fixture_step

#define OUT_DESCRIPTOR_DMA UINT32_C(0x13579bd0)
#define IN_DESCRIPTOR_DMA UINT32_C(0xa468ace0)
#define OUT_PACKET_DMA UINT32_C(0x3579bdf0)
#define IN_PACKET_DMA UINT32_C(0xb68ace00)
#define EP0_SNAPSHOTS 8u

uint32_t hp1020_ep0_fixture_stats[104];
static _Alignas(16) struct hp1020_udc_ep0 ep0;
static struct {
    _Alignas(16) uint8_t guard0[16], out_descriptor[16], guard1[16];
    uint8_t in_descriptor[16], guard2[16], out_sink[64], guard3[16];
    uint8_t in_staging[64], guard4[16];
} ep0_memory;
_Static_assert(sizeof(ep0_memory) == 240, "portable guarded EP0 capture");
static uint8_t descriptor_shadow[2][16], packet_shadow[2][64];
static struct hp1020_udc_ep0_submission publications[2];
static uint8_t publication_bytes[2][16];
static struct hp1020_udc_ep0_observation ep0_saved[EP0_SNAPSHOTS];
static uint8_t ep0_saved_valid[EP0_SNAPSHOTS];
static struct {
    uint32_t result, violations, steps, last_endpoint, device_id_length;
    struct {
        uint32_t preparations, proposals, completions, cancellations, stale, cancel_marks;
        uint32_t observed_id, observed_status, observed_fault, observed_facts, observed_actual;
        uint32_t injection;
        uint8_t automatic;
        struct hp1020_udc_ep0_publish_facts publish;
    } slot[2];
} ep0_state;

static int ep0_index(uint8_t endpoint) {
    return endpoint == 0 ? 0 : endpoint == 0x80 ? 1 : -1;
}
static uint8_t *ep0_descriptor(uint32_t i) {
    return i ? ep0_memory.in_descriptor : ep0_memory.out_descriptor;
}
static uint8_t *ep0_packet(uint32_t i) {
    return i ? ep0_memory.in_staging : ep0_memory.out_sink;
}
static uint32_t ep0_be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
        ((uint32_t)p[2] << 8) | p[3];
}
static void ep0_violation(void) {
    ep0_state.violations++; state.violations++;
}
static int ep0_guards(void) {
    for (uint32_t i = 0; i < 16; i++)
        if (ep0_memory.guard0[i] != state.fill || ep0_memory.guard1[i] != state.fill ||
            ep0_memory.guard2[i] != state.fill || ep0_memory.guard3[i] != state.fill ||
            ep0_memory.guard4[i] != state.fill) return 0;
    return 1;
}
static int ep0_shadows(void) {
    for (uint32_t i = 0; i < 2; i++)
        if (memcmp(descriptor_shadow[i], ep0_descriptor(i), 16) ||
            memcmp(packet_shadow[i], ep0_packet(i), 64)) return 0;
    return 1;
}
static void ep0_check(void) {
    if (!ep0_guards() || !ep0_shadows()) ep0_violation();
}
static int ep0_history(uint32_t id, struct hp1020_tusb_cookie *cookie) {
    if (!id || id >= 4096 || history[id].id != id) return 0;
    *cookie = history[id]; return 1;
}
static struct hp1020_tusb_cookie ep0_mutate(struct hp1020_tusb_cookie cookie, uint32_t mutation) {
    if (mutation == 1) cookie.id ^= UINT32_C(0x80000000);
    else if (mutation == 2) cookie.epoch ^= UINT32_C(0x80000000);
    else if (mutation == 3) cookie.generation ^= UINT32_C(0x80000000);
    else if (mutation == 4) cookie.sequence ^= UINT32_C(0x80000000);
    else if (mutation == 5) cookie.endpoint ^= 0x80;
    return cookie;
}
static int ep0_current(struct hp1020_tusb_cookie cookie) {
    const int i = ep0_index(cookie.endpoint);
    return i >= 0 && cookie.id && ep0.slots[i].phase != HP1020_UDC_EP0_FREE &&
        same_cookie(ep0.slots[i].cookie, cookie);
}
static struct hp1020_udc_ep0_spans ep0_spans(void) {
    const struct hp1020_udc_ep0_spans spans = {
        {ep0_memory.out_descriptor, OUT_DESCRIPTOR_DMA, 16},
        {ep0_memory.in_descriptor, IN_DESCRIPTOR_DMA, 16},
        {ep0_memory.out_sink, OUT_PACKET_DMA, 64},
        {ep0_memory.in_staging, IN_PACKET_DMA, 64}
    };
    return spans;
}
static void ep0_cookie_words(uint32_t *out, struct hp1020_tusb_cookie cookie) {
    out[0] = cookie.id; out[1] = cookie.epoch; out[2] = cookie.generation;
    out[3] = cookie.sequence; out[4] = cookie.endpoint;
}
static void ep0_snapshot(void) {
    uint32_t *g = hp1020_ep0_fixture_stats;
    memset(g, 0, sizeof(hp1020_ep0_fixture_stats));
    g[0] = ep0_state.result; g[1] = ep0.initialized; g[2] = ep0_state.violations;
    g[3] = (uint32_t)ep0_guards(); g[4] = (uint32_t)ep0_shadows();
    g[5] = ep0_state.steps; g[6] = ep0_state.last_endpoint; g[7] = ep0_state.device_id_length;
    for (uint32_t i = 0; i < 2; i++) {
        uint32_t *o = g + 8 + 48*i;
        const struct hp1020_udc_ep0_slot *p = &ep0.slots[i];
        const struct hp1020_udc_ep0_submission *q = &publications[i];
        o[0] = p->phase; o[1] = p->cancel_requested; o[2] = p->fault_reported;
        o[3] = p->fault_reason; o[4] = p->last_adapter_result; o[5] = p->requested;
        ep0_cookie_words(o + 6, p->cookie);
        o[11] = p->descriptor.dma; o[12] = p->packet.dma; o[13] = p->packet.bytes;
        for (uint32_t j = 0; j < 4; j++) {
            o[14+j] = ep0_be32(ep0_descriptor(i) + 4*j);
            o[18+j] = ep0_be32(publication_bytes[i] + 4*j);
        }
        ep0_cookie_words(o + 22, q->cookie);
        o[27] = q->descriptor_dma; o[28] = q->packet_dma;
        o[29] = q->requested; o[30] = q->allocation_bytes;
        o[31] = ep0_state.slot[i].preparations; o[32] = ep0_state.slot[i].proposals;
        o[33] = ep0_state.slot[i].completions; o[34] = ep0_state.slot[i].cancellations;
        o[35] = ep0_state.slot[i].stale; o[36] = ep0_state.slot[i].cancel_marks;
        o[37] = ep0_state.slot[i].observed_id; o[38] = ep0_state.slot[i].observed_status;
        o[39] = ep0_state.slot[i].observed_fault; o[40] = ep0_state.slot[i].observed_facts;
        o[41] = ep0_state.slot[i].observed_actual; o[42] = fnv(ep0_packet(i), 64);
        /* Use the independently retained real DCD pointer, never dereference
         * a possibly incorrect component-returned original pointer for stats. */
        o[43] = packets[i].live ? fnv(packets[i].buffer, packets[i].length) : fnv(NULL, 0);
        o[44] = ((uint32_t)ep0_state.slot[i].automatic << 24) |
            ((uint32_t)ep0_state.slot[i].publish.mode_packet64_be << 16) |
            ((uint32_t)ep0_state.slot[i].publish.descriptor_visible << 8) |
            ep0_state.slot[i].publish.packet_dma_ready;
        o[45] = ep0_state.slot[i].injection;
        o[46] = p->phase != HP1020_UDC_EP0_FREE && !p->original_buffer;
        o[47] = ep0_state.slot[i].proposals && !q->original_buffer;
    }
}
static enum hp1020_udc_ep0_result ep0_publish(struct hp1020_tusb_cookie cookie,
    uint32_t flags, uint32_t mutation) {
    if (flags > UINT32_C(0xffffff) || mutation > 5) return HP1020_UDC_EP0_INVALID;
    const int i = ep0_index(cookie.endpoint);
    cookie = ep0_mutate(cookie, mutation);
    const struct hp1020_udc_ep0_publish_facts facts = {
        (uint8_t)(flags >> 16), (uint8_t)(flags >> 8), (uint8_t)flags
    };
    struct hp1020_udc_ep0_submission next;
    const enum hp1020_udc_ep0_result r = hp1020_udc_ep0_take_submission(&ep0, cookie, facts, &next);
    ep0_state.result = (uint32_t)r;
    if (r == HP1020_UDC_EP0_OK) {
        if (i < 0) { ep0_violation(); return r; }
        publications[i] = next; ep0_state.slot[i].proposals++;
        if (!packets[i].live || next.original_buffer != packets[i].buffer ||
            next.descriptor_cpu != ep0_descriptor((uint32_t)i) ||
            next.packet_cpu != ep0_packet((uint32_t)i) || next.endpoint != cookie.endpoint ||
            next.requested != packets[i].length || next.requested > 64 ||
            next.allocation_bytes != 64 || !same_cookie(next.cookie, packets[i].cookie) ||
            next.descriptor_dma != (i ? IN_DESCRIPTOR_DMA : OUT_DESCRIPTOR_DMA) ||
            next.packet_dma != (i ? IN_PACKET_DMA : OUT_PACKET_DMA)) ep0_violation();
        else {
            memcpy(publication_bytes[i], next.descriptor_cpu, 16);
            if (i == 1) {
                if (next.requested > sizeof(hp1020_bulk_fixture_wire) - state.wire_bytes) ep0_violation();
                else {
                    /* Capture the actual staging bytes proposed for DMA, not
                     * a second copy of the source that could hide copy bugs. */
                    if (next.requested) memcpy(hp1020_bulk_fixture_wire + state.wire_bytes,
                        next.packet_cpu, next.requested);
                    state.wire_bytes += next.requested;
                }
            }
        }
    } else if (r == HP1020_UDC_EP0_STALE && i >= 0) ep0_state.slot[i].stale++;
    return r;
}

bool dcd_edpt_xfer(uint8_t rhport, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, bool in_isr) {
    const int i = ep0_index(endpoint);
    if (i < 0) return hp1020_ep0_base_dcd_edpt_xfer(rhport, endpoint, buffer, length, in_isr);
    (void)in_isr; check_owned(); ep0_check();
    ep0_state.last_endpoint = endpoint;
    if (rhport || packets[i].live || length > 64 || (!i && length) ||
        (length && !buffer) || (!length && buffer) ||
        !(state.open_mask & endpoint_bit(endpoint))) { ep0_violation(); return false; }
    uint8_t source_before[64];
    if (length) memcpy(source_before, buffer, length);
    const uint32_t injection = ep0_state.slot[i].injection;
    ep0_state.slot[i].injection = 0;
    const uint32_t failure = state.fail_submission; state.fail_submission = 0;
    if (failure == 1 || injection == 10) return false;
    uint8_t *original = buffer, requested_endpoint = endpoint;
    uint16_t requested = length;
    if (injection == 1) original = NULL;
    else if (injection == 2) requested = 65;
    else if (injection == 3) { requested_endpoint = 0; requested = 1; }
    else if (injection == 4) { original = ep0_memory.in_staging; requested = 0; }
    else if (injection == 5) { original = ep0_memory.in_staging; requested = 1; }
    else if (injection == 6) { original = ep0_descriptor((uint32_t)i); requested = 1; }
    else if (injection == 7) { original = (uint8_t *)(void *)&ep0; requested = 1; }
    else if (injection == 8) { original = (uint8_t *)(UINTPTR_MAX - 15); requested = 64; }
    else if (injection == 9) requested_endpoint = 1;
    struct hp1020_tusb_cookie cookie;
    enum hp1020_udc_ep0_result r = hp1020_udc_ep0_prepare(&ep0, requested_endpoint,
        original, requested, &cookie);
    ep0_state.result = (uint32_t)r;
    if (r != HP1020_UDC_EP0_OK) return false;
    /* The independent allowed packet image was captured BEFORE binding/copy.
     * Only actual requested IN bytes may change; tails and all ZLP bytes stay. */
    if (i == 1 && length) memcpy(packet_shadow[i], source_before, length);
    memcpy(descriptor_shadow[i], ep0_descriptor((uint32_t)i), 16);
    ep0_state.slot[i].preparations++;
    struct packet *p = &packets[i];
    p->cookie = cookie; p->buffer = buffer; p->length = length;
    p->live = 1; p->cancel_requested = 0;
    if (length) memcpy(p->shadow, source_before, length);
    state.submissions++; state.last_id = cookie.id;
    state.last_ep = endpoint; state.last_length = length;
    if (!cookie.id || cookie.id >= 4096) { ep0_violation(); return false; }
    history[cookie.id] = cookie;
    if (ep0.slots[i].original_buffer != buffer || ep0.slots[i].requested != length ||
        cookie.endpoint != endpoint || adapter.owners[i].buffer != buffer ||
        adapter.owners[i].length != length || adapter.owners[i].state != HP1020_TUSB_OWNER_DCD ||
        !same_cookie(adapter.owners[i].cookie, cookie)) ep0_violation();
    ep0_check(); check_owned();
    if (injection == 11) return false;
    if (ep0_state.slot[i].automatic) {
        const struct hp1020_udc_ep0_publish_facts f = ep0_state.slot[i].publish;
        r = ep0_publish(cookie, ((uint32_t)f.mode_packet64_be << 16) |
            ((uint32_t)f.descriptor_visible << 8) | f.packet_dma_ready, 0);
        if (r != HP1020_UDC_EP0_OK && r != HP1020_UDC_EP0_WAIT) return false;
    }
    return failure != 2 && injection != 12;
}
void dcd_set_address(uint8_t rhport, uint8_t address) {
    state.pending_address = address; state.address_epoch = adapter.active_control_epoch;
    /* The included base implementation would call its renamed internal xfer.
     * Route this direct status through the actual EP0 descriptor wrapper. */
    if (!dcd_edpt_xfer(rhport, 0x80, NULL, 0, false)) state.violations++;
}

static enum hp1020_udc_ep0_result ep0_cancel_request(struct hp1020_tusb_cookie cookie, uint32_t mutation) {
    if (mutation > 5) return HP1020_UDC_EP0_INVALID;
    const int i = ep0_index(cookie.endpoint);
    const uint8_t previous = i >= 0 ? ep0.slots[i].cancel_requested : 0;
    cookie = ep0_mutate(cookie, mutation);
    const enum hp1020_udc_ep0_result r = hp1020_udc_ep0_request_cancel(&ep0, cookie);
    ep0_state.result = (uint32_t)r;
    if (i >= 0 && r == HP1020_UDC_EP0_OK && !previous) ep0_state.slot[i].cancel_marks++;
    if (i >= 0 && r == HP1020_UDC_EP0_STALE) ep0_state.slot[i].stale++;
    return r;
}
static void ep0_drain_cancel_requests(void) {
    for (uint32_t i = 0; i < 2; i++)
        if (packets[i].live && packets[i].cancel_requested && ep0_current(packets[i].cookie) &&
            !ep0.slots[i].cancel_requested) {
            const uint32_t primary = ep0_state.result;
            if (ep0_cancel_request(packets[i].cookie, 0) != HP1020_UDC_EP0_OK) ep0_violation();
            ep0_state.result = primary;
        }
}
static enum hp1020_udc_ep0_result ep0_observe(struct hp1020_udc_ep0_observation observation,
    uint32_t flags, uint32_t actual, uint32_t mutation) {
    if (mutation > 5) return HP1020_UDC_EP0_INVALID;
    const int i = ep0_index(observation.cookie.endpoint);
    observation.cookie = ep0_mutate(observation.cookie, mutation);
    if (i >= 0) {
        ep0_state.slot[i].observed_id = observation.cookie.id;
        ep0_state.slot[i].observed_status = ep0_be32(observation.descriptor);
        ep0_state.slot[i].observed_fault = observation.endpoint_fault;
        ep0_state.slot[i].observed_facts = flags; ep0_state.slot[i].observed_actual = actual;
    }
    const struct hp1020_udc_ep0_completion_facts facts = {
        (uint8_t)(flags >> 24), (uint8_t)(flags >> 16), (uint8_t)(flags >> 8), (uint8_t)flags, actual
    };
    const enum hp1020_udc_ep0_result r = hp1020_udc_ep0_observe(&ep0, &observation, facts);
    /* Check the borrowed original while its independent ledger is still live,
     * including any accidental write during component/adapter retirement. */
    check_owned();
    ep0_state.result = (uint32_t)r;
    if (r == HP1020_UDC_EP0_OK) {
        if (i < 0) { ep0_violation(); return r; }
        if (!packets[i].live || !same_cookie(packets[i].cookie, observation.cookie)) ep0_violation();
        packets[i].live = 0; state.completions++; ep0_state.slot[i].completions++;
    } else if (r == HP1020_UDC_EP0_STALE) {
        state.stale++; if (i >= 0) ep0_state.slot[i].stale++;
    }
    return r;
}
static enum hp1020_udc_ep0_result ep0_cancelled(struct hp1020_tusb_cookie cookie,
    uint32_t settled, uint32_t mutation) {
    if (settled > 255 || mutation > 5) return HP1020_UDC_EP0_INVALID;
    const int i = ep0_index(cookie.endpoint);
    cookie = ep0_mutate(cookie, mutation);
    const enum hp1020_udc_ep0_result r = hp1020_udc_ep0_cancelled(&ep0, cookie, (uint8_t)settled);
    check_owned(); /* Settlement must not erase the original-buffer oracle. */
    ep0_state.result = (uint32_t)r;
    if (r == HP1020_UDC_EP0_OK) {
        if (i < 0) { ep0_violation(); return r; }
        if (!packets[i].live || !same_cookie(packets[i].cookie, cookie)) ep0_violation();
        packets[i].live = 0; state.cancellations++; ep0_state.slot[i].cancellations++;
    } else if (r == HP1020_UDC_EP0_STALE) {
        state.stale++; if (i >= 0) ep0_state.slot[i].stale++;
    }
    return r;
}
static enum hp1020_udc_ep0_result ep0_probe_init(uint32_t region, uint32_t kind,
    uint32_t dma, uint32_t bytes) {
    if (region > 3 || kind > 12) return HP1020_UDC_EP0_INVALID;
    _Alignas(16) struct hp1020_udc_ep0 probe;
    memset(&probe, (int)state.fill, sizeof(probe));
    struct hp1020_udc_ep0_spans config = ep0_spans();
    struct hp1020_udc_ep0_span *spans[4] = {
        &config.out_descriptor, &config.in_descriptor, &config.out_sink, &config.in_staging
    };
    struct hp1020_udc_ep0_span *p = spans[region];
    const uint32_t next = (region + 1) & 3;
    if (kind == 1) p->cpu = NULL;
    else if (kind == 2) p->cpu++;
    else if (kind == 3) p->bytes--;
    else if (kind == 4) p->dma++;
    else if (kind == 5) p->dma = 0;
    else if (kind == 6) { p->dma = UINT32_C(0xfffffff0); p->bytes += 16; }
    else if (kind == 7) p->cpu = (uint8_t *)(void *)&probe;
    else if (kind == 8) p->dma = spans[next]->dma;
    else if (kind == 9) p->cpu = spans[next]->cpu;
    else if (kind == 10) p->cpu = (uint8_t *)(void *)&adapter;
    else if (kind == 11) { p->dma = dma; p->bytes = bytes; }
    else if (kind == 12) p->cpu = (uint8_t *)(UINTPTR_MAX - 7);
    return hp1020_udc_ep0_init(&probe, &adapter, &config);
}

uint32_t hp1020_bulk_fixture_reset(uint32_t fill, uint32_t capacity,
    uint32_t interface_number, uint32_t fail_at) {
    /* Fresh process/ELF required; this is not a runtime reset implementation. */
    memset(&ep0_state, 0, sizeof(ep0_state)); memset(&ep0, 0, sizeof(ep0));
    memset(publications, 0, sizeof(publications)); memset(publication_bytes, 0, sizeof(publication_bytes));
    memset(ep0_saved_valid, 0, sizeof(ep0_saved_valid));
    memset(&ep0_memory, (int)(fill & 255), sizeof(ep0_memory));
    memset(descriptor_shadow, (int)(fill & 255), sizeof(descriptor_shadow));
    memset(packet_shadow, (int)(fill & 255), sizeof(packet_shadow));
    ep0_state.last_endpoint = UINT32_MAX; ep0_state.device_id_length = 400;
    for (uint32_t i = 0; i < 2; i++) {
        ep0_state.slot[i].automatic = 1;
        ep0_state.slot[i].publish = (struct hp1020_udc_ep0_publish_facts){1, 1, 1};
    }
    uint32_t r = hp1020_ep0_base_reset(fill, capacity, interface_number, fail_at);
    if (!r) { const struct hp1020_udc_ep0_spans spans = ep0_spans(); r = (uint32_t)hp1020_udc_ep0_init(&ep0, &adapter, &spans); }
    ep0_state.result = r; state.initialized = r;
    ep0_check(); snapshot(r); ep0_snapshot(); return r;
}
uint32_t hp1020_bulk_fixture_step(uint32_t op, uint32_t a, uint32_t b, uint32_t c, uint32_t d) {
    uint32_t r = HP1020_UDC_EP0_INVALID;
    struct hp1020_tusb_cookie cookie = {0};
    const int have_cookie = ep0_history(a, &cookie);
    const int control_cookie = have_cookie && ep0_index(cookie.endpoint) >= 0;
    check_owned(); ep0_check(); ep0_state.steps++;
    if (op < 40 && !(op == 4 && control_cookie)) {
        /* Do not normalize an EP0 success or write a logical NULL/0 buffer.
         * All EP0 packet storage activity uses explicit component operations. */
        if ((op == 2 || op == 3) && control_cookie)
            memset(hp1020_bulk_fixture_input, state.fill ^ 255, sizeof(hp1020_bulk_fixture_input));
        else r = hp1020_ep0_base_step(op, a, b, c, d);
    } else {
        memcpy(&protected_memory, &memory.data, sizeof(memory.data));
        if (op == 4 && control_cookie) r = (uint32_t)ep0_cancelled(cookie, 1, 0);
        else if (op == 40 && (a == 0 || a == 0x80) && b <= 1 && c <= UINT32_C(0xffffff)) {
            const uint32_t i = a ? 1 : 0;
            ep0_state.slot[i].automatic = (uint8_t)b;
            ep0_state.slot[i].publish = (struct hp1020_udc_ep0_publish_facts){
                (uint8_t)(c >> 16), (uint8_t)(c >> 8), (uint8_t)c
            };
            r = HP1020_UDC_EP0_OK;
        } else if (op == 41 && have_cookie && d <= 5)
            r = (uint32_t)ep0_publish(cookie, b, d);
        else if (op == 42 && have_cookie && d <= 5)
            r = (uint32_t)ep0_cancel_request(cookie, d);
        else if (op == 43 && have_cookie) r = (uint32_t)ep0_cancelled(cookie, b, d);
        else if (op == 44 && have_cookie) {
            struct hp1020_udc_ep0_observation observation;
            observation.cookie = cookie; observation.endpoint_fault = c;
            memcpy(observation.descriptor, hp1020_bulk_fixture_input, 16);
            r = (uint32_t)ep0_observe(observation, b, ep0_be32(hp1020_bulk_fixture_input + 16), d);
        } else if (op == 45 && (a == 0 || a == 0x80) && b <= 12) {
            ep0_state.slot[a ? 1 : 0].injection = b; r = HP1020_UDC_EP0_OK;
        } else if (op == 46 && control_cookie && ep0_current(cookie)) {
            const uint32_t i = cookie.endpoint ? 1 : 0;
            const uint32_t capacity = b == 0 ? 16 : b == 1 && !i ? 64 : 0;
            if (ep0.slots[i].phase == HP1020_UDC_EP0_EXPOSED && capacity && c <= capacity && d <= capacity-c) {
                uint8_t *target = b ? ep0_packet(i) : ep0_descriptor(i);
                uint8_t *shadow = b ? packet_shadow[i] : descriptor_shadow[i];
                memcpy(target + c, hp1020_bulk_fixture_input, d);
                memcpy(shadow + c, hp1020_bulk_fixture_input, d); r = HP1020_UDC_EP0_OK;
            }
        } else if (op == 47 && control_cookie && ep0_current(cookie) && b < EP0_SNAPSHOTS) {
            const uint32_t i = cookie.endpoint ? 1 : 0;
            if (ep0.slots[i].phase == HP1020_UDC_EP0_EXPOSED) {
                ep0_saved[b].cookie = cookie; ep0_saved[b].endpoint_fault = 0;
                memcpy(ep0_saved[b].descriptor, ep0_descriptor(i), 16);
                ep0_saved_valid[b] = 1; r = HP1020_UDC_EP0_OK;
            }
        } else if (op == 48 && a < EP0_SNAPSHOTS && ep0_saved_valid[a]) {
            struct hp1020_udc_ep0_observation observation = ep0_saved[a];
            observation.endpoint_fault = c;
            r = (uint32_t)ep0_observe(observation, b, ep0_be32(hp1020_bulk_fixture_input), d);
        } else if (op == 49 && (a == 64 || a == 400) && ep0_state.steps == 1 &&
            !adapter.last_submission_id && !adapter.control_epoch && !printer.last_request_id &&
            !tud_task_event_ready() && !packets[0].live && !packets[1].live && !packets[2].live) {
            /* FIRST-USE test input only, before any adapter/USB event. This is
             * not a production API for mutating an initialized class profile. */
            device_id[0] = (uint8_t)(a >> 8); device_id[1] = (uint8_t)a;
            printer.config.device_id_length = (uint16_t)a;
            ep0_state.device_id_length = a; r = HP1020_UDC_EP0_OK;
        } else if (op == 50) r = (uint32_t)ep0_probe_init(a, b, c, d);
        if (memcmp(&protected_memory, &memory.data, sizeof(memory.data))) ep0_violation();
        memset(hp1020_bulk_fixture_input, state.fill ^ 255, sizeof(hp1020_bulk_fixture_input));
        ep0_state.result = r;
    }
    ep0_drain_cancel_requests();
    ep0_check(); snapshot(r); ep0_snapshot(); return r;
}
uint8_t *hp1020_ep0_fixture_storage(void) { return (uint8_t *)(void *)&ep0_memory; }
uint32_t hp1020_ep0_fixture_storage_bytes(void) { return (uint32_t)sizeof(ep0_memory); }
uint32_t hp1020_ep0_fixture_component_bytes(void) {
    return (uint32_t)(sizeof(struct hp1020_udc_ep0) + sizeof(struct hp1020_udc_ep0_memory));
}
