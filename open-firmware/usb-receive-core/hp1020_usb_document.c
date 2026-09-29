/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_usb_document.h"
#include <string.h>
enum hp1020_rx_result hp1020_usb_document_init(struct hp1020_usb_document *s,
    struct hp1020_usb_document_memory *m,hp1020_output_progress progress,void *context) {
    memset(s,0,sizeof(*s));s->memory=m;
    enum hp1020_rx_result r=hp1020_usb_receive_init(&s->receive,m?&m->receive:NULL);
    if(r)return r;
    s->payload_error=hp1020_image_output_init(&s->output,&m->output,progress,context);
    if(s->payload_error) { hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD; }
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_document_pump(struct hp1020_usb_document *s) {
    if(s->receive.stopped)return HP1020_RX_STOPPED;
    struct hp1020_rx_view view;
    while(hp1020_usb_receive_peek(&s->receive,&view)==HP1020_RX_OK) {
        /* Empty transfers do not start/finish documents. */
        if(view.length)s->payload_error=hp1020_image_output_feed(&s->output,view.data,view.length);
        if(s->payload_error) {
            hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD;
        }
        enum hp1020_rx_result r=hp1020_usb_receive_release(&s->receive,view.ticket);
        if(r) { hp1020_usb_receive_stop(&s->receive);return r; }
    }
    return s->receive.count?HP1020_RX_WAIT:HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_document_finish(struct hp1020_usb_document *s) {
    if(s->finished)return HP1020_RX_OK;
    if(s->receive.stopped)return HP1020_RX_STOPPED;
    if(s->receive.count)return HP1020_RX_WAIT;
    s->payload_error=hp1020_image_output_finish(&s->output);
    hp1020_usb_receive_stop(&s->receive);
    if(s->payload_error)return HP1020_RX_PAYLOAD;
    s->finished=1;return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_document_output_quiesced(struct hp1020_usb_document *s,uint32_t generation) {
    if(generation!=s->receive.generation)return HP1020_RX_STALE;
    if(!s->receive.stopped)return HP1020_RX_ORDER;
    s->output_quiescent=1;return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_document_restart(struct hp1020_usb_document *s) {
    if(!s->output_quiescent)return HP1020_RX_ORDER;
    hp1020_output_progress progress=s->output.progress;void *context=s->output.context;
    enum hp1020_rx_result r=hp1020_usb_receive_restart(&s->receive);
    if(r)return r;
    s->payload_error=hp1020_image_output_init(&s->output,&s->memory->output,progress,context);
    s->finished=0;s->output_quiescent=0;
    if(s->payload_error) { hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD; }
    return HP1020_RX_OK;
}
