/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_USB_DOCUMENT_H
#define HP1020_USB_DOCUMENT_H
#include "hp1020_usb_receive.h"
#include "hp1020_image_output.h"
struct hp1020_usb_document_memory {
    struct hp1020_rx_memory receive;
    struct hp1020_image_output_memory output;
};
struct hp1020_usb_document {
    struct hp1020_usb_receive receive;
    struct hp1020_image_output output;
    struct hp1020_usb_document_memory *memory;
    enum hp1020_result payload_error;
    uint8_t finished, output_quiescent;
};
/* First-use initialization only. Nonreentrant, single context. Use the receive
 * API to reserve and complete incoming transfers; pump consumes completed data
 * in reservation order through the existing bounded parser/decoder/output path.
 * No USB hardware, EOF inference, copy replay or physical output is supplied. */
enum hp1020_rx_result hp1020_usb_document_init(struct hp1020_usb_document *,
    struct hp1020_usb_document_memory *, hp1020_output_progress, void *context);
enum hp1020_rx_result hp1020_usb_document_pump(struct hp1020_usb_document *);
/* Explicit end-of-input only after external transport admission is closed by
 * the caller and all reserved transfers consumed. Do not call receive_stop to
 * close admission: it also fences pumping/finishing. A short packet/ZLP is not EOF.
 * Success fences further input and describes software consumption only. */
enum hp1020_rx_result hp1020_usb_document_finish(struct hp1020_usb_document *);
/* Stop via receive_stop; errors also fence consumption. Restart retains all
 * state until BOTH receive_quiesced and output_quiesced are acknowledged for
 * this stopped generation. These are external promises, not hardware proofs.
 * The output promise includes all published/accepted slots and callbacks.
 * Never restart receive alone while it belongs to this document composition. */
enum hp1020_rx_result hp1020_usb_document_output_quiesced(struct hp1020_usb_document *,uint32_t generation);
enum hp1020_rx_result hp1020_usb_document_restart(struct hp1020_usb_document *);
#endif
