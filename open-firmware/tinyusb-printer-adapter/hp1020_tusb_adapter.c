/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Generic TinyUSB/class/receive composition; controller operations are supplied. */
#include "hp1020_tusb_adapter.h"
#include "device/dcd.h"
#include <string.h>

enum { PENDING_NONE, PENDING_SETUP, PENDING_BUS_RESET, PENDING_OFFLOAD };
enum { OWNER_EP0_OUT, OWNER_EP0_IN, OWNER_BULK_OUT };
enum { REASON_ADMISSION = 1, REASON_TRANSFER, REASON_CONTRACT, REASON_LIMIT };

/* TinyUSB's class callbacks have no caller context and its device core has one
 * active rhport. The object and all borrowed storage are nevertheless owned by
 * the application. A second binding is deliberately unsupported. */
static struct hp1020_tusb_adapter *bound;

static uint16_t le16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static bool valid(const struct hp1020_tusb_adapter *s) {
    return s && s == bound && s->initialized && s->printer &&
        s->printer->initialized && s->printer->document;
}

static enum hp1020_tusb_result enter(struct hp1020_tusb_adapter *s) {
    if (!valid(s)) return HP1020_TUSB_INVALID;
    if (s->busy) return HP1020_TUSB_WAIT;
    s->busy = 1;
    return HP1020_TUSB_OK;
}

static enum hp1020_tusb_result leave(struct hp1020_tusb_adapter *s,
    enum hp1020_tusb_result r) {
    s->busy = 0;
    return r;
}

static bool same_cookie(struct hp1020_tusb_cookie a, struct hp1020_tusb_cookie b) {
    return a.id == b.id && a.epoch == b.epoch &&
        a.generation == b.generation && a.sequence == b.sequence &&
        a.endpoint == b.endpoint;
}

static struct hp1020_tusb_owner *owner_for(struct hp1020_tusb_adapter *s,
    uint8_t ep) {
    if (ep == 0) return &s->owners[OWNER_EP0_OUT];
    if (ep == 0x80) return &s->owners[OWNER_EP0_IN];
    if (ep == s->config.ep_out) return &s->owners[OWNER_BULK_OUT];
    return NULL;
}

static bool ep0_owned(const struct hp1020_tusb_adapter *s) {
    return s->owners[OWNER_EP0_OUT].state || s->owners[OWNER_EP0_IN].state;
}

static bool bulk_owned(const struct hp1020_tusb_adapter *s) {
    return s->owners[OWNER_BULK_OUT].state || s->prepared ||
        (s->delivering_live && s->delivering.cookie.endpoint == s->config.ep_out);
}

static void request_cancel(struct hp1020_tusb_adapter *s,
    struct hp1020_tusb_owner *p) {
    if (p->state != HP1020_TUSB_OWNER_DCD || p->cancel_requested) return;
    p->cancel_requested = 1;
    s->ops.request_cancel(s->ops.context, p->cookie);
}

static void cancel_ep0(struct hp1020_tusb_adapter *s) {
    request_cancel(s, &s->owners[OWNER_EP0_OUT]);
    request_cancel(s, &s->owners[OWNER_EP0_IN]);
}

static void terminal(struct hp1020_tusb_adapter *s) {
    s->exhausted = 1;
    s->fenced = 1;
    s->input_closed = 1;
    s->deferred = 0;
    s->binding_pending_epoch = 0;
    s->reset_transport_epoch = 0;
    s->pending_kind = PENDING_NONE;
    s->last_class_result = hp1020_usb_printer_fault(s->printer,
        s->printer->document->receive.generation, REASON_LIMIT);
    request_cancel(s, &s->owners[OWNER_BULK_OUT]);
    cancel_ep0(s);
}

static bool advance(struct hp1020_tusb_adapter *s, uint32_t *identity) {
    if (s->exhausted || *identity == UINT32_MAX) {
        terminal(s);
        return false;
    }
    ++*identity;
    return true;
}

static enum hp1020_tusb_result fence(struct hp1020_tusb_adapter *s,
    uint32_t generation, uint32_t reason) {
    if (generation != s->printer->document->receive.generation)
        return HP1020_TUSB_STALE;
    if (!reason) return HP1020_TUSB_OK;
    s->fenced = 1;
    s->input_closed = 1;
    s->deferred = 0;
    s->binding_pending_epoch = 0;
    s->reset_transport_epoch = 0;
    s->last_class_result = hp1020_usb_printer_fault(s->printer, generation, reason);
    if (!advance(s, &s->transport_epoch)) return HP1020_TUSB_LIMIT;
    request_cancel(s, &s->owners[OWNER_BULK_OUT]);
    return HP1020_TUSB_OK;
}

static void release_response(struct hp1020_tusb_adapter *s) {
    if (!s->response_owned || ep0_owned(s)) return;
    s->last_class_result = hp1020_usb_printer_ep0_quiesced(s->printer,
        s->response.request_id);
    if (s->last_class_result == HP1020_PRINTER_OK) {
        s->response_owned = 0;
    } else {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
    }
}

static bool take_reply(struct hp1020_tusb_adapter *s) {
    if (s->exhausted || s->pending_kind ||
        s->active_control_epoch != s->control_epoch || ep0_owned(s) || s->response_owned)
        return false;
    s->last_class_result = hp1020_usb_printer_take_response(s->printer, &s->response);
    if (s->last_class_result != HP1020_PRINTER_OK) return false;
    s->response_owned = 1;
    s->response_epoch = s->active_control_epoch;
    bool ok = false;
    const uint8_t previous = s->stack_active;
    s->stack_active = 1;
    if (s->response.kind == HP1020_PRINTER_DATA) {
        ok = tud_control_xfer(s->config.rhport, &s->class_request,
            (void *)s->response.data, s->response.length);
    } else if (s->response.kind == HP1020_PRINTER_ACK) {
        ok = tud_control_status(s->config.rhport, &s->class_request);
    }
    s->stack_active = previous;
    if (!ok) {
        (void)fence(s, s->printer->document->receive.generation, REASON_TRANSFER);
        cancel_ep0(s);
        release_response(s);
    }
    return ok;
}

static void driver_init(void) { }

static bool driver_deinit(void) {
    /* Deinitialization is not a shortcut around pending DCD ownership. The
     * surrounding application must settle every owner before tusb_deinit. */
    if (!valid(bound)) return true;
    if (ep0_owned(bound) || bulk_owned(bound) || bound->response_owned) return false;
    (void)fence(bound, bound->printer->document->receive.generation, REASON_ADMISSION);
    bound->opened = 0;
    return true;
}

static void driver_reset(uint8_t rhport) {
    struct hp1020_tusb_adapter *s = bound;
    if (!valid(s) || rhport != s->config.rhport) return;
    /* Admission already stopped the document; configuration_reset must not be
     * reached until old endpoint callbacks have used their original mapping. */
    if (bulk_owned(s) || ep0_owned(s)) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
    } else if (!s->fenced) {
        (void)fence(s, s->printer->document->receive.generation, REASON_ADMISSION);
    }
    s->opened = 0;
    s->configuration_value = 0;
    s->deferred = 0;
    s->binding_pending_epoch = 0;
    s->reset_transport_epoch = 0;
}

static bool endpoint_descriptor(const uint8_t *p, uint8_t address) {
    return p[0] == 7 && p[1] == TUSB_DESC_ENDPOINT && p[2] == address &&
        p[3] == TUSB_XFER_BULK && le16(p + 4) == 64 && p[6] == 0;
}

static uint16_t driver_open(uint8_t rhport, const tusb_desc_interface_t *itf,
    uint16_t maximum) {
    struct hp1020_tusb_adapter *s = bound;
    if (!valid(s) || rhport != s->config.rhport || !itf || maximum < 23 ||
        tud_speed_get() != TUSB_SPEED_FULL) return 0;
    const uint8_t *p = (const uint8_t *)itf;
    if (p[0] != 9 || p[1] != TUSB_DESC_INTERFACE ||
        p[2] != s->printer->config.interface_number || p[3] || p[4] != 2 ||
        p[5] != 7 || p[6] != 1 || p[7] != 2 ||
        !endpoint_descriptor(p + 9, s->config.ep_out) ||
        !endpoint_descriptor(p + 16, s->config.ep_in)) return 0;
    if (s->programming_dirty) return 0;
    if (bulk_owned(s) || s->opened) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return 0;
    }
    if (!usbd_edpt_open(rhport, (const tusb_desc_endpoint_t *)(p + 9)) ||
        !usbd_edpt_open(rhport, (const tusb_desc_endpoint_t *)(p + 16))) {
        s->programming_failure = (struct hp1020_tusb_programming_ticket){
            s->active_offload.sequence, s->active_control_epoch, s->transport_epoch};
        s->programming_dirty = 1;
        (void)fence(s, s->printer->document->receive.generation, REASON_TRANSFER);
        return 0;
    }
    s->opened = 1;
    s->active_transport_epoch = s->transport_epoch;
    /* This is a new endpoint binding, not a poll of mounted/fenced state.
     * Do not begin recovery inside open: the complete configuration still has
     * to succeed. A later fault clears this one-shot indication. */
    s->binding_pending_epoch = s->transport_epoch;
    return 23;
}

static enum hp1020_tusb_result begin_binding_recovery(struct hp1020_tusb_adapter *s) {
    const uint32_t epoch = s->binding_pending_epoch;
    if (!epoch) return HP1020_TUSB_OK;
    s->binding_pending_epoch = 0;
    if (s->exhausted) return HP1020_TUSB_LIMIT;
    if (epoch != s->transport_epoch || !s->opened || !tud_mounted() ||
        !s->fenced || !s->printer->document->receive.stopped || bulk_owned(s)) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_ERROR;
    }
    /* A newly opened configuration must also have had its ordinary status
     * packet accepted for submission. The pinned core can swallow an initial
     * standard-request submission failure. Never allocate a recovery identity
     * for that failed attempt or move its retained cookie past a restart. */
    const uint8_t ep_status = (le16(s->active_setup + 6) &&
        (s->active_setup[0] & 0x80)) ? 0 : 0x80;
    struct hp1020_tusb_owner *status = owner_for(s, ep_status);
    const bool configuration = !(s->active_setup[0] & 0x7f) &&
        s->active_setup[1] == TUSB_REQ_SET_CONFIGURATION;
    const bool reselection = s->active_offload.sequence &&
        s->active_offload.kind == HP1020_TUSB_OFFLOAD_INTERFACE &&
        s->active_setup[0] == 1 && s->active_setup[1] == TUSB_REQ_SET_INTERFACE;
    if ((!configuration && !reselection) ||
        status->state != HP1020_TUSB_OWNER_DCD || status->length ||
        !status->cookie.id || status->cookie.epoch != s->active_control_epoch ||
        status->cookie.epoch != s->control_epoch ||
        status->cookie.generation != s->printer->document->receive.generation ||
        !usbd_edpt_busy(s->config.rhport, ep_status) ||
        (s->active_offload.sequence && !status->auto_status)) {
        (void)fence(s, s->printer->document->receive.generation, REASON_TRANSFER);
        cancel_ep0(s);
        return s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_ERROR;
    }
    struct hp1020_printer_reset_ticket ticket;
    s->last_class_result = hp1020_usb_printer_begin_transport_recovery(s->printer, &ticket);
    if (s->last_class_result != HP1020_PRINTER_OK) {
        if (s->last_class_result == HP1020_PRINTER_LIMIT) {
            terminal(s);
            return HP1020_TUSB_LIMIT;
        }
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_ERROR;
    }
    s->reset_transport_epoch = epoch;
    s->deferred = 0; /* Internal recovery has no EP0 reply permission. */
    return HP1020_TUSB_OK;
}

static bool request_matches(const struct hp1020_tusb_adapter *s,
    const tusb_control_request_t *r) {
    return r->bmRequestType == s->active_setup[0] &&
        r->bRequest == s->active_setup[1] && r->wValue == le16(s->active_setup + 2) &&
        r->wIndex == le16(s->active_setup + 4) && r->wLength == le16(s->active_setup + 6);
}

static bool driver_control(uint8_t rhport, uint8_t stage,
    const tusb_control_request_t *request) {
    struct hp1020_tusb_adapter *s = bound;
    if (!valid(s) || rhport != s->config.rhport || !request || !s->stack_active ||
        request->bmRequestType_bit.type != TUSB_REQ_TYPE_CLASS) return false;
    if (s->active_control_epoch != s->control_epoch || !request_matches(s, request)) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return false;
    }
    if (stage == CONTROL_STAGE_SETUP) {
        s->class_request = *request;
        s->last_class_result = hp1020_usb_printer_setup(s->printer,
            s->active_setup, 8, &s->active_status, &s->class_request_id);
        if (s->last_class_result != HP1020_PRINTER_OK) {
            if (s->last_class_result == HP1020_PRINTER_LIMIT) terminal(s);
            return false;
        }
        if (s->printer->reset_active && s->printer->reset_request_id &&
            s->printer->reset_request_id == s->class_request_id) {
            s->reset_transport_epoch = s->transport_epoch;
            s->deferred = 1;
            s->deferred_epoch = s->active_control_epoch;
            return true;
        }
        const bool ok = take_reply(s);
        /* If a broken DCD accepted a cookie but then rejected submission, it
         * still owns the pointer. Hold this request until explicit settlement
         * instead of inviting the core to stall over the retained transfer. */
        return ok || ep0_owned(s);
    }
    if (stage == CONTROL_STAGE_DATA) return true;
    if (stage == CONTROL_STAGE_ACK) {
        if (!s->response_owned || s->response_epoch != s->active_control_epoch) {
            (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
            return false;
        }
        release_response(s);
        return !s->response_owned;
    }
    return false;
}

static bool driver_xfer(uint8_t rhport, uint8_t endpoint, xfer_result_t result,
    uint32_t length) {
    struct hp1020_tusb_adapter *s = bound;
    if (!valid(s) || rhport != s->config.rhport) return false;
    if (!s->delivering_live || s->delivered || endpoint != s->config.ep_out ||
        s->delivering.cookie.endpoint != endpoint || s->delivering.actual != length ||
        s->delivering.result != (uint8_t)result) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return false;
    }
    s->delivered = 1;
    const struct hp1020_tusb_cookie cookie = s->delivering.cookie;
    /* A real cancelled completion passes through TinyUSB to clear its BUSY
     * state. It must not invent another fault and erase fresh reset promises. */
    if (s->delivering.expected_cancel || s->fenced ||
        cookie.generation != s->printer->document->receive.generation ||
        cookie.epoch != s->active_transport_epoch ||
        s->printer->document->receive.stopped) return true;
    if (result != XFER_RESULT_SUCCESS) {
        (void)fence(s, cookie.generation, REASON_TRANSFER);
        return true;
    }
    const struct hp1020_rx_ticket ticket = {cookie.generation, cookie.sequence};
    /* Deliberately normalized transport completion, never fabricated stock
     * descriptor bits. */
    s->last_receive_result = hp1020_usb_receive_complete_data(
        &s->printer->document->receive, ticket, length);
    if (s->last_receive_result != HP1020_RX_OK)
        (void)fence(s, cookie.generation, REASON_CONTRACT);
    return true;
}

static const usbd_class_driver_t class_driver = {
    .name = "HP1020-printer-adapter", .init = driver_init, .deinit = driver_deinit,
    .reset = driver_reset, .open = driver_open, .control_xfer_cb = driver_control,
    .xfer_cb = driver_xfer
};

const usbd_class_driver_t *hp1020_tusb_adapter_driver(void) { return &class_driver; }

enum hp1020_tusb_result hp1020_tusb_adapter_init(struct hp1020_tusb_adapter *s,
    struct hp1020_usb_printer *printer, const struct hp1020_tusb_config *config,
    const struct hp1020_tusb_ops *ops) {
    if (!s || bound || tud_inited() || !printer || !printer->initialized ||
        !printer->document || !config || !ops || !ops->request_cancel ||
        config->rhport || !config->ep_out || (config->ep_out & 0xf0) ||
        (config->ep_in & 0xf0) != 0x80 || !(config->ep_in & 15) ||
        config->ep_out >= CFG_TUD_ENDPPOINT_MAX ||
        (config->ep_in & 15) >= CFG_TUD_ENDPPOINT_MAX ||
        config->out_capacity < 64 || config->out_capacity > HP1020_RX_CAPACITY ||
        (config->out_capacity % 64) || printer->config.alternate_setting ||
        CFG_TUD_ENDPOINT0_SIZE != 64 || CFG_TUD_ENDPOINT0_BUFSIZE != 64)
        return HP1020_TUSB_INVALID;
    memset(s, 0, sizeof(*s));
    s->printer = printer;
    s->config = *config;
    s->ops = *ops;
    s->transport_epoch = 1;
    s->active_transport_epoch = 1;
    s->initialized = 1;
    s->fenced = 1;
    s->input_closed = 1;
    bound = s;
    hp1020_usb_receive_stop(&printer->document->receive);
    return HP1020_TUSB_OK;
}

bool hp1020_tusb_adapter_route(uint8_t rhport, const tusb_control_request_t *r,
    uint8_t *interface_number) {
    const struct hp1020_tusb_adapter *s = bound;
    if (!valid(s) || rhport != s->config.rhport || !r || !interface_number)
        return false;
    const uint8_t itf = s->printer->config.interface_number;
    const bool id = r->bmRequestType == 0xa1 && r->bRequest == 0 && (r->wIndex >> 8) == itf;
    const bool legacy = r->bmRequestType == 0x23 && r->bRequest == 2 && r->wIndex == itf;
    if (!id && !legacy) return false;
    *interface_number = itf;
    return true; /* Unchanged fields reach the class; claimed rejection is final. */
}

static bool valid_soft_reset(const struct hp1020_tusb_adapter *s, const uint8_t *raw) {
    return (raw[0] == 0x21 || raw[0] == 0x23) && raw[1] == 2 &&
        le16(raw + 2) == 0 && le16(raw + 4) == s->printer->config.interface_number &&
        le16(raw + 6) == 0;
}

static bool changes_endpoints(const struct hp1020_tusb_adapter *s, const uint8_t *raw) {
    /* Match what this pinned core actually dispatches, including ignored
     * direction/high value bytes, so malformed fields cannot bypass admission. */
    const uint8_t recipient_and_type = raw[0] & 0x7f;
    if (recipient_and_type == 0 && raw[1] == TUSB_REQ_SET_CONFIGURATION)
        return raw[2] != 0 || s->configuration_value != 0;
    if (recipient_and_type == 1 && raw[1] == TUSB_REQ_SET_INTERFACE &&
        raw[4] == s->printer->config.interface_number) return true;
    if (recipient_and_type == 2 &&
        (raw[1] == TUSB_REQ_SET_FEATURE || raw[1] == TUSB_REQ_CLEAR_FEATURE) &&
        le16(raw + 2) == TUSB_REQ_FEATURE_EDPT_HALT &&
        /* The pinned core ignores address-reserved bits 6:4. Admission must
         * cover those aliases before it stalls/clears the same endpoint. */
        ((raw[4] & 0x8f) == s->config.ep_out ||
         (raw[4] & 0x8f) == s->config.ep_in)) return true;
    return false;
}

static enum hp1020_tusb_result admit_control(struct hp1020_tusb_adapter *s,
    const uint8_t raw[8], const struct hp1020_printer_status *status,
    const struct hp1020_tusb_offload *offload) {
    if (s->exhausted) return HP1020_TUSB_LIMIT;
    if (s->pending_kind == PENDING_BUS_RESET) return HP1020_TUSB_WAIT;
    if (!advance(s, &s->control_epoch)) return HP1020_TUSB_LIMIT;
    const bool destructive = changes_endpoints(s, raw);
    const bool reset = valid_soft_reset(s, raw);
    s->deferred = 0; /* Also applies to standard requests not routed to the class. */
    if (destructive || reset) {
        const enum hp1020_tusb_result r = fence(s,
            s->printer->document->receive.generation, REASON_ADMISSION);
        if (r) return r;
    }
    memcpy(s->pending_setup, raw, 8);
    s->pending_status = status ? *status : (struct hp1020_printer_status){0, 0};
    s->pending_offload = offload ? *offload : (struct hp1020_tusb_offload){0};
    s->pending_kind = offload ? PENDING_OFFLOAD : PENDING_SETUP;
    s->pending_destructive = (uint8_t)destructive;
    cancel_ep0(s);
    return HP1020_TUSB_OK;
}

enum hp1020_tusb_result hp1020_tusb_adapter_setup(struct hp1020_tusb_adapter *s,
    const uint8_t *raw, uint32_t length, const struct hp1020_printer_status *status) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (!raw || length != 8) return leave(s, HP1020_TUSB_INVALID);
    return leave(s, admit_control(s, raw, status, NULL));
}

enum hp1020_tusb_result hp1020_tusb_adapter_offload(struct hp1020_tusb_adapter *s,
    const struct hp1020_tusb_offload *o) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (!o || !o->sequence || o->sequence == UINT32_MAX ||
        s->printer->config.interface_number || o->interface_number || o->alternate ||
        o->configuration > 1 ||
        (o->kind != HP1020_TUSB_OFFLOAD_CONFIGURATION &&
         o->kind != HP1020_TUSB_OFFLOAD_INTERFACE))
        return leave(s, HP1020_TUSB_INVALID);
    if (o->kind == HP1020_TUSB_OFFLOAD_INTERFACE &&
        (o->configuration != 1 || s->configuration_value != 1 ||
         !s->opened || !tud_mounted())) return leave(s, HP1020_TUSB_INVALID);
    if (s->programming_dirty) return leave(s, HP1020_TUSB_WAIT);
    /* Canonical fields for TinyUSB only: these bytes are never published as
     * an original SETUP capture or sent to a controller. Provenance is separate. */
    uint8_t canonical[8] = {0};
    if (o->kind == HP1020_TUSB_OFFLOAD_CONFIGURATION) {
        canonical[1] = TUSB_REQ_SET_CONFIGURATION;
        canonical[2] = o->configuration;
    } else {
        canonical[0] = TUSB_REQ_RCPT_INTERFACE;
        canonical[1] = TUSB_REQ_SET_INTERFACE;
    }
    return leave(s, admit_control(s, canonical, NULL, o));
}

enum hp1020_tusb_result hp1020_tusb_adapter_bus_reset(struct hp1020_tusb_adapter *s,
    tusb_speed_t speed) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (speed != TUSB_SPEED_FULL) return leave(s, HP1020_TUSB_INVALID);
    if (s->exhausted) return leave(s, HP1020_TUSB_LIMIT);
    if (!advance(s, &s->control_epoch)) return leave(s, HP1020_TUSB_LIMIT);
    r = fence(s, s->printer->document->receive.generation, REASON_ADMISSION);
    if (r) return leave(s, r);
    s->pending_kind = PENDING_BUS_RESET;
    s->pending_speed = (uint8_t)speed;
    s->pending_destructive = 1;
    cancel_ep0(s);
    return leave(s, HP1020_TUSB_OK);
}

static enum hp1020_tusb_result bind_submission(
    struct hp1020_tusb_adapter *s, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, struct hp1020_tusb_cookie *cookie, bool auto_status) {
    if (!valid(s) || !cookie || !s->busy || !s->stack_active)
        return HP1020_TUSB_INVALID;
    if (s->exhausted) return HP1020_TUSB_LIMIT;
    if (auto_status) {
        if (!s->active_offload.sequence || endpoint != 0x80 || buffer || length ||
            s->programming_dirty ||
            s->offload_transport_epoch != s->transport_epoch ||
            !usbd_edpt_busy(s->config.rhport, endpoint))
            return HP1020_TUSB_INVALID;
    } else if ((endpoint == 0 || endpoint == 0x80) && s->active_offload.sequence) {
        return HP1020_TUSB_INVALID;
    }
    struct hp1020_tusb_owner *p = owner_for(s, endpoint);
    if (!p || p->state || (length && !buffer)) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return HP1020_TUSB_INVALID;
    }
    struct hp1020_tusb_cookie next = {0};
    next.endpoint = endpoint;
    if (endpoint == s->config.ep_out) {
        if (!s->prepared || buffer != s->prepared_buffer ||
            length != s->config.out_capacity || s->fenced ||
            s->printer->document->receive.stopped) {
            (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
            return HP1020_TUSB_INVALID;
        }
        next.epoch = s->active_transport_epoch;
        next.generation = s->prepared_ticket.generation;
        next.sequence = s->prepared_ticket.sequence;
    } else {
        if (length > 64 || !s->active_control_epoch ||
            s->active_control_epoch != s->control_epoch || s->pending_kind) {
            (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
            return HP1020_TUSB_INVALID;
        }
        next.epoch = s->active_control_epoch;
        next.generation = s->printer->document->receive.generation;
    }
    if (!advance(s, &s->last_submission_id)) return HP1020_TUSB_LIMIT;
    next.id = s->last_submission_id;
    memset(p, 0, sizeof(*p));
    p->cookie = next;
    p->buffer = buffer;
    p->length = length;
    p->state = HP1020_TUSB_OWNER_DCD;
    p->auto_status = (uint8_t)auto_status;
    if (endpoint != s->config.ep_out)
        p->core_busy_at_bind = (uint8_t)usbd_edpt_busy(s->config.rhport, endpoint);
    *cookie = next;
    return HP1020_TUSB_OK;
}

enum hp1020_tusb_result hp1020_tusb_adapter_bind_submission(
    struct hp1020_tusb_adapter *s, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, struct hp1020_tusb_cookie *cookie) {
    return bind_submission(s, endpoint, buffer, length, cookie, false);
}

enum hp1020_tusb_result hp1020_tusb_adapter_bind_auto_status(
    struct hp1020_tusb_adapter *s, uint8_t endpoint, uint8_t *buffer,
    uint16_t length, struct hp1020_tusb_cookie *cookie) {
    return bind_submission(s, endpoint, buffer, length, cookie, true);
}

enum hp1020_tusb_result hp1020_tusb_adapter_take_auto_status(
    struct hp1020_tusb_adapter *s, struct hp1020_tusb_cookie cookie,
    uint32_t original_sequence, struct hp1020_tusb_auto_status_grant *grant) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (!grant || !original_sequence) return leave(s, HP1020_TUSB_INVALID);
    struct hp1020_tusb_owner *p = owner_for(s, cookie.endpoint);
    if (!p || p->state != HP1020_TUSB_OWNER_DCD || !p->auto_status ||
        !same_cookie(p->cookie, cookie) || !cookie.id || p->auto_granted ||
        !s->active_offload.sequence || s->active_offload.sequence != original_sequence ||
        cookie.epoch != s->control_epoch || cookie.epoch != s->active_control_epoch ||
        s->pending_kind || p->cancel_requested || p->packet_fault ||
        s->offload_transport_epoch != s->transport_epoch || s->programming_dirty)
        return leave(s, HP1020_TUSB_STALE);
    if (s->exhausted) return leave(s, HP1020_TUSB_LIMIT);
    if (cookie.endpoint != 0x80 || p->buffer || p->length ||
        !usbd_edpt_busy(s->config.rhport, 0x80) || usbd_edpt_stalled(s->config.rhport, 0x80))
        return leave(s, HP1020_TUSB_ERROR);
    /* CSR programming includes the affected endpoints' default/toggle/halt
     * state. A retained core halt contradicts that promise. A new bulk owner
     * may legitimately be armed after recovery, so BUSY alone is not a fault. */
    if (s->active_offload.configuration == 1 &&
        (usbd_edpt_stalled(s->config.rhport, s->config.ep_out) ||
         usbd_edpt_stalled(s->config.rhport, s->config.ep_in)))
        return leave(s, HP1020_TUSB_WAIT);
    /* A recovered document can have a newer generation while this original
     * control owner is held. Do not retag its cookie or equate the two domains. */
    const struct hp1020_tusb_auto_status_grant next = {p->cookie, s->active_offload};
    p->auto_granted = 1;
    *grant = next;
    return leave(s, HP1020_TUSB_OK);
}

enum hp1020_tusb_result hp1020_tusb_adapter_pending_programming_cleanup(
    const struct hp1020_tusb_adapter *s, struct hp1020_tusb_programming_ticket *ticket) {
    if (!valid(s) || !ticket) return HP1020_TUSB_INVALID;
    if (s->busy) return HP1020_TUSB_WAIT;
    if (!s->programming_dirty) return HP1020_TUSB_STALE;
    *ticket = s->programming_failure;
    return HP1020_TUSB_OK;
}

enum hp1020_tusb_result hp1020_tusb_adapter_ack_programming_cleanup(
    struct hp1020_tusb_adapter *s, struct hp1020_tusb_programming_ticket ticket,
    uint8_t controller_programming_clean) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (controller_programming_clean > 1) return leave(s, HP1020_TUSB_INVALID);
    if (!s->programming_dirty || !ticket.control_epoch ||
        ticket.sequence != s->programming_failure.sequence ||
        ticket.control_epoch != s->programming_failure.control_epoch ||
        ticket.transport_epoch != s->programming_failure.transport_epoch)
        return leave(s, HP1020_TUSB_STALE);
    if (!controller_programming_clean || ep0_owned(s) || bulk_owned(s) ||
        s->delivering_live || s->response_owned)
        return leave(s, HP1020_TUSB_WAIT);
    if (s->exhausted) return leave(s, HP1020_TUSB_LIMIT);
    if (!s->fenced || !s->printer->document->receive.stopped || s->opened || tud_mounted())
        return leave(s, HP1020_TUSB_ERROR);
    s->programming_dirty = 0;
    return leave(s, HP1020_TUSB_OK);
}

static enum hp1020_tusb_result complete_locked(struct hp1020_tusb_adapter *s,
    struct hp1020_tusb_cookie cookie, xfer_result_t result, uint32_t length) {
    struct hp1020_tusb_owner *p = owner_for(s, cookie.endpoint);
    if (!p || p->state != HP1020_TUSB_OWNER_DCD || !cookie.id ||
        !same_cookie(p->cookie, cookie)) return HP1020_TUSB_STALE;
    if ((unsigned)result >= (unsigned)XFER_RESULT_INVALID || length > p->length ||
        (p->auto_status && (result != XFER_RESULT_ABORTED || length))) {
        /* A prohibited late success for a superseded auto-status owner cannot
         * poison a newer request that still has the same receive generation. */
        if (!p->auto_status || cookie.epoch == s->control_epoch)
            (void)fence(s, cookie.generation, REASON_CONTRACT);
        request_cancel(s, p);
        return HP1020_TUSB_INVALID; /* Retain ownership, including on overrun. */
    }
    p->actual = length;
    p->result = (uint8_t)result;
    p->expected_cancel = (uint8_t)(p->cancel_requested && result == XFER_RESULT_ABORTED);
    p->state = HP1020_TUSB_OWNER_PENDING;
    if (result != XFER_RESULT_SUCCESS && !p->expected_cancel && !p->packet_fault) {
        /* Stop consumption at event admission, before a caller can pump READY
         * data. A failure from a superseded EP0 request cannot fault new work. */
        if (cookie.endpoint == s->config.ep_out || cookie.epoch == s->control_epoch)
            (void)fence(s, cookie.generation, REASON_TRANSFER);
    }
    return HP1020_TUSB_OK;
}

enum hp1020_tusb_result hp1020_tusb_adapter_complete(struct hp1020_tusb_adapter *s,
    struct hp1020_tusb_cookie cookie, xfer_result_t result, uint32_t length) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    return leave(s, complete_locked(s, cookie, result, length));
}

enum hp1020_tusb_result hp1020_tusb_adapter_cancelled(struct hp1020_tusb_adapter *s,
    struct hp1020_tusb_cookie cookie) {
    return hp1020_tusb_adapter_complete(s, cookie, XFER_RESULT_ABORTED, 0);
}

enum hp1020_tusb_result hp1020_tusb_adapter_packet_fault(struct hp1020_tusb_adapter *s,
    struct hp1020_tusb_cookie cookie, uint32_t reason) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    struct hp1020_tusb_owner *p = owner_for(s, cookie.endpoint);
    if (!p || p->state != HP1020_TUSB_OWNER_DCD || !cookie.id ||
        !same_cookie(p->cookie, cookie)) return leave(s, HP1020_TUSB_STALE);
    if (cookie.generation != s->printer->document->receive.generation)
        return leave(s, HP1020_TUSB_STALE);
    if (cookie.endpoint == s->config.ep_out) {
        if (!cookie.epoch || cookie.epoch != s->active_transport_epoch)
            return leave(s, HP1020_TUSB_STALE);
    } else if (!cookie.epoch || cookie.epoch != s->control_epoch ||
        cookie.epoch != s->active_control_epoch || s->pending_kind) {
        return leave(s, HP1020_TUSB_STALE);
    }
    if (!reason) return leave(s, HP1020_TUSB_OK);
    if (s->exhausted) return leave(s, HP1020_TUSB_LIMIT);
    if (p->packet_fault) return leave(s, HP1020_TUSB_OK);
    /* A fault is not settlement. Latch once before requesting cancellation;
     * duplicate observations cannot erase later promises or exhaust identities.
     * EP0 uses its control identity, never the bulk transport-epoch API. */
    p->packet_fault = 1;
    r = fence(s, cookie.generation, reason);
    request_cancel(s, p);
    return leave(s, r);
}

enum hp1020_tusb_result hp1020_tusb_adapter_fault(struct hp1020_tusb_adapter *s,
    uint32_t epoch, uint32_t generation, uint32_t reason) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (epoch != s->active_transport_epoch || !epoch)
        return leave(s, HP1020_TUSB_STALE);
    return leave(s, fence(s, generation, reason));
}

static bool drain_stack(struct hp1020_tusb_adapter *s) {
    const uint8_t previous = s->stack_active;
    s->stack_active = 1;
    unsigned rounds = 0;
    while (tud_task_event_ready() && rounds++ < 32) tud_task_ext(0, false);
    s->stack_active = previous;
    if (tud_task_event_ready()) {
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return false;
    }
    return true;
}

static bool deliver(struct hp1020_tusb_adapter *s, struct hp1020_tusb_owner *p) {
    if (p->state != HP1020_TUSB_OWNER_PENDING) return true;
    s->delivering = *p;
    s->delivering_live = 1;
    s->delivered = 0;
    memset(p, 0, sizeof(*p));
    const bool bulk = s->delivering.cookie.endpoint == s->config.ep_out;
    const uint32_t submission_generation = s->printer->document->receive.generation;
    /* A genuinely settled packet may still arrive as SUCCESS after its fault.
     * Retire that ownership, but never acknowledge or advance a faulted EP0
     * request. A fresh SETUP resets the core's control state after retirement.
     * Bulk settlement still dispatches to clear BUSY; the document is fenced. */
    if (!s->delivering.auto_status && (bulk || (!s->delivering.packet_fault && !s->exhausted &&
        s->delivering.cookie.epoch == s->control_epoch &&
        s->delivering.cookie.epoch == s->active_control_epoch))) {
        /* The side ledger is retained until TinyUSB invokes the real class
         * callback, which receives only endpoint/result/count upstream. */
        dcd_event_xfer_complete(s->config.rhport, s->delivering.cookie.endpoint,
            s->delivering.actual, s->delivering.result, false);
        if (!drain_stack(s) || (bulk && !s->delivered)) {
            (void)fence(s, s->delivering.cookie.generation, REASON_CONTRACT);
            s->delivering_live = 0;
            return false;
        }
        if (!bulk && s->delivering.result == XFER_RESULT_SUCCESS &&
            le16(s->active_setup + 6) != 0 &&
            s->delivering.cookie.endpoint == (s->active_setup[0] & 0x80)) {
            /* Every successful current DATA packet in this profile must be
             * followed by another DATA or the opposite STATUS packet. TinyUSB
             * can swallow failure to submit that next packet. An absent owner,
             * or a bound owner whose submission cleared BUSY on failure, is a
             * submission fault, not a completed response. No event is invented. */
            struct hp1020_tusb_owner *next = s->owners[OWNER_EP0_IN].state ?
                &s->owners[OWNER_EP0_IN] : &s->owners[OWNER_EP0_OUT];
            if (!next->state || !usbd_edpt_busy(s->config.rhport, next->cookie.endpoint)) {
                s->delivering_live = 0;
                /* A successful old-generation DATA packet can continue after
                 * document recovery. Failure belongs to the NEW submission,
                 * unlike an actual failed completion of that old packet. */
                (void)fence(s, next->state ? next->cookie.generation : submission_generation,
                    REASON_TRANSFER);
                cancel_ep0(s);
                release_response(s);
                return false;
            }
        }
    }
    const bool failed = s->delivering.result != XFER_RESULT_SUCCESS;
    s->delivering_live = 0;
    if (!bulk && (failed || s->delivering.packet_fault)) release_response(s);
    return true;
}

/* Detect a rejected initial EP0 submission even when a standard request
 * handler swallowed its false return. BUSY was set before bind_submission and
 * is cleared by this pinned core on rejection. A stalled newly bound packet
 * likewise cannot remain a healthy owner. Neither a stall nor this observation
 * settles the DCD's pointer; request cancellation and preserve its cookie.
 * Direct-DCD SET_ADDRESS status has no core BUSY transition and is excluded. */
static enum hp1020_tusb_result check_initial_ep0_submission(struct hp1020_tusb_adapter *s) {
    for (unsigned i = OWNER_EP0_OUT; i <= OWNER_EP0_IN; ++i) {
        struct hp1020_tusb_owner *p = &s->owners[i];
        if (p->state != HP1020_TUSB_OWNER_DCD || !p->core_busy_at_bind ||
            p->cancel_requested) continue;
        if (!usbd_edpt_busy(s->config.rhport, p->cookie.endpoint) ||
            usbd_edpt_stalled(s->config.rhport, p->cookie.endpoint)) {
            (void)fence(s, p->cookie.generation, REASON_TRANSFER);
            cancel_ep0(s);
            return s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_ERROR;
        }
    }
    return HP1020_TUSB_OK;
}

enum hp1020_tusb_result hp1020_tusb_adapter_service(struct hp1020_tusb_adapter *s) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (!tud_inited()) return leave(s, HP1020_TUSB_INVALID);
    if (!drain_stack(s)) return leave(s, HP1020_TUSB_ERROR);
    for (unsigned i = 0; i < 3; ++i)
        if (!deliver(s, &s->owners[i])) return leave(s, HP1020_TUSB_ERROR);
    if (s->exhausted) {
        if (!ep0_owned(s)) release_response(s);
        return leave(s, HP1020_TUSB_LIMIT);
    }
    if (!s->pending_kind) return leave(s, HP1020_TUSB_OK);
    if (ep0_owned(s) || (s->pending_destructive && bulk_owned(s)))
        return leave(s, HP1020_TUSB_WAIT);
    release_response(s);
    if (s->response_owned) return leave(s, HP1020_TUSB_ERROR);
    const uint8_t kind = s->pending_kind;
    s->pending_kind = PENDING_NONE;
    s->pending_destructive = 0;
    s->active_control_epoch = s->control_epoch;
    if (kind == PENDING_SETUP || kind == PENDING_OFFLOAD) {
        memcpy(s->active_setup, s->pending_setup, 8);
        s->active_status = s->pending_status;
        s->active_offload = s->pending_offload;
        s->offload_transport_epoch = s->active_offload.sequence ? s->transport_epoch : 0;
        /* This printer profile has no control OUT data requests. In particular,
         * malformed OUT GET_STATUS/GET_CONFIGURATION would make the pinned
         * core retain a stack-local reply pointer as a later receive target.
         * Reject before dispatch, after old EP0 ownership is settled. A fresh
         * SETUP still supersedes old reply permission and preserves any fence. */
        if (!(s->active_setup[0] & 0x80) && le16(s->active_setup + 6)) {
            usbd_edpt_stall(s->config.rhport, 0);
            usbd_edpt_stall(s->config.rhport, 0x80);
            return leave(s, HP1020_TUSB_OK);
        }
        dcd_event_setup_received(s->config.rhport, s->active_setup, false);
    } else {
        memset(s->active_setup, 0, 8);
        memset(&s->active_offload, 0, sizeof(s->active_offload));
        s->offload_transport_epoch = 0;
        dcd_event_bus_reset(s->config.rhport, (tusb_speed_t)s->pending_speed, false);
    }
    if (!drain_stack(s)) return leave(s, HP1020_TUSB_ERROR);
    if ((kind == PENDING_SETUP || kind == PENDING_OFFLOAD) &&
        (s->active_setup[0] & 0x7f) == 0 &&
        s->active_setup[1] == TUSB_REQ_SET_CONFIGURATION)
        s->configuration_value = tud_mounted() ? s->active_setup[2] : 0;
    r = check_initial_ep0_submission(s);
    if (r != HP1020_TUSB_OK) return leave(s, r);
    if (kind == PENDING_OFFLOAD) {
        const struct hp1020_tusb_owner *p = &s->owners[OWNER_EP0_IN];
        if (p->state != HP1020_TUSB_OWNER_DCD || !p->auto_status ||
            p->buffer || p->length || p->cancel_requested || p->packet_fault ||
            p->cookie.epoch != s->control_epoch ||
            p->cookie.generation != s->printer->document->receive.generation ||
            !usbd_edpt_busy(s->config.rhport, 0x80) ||
            s->offload_transport_epoch != s->transport_epoch) {
            (void)fence(s, s->printer->document->receive.generation, REASON_TRANSFER);
            cancel_ep0(s);
            return leave(s, s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_ERROR);
        }
        if (s->active_offload.kind == HP1020_TUSB_OFFLOAD_INTERFACE) {
            /* TinyUSB's same-alt fallback never invokes driver_open. This
             * successful typed reselection establishes one transport binding,
             * after admission settled the old owners. Recovery still needs
             * all three external promises and creates no host class request. */
            s->active_transport_epoch = s->transport_epoch;
            s->binding_pending_epoch = s->transport_epoch;
        }
    }
    /* driver_open marks every successful nonzero configuration selection;
     * typed SI marks one reselection. Repeated zero configuration,
     * a superseded destructive SETUP and ordinary service polls create none.
     * TinyUSB still owns its normal SET_CONFIGURATION status transfer; internal
     * recovery creates no SETUP, response or extra packet. */
    r = begin_binding_recovery(s);
    return leave(s, s->exhausted ? HP1020_TUSB_LIMIT : r);
}

enum hp1020_tusb_result hp1020_tusb_adapter_arm_out(struct hp1020_tusb_adapter *s) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    if (s->exhausted) return leave(s, HP1020_TUSB_LIMIT);
    if (!tud_inited() || !tud_ready() || !s->opened || s->fenced || s->input_closed ||
        s->printer->document->receive.stopped || s->printer->reset_active ||
        (s->pending_kind && s->pending_destructive) || bulk_owned(s) ||
        usbd_edpt_busy(s->config.rhport, s->config.ep_out) ||
        usbd_edpt_stalled(s->config.rhport, s->config.ep_out))
        return leave(s, HP1020_TUSB_WAIT);
    if (!usbd_edpt_claim(s->config.rhport, s->config.ep_out))
        return leave(s, HP1020_TUSB_WAIT);
    s->last_receive_result = hp1020_usb_receive_reserve(&s->printer->document->receive,
        s->config.out_capacity, &s->prepared_ticket, &s->prepared_buffer);
    if (s->last_receive_result != HP1020_RX_OK) {
        (void)usbd_edpt_release(s->config.rhport, s->config.ep_out);
        if (s->last_receive_result == HP1020_RX_WAIT) return leave(s, HP1020_TUSB_WAIT);
        (void)fence(s, s->printer->document->receive.generation, REASON_CONTRACT);
        return leave(s, HP1020_TUSB_ERROR);
    }
    s->prepared = 1;
    s->stack_active = 1;
    const bool submitted = usbd_edpt_xfer(s->config.rhport, s->config.ep_out,
        s->prepared_buffer, s->config.out_capacity, false);
    s->stack_active = 0;
    s->prepared = 0;
    if (!submitted || s->owners[OWNER_BULK_OUT].state != HP1020_TUSB_OWNER_DCD ||
        s->owners[OWNER_BULK_OUT].cookie.sequence != s->prepared_ticket.sequence) {
        /* Reservation cannot be rolled back or skipped. Keep its bytes until
         * all three reset promises allow a new document generation. */
        (void)fence(s, s->prepared_ticket.generation, REASON_TRANSFER);
        return leave(s, s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_ERROR);
    }
    return leave(s, HP1020_TUSB_OK);
}

enum hp1020_rx_result hp1020_tusb_adapter_pump(struct hp1020_tusb_adapter *s) {
    const enum hp1020_tusb_result r = enter(s);
    if (r) return r == HP1020_TUSB_WAIT ? HP1020_RX_WAIT : HP1020_RX_ORDER;
    s->last_receive_result = hp1020_usb_document_pump(s->printer->document);
    if (s->last_receive_result != HP1020_RX_OK && s->last_receive_result != HP1020_RX_WAIT &&
        s->last_receive_result != HP1020_RX_STOPPED)
        (void)fence(s, s->printer->document->receive.generation, REASON_TRANSFER);
    s->busy = 0;
    return s->last_receive_result;
}

enum hp1020_tusb_result hp1020_tusb_adapter_close_input(struct hp1020_tusb_adapter *s) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r;
    s->input_closed = 1;
    return leave(s, s->exhausted ? HP1020_TUSB_LIMIT : HP1020_TUSB_OK);
}

enum hp1020_rx_result hp1020_tusb_adapter_finish(struct hp1020_tusb_adapter *s) {
    const enum hp1020_tusb_result r = enter(s);
    if (r) return r == HP1020_TUSB_WAIT ? HP1020_RX_WAIT : HP1020_RX_ORDER;
    if (!s->input_closed || bulk_owned(s)) {
        s->busy = 0;
        return HP1020_RX_WAIT;
    }
    s->last_receive_result = hp1020_usb_document_finish(s->printer->document);
    if (s->last_receive_result == HP1020_RX_OK) s->fenced = 1;
    else if (s->last_receive_result != HP1020_RX_WAIT && s->last_receive_result != HP1020_RX_STOPPED)
        (void)fence(s, s->printer->document->receive.generation, REASON_TRANSFER);
    s->busy = 0;
    return s->last_receive_result;
}

enum hp1020_printer_result hp1020_tusb_adapter_pending_reset(
    const struct hp1020_tusb_adapter *s, struct hp1020_printer_reset_ticket *ticket) {
    if (!valid(s)) return HP1020_PRINTER_INVALID;
    if (s->exhausted) return HP1020_PRINTER_LIMIT;
    return hp1020_usb_printer_pending_reset(s->printer, ticket);
}

static bool same_reset(const struct hp1020_tusb_adapter *s,
    struct hp1020_printer_reset_ticket ticket) {
    return s->printer->reset_active && ticket.recovery_id &&
        ticket.recovery_id == s->printer->reset.recovery_id &&
        ticket.generation == s->printer->reset.generation &&
        s->reset_transport_epoch && s->reset_transport_epoch == s->transport_epoch;
}

static bool transport_ready(const struct hp1020_tusb_adapter *s) {
    return !s->programming_dirty && s->opened && tud_mounted() &&
        !usbd_edpt_busy(s->config.rhport, s->config.ep_out) &&
        !usbd_edpt_busy(s->config.rhport, s->config.ep_in) &&
        !usbd_edpt_stalled(s->config.rhport, s->config.ep_out) &&
        !usbd_edpt_stalled(s->config.rhport, s->config.ep_in);
}

enum hp1020_printer_result hp1020_tusb_adapter_ack_reset(struct hp1020_tusb_adapter *s,
    struct hp1020_printer_reset_ticket ticket, enum hp1020_printer_reset_part part) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r == HP1020_TUSB_WAIT ? HP1020_PRINTER_WAIT : HP1020_PRINTER_INVALID;
    enum hp1020_printer_result result;
    if (s->exhausted) result = HP1020_PRINTER_LIMIT;
    else if (!same_reset(s, ticket)) result = HP1020_PRINTER_STALE;
    else if ((part == HP1020_PRINTER_RECEIVE_QUIESCED ||
        part == HP1020_PRINTER_TRANSPORT_RESET) && bulk_owned(s)) result = HP1020_PRINTER_WAIT;
    else if (part == HP1020_PRINTER_TRANSPORT_RESET && !transport_ready(s))
        result = HP1020_PRINTER_WAIT;
    else result = hp1020_usb_printer_ack_reset(s->printer, ticket, part);
    s->last_class_result = result;
    s->busy = 0;
    return result;
}

enum hp1020_printer_result hp1020_tusb_adapter_finish_reset(struct hp1020_tusb_adapter *s,
    struct hp1020_printer_reset_ticket ticket) {
    enum hp1020_tusb_result r = enter(s);
    if (r) return r == HP1020_TUSB_WAIT ? HP1020_PRINTER_WAIT : HP1020_PRINTER_INVALID;
    enum hp1020_printer_result result;
    if (s->exhausted) result = HP1020_PRINTER_LIMIT;
    else if (!same_reset(s, ticket)) result = HP1020_PRINTER_STALE;
    else if (bulk_owned(s) || !transport_ready(s) ||
        (s->pending_kind && s->pending_destructive)) result = HP1020_PRINTER_WAIT;
    else {
        /* Capture genuine request linkage before the class consumes it. The
         * independent recovery ID must never be interpreted as a host request. */
        const bool wire_reply = s->printer->reset_request_id &&
            s->printer->reset_request_id == s->class_request_id;
        result = hp1020_usb_printer_finish_reset(s->printer, ticket);
        if (result == HP1020_PRINTER_OK) {
            s->reset_transport_epoch = 0;
            s->active_transport_epoch = s->transport_epoch;
            s->fenced = 0;
            s->input_closed = 0;
            if (wire_reply && s->deferred && s->deferred_epoch == s->control_epoch &&
                s->deferred_epoch == s->active_control_epoch && !s->pending_kind) {
                s->deferred = 0;
                if (!take_reply(s)) result = HP1020_PRINTER_DOCUMENT_ERROR;
            }
        }
    }
    s->last_class_result = result;
    s->busy = 0;
    return result;
}
