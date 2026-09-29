/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_USB_DOCUMENT_H
#define HP1020_USB_DOCUMENT_H
#include "hp1020_usb_receive.h"
#include "hp1020_image_output.h"
struct hp1020_usb_document_memory {
    struct hp1020_rx_memory receive;
    struct hp1020_image_output_memory output;
};
struct hp1020_usb_document_event {
    uint32_t generation; /* Original receive ticket generation at feed admission. */
    uint32_t document_id, first_page, pages; /* Encoded pages, not copy replay. */
};
/* Synchronous validated/completed document notification. The borrowed event is
 * valid only during the callback. Retain its identity by value, including the
 * original generation; never attach today's generation to a late observation.
 * Returning an error stops consumption before following input, without retrying
 * or retracting already accepted output. Do not re-enter/mutate the document. */
typedef enum hp1020_result (*hp1020_usb_document_consumer)(
    const struct hp1020_usb_document_event *,void *context);
struct hp1020_usb_document {
    struct hp1020_usb_receive receive;
    struct hp1020_image_output output;
    struct hp1020_usb_document_memory *memory;
    hp1020_usb_document_consumer consume_document;
    void *document_context;
    uint32_t feed_generation;
    enum hp1020_result payload_error;
    uint8_t finished, output_quiescent, feeding;
};
/* First-use initialization only. Nonreentrant, single context. Use the receive
 * API to reserve and complete incoming transfers; pump consumes completed data
 * in reservation order through the existing bounded parser/decoder/output path.
 * No USB hardware, EOF inference, copy replay or physical output is supplied. */
enum hp1020_rx_result hp1020_usb_document_init(struct hp1020_usb_document *,
    struct hp1020_usb_document_memory *, hp1020_output_progress, void *context);
/* Original initializer wraps this with no notification. Valid END_PAGE drains
 * the page; END_DOC counts/notifies and leaves receive admission/generation
 * unchanged. Multiple document boundaries in one input buffer are observed. */
enum hp1020_rx_result hp1020_usb_document_init_documents(struct hp1020_usb_document *,
    struct hp1020_usb_document_memory *,hp1020_output_progress,void *progress_context,
    hp1020_usb_document_consumer,void *document_context);
enum hp1020_rx_result hp1020_usb_document_pump(struct hp1020_usb_document *);
/* Explicit end-of-input only after external transport admission is closed by
 * the caller and all reserved transfers consumed. Do not call receive_stop to
 * close admission: it also fences pumping/finishing. A short packet/ZLP is not EOF.
 * Success fences further input and describes software consumption only. Normal
 * continuous operation uses pump without close/finish after each document. */
enum hp1020_rx_result hp1020_usb_document_finish(struct hp1020_usb_document *);
/* Stop via receive_stop; errors also fence consumption. Restart retains all
 * state until BOTH receive_quiesced and output_quiesced are acknowledged for
 * this stopped generation. These are external promises, not hardware proofs.
 * The output promise includes all published/accepted slots and callbacks.
 * Never restart receive alone while it belongs to this document composition.
 * Restart preserves both callback/context pairs and resets document counters
 * only after advancing the receive generation through these existing gates. */
enum hp1020_rx_result hp1020_usb_document_output_quiesced(struct hp1020_usb_document *,uint32_t generation);
enum hp1020_rx_result hp1020_usb_document_restart(struct hp1020_usb_document *);
#endif
