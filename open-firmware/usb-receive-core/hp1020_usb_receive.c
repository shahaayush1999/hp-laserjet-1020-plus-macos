/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_usb_receive.h"
#include <string.h>

static enum hp1020_rx_result fail(struct hp1020_usb_receive *s, enum hp1020_rx_result r) {
    if(!s->error)s->error=r;
    s->stopped=1;
    return s->error;
}
static struct hp1020_rx_slot *slot(struct hp1020_usb_receive *s, struct hp1020_rx_ticket t) {
    if(t.generation!=s->generation || !t.sequence || t.sequence<=s->consumed || t.sequence>s->issued)
        return NULL;
    struct hp1020_rx_slot *p=&s->slots[(t.sequence-1)%HP1020_RX_SLOTS];
    return p->sequence==t.sequence?p:NULL;
}
enum hp1020_rx_result hp1020_usb_receive_init(struct hp1020_usb_receive *s, struct hp1020_rx_memory *m) {
    memset(s,0,sizeof(*s));s->generation=1;s->memory=m;
    if(!m)return fail(s,HP1020_RX_LIMIT);
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_receive_reserve(struct hp1020_usb_receive *s,uint32_t capacity,
    struct hp1020_rx_ticket *ticket,uint8_t **buffer) {
    if(s->stopped)return HP1020_RX_STOPPED;
    if(!ticket || !buffer || !capacity || capacity>HP1020_RX_CAPACITY)return HP1020_RX_LIMIT;
    if(s->count==HP1020_RX_SLOTS)return HP1020_RX_WAIT;
    if(s->issued==UINT32_MAX)return fail(s,HP1020_RX_LIMIT);
    uint32_t at=s->issued%HP1020_RX_SLOTS;
    struct hp1020_rx_slot *p=&s->slots[at];
    p->sequence=++s->issued;p->capacity=capacity;p->length=0;p->ready=0;s->count++;
    ticket->generation=s->generation;ticket->sequence=p->sequence;*buffer=s->memory->data[at];
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_receive_complete(struct hp1020_usb_receive *s,
    struct hp1020_rx_ticket ticket,uint32_t status,uint32_t endpoint_fault) {
    struct hp1020_rx_slot *p=slot(s,ticket);
    if(!p || p->ready)return HP1020_RX_STALE;
    if(s->stopped)return HP1020_RX_STOPPED;
    if(endpoint_fault)return fail(s,HP1020_RX_ENDPOINT);
    if((status>>30)!=2)return HP1020_RX_WAIT;
    if((status&0x30000000u) || !(status&0x08000000u))return fail(s,HP1020_RX_STATUS);
    return hp1020_usb_receive_complete_data(s,ticket,status&0xffffu);
}
enum hp1020_rx_result hp1020_usb_receive_complete_data(struct hp1020_usb_receive *s,
    struct hp1020_rx_ticket ticket,uint32_t length) {
    struct hp1020_rx_slot *p=slot(s,ticket);
    if(!p || p->ready)return HP1020_RX_STALE;
    if(s->stopped)return HP1020_RX_STOPPED;
    if(length>p->capacity)return fail(s,HP1020_RX_LIMIT);
    p->length=length;p->ready=1;
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_receive_fault(struct hp1020_usb_receive *s,uint32_t generation,uint32_t fault) {
    if(generation!=s->generation)return HP1020_RX_STALE;
    if(!fault)return HP1020_RX_OK;
    if(s->stopped)return HP1020_RX_STOPPED;
    return fail(s,HP1020_RX_ENDPOINT);
}
enum hp1020_rx_result hp1020_usb_receive_peek(const struct hp1020_usb_receive *s,struct hp1020_rx_view *view) {
    if(!view)return HP1020_RX_ORDER;
    if(s->stopped)return HP1020_RX_STOPPED;
    if(!s->count)return HP1020_RX_WAIT;
    uint32_t at=s->consumed%HP1020_RX_SLOTS;
    const struct hp1020_rx_slot *p=&s->slots[at];
    if(!p->ready)return HP1020_RX_WAIT;
    view->ticket.generation=s->generation;view->ticket.sequence=p->sequence;
    view->data=s->memory->data[at];view->length=p->length;
    return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_receive_release(struct hp1020_usb_receive *s,struct hp1020_rx_ticket ticket) {
    struct hp1020_rx_slot *p=slot(s,ticket);
    if(!p)return HP1020_RX_STALE;
    if(s->stopped)return HP1020_RX_STOPPED;
    if(ticket.sequence!=s->consumed+1 || !p->ready)return HP1020_RX_ORDER;
    memset(p,0,sizeof(*p));s->consumed++;s->count--;
    return HP1020_RX_OK;
}
void hp1020_usb_receive_stop(struct hp1020_usb_receive *s) { s->stopped=1; }
enum hp1020_rx_result hp1020_usb_receive_quiesced(struct hp1020_usb_receive *s,uint32_t generation) {
    if(generation!=s->generation)return HP1020_RX_STALE;
    if(!s->stopped)return HP1020_RX_ORDER;
    s->quiescent=1;return HP1020_RX_OK;
}
enum hp1020_rx_result hp1020_usb_receive_restart(struct hp1020_usb_receive *s) {
    if(!s->stopped || !s->quiescent)return HP1020_RX_ORDER;
    if(!s->memory || s->generation==UINT32_MAX)return fail(s,HP1020_RX_LIMIT);
    s->generation++;s->issued=0;s->consumed=0;s->count=0;s->error=HP1020_RX_OK;
    memset(s->slots,0,sizeof(s->slots));s->stopped=0;s->quiescent=0;
    return HP1020_RX_OK;
}
