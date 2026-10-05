/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Experimental injected recording hooks only; no physical backend. */
#include "hp1020_udc_publish.h"
#include <stddef.h>

#define PERMISSION_ALL (HP1020_UDC_SETUP_ALLOW_SERVICE | HP1020_UDC_SETUP_ALLOW_ARM | HP1020_UDC_SETUP_ALLOW_PUMP)
#define OUT_CTL UINT32_C(0x220)
#define OUT_MPS UINT32_C(0x22c)
#define OUT_DESPTR UINT32_C(0x234)
#define DEVCTL UINT32_C(0x404)
#define DEVSTS UINT32_C(0x408)
#define DEVCTL_REQUIRED UINT32_C(0x220)
#define DEVCTL_FORBIDDEN UINT32_C(0x0000fcd7)
#define DEVCTL_PRESERVE UINT32_C(0xffff0328)
#define RDE UINT32_C(4)
#define OUT_BULK UINT32_C(0x20)
#define OUT_BULK_NAK UINT32_C(0x60)
#define OUT_BULK_CNAK UINT32_C(0x120)
#define RXFIFO_EMPTY UINT32_C(0x8000)

static bool valid(const struct hp1020_udc_publish *p) {
    return p && p->initialized && p->program && p->program->initialized &&
        p->program->ingress && p->program->ingress->initialized &&
        p->program->ingress->adapter && p->program->ingress->adapter->initialized &&
        p->out && p->out->initialized && p->out->adapter == p->program->ingress->adapter;
}
static struct hp1020_tusb_adapter *adapter(const struct hp1020_udc_publish *p) {
    return p->program->ingress->adapter;
}
static bool same_cookie(struct hp1020_tusb_cookie a, struct hp1020_tusb_cookie b) {
    return a.id == b.id && a.epoch == b.epoch && a.generation == b.generation &&
        a.sequence == b.sequence && a.endpoint == b.endpoint;
}
static bool cpu_range_valid(const void *p, uintptr_t bytes) {
    return p && bytes && (uintptr_t)p <= UINTPTR_MAX - (bytes - 1u);
}
static bool cpu_overlap(const void *a, uintptr_t an, const void *b, uintptr_t bn) {
    return (uintptr_t)a <= (uintptr_t)b + bn - 1u &&
        (uintptr_t)b <= (uintptr_t)a + an - 1u;
}
static bool dma_range_valid(uint32_t address, uint32_t bytes) {
    return address && bytes && !(address & 15u) && address <= UINT32_MAX - (bytes - 1u);
}
static bool dma_overlap(uint32_t a, uint32_t an, uint32_t b, uint32_t bn) {
    return a <= b + bn - 1u && b <= a + an - 1u;
}
static bool mappings_valid(const struct hp1020_udc_out *out,
    const struct hp1020_udc_publish_mapping *m) {
    const struct hp1020_rx_memory *memory = out->adapter->printer->document->receive.memory;
    const struct hp1020_udc_out_span d = out->descriptor;
    if (!memory || d.bytes < 16 || !cpu_range_valid(d.cpu, d.bytes) ||
        ((uintptr_t)d.cpu & 15u) || !dma_range_valid(d.dma, d.bytes)) return false;
    for (unsigned i = 0; i < HP1020_RX_SLOTS; ++i) {
        const uint8_t *b = memory->data[i];
        if (!cpu_range_valid(b, 64) || ((uintptr_t)b & 15u) ||
            !dma_range_valid(m->receive_dma[i], 64) ||
            cpu_overlap(b, 64, d.cpu, 16) || dma_overlap(m->receive_dma[i], 64, d.dma, 16))
            return false;
        for (unsigned j = 0; j < i; ++j)
            if (cpu_overlap(b, 64, memory->data[j], 64) ||
                dma_overlap(m->receive_dma[i], 64, m->receive_dma[j], 64)) return false;
    }
    return true;
}
static bool no_owners(const struct hp1020_tusb_adapter *a) {
    return !a->owners[0].state && !a->owners[1].state && !a->owners[2].state &&
        !a->owners[3].state && !a->in_prepared &&
        !a->prepared && !a->delivering_live && !a->response_owned;
}
static enum hp1020_udc_publish_result leave(struct hp1020_udc_publish *p,
    enum hp1020_udc_publish_result result) {
    p->busy = 0;
    return result;
}
static enum hp1020_udc_publish_result facts_valid(struct hp1020_udc_publish_facts f) {
    const uint8_t facts[7] = {f.io_profile, f.receive_dma_idle, f.register_window_stable,
        f.global_receive_ready, f.cnak_window_safe, f.mapping_lease, f.cache_range_safe};
    bool missing = false;
    for (unsigned i = 0; i < 7; ++i) {
        if (facts[i] > 1) return HP1020_UDC_PUBLISH_INVALID;
        if (i != 4 && !facts[i]) missing = true;
    }
    return missing ? HP1020_UDC_PUBLISH_WAIT : HP1020_UDC_PUBLISH_OK;
}
static void fail(struct hp1020_udc_publish *p, struct hp1020_tusb_cookie cookie,
    uint8_t operation, uint32_t offset, uint32_t value, uint32_t dma, uint32_t bytes,
    enum hp1020_udc_program_io_result io_result) {
    if (p->failed) return;
    p->failure = (struct hp1020_udc_publish_failure){
        cookie, p->prefix, offset, value, dma, bytes, operation, (uint8_t)io_result,
        (uint8_t)((p->prefix & HP1020_UDC_PUBLISH_EXPOSED) != 0),
        (uint8_t)p->last_out_result};
    p->failed = 1;
}
static bool order(struct hp1020_udc_publish *p, struct hp1020_tusb_cookie cookie,
    uint32_t completed_bit) {
    const enum hp1020_udc_program_io_result r = p->program->io.order(p->program->io.context);
    if (r != HP1020_UDC_PROGRAM_IO_OK) {
        fail(p, cookie, HP1020_UDC_PUBLISH_ORDER, UINT32_MAX, 0, 0, 0, r);
        return false;
    }
    p->prefix |= completed_bit;
    return true;
}
static bool write32(struct hp1020_udc_publish *p, struct hp1020_tusb_cookie cookie,
    uint32_t offset, uint32_t value, uint32_t completed_bit) {
    const enum hp1020_udc_program_io_result r =
        p->program->io.write32(p->program->io.context, offset, value);
    if (r != HP1020_UDC_PROGRAM_IO_OK) {
        fail(p, cookie, HP1020_UDC_PUBLISH_WRITE, offset, value, 0, 0, r);
        return false;
    }
    p->prefix |= completed_bit;
    return true;
}
static enum hp1020_udc_publish_result preflight_read(struct hp1020_udc_publish *p,
    uint32_t offset, uint32_t *value) {
    uint32_t observed = 0;
    const enum hp1020_udc_program_io_result r =
        p->program->io.read32(p->program->io.context, offset, &observed);
    p->preflight = (struct hp1020_udc_publish_preflight){offset,
        r == HP1020_UDC_PROGRAM_IO_OK ? observed : 0, (uint8_t)r, 0};
    if (r != HP1020_UDC_PROGRAM_IO_OK) return HP1020_UDC_PUBLISH_PREFLIGHT_ERROR;
    *value = observed;
    return HP1020_UDC_PUBLISH_OK;
}
static enum hp1020_udc_publish_result preflight_refuse(struct hp1020_udc_publish *p) {
    p->preflight.refused = 1;
    return HP1020_UDC_PUBLISH_WAIT;
}
static enum hp1020_udc_publish_result preflight(struct hp1020_udc_publish *p,
    struct hp1020_udc_publish_facts f) {
    uint32_t v;
    enum hp1020_udc_publish_result r = preflight_read(p, DEVCTL, &v);
    if (r) return r;
    if ((v & DEVCTL_REQUIRED) != DEVCTL_REQUIRED || (v & DEVCTL_FORBIDDEN))
        return preflight_refuse(p);
    p->saved_devctl = v & DEVCTL_PRESERVE;
    r = preflight_read(p, OUT_CTL, &v);
    if (r) return r;
    if (v != OUT_BULK && v != OUT_BULK_NAK) return preflight_refuse(p);
    p->saved_outctl = v;
    if (v == OUT_BULK_NAK && !f.cnak_window_safe) return HP1020_UDC_PUBLISH_WAIT;
    r = preflight_read(p, OUT_MPS, &v);
    if (r) return r;
    if ((v & UINT32_C(0xffff)) != 64) return preflight_refuse(p);
    r = preflight_read(p, DEVSTS, &v);
    if (r) return r;
    if (!(v & RXFIFO_EMPTY)) return preflight_refuse(p);
    return HP1020_UDC_PUBLISH_OK;
}

enum hp1020_udc_publish_result hp1020_udc_publish_init(struct hp1020_udc_publish *p,
    struct hp1020_udc_program *program, struct hp1020_udc_out *out,
    const struct hp1020_udc_publish_mapping *mapping, const struct hp1020_udc_publish_cache *cache) {
    if (!p || !program || !program->initialized || !program->ingress ||
        !program->ingress->initialized || !program->ingress->adapter ||
        !out || !out->initialized || out->adapter != program->ingress->adapter ||
        !mapping || !cache || !cache->rx_before_device || !cache->descriptor_before_device ||
        !program->io.read32 || !program->io.write32 || !program->io.order)
        return HP1020_UDC_PUBLISH_INVALID;
    const struct hp1020_tusb_adapter *a = out->adapter;
    if (!a->initialized || !a->printer || !a->printer->document ||
        a->config.rhport || a->config.ep_out != 1 || a->config.out_capacity != 64 ||
        a->control_epoch || a->last_submission_id || program->ingress->last_sequence ||
        program->failed || program->busy || program->servicing || out->busy ||
        out->phase != HP1020_UDC_OUT_FREE || !mappings_valid(out, mapping))
        return HP1020_UDC_PUBLISH_INVALID;
    *p = (struct hp1020_udc_publish){0};
    p->program = program; p->out = out; p->mapping = *mapping; p->cache = *cache;
    p->preflight.offset = UINT32_MAX;
    p->initialized = 1;
    return HP1020_UDC_PUBLISH_OK;
}

uint32_t hp1020_udc_publish_progress(const struct hp1020_udc_publish *p) {
    if (!valid(p) || p->busy || p->arming || p->servicing) return 0;
    const uint32_t permission = hp1020_udc_program_progress(p->program);
    if (!p->failed) return permission;
    /* Program may also return SERVICE for an unprogrammed binding. Only the
     * bridge's admitted-but-inactive actual reset is a failure-drain exception. */
    return hp1020_udc_setup_progress(p->program->ingress) == HP1020_UDC_SETUP_ALLOW_SERVICE ?
        permission & HP1020_UDC_SETUP_ALLOW_SERVICE : 0;
}
bool hp1020_udc_publish_submission_allowed(struct hp1020_udc_publish *p) {
    return valid(p) && !p->busy && !p->failed &&
        hp1020_udc_program_submission_allowed(p->program);
}
enum hp1020_udc_publish_result hp1020_udc_publish_service(struct hp1020_udc_publish *p) {
    if (!valid(p)) return HP1020_UDC_PUBLISH_INVALID;
    if (!(hp1020_udc_publish_progress(p) & HP1020_UDC_SETUP_ALLOW_SERVICE))
        return HP1020_UDC_PUBLISH_WAIT;
    p->servicing = 1;
    p->last_program_result = hp1020_udc_program_service(p->program);
    p->servicing = 0;
    if (p->last_program_result == HP1020_UDC_PROGRAM_OK) return HP1020_UDC_PUBLISH_OK;
    if (p->last_program_result == HP1020_UDC_PROGRAM_WAIT) return HP1020_UDC_PUBLISH_WAIT;
    if (p->last_program_result == HP1020_UDC_PROGRAM_FAULT) return HP1020_UDC_PUBLISH_FAULT;
    return HP1020_UDC_PUBLISH_ADAPTER_ERROR;
}

enum hp1020_udc_publish_result hp1020_udc_publish_arm_out(struct hp1020_udc_publish *p,
    struct hp1020_udc_publish_facts f) {
    if (!valid(p)) return HP1020_UDC_PUBLISH_INVALID;
    if (p->busy || p->arming || p->servicing) return HP1020_UDC_PUBLISH_WAIT;
    if (p->failed) return HP1020_UDC_PUBLISH_FAULT;
    struct hp1020_tusb_adapter *a = adapter(p);
    struct hp1020_usb_receive *receive = &a->printer->document->receive;
    enum hp1020_udc_publish_result r = facts_valid(f);
    if (r) return r;
    if (hp1020_udc_publish_progress(p) != PERMISSION_ALL || !p->program->binding_ready ||
        p->out->busy || p->out->phase != HP1020_UDC_OUT_FREE || a->busy || a->stack_active ||
        a->owners[2].state || a->prepared || a->delivering_live ||
        !tud_inited() || !tud_ready() || !a->opened || a->fenced || a->input_closed ||
        receive->stopped || a->printer->reset_active ||
        (a->pending_kind && a->pending_destructive) ||
        usbd_edpt_busy(a->config.rhport, a->config.ep_out) ||
        usbd_edpt_stalled(a->config.rhport, a->config.ep_out) ||
        receive->count >= HP1020_RX_SLOTS)
        return HP1020_UDC_PUBLISH_WAIT;
    p->busy = 1;
    p->prefix = 0;
    p->preflight = (struct hp1020_udc_publish_preflight){UINT32_MAX, 0, 0, 0};
    r = preflight(p, f);
    if (r) return leave(p, r);
    p->arm_control_epoch = a->control_epoch;
    p->arm_transport_epoch = a->transport_epoch;
    p->arm_generation = receive->generation;
    p->arm_ingress_sequence = p->program->ingress->last_sequence;
    p->busy = 0;
    p->arming = p->window = 1;
    p->last_adapter_result = hp1020_tusb_adapter_arm_out(a);
    p->window = p->arming = 0;
    if (p->failed) return HP1020_UDC_PUBLISH_FAULT;
    if (p->last_adapter_result == HP1020_TUSB_OK)
        return (p->prefix & HP1020_UDC_PUBLISH_RDE_ORDERED) ?
            HP1020_UDC_PUBLISH_OK : HP1020_UDC_PUBLISH_ADAPTER_ERROR;
    if (p->last_adapter_result == HP1020_TUSB_WAIT) return HP1020_UDC_PUBLISH_WAIT;
    return HP1020_UDC_PUBLISH_ADAPTER_ERROR;
}

enum hp1020_udc_publish_result hp1020_udc_publish_prepare_and_publish(
    struct hp1020_udc_publish *p, uint8_t rhport, uint8_t endpoint,
    uint8_t *buffer, uint16_t length, struct hp1020_tusb_cookie *cookie_out) {
    if (!valid(p)) return HP1020_UDC_PUBLISH_INVALID;
    if (!p->arming || !p->window || p->busy || p->servicing || p->failed)
        return HP1020_UDC_PUBLISH_INVALID;
    /* Consume the sole callback window even when its supplied arguments reject.
     * No pre-bind error invents a packet identity or a local failure record. */
    p->window = 0;
    struct hp1020_tusb_adapter *a = adapter(p);
    const struct hp1020_udc_setup *ingress = p->program->ingress;
    if (!cookie_out || rhport || endpoint != 1 || length != 64 || !buffer ||
        !a->busy || !a->stack_active || !a->prepared || buffer != a->prepared_buffer ||
        a->control_epoch != p->arm_control_epoch || a->transport_epoch != p->arm_transport_epoch ||
        a->printer->document->receive.generation != p->arm_generation ||
        ingress->last_sequence != p->arm_ingress_sequence || ingress->pending_kind || ingress->terminal ||
        a->control_epoch != ingress->adapter_control_epoch ||
        !p->program->binding_ready || p->program->servicing ||
        !hp1020_udc_program_submission_allowed(p->program))
        return HP1020_UDC_PUBLISH_INVALID;
    unsigned slot = HP1020_RX_SLOTS;
    for (unsigned i = 0; i < HP1020_RX_SLOTS; ++i)
        if (buffer == a->printer->document->receive.memory->data[i]) slot = i;
    if (slot == HP1020_RX_SLOTS) return HP1020_UDC_PUBLISH_INVALID;
    p->busy = 1;
    const struct hp1020_udc_out_span rx = {buffer, p->mapping.receive_dma[slot], 64};
    struct hp1020_tusb_cookie cookie = {0};
    p->last_out_result = hp1020_udc_out_prepare(p->out, endpoint, rx, length, &cookie);
    if (p->last_out_result != HP1020_UDC_OUT_OK) return leave(p, HP1020_UDC_PUBLISH_ADAPTER_ERROR);
    *cookie_out = cookie;
    p->prefix = HP1020_UDC_PUBLISH_PREPARED;
    enum hp1020_udc_program_io_result io = p->cache.rx_before_device(p->cache.context, cookie, rx);
    if (io != HP1020_UDC_PROGRAM_IO_OK) {
        fail(p, cookie, HP1020_UDC_PUBLISH_RX_CACHE, UINT32_MAX, 0, rx.dma, rx.bytes, io);
        return leave(p, HP1020_UDC_PUBLISH_FAULT);
    }
    p->prefix |= HP1020_UDC_PUBLISH_RX_READY;
    const struct hp1020_udc_out_span descriptor = {p->out->descriptor.cpu, p->out->descriptor.dma, 16};
    io = p->cache.descriptor_before_device(p->cache.context, cookie, descriptor);
    if (io != HP1020_UDC_PROGRAM_IO_OK) {
        fail(p, cookie, HP1020_UDC_PUBLISH_DESCRIPTOR_CACHE, UINT32_MAX, 0,
            descriptor.dma, descriptor.bytes, io);
        return leave(p, HP1020_UDC_PUBLISH_FAULT);
    }
    p->prefix |= HP1020_UDC_PUBLISH_DESCRIPTOR_READY;
    if (!order(p, cookie, HP1020_UDC_PUBLISH_MEMORY_ORDERED))
        return leave(p, HP1020_UDC_PUBLISH_FAULT);
    const struct hp1020_udc_out_publish_facts facts = {1, 1, 1};
    struct hp1020_udc_out_submission submission;
    p->last_out_result = hp1020_udc_out_take_submission(p->out, cookie, facts, &submission);
    if (p->last_out_result != HP1020_UDC_OUT_OK) {
        fail(p, cookie, HP1020_UDC_PUBLISH_TAKE, UINT32_MAX, 0, 0, 0,
            HP1020_UDC_PROGRAM_IO_NOT_PERFORMED);
        return leave(p, HP1020_UDC_PUBLISH_FAULT);
    }
    p->prefix |= HP1020_UDC_PUBLISH_EXPOSED;
    /* Local proposal only. The supplied lease, immediate hooks and closed
     * callback window prohibit an intervening reset/SETUP/writer here. */
    if (!write32(p, cookie, OUT_DESPTR, submission.descriptor_dma, HP1020_UDC_PUBLISH_DESPTR_WRITTEN) ||
        !order(p, cookie, HP1020_UDC_PUBLISH_DESPTR_ORDERED))
        return leave(p, HP1020_UDC_PUBLISH_FAULT);
    if (p->saved_outctl == OUT_BULK_NAK) {
        if (!write32(p, cookie, OUT_CTL, OUT_BULK_CNAK, HP1020_UDC_PUBLISH_CNAK_WRITTEN) ||
            !order(p, cookie, HP1020_UDC_PUBLISH_CNAK_ORDERED))
            return leave(p, HP1020_UDC_PUBLISH_FAULT);
        uint32_t observed = 0;
        io = p->program->io.read32(p->program->io.context, OUT_CTL, &observed);
        if (io != HP1020_UDC_PROGRAM_IO_OK) {
            fail(p, cookie, HP1020_UDC_PUBLISH_READ, OUT_CTL, 0, 0, 0, io);
            return leave(p, HP1020_UDC_PUBLISH_FAULT);
        }
        if (observed != OUT_BULK) {
            fail(p, cookie, HP1020_UDC_PUBLISH_READBACK, OUT_CTL, observed, 0, 0, io);
            return leave(p, HP1020_UDC_PUBLISH_FAULT);
        }
        p->prefix |= HP1020_UDC_PUBLISH_NAK_CLEARED;
    }
    if (!write32(p, cookie, DEVCTL, p->saved_devctl | RDE, HP1020_UDC_PUBLISH_RDE_WRITTEN) ||
        !order(p, cookie, HP1020_UDC_PUBLISH_RDE_ORDERED))
        return leave(p, HP1020_UDC_PUBLISH_FAULT);
    return leave(p, HP1020_UDC_PUBLISH_OK);
}

enum hp1020_udc_publish_result hp1020_udc_publish_pending_cleanup(
    const struct hp1020_udc_publish *p, struct hp1020_udc_publish_failure *failure) {
    if (!valid(p) || !failure) return HP1020_UDC_PUBLISH_INVALID;
    if (p->busy || p->arming || p->servicing) return HP1020_UDC_PUBLISH_WAIT;
    if (!p->failed) return HP1020_UDC_PUBLISH_STALE;
    *failure = p->failure;
    return HP1020_UDC_PUBLISH_OK;
}
enum hp1020_udc_publish_result hp1020_udc_publish_ack_cleanup(
    struct hp1020_udc_publish *p, struct hp1020_tusb_cookie cookie, uint8_t clean) {
    if (!valid(p) || clean > 1) return HP1020_UDC_PUBLISH_INVALID;
    struct hp1020_tusb_adapter *a = adapter(p);
    if (p->busy || p->arming || p->servicing || p->program->busy || p->program->servicing ||
        p->program->ingress->busy || a->busy || p->out->busy) return HP1020_UDC_PUBLISH_WAIT;
    if (!p->failed || !cookie.id || cookie.endpoint != 1 || !same_cookie(cookie, p->failure.cookie))
        return HP1020_UDC_PUBLISH_STALE;
    if (!clean || p->out->phase != HP1020_UDC_OUT_FREE || !no_owners(a) ||
        !a->fenced || !a->printer->document->receive.stopped || a->opened || tud_mounted())
        return HP1020_UDC_PUBLISH_WAIT;
    if (a->exhausted) return HP1020_UDC_PUBLISH_ADAPTER_ERROR;
    p->failed = 0;
    /* Preserve diagnostics, descriptor bytes, program history and the receive
     * queue's fenced reservation. Only normal later recovery may reuse them. */
    return HP1020_UDC_PUBLISH_OK;
}
