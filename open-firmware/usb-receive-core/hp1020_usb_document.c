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
enum hp1020_rx_result hp1020_usb_document_init_cooperative(struct hp1020_usb_document *s,
    struct hp1020_usb_document_memory *m,hp1020_usb_document_consumer document,void *context) {
    memset(s,0,sizeof(*s));s->memory=m;s->cooperative=1;
    s->consume_document=document;s->document_context=context;
    enum hp1020_rx_result r=hp1020_usb_receive_init(&s->receive,m?&m->receive:NULL);
    if(r)return r;
    if(hp1020_image_pump_init(&s->pump,&m->pump)!=HP1020_PUMP_MORE) {
        s->payload_error=HP1020_ORDER;hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD;
    }
    return HP1020_RX_OK;
}
static enum hp1020_rx_result pump_result(struct hp1020_usb_document *s,enum hp1020_pump_result r) {
    if(r==HP1020_PUMP_PAGE || r==HP1020_PUMP_DOCUMENT) {
        if(r==HP1020_PUMP_DOCUMENT) {
            const struct hp1020_output_document event={s->pump.event.document_id,
                s->pump.event.first_page,s->pump.event.pages};
            s->payload_error=document_out(&event,s);
        }
        if(!s->payload_error && hp1020_image_pump_ack(&s->pump,r)!=HP1020_PUMP_MORE)
            s->payload_error=HP1020_ORDER;
    } else if(r==HP1020_PUMP_ERROR)s->payload_error=s->pump.error?s->pump.error:HP1020_ORDER;
    else if(r==HP1020_PUMP_STOPPED)return HP1020_RX_STOPPED;
    if(s->payload_error) {
        hp1020_usb_receive_stop(&s->receive);hp1020_image_pump_stop(&s->pump);return HP1020_RX_PAYLOAD;
    }
    return r==HP1020_PUMP_WAIT_OUTPUT?HP1020_RX_WAIT:HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_document_feed(struct hp1020_usb_document *s,
    uint32_t generation,const uint8_t *data,size_t size,size_t *used) {
    if(!used)return HP1020_RX_ORDER;
    *used=0;
    if(generation!=s->receive.generation)return HP1020_RX_STALE;
    if(s->receive.stopped || s->finished)return HP1020_RX_STOPPED;
    if(s->feeding)return HP1020_RX_ORDER;
    s->feed_generation=generation;s->feeding=1;
    enum hp1020_rx_result r=HP1020_RX_OK;
    if(s->cooperative)r=pump_result(s,hp1020_image_pump_feed(&s->pump,data,size,used));
    else {
        s->payload_error=hp1020_image_output_feed(&s->output,data,size);*used=size;
        if(s->payload_error) { hp1020_usb_receive_stop(&s->receive);r=HP1020_RX_PAYLOAD; }
    }
    s->feeding=0;return r;
}
enum hp1020_rx_result hp1020_usb_document_pump(struct hp1020_usb_document *s) {
    if(s->receive.stopped)return HP1020_RX_STOPPED;
    struct hp1020_rx_view view;
    if(s->cooperative) {
        enum hp1020_rx_result r=hp1020_usb_receive_peek(&s->receive,&view);
        if(r!=HP1020_RX_OK)return s->receive.count?r:HP1020_RX_OK;
        if(s->have_input) {
            if(s->input.generation!=view.ticket.generation || s->input.sequence!=view.ticket.sequence ||
                s->offset>view.length) { hp1020_usb_receive_stop(&s->receive);return HP1020_RX_ORDER; }
        } else { s->input=view.ticket;s->offset=0;s->have_input=1; }
        size_t used=0;
        r=hp1020_usb_document_feed(s,view.ticket.generation,view.data+s->offset,view.length-s->offset,&used);
        s->offset+=(uint32_t)used;
        if(r)return r;
        if(s->offset==view.length && !hp1020_usb_document_buffered(s)) {
            r=hp1020_usb_receive_release(&s->receive,view.ticket);
            if(r) { hp1020_usb_receive_stop(&s->receive);return r; }
            s->have_input=0;s->offset=0;
        }
        return s->receive.count?HP1020_RX_WAIT:HP1020_RX_OK;
    }
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
    if(s->cooperative) {
        s->feed_generation=s->receive.generation;s->feeding=1;
        enum hp1020_pump_result result=hp1020_image_pump_finish(&s->pump);
        enum hp1020_rx_result r=pump_result(s,result);
        s->feeding=0;
        if(r)return r;
        if(result!=HP1020_PUMP_DONE)return HP1020_RX_WAIT;
        hp1020_usb_receive_stop(&s->receive);s->finished=1;return HP1020_RX_OK;
    }
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
    hp1020_output_progress progress=NULL;void *context=NULL;
    if(!s->cooperative) { progress=s->output.progress;context=s->output.context; }
    enum hp1020_rx_result r=hp1020_usb_receive_restart(&s->receive);
    if(r)return r;
    s->feed_generation=0;s->feeding=0;s->have_input=0;s->offset=0;
    /* consume_document/document_context remain attached to this caller-owned
     * document while the output bridge is rebuilt for the new generation. */
    if(s->cooperative) {
        memset(&s->pump,0,sizeof(s->pump));
        s->payload_error=hp1020_image_pump_init(&s->pump,&s->memory->pump)==HP1020_PUMP_MORE?
            HP1020_OK:HP1020_ORDER;
    } else s->payload_error=hp1020_image_output_init_documents(&s->output,&s->memory->output,
        progress,context,document_out,s);
    s->finished=0;s->output_quiescent=0;
    if(s->payload_error) { hp1020_usb_receive_stop(&s->receive);return HP1020_RX_PAYLOAD; }
    return HP1020_RX_OK;
}
