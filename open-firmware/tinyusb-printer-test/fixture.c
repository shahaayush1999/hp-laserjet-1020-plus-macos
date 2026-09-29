/* SPDX-License-Identifier: GPL-2.0-or-later
 * Synthetic DCD, borrowed-buffer ledger and pixel consumer. No device access.
 * All reset/cancellation promises are supplied by the fixture.
 */
#include "hp1020_tusb_adapter.h"
#include "device/dcd.h"
#include <string.h>

uint8_t hp1020_bulk_fixture_input[1024];
uint8_t hp1020_bulk_fixture_pixels[262144];
uint8_t hp1020_bulk_fixture_wire[32768];
uint32_t hp1020_bulk_fixture_stats[96];
uint32_t hp1020_bulk_fixture_documents[512][5];

struct packet {
    struct hp1020_tusb_cookie cookie;
    uint8_t *buffer;
    uint8_t shadow[1024];
    uint16_t length;
    uint8_t live, cancel_requested;
};
static struct packet packets[3];
static struct hp1020_tusb_cookie history[4096];
static struct hp1020_tusb_adapter adapter;
static struct hp1020_usb_document document;
static struct hp1020_usb_printer printer;
static struct {
    uint8_t before[16];
    struct hp1020_usb_document_memory data;
    uint8_t after[16];
} memory;
static struct hp1020_usb_document_memory protected_memory;
static struct hp1020_printer_reset_ticket reset_tickets[8];
static uint8_t device_id[400], configuration[64];
static const uint8_t device_descriptor[18] = {
    18,1,0,2,0,0,0,64,0xfe,0xca,0,0x40,0,1,0,0,0,1
};
static const uint8_t language_descriptor[4] TU_ATTR_ALIGNED(2) = {4,3,9,4};
static struct {
    uint32_t fill, interface_number, initialized, open_mask, stall_mask;
    uint32_t violations, submissions, completions, cancellations, stale;
    uint32_t last_id, last_ep, last_length, wire_bytes, pixel_bytes;
    uint32_t accepted, completed, inflight, calls, owned_hash[4], fail_at;
    uint32_t fail_submission, address, pending_address, address_epoch;
    uint32_t cancel_requests, dcd_writes;
    uint32_t document_calls, documents_completed, document_fail_at;
} state;

static uint32_t fnv(const uint8_t *p,uint32_t n) {
    uint32_t h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;
}
static int packet_index(uint8_t ep) {
    return ep==0?0:ep==0x80?1:ep==1?2:-1;
}
static uint32_t endpoint_bit(uint8_t ep) { return 1u<<(2*(ep&15u)+(ep>>7)); }
static uint32_t owned_mask(void) {
    uint32_t bits=0;
    for(uint32_t i=0;i<3;i++)if(packets[i].live)bits|=endpoint_bit(packets[i].cookie.endpoint);
    return bits;
}
static uint32_t cancel_mask(void) {
    uint32_t bits=0;
    for(uint32_t i=0;i<3;i++)if(packets[i].live && packets[i].cancel_requested)
        bits|=endpoint_bit(packets[i].cookie.endpoint);
    return bits;
}
static int same_cookie(struct hp1020_tusb_cookie a,struct hp1020_tusb_cookie b) {
    return a.id==b.id && a.epoch==b.epoch && a.generation==b.generation &&
        a.sequence==b.sequence && a.endpoint==b.endpoint;
}
static void check_owned(void) {
    for(uint32_t i=0;i<3;i++)if(packets[i].live && packets[i].length &&
        memcmp(packets[i].shadow,packets[i].buffer,packets[i].length))state.violations++;
    for(uint32_t i=0;i<4;i++)if(document.output.ring.slots[i].state==2 &&
        state.owned_hash[i]!=fnv(memory.data.output.slots+i*document.output.ring.slot_bytes,
            document.output.ring.slots[i].rows*document.output.ring.stride))state.violations++;
}
static void request_cancel(void *context,struct hp1020_tusb_cookie cookie) {
    (void)context;
    int i=packet_index(cookie.endpoint);
    if(i<0 || !packets[i].live || !same_cookie(packets[i].cookie,cookie)) {
        state.violations++;return;
    }
    if(!packets[i].cancel_requested)state.cancel_requests++;
    packets[i].cancel_requested=1; /* A request does not settle ownership. */
}
static enum hp1020_result document_complete(const struct hp1020_usb_document_event *event,void *context) {
    (void)context;
    if(adapter.stack_active || state.document_calls>=512) { state.violations++;return HP1020_LIMIT; }
    const enum hp1020_result result=state.document_calls>=state.document_fail_at?HP1020_ORDER:HP1020_OK;
    uint32_t *record=hp1020_bulk_fixture_documents[state.document_calls++];
    record[0]=event->generation;record[1]=event->document_id;
    record[2]=event->first_page;record[3]=event->pages;record[4]=(uint32_t)result;
    if(!result)state.documents_completed++;
    return result;
}
static enum hp1020_result progress(const struct hp1020_page_plan *plan,
    struct hp1020_image_ring *ring,void *context) {
    (void)context;state.calls++;
    if(adapter.stack_active)state.violations++; /* Decode/output stays outside TinyUSB callbacks. */
    if(plan->stride!=ring->stride || plan->rows!=ring->rows)state.violations++;
    if(state.calls>state.fail_at)return HP1020_ORDER;
    struct hp1020_ring_view view;
    enum hp1020_ring_result result=hp1020_image_ring_peek(ring,&view);
    if(state.inflight && (state.inflight==3 || result!=HP1020_RING_OK)) {
        uint32_t at=ring->completion,n=ring->slots[at].rows*ring->stride;
        if(state.owned_hash[at]!=fnv(ring->storage+at*ring->slot_bytes,n))state.violations++;
        if(hp1020_image_ring_complete(ring,at))return HP1020_ORDER;
        state.inflight--;state.completed++;
    } else {
        if(result!=HP1020_RING_OK)return HP1020_ORDER;
        uint32_t n=view.rows*ring->stride;
        if(n>sizeof(hp1020_bulk_fixture_pixels)-state.pixel_bytes)return HP1020_LIMIT;
        memcpy(hp1020_bulk_fixture_pixels+state.pixel_bytes,view.pixels,n);state.pixel_bytes+=n;
        state.owned_hash[view.index]=fnv(view.pixels,n);
        if(hp1020_image_ring_accept(ring,view.index))return HP1020_ORDER;
        state.inflight++;state.accepted++;
    }
    return HP1020_OK;
}

/* A second driver supplies empty vendor interfaces so the printer can also be
 * exercised at a nonzero interface number without changing its class logic. */
static void dummy_init(void) {}
static bool dummy_deinit(void) { return true; }
static void dummy_reset(uint8_t rhport) { (void)rhport; }
static uint16_t dummy_open(uint8_t rhport,const tusb_desc_interface_t *itf,uint16_t maximum) {
    (void)rhport;
    return maximum>=9 && itf->bInterfaceNumber<state.interface_number &&
        itf->bInterfaceClass==0xff && !itf->bNumEndpoints?9:0;
}
static bool dummy_control(uint8_t rhport,uint8_t stage,const tusb_control_request_t *request) {
    (void)rhport;(void)stage;(void)request;return false;
}
static bool dummy_xfer(uint8_t rhport,uint8_t endpoint,xfer_result_t result,uint32_t count) {
    (void)rhport;(void)endpoint;(void)result;(void)count;state.violations++;return false;
}
const usbd_class_driver_t *usbd_app_driver_get_cb(uint8_t *count) {
    static usbd_class_driver_t drivers[2];
    drivers[0]=*hp1020_tusb_adapter_driver();
    const usbd_class_driver_t dummy={.name="empty-interface",.init=dummy_init,.deinit=dummy_deinit,
        .reset=dummy_reset,.open=dummy_open,.control_xfer_cb=dummy_control,.xfer_cb=dummy_xfer};
    drivers[1]=dummy;*count=2;return drivers;
}
bool usbd_app_control_route_cb(uint8_t rhport,const tusb_control_request_t *request,uint8_t *interface_number) {
    return hp1020_tusb_adapter_route(rhport,request,interface_number);
}
const uint8_t *tud_descriptor_device_cb(void) { return device_descriptor; }
const uint8_t *tud_descriptor_configuration_cb(uint8_t index) { return index?NULL:configuration; }
const uint16_t *tud_descriptor_string_cb(uint8_t index,uint16_t language) {
    (void)language;return index?NULL:(const uint16_t *)(const void *)language_descriptor;
}
uint32_t tusb_time_millis_api(void) { return 0; }

bool dcd_init(uint8_t rhport,const tusb_rhport_init_t *config) {
    if(rhport || !config || config->role!=TUSB_ROLE_DEVICE)return false;
    state.open_mask=3;return true;
}
bool dcd_deinit(uint8_t rhport) { (void)rhport;return true; }
void dcd_int_handler(uint8_t rhport) { (void)rhport; }
void dcd_int_enable(uint8_t rhport) { (void)rhport; }
void dcd_int_disable(uint8_t rhport) { (void)rhport; }
void dcd_connect(uint8_t rhport) { (void)rhport; }
void dcd_disconnect(uint8_t rhport) { (void)rhport; }
void dcd_remote_wakeup(uint8_t rhport) { (void)rhport; }
void dcd_sof_enable(uint8_t rhport,bool enabled) { (void)rhport;(void)enabled; }
bool dcd_edpt_open(uint8_t rhport,const tusb_desc_endpoint_t *endpoint) {
    if(rhport || (endpoint->bEndpointAddress!=1 && endpoint->bEndpointAddress!=0x81) ||
        endpoint->bmAttributes.xfer!=TUSB_XFER_BULK || tu_le16toh(endpoint->wMaxPacketSize)!=64)return false;
    state.open_mask|=endpoint_bit(endpoint->bEndpointAddress);return true;
}
void dcd_edpt_close(uint8_t rhport,uint8_t endpoint) {
    (void)rhport;check_owned();
    int i=packet_index(endpoint);
    if(i>=0 && packets[i].live)state.violations++;
    state.open_mask&=~endpoint_bit(endpoint);
}
void dcd_edpt_close_all(uint8_t rhport) {
    (void)rhport;check_owned();if(packets[2].live)state.violations++;
    state.open_mask&=3;state.stall_mask&=3;
}
bool dcd_edpt_xfer(uint8_t rhport,uint8_t endpoint,uint8_t *buffer,uint16_t length,bool in_isr) {
    (void)in_isr;check_owned();
    int i=packet_index(endpoint);
    if(rhport || i<0 || length>1024 || (length && !buffer) || packets[i].live ||
        !(state.open_mask&endpoint_bit(endpoint))) { state.violations++;return false; }
    uint32_t fail=state.fail_submission;state.fail_submission=0;
    if(fail==1)return false; /* Rejected before acquiring any ownership. */
    struct hp1020_tusb_cookie cookie;
    if(hp1020_tusb_adapter_bind_submission(&adapter,endpoint,buffer,length,&cookie)!=HP1020_TUSB_OK)return false;
    if(!cookie.id || cookie.id>=4096) { state.violations++;return false; }
    history[cookie.id]=cookie;
    struct packet *p=&packets[i];
    p->cookie=cookie;p->buffer=buffer;p->length=length;p->live=1;p->cancel_requested=0;
    if(length)memcpy(p->shadow,buffer,length);
    state.submissions++;state.last_id=cookie.id;state.last_ep=endpoint;state.last_length=length;
    if(endpoint&0x80) {
        if(length>sizeof(hp1020_bulk_fixture_wire)-state.wire_bytes) { state.violations++;return false; }
        if(length)memcpy(hp1020_bulk_fixture_wire+state.wire_bytes,buffer,length);
        state.wire_bytes+=length;
    }
    return fail!=2; /* Accepted but failed: ownership still needs explicit settlement. */
}
void dcd_set_address(uint8_t rhport,uint8_t address) {
    state.pending_address=address;state.address_epoch=adapter.active_control_epoch;
    if(!dcd_edpt_xfer(rhport,0x80,NULL,0,false))state.violations++;
}
void dcd_edpt0_status_complete(uint8_t rhport,const tusb_control_request_t *request) {
    (void)rhport;
    if(request->bmRequestType==0 && request->bRequest==5 &&
        state.address_epoch==adapter.active_control_epoch)state.address=state.pending_address;
}
void dcd_edpt_stall(uint8_t rhport,uint8_t endpoint) {
    (void)rhport;state.stall_mask|=endpoint_bit(endpoint);
}
void dcd_edpt_clear_stall(uint8_t rhport,uint8_t endpoint) {
    (void)rhport;state.stall_mask&=~endpoint_bit(endpoint);
}

static void snapshot(uint32_t result) {
    check_owned();
    uint32_t *o=hp1020_bulk_fixture_stats;memset(o,0,96*sizeof(*o));
    const struct hp1020_usb_receive *rx=&document.receive;
    o[0]=result;o[1]=state.initialized;o[2]=adapter.control_epoch;o[3]=adapter.active_control_epoch;
    o[4]=adapter.transport_epoch;o[5]=adapter.active_transport_epoch;o[6]=adapter.pending_kind;
    o[7]=adapter.fenced;o[8]=adapter.opened;o[9]=adapter.input_closed;o[10]=tud_mounted();
    o[11]=state.stall_mask;o[12]=state.open_mask;o[13]=owned_mask();o[14]=cancel_mask();
    o[15]=state.violations;o[16]=1;
    for(uint32_t i=0;i<16;i++)if(memory.before[i]!=state.fill || memory.after[i]!=state.fill)o[16]=0;
    o[17]=state.submissions;o[18]=state.completions;o[19]=state.cancellations;o[20]=state.stale;
    o[21]=state.last_id;o[22]=state.last_ep;o[23]=state.last_length;o[24]=state.wire_bytes;
    o[25]=fnv(hp1020_bulk_fixture_wire,state.wire_bytes);
    for(uint32_t i=0;i<3;i++)if(packets[i].live) { o[26+2*i]=packets[i].cookie.id;o[27+2*i]=packets[i].length; }
    o[32]=rx->generation;o[33]=rx->issued;o[34]=rx->consumed;o[35]=rx->count;
    o[36]=rx->stopped;o[37]=rx->quiescent;o[38]=rx->error;o[39]=document.payload_error;
    o[40]=document.finished;o[41]=document.output_quiescent;
    o[42]=printer.reset.recovery_id;o[43]=printer.reset.generation;o[44]=printer.reset_active;
    o[45]=printer.reset_parts;o[46]=printer.ep0_live;o[47]=adapter.deferred;
    o[48]=adapter.last_class_result;o[49]=adapter.last_receive_result;
    o[50]=state.pixel_bytes;o[51]=fnv(hp1020_bulk_fixture_pixels,state.pixel_bytes);
    o[52]=state.accepted;o[53]=state.completed;o[54]=state.inflight;o[55]=state.calls;
    o[56]=document.output.stream.parser.documents;o[57]=document.output.stream.pages;o[58]=document.output.pages_drained;
    o[59]=sizeof(document)+sizeof(printer)+sizeof(adapter)+sizeof(memory.data);
    o[60]=fnv(memory.data.receive.data[0],sizeof(memory.data.receive.data));
    o[61]=fnv(memory.data.output.slots,sizeof(memory.data.output.slots));
    o[62]=state.fail_submission;o[63]=tud_task_event_ready();o[64]=state.address;o[65]=state.pending_address;
    o[66]=state.cancel_requests;o[67]=state.dcd_writes;
    for(uint32_t i=0;i<4;i++) { o[69+i]=rx->slots[i].ready;o[73+i]=document.output.ring.slots[i].state; }
    o[77]=adapter.response_owned;o[78]=adapter.response.kind;o[79]=adapter.response.length;o[80]=adapter.class_request_id;
    o[81]=usbd_edpt_busy(0,1);o[82]=usbd_edpt_stalled(0,1);
    o[83]=usbd_edpt_busy(0,0x81);o[84]=usbd_edpt_stalled(0,0x81);
    o[85]=adapter.prepared;o[86]=adapter.exhausted;
    o[90]=state.document_calls;o[91]=state.documents_completed;o[92]=document.output.documents_completed;
    o[93]=state.document_calls?hp1020_bulk_fixture_documents[state.document_calls-1][0]:0;
    o[94]=state.document_fail_at;o[95]=state.document_calls?hp1020_bulk_fixture_documents[state.document_calls-1][1]:0;
    if(state.last_id) { o[87]=history[state.last_id].epoch;o[88]=history[state.last_id].generation;o[89]=history[state.last_id].sequence; }
}

uint32_t hp1020_bulk_fixture_reset(uint32_t fill,uint32_t capacity,uint32_t interface_number,uint32_t fail_at) {
    /* A fresh process/ELF load is required, matching the adapter's first-use contract. */
    memset(&state,0,sizeof(state));state.fill=fill&255;state.interface_number=interface_number;state.fail_at=fail_at;state.document_fail_at=UINT32_MAX;
    memset(&memory,state.fill,sizeof(memory));memset(hp1020_bulk_fixture_pixels,state.fill,sizeof(hp1020_bulk_fixture_pixels));
    memset(hp1020_bulk_fixture_wire,state.fill,sizeof(hp1020_bulk_fixture_wire));
    device_id[0]=1;device_id[1]=144;
    uint8_t letter='A';
    for(uint32_t i=2;i<sizeof(device_id);i++) {
        device_id[i]=letter;letter=letter=='Z'?'A':(uint8_t)(letter+1);
    }
    if(interface_number>3)return HP1020_TUSB_INVALID;
    uint32_t total=32+9*interface_number;
    const uint8_t prefix[9]={9,2,(uint8_t)total,0,(uint8_t)(interface_number+1),1,0,0xc0,50};
    memcpy(configuration,prefix,9);
    for(uint32_t i=0;i<interface_number;i++) {
        const uint8_t empty[9]={9,4,(uint8_t)i,0,0,0xff,0,0,0};memcpy(configuration+9+9*i,empty,9);
    }
    const uint8_t printer_interface[23]={9,4,(uint8_t)interface_number,0,2,7,1,2,0,
        7,5,1,2,64,0,0,7,5,0x81,2,64,0,0};
    memcpy(configuration+9+9*interface_number,printer_interface,23);
    uint32_t r=hp1020_usb_document_init_documents(&document,&memory.data,progress,NULL,document_complete,NULL);
    const struct hp1020_printer_config pc={device_id,sizeof(device_id),(uint8_t)interface_number,0,0};
    if(!r)r=hp1020_usb_printer_init(&printer,&document,&pc);
    const struct hp1020_tusb_config ac={0,1,0x81,(uint16_t)capacity};
    const struct hp1020_tusb_ops ops={request_cancel,NULL};
    if(!r)r=hp1020_tusb_adapter_init(&adapter,&printer,&ac,&ops);
    const tusb_rhport_init_t usb={.role=TUSB_ROLE_DEVICE,.speed=TUSB_SPEED_FULL};
    if(!r && !tusb_init(0,&usb))r=HP1020_TUSB_ERROR;
    state.initialized=r;snapshot(r);return r;
}

uint32_t hp1020_bulk_fixture_step(uint32_t op,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    uint32_t r=HP1020_TUSB_INVALID,old_generation=document.receive.generation;
    check_owned();
    int protect=op!=3 && op!=7 && op!=9;
    if(protect)memcpy(&protected_memory,&memory.data,sizeof(memory.data));
    if(op==0) {
        const struct hp1020_printer_status status={(uint8_t)c,(uint8_t)b};
        r=hp1020_tusb_adapter_setup(&adapter,hp1020_bulk_fixture_input,a,&status);
        if(!r)state.stall_mask&=~3u; /* Synthetic SETUP clears hardware EP0 stalls. */
    } else if(op==1)r=hp1020_tusb_adapter_service(&adapter);
    else if(op==2 && a>0 && a<4096 && history[a].id==a) {
        struct hp1020_tusb_cookie cookie=history[a];int i=packet_index(cookie.endpoint);
        if(i>=0 && packets[i].live && same_cookie(packets[i].cookie,cookie) && b<=XFER_RESULT_ABORTED && c<=packets[i].length) {
            packets[i].live=0;state.completions++;
        } else state.stale++;
        r=hp1020_tusb_adapter_complete(&adapter,cookie,(xfer_result_t)b,c);
    } else if(op==3 && a>0 && a<4096 && history[a].id==a) {
        int i=packet_index(history[a].endpoint);
        if(i>=0 && !(history[a].endpoint&0x80) && packets[i].live &&
            same_cookie(packets[i].cookie,history[a]) && b<=1024 && c<=packets[i].length && b<=packets[i].length-c) {
            if(b) { memcpy(packets[i].buffer+c,hp1020_bulk_fixture_input,b);memcpy(packets[i].shadow+c,hp1020_bulk_fixture_input,b); }
            state.dcd_writes++;r=HP1020_TUSB_OK;
        }
    } else if(op==4 && a>0 && a<4096 && history[a].id==a) {
        struct hp1020_tusb_cookie cookie=history[a];int i=packet_index(cookie.endpoint);
        if(i>=0 && packets[i].live && same_cookie(packets[i].cookie,cookie)) {
            packets[i].live=0;state.cancellations++;
        } else state.stale++;
        r=hp1020_tusb_adapter_cancelled(&adapter,cookie);
    } else if(op==5)r=hp1020_tusb_adapter_bus_reset(&adapter,(tusb_speed_t)a);
    else if(op==6)r=hp1020_tusb_adapter_arm_out(&adapter);
    else if(op==7)r=hp1020_tusb_adapter_pump(&adapter);
    else if(op==8)r=hp1020_tusb_adapter_close_input(&adapter);
    else if(op==9)r=hp1020_tusb_adapter_finish(&adapter);
    else if(op==10 && a<8)r=hp1020_tusb_adapter_pending_reset(&adapter,&reset_tickets[a]);
    else if(op==11 && a<8)r=hp1020_tusb_adapter_ack_reset(&adapter,reset_tickets[a],(enum hp1020_printer_reset_part)b);
    else if(op==12 && a<8) {
        r=hp1020_tusb_adapter_finish_reset(&adapter,reset_tickets[a]);
        if(old_generation!=document.receive.generation)state.inflight=0;
    } else if(op==13 && a>0 && a<4096 && history[a].id==a)
        r=hp1020_tusb_adapter_fault(&adapter,history[a].epoch,history[a].generation,b);
    else if(op==14 && a<=2) { state.fail_submission=a;r=HP1020_TUSB_OK; }
    else if(op==15) {
        /* Synthetic controller promise: no reads/writes remain; clear the two
         * software endpoint states too. This is not a controller implementation. */
        if(packets[2].live)r=HP1020_TUSB_WAIT;
        else { usbd_edpt_clear_stall(0,1);usbd_edpt_clear_stall(0,0x81);r=HP1020_TUSB_OK; }
    } else if(op==16) { state.fail_at=a;r=HP1020_TUSB_OK; }
    else if(op==17) { state.document_fail_at=a;r=HP1020_TUSB_OK; }
    else if(op==18 && !document.receive.issued && !document.output.active && !state.document_calls) {
        /* Synthetic counter saturation only; no production restart/repair API. */
        document.output.stream.parser.documents=a;
        document.output.documents_completed=a;r=HP1020_TUSB_OK;
    }
    (void)d;
    if(protect && old_generation==document.receive.generation &&
        memcmp(&protected_memory,&memory.data,sizeof(memory.data)))state.violations++;
    memset(hp1020_bulk_fixture_input,state.fill^255,sizeof(hp1020_bulk_fixture_input));
    snapshot(r);return r;
}
uint8_t *hp1020_bulk_fixture_receive_storage(void) { return memory.data.receive.data[0]; }
uint8_t *hp1020_bulk_fixture_output_storage(void) { return memory.data.output.slots; }
