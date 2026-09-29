/* SPDX-License-Identifier: GPL-2.0-or-later
 * Synthetic class/transport/output observations only. No device operations. */
#include "hp1020_usb_printer.h"
#include <string.h>

uint8_t hp1020_pc_fixture_input[1024], hp1020_pc_fixture_capture[262144];
uint8_t hp1020_pc_fixture_replies[32768];
uint32_t hp1020_pc_fixture_stats[64];
static struct hp1020_usb_document document;
static struct hp1020_usb_printer printer;
static struct { uint8_t before[16];struct hp1020_usb_document_memory data;uint8_t after[16]; } memory;
static struct hp1020_usb_document_memory retained_memory;
static struct hp1020_image_output retained_output;
static struct hp1020_rx_slot retained_slots[4];
static struct hp1020_rx_ticket transfers[8];
static struct hp1020_printer_reset_ticket resets[8];
static struct hp1020_printer_response replies[8], last_reply, owned_ep0;
static uint8_t device_id[400];
static uint32_t fill, last_request, image_bytes, reply_bytes, accepted, completed, inflight, calls;
static uint32_t violations, owned_hash[4], ep0_hash, initialization, owned_ep0_live;

static uint32_t hash(const uint8_t *data,uint32_t n) {
    uint32_t h=2166136261u;while(n--)h=(h^*data++)*16777619u;return h;
}
static enum hp1020_result progress(const struct hp1020_page_plan *plan,
    struct hp1020_image_ring *ring,void *context) {
    (void)context;calls++;
    if(plan->stride!=ring->stride || plan->rows!=ring->rows)violations++;
    struct hp1020_ring_view view;
    enum hp1020_ring_result r=hp1020_image_ring_peek(ring,&view);
    if(inflight && (inflight==3 || r!=HP1020_RING_OK)) {
        uint32_t at=ring->completion,n=ring->slots[at].rows*ring->stride;
        if(owned_hash[at]!=hash(ring->storage+at*ring->slot_bytes,n))violations++;
        if(hp1020_image_ring_complete(ring,at))return HP1020_ORDER;
        inflight--;completed++;
    } else {
        if(r!=HP1020_RING_OK)return HP1020_ORDER;
        uint32_t n=view.rows*ring->stride;
        if(n>sizeof(hp1020_pc_fixture_capture)-image_bytes)return HP1020_LIMIT;
        memcpy(hp1020_pc_fixture_capture+image_bytes,view.pixels,n);image_bytes+=n;
        owned_hash[view.index]=hash(view.pixels,n);
        if(hp1020_image_ring_accept(ring,view.index))return HP1020_ORDER;
        inflight++;accepted++;
    }
    return HP1020_OK;
}
static void check_owned(void) {
    if(printer.ep0_live!=owned_ep0_live ||
       (owned_ep0_live && (owned_ep0.request_id!=printer.ep0_request_id ||
        hash(owned_ep0.data,owned_ep0.length)!=ep0_hash)))violations++;
    for(uint32_t i=0;i<4;i++)if(document.output.ring.slots[i].state==2 &&
        owned_hash[i]!=hash(memory.data.output.slots+i*document.output.ring.slot_bytes,
                           document.output.ring.slots[i].rows*document.output.ring.stride))violations++;
}
static void snapshot(uint32_t result) {
    uint32_t *o=hp1020_pc_fixture_stats;memset(o,0,64*sizeof(*o));
    const struct hp1020_usb_receive *rx=&document.receive;check_owned();
    o[0]=result;o[1]=last_request;o[2]=printer.current_request_id;
    o[3]=printer.reset.request_id;o[4]=printer.reset.generation;o[5]=printer.reset_active;
    o[6]=printer.reset_parts;o[7]=printer.exhausted;o[8]=printer.ep0_live;o[9]=printer.ep0_request_id;
    o[10]=last_reply.kind;o[11]=last_reply.length;o[12]=last_reply.request_id;o[13]=last_reply.status_fallback;
    o[14]=hash(last_reply.data,last_reply.length);o[15]=printer.response_status;
    o[16]=rx->generation;o[17]=rx->issued;o[18]=rx->consumed;o[19]=rx->count;
    o[20]=rx->stopped;o[21]=rx->quiescent;o[22]=document.output_quiescent;o[23]=rx->error;
    o[24]=document.payload_error;o[25]=document.finished;o[26]=image_bytes;
    o[27]=hash(hp1020_pc_fixture_capture,image_bytes);o[28]=accepted;o[29]=completed;o[30]=inflight;o[31]=calls;
    o[32]=hash(memory.data.receive.data[0],sizeof(memory.data.receive.data));
    o[33]=hash(memory.data.output.slots,sizeof(memory.data.output.slots));o[34]=violations;o[35]=1;
    for(uint32_t i=0;i<16;i++)if(memory.before[i]!=fill || memory.after[i]!=fill)o[35]=0;
    o[36]=document.output.stream.parser.documents;o[37]=document.output.stream.pages;
    o[38]=document.output.pages_drained;o[39]=document.output.stream.image.pending;
    o[40]=sizeof(document)+sizeof(printer);o[41]=sizeof(memory.data);
    o[42]=reply_bytes;o[43]=hash(hp1020_pc_fixture_replies,reply_bytes);
    o[44]=printer.current_action;o[45]=printer.current_issued;o[46]=printer.initialized;
    o[47]=printer.staged_status;o[48]=printer.staged_fallback;o[49]=initialization;
    o[50]=hash(device_id,sizeof(device_id));
    for(uint32_t i=0;i<4;i++)o[51+i]=document.output.ring.slots[i].state;
}
uint32_t hp1020_pc_fixture_reset(uint32_t initial_fill,uint32_t config_fields,uint32_t invalid) {
    fill=initial_fill&255;last_request=0;image_bytes=0;reply_bytes=0;accepted=0;completed=0;inflight=0;
    calls=0;violations=0;ep0_hash=2166136261u;owned_ep0_live=0;
    memset(&memory,fill,sizeof(memory));memset(transfers,0,sizeof(transfers));memset(resets,0,sizeof(resets));
    memset(replies,0,sizeof(replies));memset(&last_reply,0,sizeof(last_reply));memset(&owned_ep0,0,sizeof(owned_ep0));
    memset(owned_hash,0,sizeof(owned_hash));memset(hp1020_pc_fixture_capture,fill,sizeof(hp1020_pc_fixture_capture));
    memset(hp1020_pc_fixture_replies,fill,sizeof(hp1020_pc_fixture_replies));
    device_id[0]=1;device_id[1]=144;
    uint8_t letter='A';
    for(uint32_t i=2;i<sizeof(device_id);i++) {
        device_id[i]=letter;
        letter=letter=='Z'?'A':(uint8_t)(letter+1);
    }
    if(invalid==2)device_id[1]=145;
    uint32_t r=hp1020_usb_document_init(&document,&memory.data,progress,0);
    if(r) { snapshot(r);return r; }
    struct hp1020_printer_config config={device_id,(uint16_t)(invalid==1?1:sizeof(device_id)),
        (uint8_t)(config_fields>>8),(uint8_t)(config_fields>>16),(uint8_t)config_fields};
    if(invalid==3)config.device_id=0;
    r=hp1020_usb_printer_init(&printer,invalid==4?0:&document,&config);
    initialization=r;snapshot(r);return r;
}

/* Fixtures cache ORIGINAL identities, never the generation at callback time.
 * Setup data and input bytes are poisoned after each call. External DMA/EP0
 * quiescence acknowledgements remain promises supplied by this test harness. */
uint32_t hp1020_pc_fixture_step(uint32_t op,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    struct hp1020_usb_receive *rx=&document.receive;uint32_t r=HP1020_PRINTER_INVALID;
    uint32_t old_generation=rx->generation,old_issued=rx->issued,old_consumed=rx->consumed,old_count=rx->count;
    int protect=op<=6 || op==12 || op==14;
    check_owned();
    if(protect) {
        memcpy(&retained_memory,&memory.data,sizeof(memory.data));
        memcpy(&retained_output,&document.output,sizeof(document.output));
        memcpy(retained_slots,rx->slots,sizeof(rx->slots));
    }
    if(op==0) {
        struct hp1020_printer_status status={(uint8_t)c,(uint8_t)(b-1)};
        r=hp1020_usb_printer_setup(&printer,hp1020_pc_fixture_input,a,b?&status:0,&last_request);
    } else if(op==1 && a<8) {
        struct hp1020_printer_response response;
        r=hp1020_usb_printer_take_response(&printer,&response);
        if(!r) {
            if(owned_ep0_live)violations++;
            owned_ep0_live=1;
            replies[a]=response;last_reply=response;owned_ep0=response;
            ep0_hash=hash(response.data,response.length);
            if(response.length>sizeof(hp1020_pc_fixture_replies)-reply_bytes)violations++;
            else { if(response.length)memcpy(hp1020_pc_fixture_replies+reply_bytes,response.data,response.length);reply_bytes+=response.length; }
        }
    } else if(op==2 && a<8)r=hp1020_usb_printer_pending_reset(&printer,&resets[a]);
    else if(op==3 && a<8)r=hp1020_usb_printer_ack_reset(&printer,resets[a],(enum hp1020_printer_reset_part)b);
    else if(op==4 && a<8) {
        r=hp1020_usb_printer_finish_reset(&printer,resets[a]);
        if(old_generation!=rx->generation)inflight=0; /* Supplied output quiescence, not a completion. */
    } else if(op==5 && a<8)r=hp1020_usb_printer_ep0_quiesced(&printer,replies[a].request_id);
    else if(op==6)r=hp1020_usb_printer_fault(&printer,a,b);
    else if(op==7 && c<8 && b<=1024 && b<=a) {
        uint8_t *buffer=0;r=hp1020_usb_receive_reserve(rx,a,&transfers[c],&buffer);
        if(!r) { memset(buffer,fill,1024);memcpy(buffer,hp1020_pc_fixture_input,b); }
    } else if(op==8 && a<8)r=hp1020_usb_receive_complete(rx,transfers[a],b,c);
    else if(op==9) {
        r=hp1020_usb_document_pump(&document);
        for(uint32_t i=old_consumed;i<rx->consumed;i++)memset(memory.data.receive.data[i%4],fill^255,1024);
    } else if(op==10)r=hp1020_usb_document_finish(&document);
    else if(op==11 && !printer.last_request_id && !rx->issued && !printer.ep0_live && !printer.reset_active && b) {
        /* Synthetic exhaustion controls, never production API behavior. */
        printer.last_request_id=a;rx->generation=b;r=HP1020_PRINTER_OK;
    } else if(op==12 && a<8) {
        resets[a].request_id=b;resets[a].generation=c;r=HP1020_PRINTER_OK;
    } else if(op==14)r=hp1020_usb_printer_ep0_quiesced(&printer,a);
    if(!r && owned_ep0_live && ((op==5 && a<8 && replies[a].request_id==owned_ep0.request_id) ||
       (op==14 && a==owned_ep0.request_id)))owned_ep0_live=0;
    (void)d;
    if(protect && old_generation==rx->generation) {
        if(memcmp(&retained_memory,&memory.data,sizeof(memory.data)) ||
           memcmp(&retained_output,&document.output,sizeof(document.output)) ||
           memcmp(retained_slots,rx->slots,sizeof(rx->slots)) ||
           old_issued!=rx->issued || old_consumed!=rx->consumed || old_count!=rx->count)violations++;
    }
    memset(hp1020_pc_fixture_input,fill^255,sizeof(hp1020_pc_fixture_input));snapshot(r);return r;
}
uint8_t *hp1020_pc_fixture_storage(void) { return memory.data.receive.data[0]; }
uint8_t *hp1020_pc_fixture_output(void) { return memory.data.output.slots; }
