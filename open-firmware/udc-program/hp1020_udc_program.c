/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Experimental injected logical register accesses only, no live backend. */
#include "hp1020_udc_program.h"
#include <stddef.h>

#define PERMISSION_ALL (HP1020_UDC_SETUP_ALLOW_SERVICE | HP1020_UDC_SETUP_ALLOW_ARM | HP1020_UDC_SETUP_ALLOW_PUMP)
#define EP_IN_CTL UINT32_C(0x020)
#define EP_IN_FIFO UINT32_C(0x028)
#define EP_IN_MPS UINT32_C(0x02c)
#define EP_IN_DESPTR UINT32_C(0x034)
#define EP_OUT_CTL UINT32_C(0x220)
#define EP_OUT_MPS UINT32_C(0x22c)
#define EP_OUT_DESPTR UINT32_C(0x234)
#define DEVCTL UINT32_C(0x404)
#define EP_IRQ_MASK UINT32_C(0x418)
#define OUT_NE UINT32_C(0x508)
#define IN_NE UINT32_C(0x50c)
#define EP_TYPE UINT32_C(0x30)
#define EP_BULK UINT32_C(0x20)
#define EP_STALL UINT32_C(0x01)
#define EP_SNAK UINT32_C(0x80)
/* Suppress old FLUSH/POLL/SNAK/CNAK/RRDY command/enable intent and do not write
 * the read-only NAK status bit. Request SNAK only, under the separate supplied
 * safe-IN-SNAK condition. SN/type/reserved fields otherwise remain as read.
 * This issues no CNAK, DMA start or FIFO flush. */
#define EP_SUPPRESS UINT32_C(0x3ca)
#define BULK_IRQ_BITS UINT32_C(0x00020002)
#define NE_FIELDS UINT32_C(0x3fffffff)
#define OUT_NE_64 UINT32_C(0x020000c1)
#define IN_NE_64 UINT32_C(0x020000d1)
#define CSR_DONE UINT32_C(0x2000)
#define DEVCTL_RDE UINT32_C(0x04)
/* Do not replay an observed resume/flush/CSR_DONE command from a DEVCTL read.
 * The bounded supplied profile requires these command bits read as zero. */
#define DEVCTL_COMMANDS UINT32_C(0x6001)

static bool valid(const struct hp1020_udc_program *p) {
    return p && p->initialized && p->ingress && p->ingress->initialized &&
        p->ingress->adapter && p->ingress->adapter->initialized;
}
static bool ticket_equal(struct hp1020_tusb_programming_ticket a,
    struct hp1020_tusb_programming_ticket b) {
    return a.sequence == b.sequence && a.control_epoch == b.control_epoch &&
        a.transport_epoch == b.transport_epoch;
}
static bool cookie_equal(struct hp1020_tusb_cookie a, struct hp1020_tusb_cookie b) {
    return a.id == b.id && a.epoch == b.epoch && a.generation == b.generation &&
        a.sequence == b.sequence && a.endpoint == b.endpoint;
}
static struct hp1020_tusb_programming_ticket active_ticket(const struct hp1020_udc_program *p) {
    const struct hp1020_tusb_adapter *a = p->ingress->adapter;
    const struct hp1020_tusb_programming_ticket t = {
        a->active_offload.sequence, a->active_control_epoch, a->transport_epoch};
    return t;
}
static uint16_t le16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | (uint16_t)((uint16_t)p[1] << 8));
}
static bool configuration_request(const struct hp1020_tusb_adapter *a) {
    const uint8_t *b = a->active_setup;
    return !(b[0] & 0x7f) && b[1] == TUSB_REQ_SET_CONFIGURATION &&
        le16(b + 2) <= 1 && !le16(b + 4) && !le16(b + 6);
}
static bool no_owners(const struct hp1020_tusb_adapter *a) {
    return !a->owners[0].state && !a->owners[1].state && !a->owners[2].state &&
        !a->prepared && !a->delivering_live && !a->response_owned;
}
static bool no_bulk(const struct hp1020_tusb_adapter *a) {
    return !a->owners[2].state && !a->prepared && !a->delivering_live;
}
static enum hp1020_udc_program_result leave(struct hp1020_udc_program *p,
    enum hp1020_udc_program_result r) {
    p->busy = 0;
    return r;
}
static enum hp1020_udc_program_result enter(struct hp1020_udc_program *p) {
    if (!valid(p)) return HP1020_UDC_PROGRAM_INVALID;
    if (p->busy) return HP1020_UDC_PROGRAM_WAIT;
    if (p->failed) return HP1020_UDC_PROGRAM_FAULT;
    p->busy = 1;
    return HP1020_UDC_PROGRAM_OK;
}
static void fail(struct hp1020_udc_program *p, struct hp1020_tusb_programming_ticket ticket,
    uint8_t operation, uint32_t offset, uint32_t value, uint8_t result, uint8_t consumed) {
    if (!p->failed) {
        p->failure = (struct hp1020_udc_program_failure){
            ticket, offset, value, operation, result, consumed};
        p->failed = 1;
    }
    p->binding_ready = 0;
}
static enum hp1020_udc_program_result fact_result(struct hp1020_udc_program_facts f) {
    const uint8_t v[7] = {f.io_profile, f.mode_packet64_be, f.dynamic_csr,
        f.affected_quiescent, f.table_coherent, f.fifo_geometry, f.in_snak_safe};
    bool missing = false;
    for (unsigned i = 0; i < 7; ++i) {
        if (v[i] > 1) return HP1020_UDC_PROGRAM_INVALID;
        if (!v[i]) missing = true;
    }
    return missing ? HP1020_UDC_PROGRAM_WAIT : HP1020_UDC_PROGRAM_OK;
}
static bool readable(uint32_t offset) {
    switch (offset) {
    case EP_IN_CTL: case EP_IN_FIFO: case EP_IN_MPS: case EP_OUT_CTL:
    case EP_OUT_MPS: case DEVCTL: case EP_IRQ_MASK: case OUT_NE: case IN_NE:
        return true;
    default: return false;
    }
}
static bool rd(struct hp1020_udc_program *p, struct hp1020_tusb_programming_ticket t,
    uint32_t offset, uint32_t *value) {
    enum hp1020_udc_program_io_result r = HP1020_UDC_PROGRAM_IO_UNKNOWN;
    if (readable(offset)) r = p->io.read32(p->io.context, offset, value);
    if (r == HP1020_UDC_PROGRAM_IO_OK) return true;
    fail(p, t, HP1020_UDC_PROGRAM_READ, offset, 0, (uint8_t)r, 0);
    return false;
}
static bool wr(struct hp1020_udc_program *p, struct hp1020_tusb_programming_ticket t,
    uint32_t offset, uint32_t value, uint8_t consumed) {
    bool permitted = offset == EP_IN_CTL || offset == EP_IN_MPS || offset == EP_OUT_CTL ||
        offset == EP_OUT_MPS || offset == EP_IRQ_MASK || offset == OUT_NE || offset == IN_NE;
    if (offset == EP_IN_DESPTR || offset == EP_OUT_DESPTR) permitted = value == 0;
    if (offset == DEVCTL) permitted = consumed && (value & CSR_DONE);
    enum hp1020_udc_program_io_result r = HP1020_UDC_PROGRAM_IO_UNKNOWN;
    if (permitted) r = p->io.write32(p->io.context, offset, value);
    if (r == HP1020_UDC_PROGRAM_IO_OK) return true;
    fail(p, t, HP1020_UDC_PROGRAM_WRITE, offset, value, (uint8_t)r, consumed);
    return false;
}
static bool order(struct hp1020_udc_program *p, struct hp1020_tusb_programming_ticket t,
    uint8_t consumed) {
    const enum hp1020_udc_program_io_result r = p->io.order(p->io.context);
    if (r == HP1020_UDC_PROGRAM_IO_OK) return true;
    fail(p, t, HP1020_UDC_PROGRAM_ORDER, UINT32_MAX, 0, (uint8_t)r, consumed);
    return false;
}
static void selection(struct hp1020_udc_program *p, struct hp1020_tusb_programming_ticket t) {
    if (!ticket_equal(p->selection, t)) {
        p->selection = t;
        p->selection_mask = 0;
        p->binding_ready = 0;
    }
}
/* This is command construction, not a controller state simulator. */
static bool program_endpoint(struct hp1020_udc_program *p,
    struct hp1020_tusb_programming_ticket t, bool in) {
    uint32_t v;
    const uint32_t ctl = in ? EP_IN_CTL : EP_OUT_CTL;
    const uint32_t mps = in ? EP_IN_MPS : EP_OUT_MPS;
    const uint32_t ne = in ? p->layout.in_ne_offset : p->layout.out_ne_offset;
    const uint32_t irq = in ? UINT32_C(2) : UINT32_C(0x20000);
    /* FIFO allocation must already be fixed at the supplied layout. Sony's
     * family guidance forbids dynamically changing it during operation. */
    if (in) {
        if (!rd(p, t, EP_IN_FIFO, &v)) return false;
        if ((v & UINT32_C(0xffff)) != p->layout.in_fifo_words) {
            fail(p, t, HP1020_UDC_PROGRAM_FACT, EP_IN_FIFO, v,
                HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
            return false;
        }
    }
    if (!rd(p, t, ctl, &v) ||
        !wr(p, t, ctl, (v & ~(EP_TYPE | EP_STALL | EP_SUPPRESS)) | EP_BULK | EP_SNAK, 0) ||
        !rd(p, t, mps, &v) || !wr(p, t, mps, (v & UINT32_C(0xffff0000)) | 64u, 0))
        return false;
    if (!rd(p, t, ne, &v) ||
        !wr(p, t, ne, (v & ~NE_FIELDS) | (in ? IN_NE_64 : OUT_NE_64), 0) ||
        !rd(p, t, EP_IRQ_MASK, &v) || !wr(p, t, EP_IRQ_MASK, v & ~irq, 0) ||
        !order(p, t, 0)) return false;
    const uint8_t bit = in ? 2u : 1u;
    p->completed_mask |= bit;
    p->selection_mask |= bit;
    if (p->selection_mask == 3) p->binding_ready = 1;
    return true;
}
static bool callback_context(const struct hp1020_udc_program *p, uint8_t rhport) {
    const struct hp1020_tusb_adapter *a = p->ingress->adapter;
    /* Trust only a current real stack callback. Request support is checked
     * AFTER this distinction so a void callback cannot silently reject an
     * unsupported raw alias which the core really dispatched. */
    return p->servicing && a->busy && a->stack_active && rhport == a->config.rhport &&
        a->active_control_epoch && a->active_control_epoch == a->control_epoch &&
        a->control_epoch == p->service_control_epoch &&
        a->control_epoch == p->ingress->adapter_control_epoch &&
        !p->ingress->pending_kind && !p->ingress->terminal &&
        p->ingress->last_sequence == p->ingress->last_admitted_sequence;
}
static bool disable_endpoints(struct hp1020_udc_program *p,
    struct hp1020_tusb_programming_ticket t) {
    selection(p, t); p->binding_ready = 0;
    uint32_t v;
    if (!rd(p, t, EP_IRQ_MASK, &v) || !wr(p, t, EP_IRQ_MASK, v | BULK_IRQ_BITS, 0) ||
        !rd(p, t, EP_OUT_CTL, &v) || !wr(p, t, EP_OUT_CTL, (v & ~EP_SUPPRESS) | EP_SNAK, 0) ||
        !wr(p, t, EP_OUT_DESPTR, 0, 0) ||
        !rd(p, t, EP_IN_CTL, &v) || !wr(p, t, EP_IN_CTL, (v & ~EP_SUPPRESS) | EP_SNAK, 0) ||
        !wr(p, t, EP_IN_DESPTR, 0, 0) || !order(p, t, 0)) return false;
    p->completed_mask = p->selection_mask = 0;
    return true;
}

enum hp1020_udc_program_result hp1020_udc_program_init(struct hp1020_udc_program *p,
    struct hp1020_udc_setup *ingress, const struct hp1020_udc_program_io *io,
    struct hp1020_udc_program_layout layout, struct hp1020_udc_program_init_facts f) {
    if (!p || !ingress || !ingress->initialized || !ingress->adapter ||
        !ingress->adapter->initialized || !io || !io->read32 || !io->write32 || !io->order ||
        layout.out_ne_offset != OUT_NE || layout.in_ne_offset != IN_NE || layout.in_fifo_words < 16 ||
        f.noncontrol_initially_clean > 1 || f.table_coherent > 1 || f.fifo_geometry > 1)
        return HP1020_UDC_PROGRAM_INVALID;
    const struct hp1020_tusb_adapter *a = ingress->adapter;
    if (a->config.rhport || a->config.ep_out != 1 || a->config.ep_in != 0x81 ||
        a->config.out_capacity != 64 || a->printer->config.interface_number ||
        a->control_epoch || a->last_submission_id || ingress->last_sequence)
        return HP1020_UDC_PROGRAM_INVALID;
    if (!f.noncontrol_initially_clean || !f.table_coherent || !f.fifo_geometry)
        return HP1020_UDC_PROGRAM_WAIT;
    *p = (struct hp1020_udc_program){0};
    p->ingress = ingress; p->io = *io; p->layout = layout; p->initialized = 1;
    return HP1020_UDC_PROGRAM_OK;
}

uint32_t hp1020_udc_program_progress(const struct hp1020_udc_program *p) {
    if (!valid(p) || p->busy || p->servicing) return 0;
    const uint32_t permission = hp1020_udc_setup_progress(p->ingress);
    if (p->failed) return permission == HP1020_UDC_SETUP_ALLOW_SERVICE ? permission : 0;
    if (!p->binding_ready && p->ingress->adapter->opened)
        return permission & HP1020_UDC_SETUP_ALLOW_SERVICE;
    return permission;
}
bool hp1020_udc_program_submission_allowed(struct hp1020_udc_program *p) {
    if (!valid(p) || p->busy || p->failed) return false;
    const struct hp1020_tusb_adapter *a = p->ingress->adapter;
    const uint8_t *b = a->active_setup;
    /* The core skips close_all when cfg0 remains0, even after a software reset
     * that did not establish controller cleanup. Match its LOW-value routing,
     * including malformed fields/direction, before any status owner is bound.
     * Only this trusted current callback may create a failure ticket; a late
     * external query never promotes stale request bytes into new provenance. */
    if (callback_context(p, a->config.rhport) && !a->active_offload.sequence &&
        !(b[0] & 0x7f) && b[1] == TUSB_REQ_SET_CONFIGURATION && b[2] == 0 &&
        (!configuration_request(a) || p->completed_mask || p->selection_mask ||
         !a->fenced || !a->printer->document->receive.stopped)) {
        fail(p, active_ticket(p), HP1020_UDC_PROGRAM_REQUEST, UINT32_MAX, 0,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
        return false;
    }
    return true;
}
enum hp1020_udc_program_result hp1020_udc_program_service(struct hp1020_udc_program *p) {
    if (!valid(p)) return HP1020_UDC_PROGRAM_INVALID;
    if (p->busy || p->servicing) return HP1020_UDC_PROGRAM_WAIT;
    const uint32_t permission = hp1020_udc_program_progress(p);
    if (!(permission & HP1020_UDC_SETUP_ALLOW_SERVICE)) return HP1020_UDC_PROGRAM_WAIT;
    const bool was_failed = p->failed != 0;
    struct hp1020_tusb_adapter *a = p->ingress->adapter;
    if (permission == HP1020_UDC_SETUP_ALLOW_SERVICE &&
        p->ingress->reset_control_epoch == a->control_epoch &&
        a->active_control_epoch != a->control_epoch) p->binding_ready = 0;
    if (a->active_control_epoch != a->control_epoch &&
        a->pending_offload.sequence && a->pending_offload.kind == HP1020_TUSB_OFFLOAD_INTERFACE)
        p->binding_ready = 0;
    p->service_control_epoch = a->control_epoch;
    p->servicing = 1;
    p->last_adapter_result = hp1020_tusb_adapter_service(a);
    p->servicing = 0;
    if (!was_failed && p->failed) return HP1020_UDC_PROGRAM_FAULT;
    if (p->last_adapter_result == HP1020_TUSB_OK) return HP1020_UDC_PROGRAM_OK;
    if (p->last_adapter_result == HP1020_TUSB_WAIT) return HP1020_UDC_PROGRAM_WAIT;
    return HP1020_UDC_PROGRAM_ADAPTER_ERROR;
}

enum hp1020_udc_program_result hp1020_udc_program_open(struct hp1020_udc_program *p,
    uint8_t rhport, const uint8_t *d, uint32_t length, struct hp1020_udc_program_facts f) {
    enum hp1020_udc_program_result r = enter(p);
    if (r) return r;
    if (!callback_context(p, rhport)) return leave(p, HP1020_UDC_PROGRAM_INVALID);
    struct hp1020_tusb_adapter *a = p->ingress->adapter;
    const struct hp1020_tusb_programming_ticket t = active_ticket(p);
    if (!configuration_request(a) || !a->fenced || !a->printer->document->receive.stopped ||
        !d || length != 7 || d[0] != 7 || d[1] != TUSB_DESC_ENDPOINT ||
        (d[2] != 1 && d[2] != 0x81) || d[3] != TUSB_XFER_BULK || le16(d + 4) != 64 ||
        d[6] || a->active_setup[2] != 1 || !no_owners(a) || a->opened) {
        fail(p, t, HP1020_UDC_PROGRAM_REQUEST, UINT32_MAX, 0,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
        return leave(p, HP1020_UDC_PROGRAM_INVALID);
    }
    r = fact_result(f);
    if (r) {
        fail(p, t, HP1020_UDC_PROGRAM_FACT, UINT32_MAX, 0,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
        return leave(p, r);
    }
    selection(p, t);
    const uint8_t bit = d[2] == 1 ? 1u : 2u;
    if (p->selection_mask & bit) return leave(p, HP1020_UDC_PROGRAM_STALE);
    return leave(p, program_endpoint(p, t, bit == 2) ? HP1020_UDC_PROGRAM_OK : HP1020_UDC_PROGRAM_FAULT);
}

enum hp1020_udc_program_result hp1020_udc_program_close_all(struct hp1020_udc_program *p,
    uint8_t rhport, struct hp1020_udc_program_facts f) {
    enum hp1020_udc_program_result r = enter(p);
    if (r) return r;
    if (!callback_context(p, rhport)) return leave(p, HP1020_UDC_PROGRAM_INVALID);
    const struct hp1020_tusb_programming_ticket t = active_ticket(p);
    const struct hp1020_tusb_adapter *a = p->ingress->adapter;
    if (!configuration_request(a) || !a->fenced || !a->printer->document->receive.stopped) {
        fail(p, t, HP1020_UDC_PROGRAM_REQUEST, UINT32_MAX, 0,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
        return leave(p, HP1020_UDC_PROGRAM_INVALID);
    }
    r = fact_result(f);
    if (r || !no_owners(p->ingress->adapter)) {
        fail(p, t, HP1020_UDC_PROGRAM_FACT, UINT32_MAX, 0,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
        return leave(p, r ? r : HP1020_UDC_PROGRAM_WAIT);
    }
    return leave(p, disable_endpoints(p, t) ? HP1020_UDC_PROGRAM_OK : HP1020_UDC_PROGRAM_FAULT);
}

enum hp1020_udc_program_result hp1020_udc_program_complete_selection(struct hp1020_udc_program *p,
    struct hp1020_udc_program_facts f) {
    enum hp1020_udc_program_result r = enter(p);
    if (r) return r;
    struct hp1020_tusb_adapter *a = p->ingress->adapter;
    if (p->servicing || a->busy || hp1020_udc_setup_progress(p->ingress) != PERMISSION_ALL)
        return leave(p, HP1020_UDC_PROGRAM_WAIT);
    const struct hp1020_tusb_offload *o = &a->active_offload;
    const struct hp1020_tusb_programming_ticket t = active_ticket(p);
    const bool unconfigure = o->kind == HP1020_TUSB_OFFLOAD_CONFIGURATION && !o->configuration;
    const bool reselect = o->kind == HP1020_TUSB_OFFLOAD_INTERFACE && o->configuration == 1;
    if (!o->sequence || (!unconfigure && !reselect) || o->interface_number ||
        o->alternate || t.control_epoch != a->control_epoch ||
        o->sequence != p->ingress->last_admitted_sequence ||
        o->sequence != p->ingress->last_sequence || a->offload_transport_epoch != t.transport_epoch)
        return leave(p, HP1020_UDC_PROGRAM_STALE);
    if ((reselect && (!a->opened || !tud_mounted())) ||
        (unconfigure && (a->opened || tud_mounted())) ||
        !a->fenced || !a->printer->document->receive.stopped || !no_bulk(a) ||
        a->owners[0].state || a->response_owned ||
        a->owners[1].state != HP1020_TUSB_OWNER_DCD || !a->owners[1].auto_status ||
        a->owners[1].auto_granted || a->owners[1].cancel_requested || a->owners[1].packet_fault ||
        a->owners[1].cookie.epoch != t.control_epoch)
        return leave(p, HP1020_UDC_PROGRAM_WAIT);
    r = fact_result(f);
    if (r == HP1020_UDC_PROGRAM_INVALID) return leave(p, r);
    if (unconfigure && !p->completed_mask && !p->selection_mask)
        return leave(p, HP1020_UDC_PROGRAM_OK); /* No new programming claim; no facts consumed. */
    if (r) return leave(p, r); /* No synchronous core callback is being accepted. */
    if (unconfigure)
        return leave(p, disable_endpoints(p, t) ? HP1020_UDC_PROGRAM_OK : HP1020_UDC_PROGRAM_FAULT);
    if (ticket_equal(p->selection, t) && p->selection_mask == 3)
        return leave(p, HP1020_UDC_PROGRAM_STALE);
    selection(p, t);
    if (!program_endpoint(p, t, false) || !program_endpoint(p, t, true))
        return leave(p, HP1020_UDC_PROGRAM_FAULT);
    return leave(p, HP1020_UDC_PROGRAM_OK);
}

enum hp1020_udc_program_result hp1020_udc_program_grant(struct hp1020_udc_program *p,
    uint32_t sequence, struct hp1020_tusb_cookie cookie, struct hp1020_udc_program_grant_facts f) {
    enum hp1020_udc_program_result r = enter(p);
    if (r) return r;
    if (p->servicing || p->ingress->adapter->busy ||
        hp1020_udc_setup_progress(p->ingress) != PERMISSION_ALL)
        return leave(p, HP1020_UDC_PROGRAM_WAIT);
    if (f.io_profile > 1 || f.dynamic_csr > 1 || f.affected_defaults > 1 ||
        f.status_gate_current > 1 || f.devctl_stable > 1)
        return leave(p, HP1020_UDC_PROGRAM_INVALID);
    if (!f.io_profile || !f.dynamic_csr || !f.affected_defaults ||
        !f.status_gate_current || !f.devctl_stable)
        return leave(p, HP1020_UDC_PROGRAM_WAIT);
    const struct hp1020_tusb_adapter *a = p->ingress->adapter;
    const struct hp1020_tusb_programming_ticket t = active_ticket(p);
    if (!sequence || sequence != t.sequence || sequence != p->ingress->last_sequence ||
        sequence != p->ingress->last_admitted_sequence || t.control_epoch != a->control_epoch ||
        t.transport_epoch != a->offload_transport_epoch)
        return leave(p, HP1020_UDC_PROGRAM_STALE);
    /* Read-only check of the EXISTING owner before even a bus read. A stale or
     * duplicate call must not turn into a fresh I/O failure. Keep the original
     * generation: a valid held owner can outlive document-generation recovery.
     * The bridge remains the final authoritative one-shot mutation below. */
    const struct hp1020_tusb_owner *owner = &a->owners[1];
    if (!cookie.id || cookie.endpoint != 0x80 || owner->state != HP1020_TUSB_OWNER_DCD ||
        !owner->auto_status || owner->auto_granted || owner->cancel_requested || owner->packet_fault ||
        !cookie_equal(cookie, owner->cookie) || cookie.epoch != a->control_epoch ||
        cookie.epoch != a->active_control_epoch || a->pending_kind || a->programming_dirty)
        return leave(p, HP1020_UDC_PROGRAM_STALE);
    if (a->exhausted || owner->buffer || owner->length ||
        !usbd_edpt_busy(a->config.rhport, 0x80) || usbd_edpt_stalled(a->config.rhport, 0x80))
        return leave(p, HP1020_UDC_PROGRAM_ADAPTER_ERROR);
    if (a->active_offload.configuration == 1) {
        if (usbd_edpt_stalled(a->config.rhport, a->config.ep_out) ||
            usbd_edpt_stalled(a->config.rhport, a->config.ep_in))
            return leave(p, HP1020_UDC_PROGRAM_WAIT);
        if (!p->binding_ready || p->completed_mask != 3 || p->selection_mask != 3 ||
            !ticket_equal(p->selection, t)) return leave(p, HP1020_UDC_PROGRAM_WAIT);
    } else if (a->active_offload.kind != HP1020_TUSB_OFFLOAD_CONFIGURATION ||
        a->active_offload.configuration || p->completed_mask || a->opened || tud_mounted()) {
        return leave(p, HP1020_UDC_PROGRAM_WAIT);
    }
    uint32_t v;
    if (!rd(p, t, DEVCTL, &v)) return leave(p, HP1020_UDC_PROGRAM_FAULT);
    /* A software bulk reservation is not evidence of physical RX enable.
     * This narrower backend never replays a sampled RDE=1 across its RMW. */
    if (v & DEVCTL_RDE) return leave(p, HP1020_UDC_PROGRAM_WAIT);
    if (v & DEVCTL_COMMANDS) {
        fail(p, t, HP1020_UDC_PROGRAM_REQUEST, DEVCTL, v,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED, 0);
        return leave(p, HP1020_UDC_PROGRAM_FAULT);
    }
    if (!order(p, t, 0)) return leave(p, HP1020_UDC_PROGRAM_FAULT);
    struct hp1020_tusb_auto_status_grant grant;
    const struct hp1020_udc_auto_status_facts facts = {f.affected_defaults, f.status_gate_current};
    p->last_bridge_result = hp1020_udc_setup_take_auto_status(p->ingress, sequence, cookie, facts, &grant);
    if (p->last_bridge_result != HP1020_UDC_SETUP_OK) {
        if (p->last_bridge_result == HP1020_UDC_SETUP_WAIT) return leave(p, HP1020_UDC_PROGRAM_WAIT);
        if (p->last_bridge_result == HP1020_UDC_SETUP_STALE) return leave(p, HP1020_UDC_PROGRAM_STALE);
        return leave(p, HP1020_UDC_PROGRAM_ADAPTER_ERROR);
    }
    /* No yield, callback into the stack, new ingress, or queued proposal here.
     * Any later failure retains the already-consumed grant; never replay it. */
    if (!wr(p, t, DEVCTL, v | CSR_DONE, 1) || !order(p, t, 1))
        return leave(p, HP1020_UDC_PROGRAM_FAULT);
    return leave(p, HP1020_UDC_PROGRAM_OK);
}

enum hp1020_udc_program_result hp1020_udc_program_pending_cleanup(
    const struct hp1020_udc_program *p, struct hp1020_udc_program_failure *failure) {
    if (!valid(p) || !failure) return HP1020_UDC_PROGRAM_INVALID;
    if (p->busy || p->servicing) return HP1020_UDC_PROGRAM_WAIT;
    if (!p->failed) return HP1020_UDC_PROGRAM_STALE;
    *failure = p->failure;
    return HP1020_UDC_PROGRAM_OK;
}
enum hp1020_udc_program_result hp1020_udc_program_ack_cleanup(struct hp1020_udc_program *p,
    struct hp1020_tusb_programming_ticket ticket, uint8_t clean) {
    if (!valid(p) || clean > 1) return HP1020_UDC_PROGRAM_INVALID;
    if (p->busy || p->servicing || p->ingress->adapter->busy) return HP1020_UDC_PROGRAM_WAIT;
    if (!p->failed || !ticket.control_epoch || !ticket_equal(ticket, p->failure.ticket))
        return HP1020_UDC_PROGRAM_STALE;
    struct hp1020_tusb_adapter *a = p->ingress->adapter;
    if (!clean || !no_owners(a) || !a->fenced || !a->printer->document->receive.stopped ||
        a->opened || tud_mounted()) return HP1020_UDC_PROGRAM_WAIT;
    if (a->exhausted) return HP1020_UDC_PROGRAM_ADAPTER_ERROR;
    p->busy = 1;
    if (a->programming_dirty) {
        p->last_adapter_result = hp1020_tusb_adapter_ack_programming_cleanup(a, ticket, clean);
        if (p->last_adapter_result != HP1020_TUSB_OK)
            return leave(p, HP1020_UDC_PROGRAM_ADAPTER_ERROR);
    }
    p->failed = 0; p->completed_mask = p->selection_mask = p->binding_ready = 0;
    p->selection = (struct hp1020_tusb_programming_ticket){0};
    /* Preserve failure bytes for diagnostics, but they no longer authorize cleanup. */
    return leave(p, HP1020_UDC_PROGRAM_OK);
}
