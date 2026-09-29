/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_usb_document.h"
#include <string.h>
static enum hp1020_result document_out(const struct hp1020_output_document *event,void *context) {
    struct hp1020_usb_document *s=context;
    /* The generation comes from the original receive view captured before
     * feed. No notification is admitted from out-of-band output calls. */
    if(!s->feeding || s->receive.stopped || !s->feed_generation ||
        s->feed_generation!=s->receive.generation)return HP1020_ORDER;
    const struct hp1020_usb_document_event completed={s->feed_generation,
        event->document_id,event->first_page,event->pages};
    return s->consume_document ? s->consume_document(&completed,s->document_context) : HP1020_OK;
}
enum hp1020_rx_result hp1020_usb_document_init(struct hp1020_usb_document *s,
    struct hp1020_usb_document_memory *m,hp1020_output_progress progress,void *context) {
    return hp1020_usb_document_init_documents(s,m,progress,context,NULL,NULL);
}
enum hp1020_rx_result hp1020_usb_document_init_documents(struct hp1020_usb_document *s,
    struct hp1020_usb_document_memory *m,hp1020_output_progress progress,void *context,
    hp1020_usb_document_consumer document,void *document_context) {
    memset(s,0,sizeof(*s));s->memory=m;
    s->consume_document=document;s->document_context=document_context;
    enum hp1020_rx_result r=hp1020_usb_receive_init(&s->receive,m?&m->receive:NULL);
    if(r)return r;
    s->payload_error=hp1020_image_output_init_documents(&s->output,&m->output,
        progress,context,document_out,s);
    if(s->payload_error) { hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD; }
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_document_pump(struct hp1020_usb_document *s) {
    if(s->receive.stopped)return HP1020_RX_STOPPED;
    struct hp1020_rx_view view;
    while(hp1020_usb_receive_peek(&s->receive,&view)==HP1020_RX_OK) {
        /* Empty transfers do not start/finish documents. */
        if(view.length) {
            s->feed_generation=view.ticket.generation;s->feeding=1;
            s->payload_error=hp1020_image_output_feed(&s->output,view.data,view.length);
            s->feeding=0;
        }
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
    s->feed_generation=0;s->feeding=0;
    /* consume_document/document_context remain attached to this caller-owned
     * document while the output bridge is rebuilt for the new generation. */
    s->payload_error=hp1020_image_output_init_documents(&s->output,&s->memory->output,
        progress,context,document_out,s);
    s->finished=0;s->output_quiescent=0;
    if(s->payload_error) { hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD; }
    return HP1020_RX_OK;
}
