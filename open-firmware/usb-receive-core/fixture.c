/* SPDX-License-Identifier: GPL-2.0-or-later
 * Synthetic transport and output only. No controller/device operations. */
#include "hp1020_usb_document.h"
#include <string.h>

uint8_t hp1020_rx_fixture_input[1024],hp1020_rx_fixture_capture[262144];
uint8_t hp1020_rx_fixture_received[8192];
uint32_t hp1020_rx_fixture_stats[48];
static struct hp1020_usb_document state;
static struct { uint8_t before[16];struct hp1020_usb_document_memory data;uint8_t after[16]; } memory;
static struct hp1020_rx_ticket tickets[8];
static struct hp1020_usb_document_memory preserved_memory;
static struct hp1020_image_output preserved_output;
static struct hp1020_rx_slot preserved_slots[4];
static uint32_t fill,mode,fail_at,inflight,owned_hash[4],violations;
static uint32_t bytes,accepted,completed,calls,received,received_hash,last_length;

static uint32_t hash(const uint8_t *p,uint32_t n) {
    uint32_t h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;
}
static enum hp1020_result progress(const struct hp1020_page_plan *plan,
    struct hp1020_image_ring *ring,void *context) {
    (void)context;
    if(calls++==fail_at)return HP1020_LIMIT;
    if(plan->stride!=ring->stride || plan->rows!=ring->rows)violations++;
    struct hp1020_ring_view view;
    enum hp1020_ring_result r=hp1020_image_ring_peek(ring,&view);
    if(inflight && (!mode || inflight==3 || r!=HP1020_RING_OK)) {
        uint32_t at=ring->completion,n=ring->slots[at].rows*ring->stride;
        if(owned_hash[at]!=hash(ring->storage+at*ring->slot_bytes,n))violations++;
        if(hp1020_image_ring_complete(ring,at))return HP1020_ORDER;
        inflight--;completed++;
    } else {
        if(r!=HP1020_RING_OK)return HP1020_ORDER;
        uint32_t n=view.rows*ring->stride;
        if(n>sizeof(hp1020_rx_fixture_capture)-bytes)return HP1020_LIMIT;
        memcpy(hp1020_rx_fixture_capture+bytes,view.pixels,n);bytes+=n;
        owned_hash[view.index]=hash(view.pixels,n);
        if(hp1020_image_ring_accept(ring,view.index))return HP1020_ORDER;
        inflight++;accepted++;
    }
    return HP1020_OK;
}
static void snapshot(uint32_t result) {
    uint32_t *o=hp1020_rx_fixture_stats;
    struct hp1020_usb_receive *s=&state.receive;
    o[0]=result;o[1]=s->generation;o[2]=s->issued;o[3]=s->consumed;o[4]=s->count;
    o[5]=s->stopped;o[6]=s->quiescent;o[7]=state.output_quiescent;o[8]=s->error;
    o[9]=state.payload_error;o[10]=state.finished;o[11]=bytes;
    o[12]=hash(hp1020_rx_fixture_capture,bytes);o[13]=accepted;o[14]=completed;o[15]=inflight;o[16]=calls;
    o[17]=state.output.stream.parser.documents;o[18]=state.output.stream.pages;
    o[19]=state.output.pages_drained;o[20]=state.output.stream.rows;
    o[21]=hash(memory.data.receive.data[0],sizeof(memory.data.receive.data));
    for(uint32_t i=0;i<4;i++)if(state.output.ring.slots[i].state==2 &&
        owned_hash[i]!=hash(memory.data.output.slots+i*state.output.ring.slot_bytes,
            state.output.ring.slots[i].rows*state.output.ring.stride))violations++;
    o[22]=hash(memory.data.output.slots,sizeof(memory.data.output.slots));o[23]=violations;
    o[24]=1;
    for(uint32_t i=0;i<16;i++)if(memory.before[i]!=fill || memory.after[i]!=fill)o[24]=0;
    o[25]=0;for(uint32_t i=0;i<4;i++)o[25]+=state.output.ring.slots[i].state!=0;
    o[26]=state.output.stream.image.pending;o[27]=received;o[28]=received_hash;o[29]=last_length;
    o[30]=sizeof(state);o[31]=sizeof(memory.data);
    for(uint32_t i=0;i<4;i++) {
        o[32+4*i]=s->slots[i].sequence;o[33+4*i]=s->slots[i].capacity;
        o[34+4*i]=s->slots[i].length;o[35+4*i]=s->slots[i].ready;
    }
}
uint32_t hp1020_rx_fixture_reset(uint32_t initial_fill,uint32_t ordering,uint32_t reject_after) {
    fill=initial_fill&255;mode=ordering;fail_at=reject_after;
    bytes=0;accepted=0;completed=0;calls=0;inflight=0;violations=0;received=0;last_length=0;
    received_hash=2166136261u;
    memset(&memory,fill,sizeof(memory));memset(tickets,0,sizeof(tickets));
    memset(hp1020_rx_fixture_capture,fill,sizeof(hp1020_rx_fixture_capture));
    memset(hp1020_rx_fixture_received,fill,sizeof(hp1020_rx_fixture_received));
    uint32_t r=hp1020_usb_document_init(&state,&memory.data,progress,NULL);snapshot(r);return r;
}
/* Event words are host-supplied observations. Transfer bytes are written only
 * after a successful reservation, exactly where a future transport would own
 * them. Poisoning after consumption catches accidental retained input pointers. */
uint32_t hp1020_rx_fixture_step(uint32_t op,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    struct hp1020_usb_receive *s=&state.receive;uint32_t r=HP1020_RX_ORDER;
    int protect=op==1 || (op>=4 && op<=7) || op==11;
    uint32_t old_count=s->count,old_issued=s->issued,old_consumed=s->consumed;
    if(protect) {
        memcpy(&preserved_memory,&memory.data,sizeof(memory.data));
        memcpy(&preserved_output,&state.output,sizeof(state.output));
        memcpy(preserved_slots,s->slots,sizeof(s->slots));
    }
    (void)d;
    if(op==0) {
        if(c>=8 || b>a || b>1024)r=HP1020_RX_LIMIT;
        else {
            uint8_t *p=NULL;
            r=hp1020_usb_receive_reserve(s,a,&tickets[c],&p);
            if(!r) { memset(p,fill,1024);memcpy(p,hp1020_rx_fixture_input,b); }
        }
    } else if(op==1) {
        if(a<8)r=hp1020_usb_receive_complete(s,tickets[a],b,c);
    } else if(op==2) {
        uint32_t before=s->consumed;r=hp1020_usb_document_pump(&state);
        for(uint32_t i=0;i<s->consumed-before;i++)
            memset(memory.data.receive.data[(before+i)%4],fill^255,1024);
    } else if(op==3)r=hp1020_usb_document_finish(&state);
    else if(op==4) { hp1020_usb_receive_stop(s);r=HP1020_RX_OK; }
    else if(op==5)r=hp1020_usb_receive_quiesced(s,a);
    else if(op==6)r=hp1020_usb_document_output_quiesced(&state,a);
    else if(op==7) {
        r=hp1020_usb_document_restart(&state);
        if(!r)inflight=0; /* External output-quiesced promise, not completion. */
    } else if(op==8) {
        /* Explicit synthetic boundary controls; never operational APIs. */
        if(!s->count && !s->stopped && a) {
            s->generation=a;s->issued=b;s->consumed=b;r=HP1020_RX_OK;
        }
    } else if(op==9) {
        if(a<8)r=hp1020_usb_receive_release(s,tickets[a]);
    } else if(op==10) {
        struct hp1020_rx_view view;
        r=hp1020_usb_receive_peek(s,&view);
        if(!r) {
            last_length=view.length;
            if(view.length>sizeof(hp1020_rx_fixture_received)-received)r=HP1020_RX_LIMIT;
            else {
                memcpy(hp1020_rx_fixture_received+received,view.data,view.length);received+=view.length;
                received_hash=hash(hp1020_rx_fixture_received,received);
                r=hp1020_usb_receive_release(s,view.ticket);
            }
        }
    } else if(op==11)r=hp1020_usb_receive_fault(s,a,b);
    if(protect && !(op==7 && r==HP1020_RX_OK)) {
        if(memcmp(&preserved_memory,&memory.data,sizeof(memory.data)) ||
           memcmp(&preserved_output,&state.output,sizeof(state.output)))violations++;
        if((op!=1 || r!=HP1020_RX_OK) && (memcmp(preserved_slots,s->slots,sizeof(s->slots)) ||
           old_count!=s->count || old_issued!=s->issued || old_consumed!=s->consumed))violations++;
    }
    memset(hp1020_rx_fixture_input,fill^255,sizeof(hp1020_rx_fixture_input));snapshot(r);return r;
}
uint8_t *hp1020_rx_fixture_storage(void) { return memory.data.receive.data[0]; }
uint8_t *hp1020_rx_fixture_output(void) { return memory.data.output.slots; }
