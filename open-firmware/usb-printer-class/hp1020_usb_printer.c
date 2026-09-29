/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Experimental request/ownership layer; no USB controller implementation. */
#include "hp1020_usb_printer.h"
#include <string.h>

enum action {
    ACTION_NONE = 0,
    ACTION_ID,
    ACTION_PORT,
    ACTION_RESET_WAIT,
    ACTION_RESET_ACK,
    ACTION_STALL
};

static uint16_t get_le16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static void invalidate_reset(struct hp1020_usb_printer *s) {
    s->reset_active = 0;
    s->reset_parts = 0;
    s->reset_request_id = 0;
    if (s->current_action == ACTION_RESET_WAIT ||
        s->current_action == ACTION_RESET_ACK)
        s->current_action = ACTION_STALL;
}

static enum hp1020_printer_result exhaust(struct hp1020_usb_printer *s) {
    hp1020_usb_receive_stop(&s->document->receive);
    invalidate_reset(s);
    s->exhausted = 1;
    s->current_request_id = 0;
    s->current_action = ACTION_NONE;
    /* Outstanding EP0 storage remains untouched and separately owned. */
    return HP1020_PRINTER_LIMIT;
}

/* Recovery identities are independent of actual host request identities.
 * Zero reply_request_id denotes an internal transport recovery, never a SETUP.
 * Starting either kind invalidates every promise from the previous attempt,
 * including when the receive generation has not changed. */
static enum hp1020_printer_result begin_recovery(struct hp1020_usb_printer *s,
    uint32_t reply_request_id) {
    if (s->exhausted || s->last_recovery_id == UINT32_MAX)
        return exhaust(s);
    hp1020_usb_receive_stop(&s->document->receive);
    invalidate_reset(s);
    s->reset.recovery_id = ++s->last_recovery_id;
    s->reset.generation = s->document->receive.generation;
    s->reset_request_id = reply_request_id;
    s->reset_active = 1;
    if (reply_request_id) {
        s->current_action = ACTION_RESET_WAIT;
    } else {
        /* The transport boundary supersedes old reply permission, not borrowed
         * EP0 storage. ep0_live, ep0_request_id and response_status stay intact. */
        s->current_request_id = 0;
        s->current_action = ACTION_NONE;
        s->current_issued = 0;
        s->requested_length = 0;
        s->staged_status = 0;
        s->staged_fallback = 0;
    }
    return HP1020_PRINTER_OK;
}

static enum hp1020_printer_result check_reset(struct hp1020_usb_printer *s,
    struct hp1020_printer_reset_ticket ticket) {
    if (!s || !s->initialized)
        return HP1020_PRINTER_INVALID;
    if (s->exhausted)
        return HP1020_PRINTER_LIMIT;
    if (!s->reset_active || !ticket.recovery_id ||
        ticket.recovery_id != s->reset.recovery_id ||
        ticket.generation != s->reset.generation)
        return HP1020_PRINTER_STALE;
    if (s->document->receive.generation != ticket.generation ||
        !s->document->receive.stopped) {
        /* A caller restarted outside the class or changed its document. This
         * violates the ownership contract; never acknowledge that reset. */
        hp1020_usb_receive_stop(&s->document->receive);
        invalidate_reset(s);
        return HP1020_PRINTER_DOCUMENT_ERROR;
    }
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_init(struct hp1020_usb_printer *s,
    struct hp1020_usb_document *document,
    const struct hp1020_printer_config *config) {
    if (!s)
        return HP1020_PRINTER_INVALID;
    memset(s, 0, sizeof(*s));
    if (!document || !document->memory ||
        document->receive.memory != &document->memory->receive ||
        !document->receive.generation)
        return HP1020_PRINTER_INVALID;
    s->document = document;
    if (!config || !config->device_id || config->device_id_length < 2 ||
        (((uint16_t)config->device_id[0] << 8) | config->device_id[1]) !=
            config->device_id_length) {
        hp1020_usb_receive_stop(&document->receive);
        return HP1020_PRINTER_INVALID;
    }
    s->config = *config;
    s->initialized = 1;
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_setup(struct hp1020_usb_printer *s,
    const uint8_t *setup, uint32_t length,
    const struct hp1020_printer_status *status, uint32_t *request_id) {
    if (request_id)
        *request_id = 0;
    if (!s || !s->initialized)
        return HP1020_PRINTER_INVALID;
    if (s->exhausted || s->last_request_id == UINT32_MAX)
        return exhaust(s);

    /* SETUP supersedes the previous control reply, not ongoing reset work. */
    s->current_request_id = ++s->last_request_id;
    s->current_action = ACTION_STALL;
    s->current_issued = 0;
    s->requested_length = 0;
    s->staged_status = 0;
    s->staged_fallback = 0;
    if (request_id)
        *request_id = s->current_request_id;
    if (!setup || length != 8)
        return HP1020_PRINTER_INVALID;

    const uint16_t value = get_le16(setup + 2);
    const uint16_t index = get_le16(setup + 4);
    const uint16_t requested = get_le16(setup + 6);

    if (setup[0] == 0xa1 && setup[1] == 0) {
        const uint16_t expected_index =
            ((uint16_t)s->config.interface_number << 8) |
            s->config.alternate_setting;
        if (value != s->config.configuration_index || index != expected_index)
            return HP1020_PRINTER_INVALID;
        s->requested_length = requested;
        s->current_action = ACTION_ID;
        return HP1020_PRINTER_OK;
    }

    if (setup[0] == 0xa1 && setup[1] == 1) {
        if (value || index != s->config.interface_number || requested != 1)
            return HP1020_PRINTER_INVALID;
        if (status && (status->known > 1 ||
            (status->known && (status->value & (uint8_t)~0x38u))))
            return HP1020_PRINTER_INVALID;
        s->staged_fallback = (uint8_t)(!status || !status->known);
        s->staged_status = s->staged_fallback ? 0x18 : status->value;
        s->requested_length = 1;
        s->current_action = ACTION_PORT;
        return HP1020_PRINTER_OK;
    }

    if ((setup[0] == 0x21 || setup[0] == 0x23) && setup[1] == 2) {
        if (value || index != s->config.interface_number || requested)
            return HP1020_PRINTER_INVALID;
        return begin_recovery(s, s->current_request_id);
    }

    return HP1020_PRINTER_INVALID;
}

enum hp1020_printer_result hp1020_usb_printer_begin_transport_recovery(
    struct hp1020_usb_printer *s, struct hp1020_printer_reset_ticket *ticket) {
    if (ticket)
        *ticket = (struct hp1020_printer_reset_ticket){0};
    if (!s || !s->initialized || !ticket)
        return HP1020_PRINTER_INVALID;
    const enum hp1020_printer_result r = begin_recovery(s, 0);
    if (r == HP1020_PRINTER_OK)
        *ticket = s->reset;
    return r;
}

enum hp1020_printer_result hp1020_usb_printer_pending_reset(
    const struct hp1020_usb_printer *s,
    struct hp1020_printer_reset_ticket *ticket) {
    if (!s || !s->initialized || !ticket)
        return HP1020_PRINTER_INVALID;
    if (s->exhausted)
        return HP1020_PRINTER_LIMIT;
    if (!s->reset_active)
        return HP1020_PRINTER_WAIT;
    *ticket = s->reset;
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_ack_reset(
    struct hp1020_usb_printer *s, struct hp1020_printer_reset_ticket ticket,
    enum hp1020_printer_reset_part part) {
    enum hp1020_printer_result r = check_reset(s, ticket);
    if (r != HP1020_PRINTER_OK)
        return r;
    enum hp1020_rx_result document_result = HP1020_RX_OK;
    switch (part) {
    case HP1020_PRINTER_RECEIVE_QUIESCED:
        document_result = hp1020_usb_receive_quiesced(
            &s->document->receive, ticket.generation);
        break;
    case HP1020_PRINTER_OUTPUT_QUIESCED:
        document_result = hp1020_usb_document_output_quiesced(
            s->document, ticket.generation);
        break;
    case HP1020_PRINTER_TRANSPORT_RESET:
        break;
    default:
        return HP1020_PRINTER_INVALID;
    }
    if (document_result != HP1020_RX_OK) {
        hp1020_usb_receive_stop(&s->document->receive);
        invalidate_reset(s);
        return HP1020_PRINTER_DOCUMENT_ERROR;
    }
    s->reset_parts |= (uint8_t)part;
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_finish_reset(
    struct hp1020_usb_printer *s, struct hp1020_printer_reset_ticket ticket) {
    enum hp1020_printer_result r = check_reset(s, ticket);
    if (r != HP1020_PRINTER_OK)
        return r;
    if (s->reset_parts != (HP1020_PRINTER_RECEIVE_QUIESCED |
        HP1020_PRINTER_OUTPUT_QUIESCED | HP1020_PRINTER_TRANSPORT_RESET))
        return HP1020_PRINTER_WAIT;
    const enum hp1020_rx_result document_result =
        hp1020_usb_document_restart(s->document);
    if (document_result != HP1020_RX_OK) {
        hp1020_usb_receive_stop(&s->document->receive);
        invalidate_reset(s);
        if (document_result == HP1020_RX_LIMIT &&
            s->document->receive.generation == UINT32_MAX)
            return exhaust(s);
        return HP1020_PRINTER_DOCUMENT_ERROR;
    }
    const uint32_t reply_request_id = s->reset_request_id;
    s->reset_active = 0;
    s->reset_parts = 0;
    s->reset_request_id = 0;
    if (reply_request_id && s->current_request_id == reply_request_id &&
        s->current_action == ACTION_RESET_WAIT)
        s->current_action = ACTION_RESET_ACK;
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_take_response(
    struct hp1020_usb_printer *s, struct hp1020_printer_response *response) {
    if (!s || !s->initialized || !response)
        return HP1020_PRINTER_INVALID;
    if (s->exhausted)
        return HP1020_PRINTER_LIMIT;
    if (s->ep0_live || s->current_issued || !s->current_request_id ||
        s->current_action == ACTION_NONE ||
        s->current_action == ACTION_RESET_WAIT)
        return HP1020_PRINTER_WAIT;

    struct hp1020_printer_response next = {0};
    next.request_id = s->current_request_id;
    switch (s->current_action) {
    case ACTION_ID:
        next.kind = HP1020_PRINTER_DATA;
        next.data = s->config.device_id;
        next.length = s->requested_length < s->config.device_id_length ?
            s->requested_length : s->config.device_id_length;
        break;
    case ACTION_PORT:
        s->response_status = s->staged_status;
        next.kind = HP1020_PRINTER_DATA;
        next.data = &s->response_status;
        next.length = 1;
        next.status_fallback = s->staged_fallback;
        break;
    case ACTION_RESET_ACK:
        next.kind = HP1020_PRINTER_ACK;
        break;
    case ACTION_STALL:
        next.kind = HP1020_PRINTER_STALL;
        break;
    default:
        return HP1020_PRINTER_INVALID;
    }
    s->ep0_live = 1;
    s->ep0_request_id = next.request_id;
    s->current_issued = 1;
    *response = next;
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_ep0_quiesced(
    struct hp1020_usb_printer *s, uint32_t response_request_id) {
    if (!s || !s->initialized)
        return HP1020_PRINTER_INVALID;
    if (!s->ep0_live || !response_request_id ||
        s->ep0_request_id != response_request_id)
        return HP1020_PRINTER_STALE;
    s->ep0_live = 0;
    s->ep0_request_id = 0;
    return HP1020_PRINTER_OK;
}

enum hp1020_printer_result hp1020_usb_printer_fault(struct hp1020_usb_printer *s,
    uint32_t generation, uint32_t fault) {
    if (!s || !s->initialized)
        return HP1020_PRINTER_INVALID;
    if (generation != s->document->receive.generation)
        return HP1020_PRINTER_STALE;
    if (!fault)
        return HP1020_PRINTER_OK;
    (void)hp1020_usb_receive_fault(&s->document->receive, generation, fault);
    hp1020_usb_receive_stop(&s->document->receive);
    invalidate_reset(s);
    return s->exhausted ? HP1020_PRINTER_LIMIT : HP1020_PRINTER_OK;
}
