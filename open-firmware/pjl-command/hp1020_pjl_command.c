/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_pjl_command.h"
#include <string.h>

static bool pjl_same(struct hp1020_tusb_cookie a,struct hp1020_tusb_cookie b) {
    return a.id==b.id && a.epoch==b.epoch && a.generation==b.generation &&
        a.sequence==b.sequence && a.endpoint==b.endpoint;
}
static void pjl_line_reset(struct hp1020_pjl_command *s) {
    s->line_used=s->line_invalid=s->line_overflow=s->uel_match=0;
}
static void pjl_sync(struct hp1020_pjl_command *s) {
    uint32_t epoch=s->adapter->transport_epoch;
    uint32_t generation=s->adapter->printer->document->receive.generation;
    if(s->epoch==epoch && s->generation==generation)return;
    pjl_line_reset(s);s->have_input=0;s->offset=0;
    if(!s->inflight) { s->queued=0;s->reply_length=0; }
    s->epoch=epoch;s->generation=generation;
}
static enum hp1020_rx_result pjl_leave(struct hp1020_pjl_command *s,enum hp1020_rx_result r) {
    s->busy=0;return r;
}
static enum hp1020_rx_result pjl_fault(struct hp1020_pjl_command *s,enum hp1020_result error) {
    struct hp1020_usb_document *d=s->adapter->printer->document;
    d->payload_error=error;
    (void)hp1020_tusb_adapter_fault(s->adapter,s->epoch,s->generation,0x80000501u);
    hp1020_usb_receive_stop(&d->receive);
    return HP1020_RX_PAYLOAD;
}
static enum hp1020_rx_result pjl_collect(struct hp1020_pjl_command *s) {
    if(!s->inflight)return HP1020_RX_OK;
    struct hp1020_tusb_in_result result;
    enum hp1020_tusb_result r=hp1020_tusb_adapter_take_in_result(s->adapter,&result);
    if(r==HP1020_TUSB_WAIT || r==HP1020_TUSB_LIMIT)return HP1020_RX_OK;
    if(r!=HP1020_TUSB_OK || !pjl_same(result.cookie,s->in_cookie)) {
        /* Contract violation: another consumer stole/replaced our result.
         * Never pretend this permits overwriting the original borrowed bytes. */
        s->terminal=1;return HP1020_RX_ORDER;
    }
    s->inflight=s->queued=s->reply_length=0;
    s->in_cookie=(struct hp1020_tusb_cookie){0};
    return HP1020_RX_OK;
}
static void pjl_submit(struct hp1020_pjl_command *s) {
    if(!s->queued || s->inflight)return;
    struct hp1020_tusb_cookie c={0};
    s->last_send=hp1020_tusb_adapter_send_in(s->adapter,s->reply,s->reply_length,&c);
    /* Binding, even followed by failure, borrows the original source. A refusal
     * before binding retains our queued packet for a later pump, without retry
     * loops or false completion. Destructive fences discard it via pjl_sync. */
    if(c.id) { s->in_cookie=c;s->inflight=1; }
}
static enum hp1020_rx_result pjl_feed_binary(struct hp1020_pjl_command *s,
    const uint8_t *data,uint32_t length,size_t *used) {
    struct hp1020_usb_document *d=s->adapter->printer->document;
    enum hp1020_rx_result r=hp1020_usb_document_feed(d,s->input.generation,data,length,used);
    if(r==HP1020_RX_PAYLOAD)return pjl_fault(s,d->payload_error);
    if(r!=HP1020_RX_OK && r!=HP1020_RX_WAIT && r!=HP1020_RX_STOPPED)return pjl_fault(s,HP1020_ORDER);
    return r;
}
static void pjl_status_reply(struct hp1020_pjl_command *s) {
    struct hp1020_pjl_status status={0};
    if(!s->read_status || !s->read_status(s->status_context,s->epoch,s->generation,&status) ||
        status.epoch!=s->epoch || status.generation!=s->generation || status.online>1 ||
        status.code>99999)return;
    static const uint8_t prefix[]="@PJL INFO STATUS\r\nCODE=";
    static const uint8_t fields[]="\r\nDISPLAY=\"\"\r\nONLINE=";
    memcpy(s->reply,prefix,sizeof(prefix)-1);
    unsigned at=sizeof(prefix)-1;
    /* Five bounded decimal digits, without adding a target remainder helper. */
    static const uint32_t places[]={10000,1000,100,10,1};
    uint32_t code=status.code;bool started=false;
    for(unsigned i=0;i<5;i++) {
        uint8_t digit='0';
        while(code>=places[i]) { code-=places[i];digit++; }
        if(digit!='0' || started || i==4) { s->reply[at++]=digit;started=true; }
    }
    memcpy(s->reply+at,fields,sizeof(fields)-1);at+=sizeof(fields)-1;
    const char *online=status.online?"TRUE":"FALSE";
    unsigned n=status.online?4:5;
    memcpy(s->reply+at,online,n);at+=n;
    memcpy(s->reply+at,"\r\n\f",3);at+=3;
    s->reply_length=(uint8_t)at;s->queued=1;
}
static enum hp1020_rx_result pjl_text(struct hp1020_pjl_command *s,uint8_t b) {
    static const uint8_t uel[]={0x1b,'%','-','1','2','3','4','5','X'};
    static const uint8_t echo[]="@PJL ECHO ";
    static const uint8_t status[]="@PJL INFO STATUS";
    if(b==0x1b) {
        pjl_line_reset(s);s->line_invalid=1;s->uel_match=1;return HP1020_RX_OK;
    }
    if(s->uel_match) {
        if(b==uel[s->uel_match]) {
            if(++s->uel_match==sizeof(uel))pjl_line_reset(s);
            return HP1020_RX_OK;
        }
        s->uel_match=0; /* Malformed escapes discard this line, not a prefix. */
    }
    if(b=='\r' || b=='\n' || b=='\f') {
        bool is_echo=s->line_used>=sizeof(echo)-1 && !memcmp(s->line,echo,sizeof(echo)-1);
        if(is_echo) {
            if(s->line_overflow)return pjl_fault(s,HP1020_LIMIT);
            if(s->line_invalid)return pjl_fault(s,HP1020_FORMAT);
            if(s->queued || s->inflight)return HP1020_RX_WAIT;
            memcpy(s->reply,s->line,s->line_used);
            memcpy(s->reply+s->line_used,"\r\n\f",3);
            s->reply_length=(uint8_t)(s->line_used+3);s->queued=1;
        } else if(!s->line_invalid && !s->line_overflow && s->line_used==sizeof(status)-1 &&
            !memcmp(s->line,status,sizeof(status)-1)) {
            if(s->queued || s->inflight)return HP1020_RX_WAIT;
            pjl_status_reply(s);
        }
        pjl_line_reset(s);return HP1020_RX_OK;
    }
    if(b<0x20 || b>0x7e)s->line_invalid=1;
    if(s->line_used==HP1020_PJL_LINE_BYTES) { s->line_overflow=1;return HP1020_RX_OK; }
    s->line[s->line_used++]=b;
    /* Raw ZjStream is recognized only at the start of an envelope line. A
     * JZJZ token inside ECHO text cannot enter binary framing. */
    if(s->line_used==4 && !s->line_invalid && !memcmp(s->line,"JZJZ",4)) {
        size_t used=0;
        enum hp1020_rx_result r=pjl_feed_binary(s,s->line,4,&used);
        if(!r && used!=4)r=pjl_fault(s,HP1020_ORDER);
        pjl_line_reset(s);return r;
    }
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_pjl_command_init(struct hp1020_pjl_command *s,
    struct hp1020_tusb_adapter *a,hp1020_pjl_status_read_fn read_status,void *context) {
    if(!s || s->initialized || !a || !a->initialized || !a->printer ||
        a->busy || a->stack_active || a->owners[3].state || a->in_prepared ||
        a->in_result_pending)return HP1020_RX_ORDER;
    memset(s,0,sizeof(*s));s->adapter=a;s->read_status=read_status;
    s->status_context=context;s->initialized=1;
    pjl_sync(s);return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_pjl_command_pump(struct hp1020_pjl_command *s) {
    if(!s || !s->initialized || !s->adapter || s->terminal)return HP1020_RX_ORDER;
    if(s->busy || s->adapter->busy || s->adapter->stack_active)return HP1020_RX_WAIT;
    s->busy=1;pjl_sync(s);
    enum hp1020_rx_result r=pjl_collect(s);
    if(r)return pjl_leave(s,r);
    struct hp1020_usb_document *d=s->adapter->printer->document;
    if(d->receive.stopped)return pjl_leave(s,HP1020_RX_STOPPED);
    pjl_submit(s);
    if(d->receive.stopped)return pjl_leave(s,HP1020_RX_STOPPED);
    if(s->queued && !s->inflight)return pjl_leave(s,HP1020_RX_WAIT);
    struct hp1020_rx_view v;
    while((r=hp1020_usb_receive_peek(&d->receive,&v))==HP1020_RX_OK) {
        if(s->have_input) {
            if(s->input.generation!=v.ticket.generation || s->input.sequence!=v.ticket.sequence ||
                s->offset>v.length) {
                r=pjl_fault(s,HP1020_ORDER);return pjl_leave(s,r);
            }
        } else { s->input=v.ticket;s->offset=0;s->have_input=1; }
        while(s->offset<v.length || hp1020_usb_document_buffered(d)) {
            const struct hp1020_semantic *parser=hp1020_usb_document_parser(d);
            bool buffered=hp1020_usb_document_buffered(d);
            bool binary=parser->framing || buffered;
            uint32_t n=1;size_t used=1;
            if(binary) {
                n=buffered?0:parser->framing==1?16-parser->header_used:parser->remaining;
                if(n>v.length-s->offset)n=v.length-s->offset;
                if(!n && !buffered) { r=pjl_fault(s,HP1020_ORDER);return pjl_leave(s,r); }
                r=pjl_feed_binary(s,v.data+s->offset,n,&used);
            } else r=pjl_text(s,v.data[s->offset]);
            if(binary)s->offset+=(uint32_t)used;
            else if(!r)s->offset++;
            if(r)return pjl_leave(s,r);
            pjl_submit(s);
            if(d->receive.stopped)return pjl_leave(s,HP1020_RX_STOPPED);
            if(s->queued && !s->inflight)return pjl_leave(s,HP1020_RX_WAIT);
            if(d->cooperative && binary)return pjl_leave(s,HP1020_RX_WAIT);
        }
        r=hp1020_usb_receive_release(&d->receive,v.ticket);
        if(r) { (void)pjl_fault(s,HP1020_ORDER);return pjl_leave(s,r); }
        s->have_input=0;s->offset=0;
    }
    if(r!=HP1020_RX_WAIT && r!=HP1020_RX_OK)return pjl_leave(s,r);
    return pjl_leave(s,d->receive.count || s->queued || s->inflight?HP1020_RX_WAIT:HP1020_RX_OK);
}
enum hp1020_rx_result hp1020_pjl_command_reap(struct hp1020_pjl_command *s) {
    if(!s || !s->initialized || !s->adapter || s->terminal)return HP1020_RX_ORDER;
    if(s->busy || s->adapter->busy || s->adapter->stack_active)return HP1020_RX_WAIT;
    s->busy=1;pjl_sync(s);
    return pjl_leave(s,pjl_collect(s));
}
