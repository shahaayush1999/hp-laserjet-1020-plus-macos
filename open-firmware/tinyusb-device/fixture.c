/* SPDX-License-Identifier: GPL-2.0-or-later
 * Synthetic DCD/EP0 integration fixture. No physical USB operations.
 * The upstream core is unchanged; failures remain visible in its wire output.
 */
#include "tusb.h"
#include "device/dcd.h"
#include "device/usbd_pvt.h"
#include "hp1020_usb_printer.h"
#include <string.h>

uint8_t hp1020_tusb_fixture_input[1024];
uint8_t hp1020_tusb_fixture_capture[32768];
uint32_t hp1020_tusb_fixture_stats[64];

enum { F_OK, F_WAIT, F_STALE, F_INVALID, F_LIMIT, F_FAIL };
enum { P_NONE, P_SETUP, P_BUS_RESET };

struct packet_owner {
    uint8_t *buffer;
    uint8_t saved[64];
    uint32_t token, epoch, length, live;
};
static struct packet_owner packets[16];
static struct hp1020_usb_document document;
static struct hp1020_usb_printer printer;
static struct {
    uint8_t before[16];
    struct hp1020_usb_document_memory data;
    uint8_t after[16];
} memory;
static struct hp1020_printer_response owned_reply;
static struct hp1020_printer_reset_ticket reset_ticket;
static struct hp1020_printer_status active_status, pending_status;
static tusb_control_request_t saved_class_request;
static uint8_t pending_setup[8], active_setup[8], device_id[400], config_descriptor[64];
static const uint8_t device_descriptor[18] = {
    18,1,0,2,0,0,0,64,0xfe,0xca,0,0x40,0,1,0,0,0,1
};
static const uint8_t language_descriptor[4] TU_ATTR_ALIGNED(2) = {4,3,9,4};
static struct {
    uint32_t fill, interface_number, initialized, epoch, active_epoch, pending_kind, pending_speed;
    uint32_t next_token, submissions, completions, cancellations, stale, stall_mask, violations;
    uint32_t capture_bytes, last_ep, last_length, last_token, last_epoch, last_hash;
    uint32_t setup_callbacks, data_callbacks, ack_callbacks, dummy_callbacks;
    uint32_t class_result, class_request, owned_class, owned_class_hash, owned_class_epoch;
    uint32_t deferred_epoch, deferred_pending, suppressed, finished_resets;
    uint32_t address, pending_address, address_epoch, driver_resets, open_mask;
    uint32_t decoded[5], reply_kind, reply_length, completion_result;
} s;

static uint32_t fnv(const uint8_t *p, uint32_t n) {
    uint32_t h=2166136261u;
    while(n--)h=(h^*p++)*16777619u;
    return h;
}
static uint16_t le16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));
}
static uint32_t endpoint_index(uint32_t ep) {
    if(ep>255 || (ep&0x70u) || (ep&15u)>=8)return UINT32_MAX;
    return 2*(ep&15u)+((ep>>7)&1u);
}
static uint32_t owned_mask(void) {
    uint32_t mask=0;
    for(uint32_t i=0;i<16;i++)if(packets[i].live)mask|=1u<<i;
    return mask;
}
static void check_owned(void) {
    for(uint32_t i=0;i<16;i++)if(packets[i].live && packets[i].length &&
        memcmp(packets[i].saved,packets[i].buffer,packets[i].length))s.violations++;
    if(printer.ep0_live!=s.owned_class || (s.owned_class &&
        (printer.ep0_request_id!=owned_reply.request_id ||
         fnv(owned_reply.data,owned_reply.length)!=s.owned_class_hash)))s.violations++;
}
static void release_class_reply(void) {
    if(!s.owned_class)return;
    check_owned();
    enum hp1020_printer_result r=hp1020_usb_printer_ep0_quiesced(&printer,owned_reply.request_id);
    if(r==HP1020_PRINTER_OK)s.owned_class=0;
    else s.violations++;
}
static enum hp1020_result unexpected_output(const struct hp1020_page_plan *plan,
    struct hp1020_image_ring *ring,void *context) {
    (void)plan;(void)ring;(void)context;
    s.violations++;
    return HP1020_ORDER;
}
static void suppress_deferred(void) {
    if(s.deferred_pending)s.suppressed++;
    s.deferred_pending=0;
}
static bool take_class_reply(uint8_t rhport) {
    struct hp1020_printer_response reply;
    s.class_result=hp1020_usb_printer_take_response(&printer,&reply);
    if(s.class_result!=HP1020_PRINTER_OK)return false;
    if(s.owned_class) { s.violations++;return false; }
    owned_reply=reply;s.owned_class=1;s.owned_class_epoch=s.active_epoch;
    s.owned_class_hash=fnv(reply.data,reply.length);
    s.reply_kind=reply.kind;s.reply_length=reply.length;
    if(reply.kind==HP1020_PRINTER_DATA)
        return tud_control_xfer(rhport,&saved_class_request,(void *)reply.data,reply.length);
    if(reply.kind==HP1020_PRINTER_ACK)
        return tud_control_status(rhport,&saved_class_request);
    /* Rejected requests are returned as false before taking their STALL. */
    s.violations++;
    return false;
}

static void driver_init(void) {}
static bool driver_deinit(void) { return true; }
static void printer_reset(uint8_t rhport) {
    (void)rhport;s.driver_resets++;s.open_mask=3;
    suppress_deferred();
    /* Bus reset/deconfiguration is a fence, never proof of document quiescence.
     * This baseline resumes only after a subsequent explicit class reset. */
    if(printer.initialized)
        s.class_result=hp1020_usb_printer_fault(&printer,document.receive.generation,0x80000000u);
}
static void dummy_reset(uint8_t rhport) { (void)rhport; }
static uint16_t printer_open(uint8_t rhport,const tusb_desc_interface_t *itf,uint16_t maximum) {
    if(maximum<23 || itf->bInterfaceNumber!=s.interface_number || itf->bAlternateSetting ||
        itf->bInterfaceClass!=7 || itf->bInterfaceSubClass!=1 || itf->bInterfaceProtocol!=2 ||
        itf->bNumEndpoints!=2)return 0;
    const uint8_t *p=(const uint8_t *)itf;
    if(!usbd_edpt_open(rhport,(const tusb_desc_endpoint_t *)(p+9)) ||
       !usbd_edpt_open(rhport,(const tusb_desc_endpoint_t *)(p+16)))return 0;
    return 23;
}
static uint16_t dummy_open(uint8_t rhport,const tusb_desc_interface_t *itf,uint16_t maximum) {
    (void)rhport;
    return maximum>=9 && itf->bInterfaceNumber<s.interface_number &&
        itf->bInterfaceClass==0xff && !itf->bNumEndpoints ? 9:0;
}
static bool printer_control(uint8_t rhport,uint8_t stage,const tusb_control_request_t *request) {
    /* Standard endpoint/interface requests belong to the upstream core. */
    if(request->bmRequestType_bit.type!=TUSB_REQ_TYPE_CLASS)return false;
    if(stage==CONTROL_STAGE_SETUP) {
        s.setup_callbacks++;
        s.decoded[0]=request->bmRequestType;s.decoded[1]=request->bRequest;
        s.decoded[2]=request->wValue;s.decoded[3]=request->wIndex;s.decoded[4]=request->wLength;
        if(request->bmRequestType!=active_setup[0] || request->bRequest!=active_setup[1] ||
           request->wValue!=le16(active_setup+2) || request->wIndex!=le16(active_setup+4) ||
           request->wLength!=le16(active_setup+6))s.violations++;
        saved_class_request=*request;
        /* The class accepts raw little-endian wire bytes. TinyUSB's request
         * fields have already been converted to host order; never memcpy them. */
        s.class_result=hp1020_usb_printer_setup(&printer,active_setup,8,&active_status,&s.class_request);
        if(s.class_result!=HP1020_PRINTER_OK)return false;
        if(printer.reset_active && printer.reset.request_id==s.class_request) {
            s.class_result=hp1020_usb_printer_pending_reset(&printer,&reset_ticket);
            if(s.class_result!=HP1020_PRINTER_OK)return false;
            s.deferred_epoch=s.active_epoch;s.deferred_pending=1;
            return true; /* Deliberately no EP0 status packet yet. */
        }
        return take_class_reply(rhport);
    }
    if(stage==CONTROL_STAGE_DATA) { s.data_callbacks++;return true; }
    if(stage==CONTROL_STAGE_ACK) {
        s.ack_callbacks++;
        if(!s.owned_class || s.owned_class_epoch!=s.active_epoch)s.violations++;
        else release_class_reply();
        return true;
    }
    return false;
}
static bool dummy_control(uint8_t rhport,uint8_t stage,const tusb_control_request_t *request) {
    (void)rhport;(void)stage;(void)request;s.dummy_callbacks++;
    return false;
}
static bool unexpected_bulk(uint8_t rhport,uint8_t ep,xfer_result_t result,uint32_t length) {
    (void)rhport;(void)ep;(void)result;(void)length;s.violations++;
    return false;
}
static const usbd_class_driver_t drivers[2] = {
    {.name="HP1020-fixture",.init=driver_init,.deinit=driver_deinit,.reset=printer_reset,
     .open=printer_open,.control_xfer_cb=printer_control,.xfer_cb=unexpected_bulk},
    {.name="routing-negative",.init=driver_init,.deinit=driver_deinit,.reset=dummy_reset,
     .open=dummy_open,.control_xfer_cb=dummy_control,.xfer_cb=unexpected_bulk}
};
const usbd_class_driver_t *usbd_app_driver_get_cb(uint8_t *count) { *count=2;return drivers; }
const uint8_t *tud_descriptor_device_cb(void) { return device_descriptor; }
const uint8_t *tud_descriptor_configuration_cb(uint8_t index) { return index?NULL:config_descriptor; }
const uint16_t *tud_descriptor_string_cb(uint8_t index,uint16_t langid) {
    (void)langid;return index?NULL:(const uint16_t *)(const void *)language_descriptor;
}
uint32_t tusb_time_millis_api(void) { return 0; }

/* Synthetic DCD: borrows each submitted pointer until a matching explicit
 * completion/cancellation event. It never dereferences a peripheral address. */
bool dcd_init(uint8_t rhport,const tusb_rhport_init_t *init) {
    if(rhport || !init || init->role!=TUSB_ROLE_DEVICE)return false;
    s.open_mask=3;return true;
}
bool dcd_deinit(uint8_t rhport) { (void)rhport;return true; }
void dcd_int_handler(uint8_t rhport) { (void)rhport; }
void dcd_int_enable(uint8_t rhport) { (void)rhport; }
void dcd_int_disable(uint8_t rhport) { (void)rhport; }
void dcd_connect(uint8_t rhport) { (void)rhport; }
void dcd_disconnect(uint8_t rhport) { (void)rhport; }
void dcd_remote_wakeup(uint8_t rhport) { (void)rhport; }
void dcd_sof_enable(uint8_t rhport,bool enabled) { (void)rhport;(void)enabled; }
bool dcd_edpt_open(uint8_t rhport,const tusb_desc_endpoint_t *ep) {
    uint32_t i=endpoint_index(ep->bEndpointAddress);
    if(rhport || i==UINT32_MAX)return false;
    s.open_mask|=1u<<i;return true;
}
void dcd_edpt_close(uint8_t rhport,uint8_t ep) {
    (void)rhport;uint32_t i=endpoint_index(ep);
    if(i==UINT32_MAX) { s.violations++;return; }
    check_owned();if(packets[i].live)s.violations++;
    s.open_mask&=~(1u<<i);
}
void dcd_edpt_close_all(uint8_t rhport) {
    (void)rhport;check_owned();
    for(uint32_t i=2;i<16;i++)if(packets[i].live)s.violations++;
    s.open_mask&=3;s.stall_mask&=3;
}
bool dcd_edpt_xfer(uint8_t rhport,uint8_t ep,uint8_t *buffer,uint16_t length,bool in_isr) {
    (void)in_isr;check_owned();
    uint32_t i=endpoint_index(ep);
    if(rhport || i>=2 || length>64 || (length && !buffer) || packets[i].live ||
       !s.active_epoch || s.next_token==UINT32_MAX) { s.violations++;return false; }
    struct packet_owner *p=&packets[i];
    p->buffer=buffer;p->length=length;p->epoch=s.active_epoch;p->token=++s.next_token;p->live=1;
    if(length)memcpy(p->saved,buffer,length);
    s.submissions++;s.last_ep=ep;s.last_length=length;s.last_token=p->token;s.last_epoch=p->epoch;
    s.last_hash=fnv(buffer,length);
    if(ep&0x80) {
        if(length>sizeof(hp1020_tusb_fixture_capture)-s.capture_bytes) { s.violations++;return false; }
        if(length)memcpy(hp1020_tusb_fixture_capture+s.capture_bytes,buffer,length);
        s.capture_bytes+=length;
    }
    return true;
}
void dcd_set_address(uint8_t rhport,uint8_t address) {
    s.pending_address=address;s.address_epoch=s.active_epoch;
    if(!dcd_edpt_xfer(rhport,0x80,NULL,0,false))s.violations++;
}
void dcd_edpt0_status_complete(uint8_t rhport,const tusb_control_request_t *request) {
    (void)rhport;
    if(request->bmRequestType==0 && request->bRequest==5 && s.address_epoch==s.active_epoch)
        s.address=s.pending_address;
}
void dcd_edpt_stall(uint8_t rhport,uint8_t ep) {
    (void)rhport;uint32_t i=endpoint_index(ep);
    if(i==UINT32_MAX) { s.violations++;return; }
    check_owned();if(packets[i].live)s.violations++;
    s.stall_mask|=1u<<i;
}
void dcd_edpt_clear_stall(uint8_t rhport,uint8_t ep) {
    (void)rhport;uint32_t i=endpoint_index(ep);
    if(i==UINT32_MAX) { s.violations++;return; }
    s.stall_mask&=~(1u<<i);
}

static void drain_stack(void) {
    uint32_t rounds=0;
    while(tud_task_event_ready() && rounds++<32)tud_task_ext(0,false);
    if(tud_task_event_ready())s.violations++;
}
static uint32_t dispatch_pending(void) {
    if(!s.pending_kind)return F_OK;
    if(owned_mask()&3)return F_WAIT;
    /* At this point all old DCD packet reads are settled and every old queued
     * core event was drained or rejected. Now the old class bytes may retire. */
    release_class_reply();
    uint32_t kind=s.pending_kind;s.pending_kind=P_NONE;s.active_epoch=s.epoch;
    s.address_epoch=0;s.pending_address=s.address;
    if(kind==P_SETUP) {
        memcpy(active_setup,pending_setup,8);active_status=pending_status;
        s.stall_mask&=~3u; /* The synthetic SETUP clears EP0's physical stalls. */
        dcd_event_setup_received(0,active_setup,false);
    } else {
        memset(active_setup,0,sizeof(active_setup));s.address=0;s.pending_address=0;
        s.stall_mask=0;s.open_mask=3;
        dcd_event_bus_reset(0,(tusb_speed_t)s.pending_speed,false);
    }
    drain_stack();return F_OK;
}
static void snapshot(uint32_t result) {
    uint32_t *o=hp1020_tusb_fixture_stats;memset(o,0,64*sizeof(*o));check_owned();
    o[0]=result;o[1]=s.initialized;o[2]=s.epoch;o[3]=s.pending_kind;o[4]=s.active_epoch;
    o[5]=s.submissions;o[6]=s.completions;o[7]=s.cancellations;o[8]=s.stale;
    o[9]=owned_mask();o[10]=s.stall_mask;o[11]=s.violations;o[12]=1;
    for(uint32_t i=0;i<16;i++)if(memory.before[i]!=s.fill || memory.after[i]!=s.fill)o[12]=0;
    o[13]=s.capture_bytes;o[14]=fnv(hp1020_tusb_fixture_capture,s.capture_bytes);
    o[15]=s.last_ep;o[16]=s.last_length;o[17]=s.last_token;o[18]=s.last_epoch;o[19]=s.last_hash;
    for(uint32_t i=0;i<2;i++)if(packets[i].live) {
        o[20+3*i]=packets[i].token;o[21+3*i]=packets[i].length;o[22+3*i]=packets[i].epoch;
    }
    o[26]=s.setup_callbacks;o[27]=s.data_callbacks;o[28]=s.ack_callbacks;o[29]=s.dummy_callbacks;
    o[30]=s.class_result;o[31]=s.class_request;o[32]=printer.ep0_live;o[33]=printer.ep0_request_id;
    o[34]=printer.reset_active;o[35]=printer.reset_parts;o[36]=document.receive.generation;
    o[37]=document.receive.stopped;o[38]=document.receive.quiescent;o[39]=document.output_quiescent;
    o[40]=s.deferred_epoch;o[41]=s.deferred_pending;o[42]=s.suppressed;o[43]=s.finished_resets;
    o[44]=reset_ticket.request_id;o[45]=reset_ticket.generation;o[46]=tud_mounted();
    o[47]=s.address;o[48]=s.pending_address;o[49]=s.driver_resets;o[50]=s.open_mask;
    o[51]=tud_task_event_ready();o[52]=le16(active_setup+6);o[53]=s.reply_kind;o[54]=s.reply_length;
    o[55]=sizeof(printer)+sizeof(document)+sizeof(memory.data);
    for(uint32_t i=0;i<5;i++)o[56+i]=s.decoded[i];
    o[61]=fnv((const uint8_t *)&memory.data,sizeof(memory.data));
    o[62]=s.owned_class;o[63]=s.completion_result;
}
uint32_t hp1020_tusb_fixture_reset(uint32_t fill,uint32_t interface_number,uint32_t id_length) {
    /* Destroy the previous synthetic world, not a production recovery API. */
    if(tud_inited())tusb_deinit(0);
    memset(&s,0,sizeof(s));memset(packets,0,sizeof(packets));
    memset(&document,0,sizeof(document));memset(&printer,0,sizeof(printer));
    memset(&owned_reply,0,sizeof(owned_reply));memset(&reset_ticket,0,sizeof(reset_ticket));
    memset(&saved_class_request,0,sizeof(saved_class_request));
    memset(active_setup,0,sizeof(active_setup));memset(pending_setup,0,sizeof(pending_setup));
    memset(&active_status,0,sizeof(active_status));memset(&pending_status,0,sizeof(pending_status));
    s.fill=fill&255;s.interface_number=interface_number;
    memset(&memory,s.fill,sizeof(memory));
    memset(hp1020_tusb_fixture_input,s.fill,sizeof(hp1020_tusb_fixture_input));
    memset(hp1020_tusb_fixture_capture,s.fill,sizeof(hp1020_tusb_fixture_capture));
    if((id_length!=384 && id_length!=400) || (interface_number!=0 && interface_number!=3)) {
        s.initialized=F_INVALID;snapshot(F_INVALID);return F_INVALID;
    }
    device_id[0]=(uint8_t)(id_length>>8);device_id[1]=(uint8_t)id_length;
    uint8_t letter='A';
    for(uint32_t i=2;i<sizeof(device_id);i++) { device_id[i]=letter;letter=letter=='Z'?'A':(uint8_t)(letter+1); }
    memset(config_descriptor,0,sizeof(config_descriptor));
    const uint8_t header[9]={9,2,(uint8_t)(32+9*interface_number),0,(uint8_t)(interface_number+1),1,0,0xe0,50};
    memcpy(config_descriptor,header,sizeof(header));
    uint32_t at=9;
    for(uint32_t i=0;i<interface_number;i++) {
        const uint8_t dummy[9]={9,4,(uint8_t)i,0,0,0xff,0,0,0};
        memcpy(config_descriptor+at,dummy,sizeof(dummy));at+=9;
    }
    const uint8_t real[23]={9,4,(uint8_t)interface_number,0,2,7,1,2,0,7,5,1,2,64,0,0,7,5,0x81,2,64,0,0};
    memcpy(config_descriptor+at,real,sizeof(real));
    s.initialized=hp1020_usb_document_init(&document,&memory.data,unexpected_output,NULL);
    if(!s.initialized) {
        const struct hp1020_printer_config config={device_id,(uint16_t)id_length,(uint8_t)interface_number,0,0};
        s.initialized=hp1020_usb_printer_init(&printer,&document,&config);
    }
    if(!s.initialized) {
        const tusb_rhport_init_t init={.role=TUSB_ROLE_DEVICE,.speed=TUSB_SPEED_FULL};
        if(!tusb_init(0,&init))s.initialized=F_FAIL;
    }
    snapshot(s.initialized);return s.initialized;
}
uint32_t hp1020_tusb_fixture_step(uint32_t op,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    uint32_t result=F_INVALID;check_owned();
    if(s.initialized || !tud_inited())result=F_INVALID;
    else if(op==0 || op==3) {
        if((op==0 && (a!=8 || b>1 || c>255 || d)) || (op==3 && (a!=TUSB_SPEED_FULL || b || c || d)))result=F_INVALID;
        /* A SETUP can supersede another queued SETUP, but cannot erase a bus
         * reset that is still waiting for explicit packet cancellation. */
        else if(op==0 && s.pending_kind==P_BUS_RESET)result=F_INVALID;
        else if(s.epoch==UINT32_MAX)result=F_LIMIT;
        else {
            const uint8_t *wire=hp1020_tusb_fixture_input;
            const bool soft_reset=op==0 && (wire[0]==0x21 || wire[0]==0x23) && wire[1]==2 &&
                !le16(wire+2) && le16(wire+4)==s.interface_number && !le16(wire+6);
            /* Admission fences data and invalidates previous reset promises
             * immediately, even when old EP0 ownership delays core dispatch.
             * This is an opaque synthetic reset reason, not a hardware bit or
             * a claim that any input/output memory has become quiescent. */
            if(op==3 || soft_reset)
                s.class_result=hp1020_usb_printer_fault(&printer,document.receive.generation,0x80000000u);
            s.epoch++;suppress_deferred();
            s.pending_kind=op==0?P_SETUP:P_BUS_RESET;
            if(op==0) {
                memcpy(pending_setup,hp1020_tusb_fixture_input,8);
                pending_status.known=(uint8_t)b;pending_status.value=(uint8_t)c;
            } else s.pending_speed=a;
            result=dispatch_pending();
        }
    } else if(op==1 || op==2) {
        uint32_t i=endpoint_index(a);
        if(i>=2 || (op==2 && (c || d)) || (op==1 && d>XFER_RESULT_INVALID))result=F_INVALID;
        else if(!b || !packets[i].live || packets[i].token!=b) { s.stale++;result=F_STALE; }
        else if(op==1 && c>packets[i].length)result=F_INVALID;
        else {
            const uint32_t epoch=packets[i].epoch;
            if(op==1 && !(a&0x80) && c)memcpy(packets[i].buffer,hp1020_tusb_fixture_input,c);
            packets[i].live=0;
            if(op==2) { s.cancellations++;result=F_OK; }
            else {
                s.completions++;s.completion_result=d;
                if(epoch!=s.epoch) { s.stale++;result=F_STALE; }
                else {
                    /* Current non-success results deliberately reach upstream.
                     * The raw baseline must expose its ignored EP0 result. */
                    dcd_event_xfer_complete(0,(uint8_t)a,c,(uint8_t)d,false);
                    drain_stack();result=F_OK;
                }
            }
            if(s.pending_kind)(void)dispatch_pending();
        }
    } else if(op==4 && !(a|b|c|d))result=dispatch_pending();
    else if(op==5 && !(b|c|d)) {
        s.class_result=hp1020_usb_printer_ack_reset(&printer,reset_ticket,(enum hp1020_printer_reset_part)a);
        result=s.class_result;
    } else if(op==6 && !(a|b|c|d)) {
        s.class_result=hp1020_usb_printer_finish_reset(&printer,reset_ticket);result=s.class_result;
        if(result==F_OK) {
            s.finished_resets++;
            if(s.deferred_pending && s.deferred_epoch==s.epoch && s.active_epoch==s.epoch && !s.pending_kind) {
                s.deferred_pending=0;
                if(!take_class_reply(0))result=F_FAIL;
            }
        }
    }
    memset(hp1020_tusb_fixture_input,s.fill^255,sizeof(hp1020_tusb_fixture_input));
    snapshot(result);return result;
}
