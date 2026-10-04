/* SPDX-License-Identifier: GPL-2.0-or-later
 * Real two-page RAM provider; unexecuted draft, 2026-10-05. Supplied register
 * reads, device images, visibility copies and output completion are explicit
 * experiment inputs. None implements physical MMIO, DMA, cache or printing.
 */
#include "hp1020_usb_runtime_contract.h"
#include "hp1020_usb_runtime_input.h" /* sole definition of the external input */
#include "device/dcd.h"
#include <string.h>

#define SECTION(n) __attribute__((section(n), aligned(16), used))
#define P hp1020_usb_runtime_provider
#define A hp1020_usb_runtime_adapter
#define D hp1020_usb_runtime_document
#define M hp1020_usb_runtime_memory
#define E hp1020_usb_runtime_ep0
#define EM hp1020_usb_runtime_ep0_memory
#define O hp1020_usb_runtime_out
#define OM hp1020_usb_runtime_out_memory
#define W hp1020_usb_runtime_witness
#define MW(n) (hp1020_usb_runtime_mailbox.words[HP1020_USB_RUNTIME_W_##n])

struct hp1020_usb_document hp1020_usb_runtime_document SECTION(".runtime_document");
struct hp1020_usb_document_memory hp1020_usb_runtime_memory SECTION(".runtime_memory");
volatile struct hp1020_usb_runtime_mailbox_type hp1020_usb_runtime_mailbox SECTION(".runtime_mailbox");
struct hp1020_usb_runtime_witness_type hp1020_usb_runtime_witness SECTION(".runtime_witness");
#define SENTINEL_ROW 0x31,0x52,0x73,0x94,0xb5,0xd6,0xf7,0x18,0x39,0x5a,0x7b,0x9c,0xbd,0xde,0xff,0x20
uint8_t hp1020_usb_runtime_sentinel[256] SECTION(".runtime_sentinel") = {
    SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,
    SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,
    SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,
    SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW,SENTINEL_ROW
};
struct hp1020_usb_printer hp1020_usb_runtime_printer;
struct hp1020_tusb_adapter hp1020_usb_runtime_adapter;
struct hp1020_udc_out hp1020_usb_runtime_out;
struct hp1020_udc_out_memory hp1020_usb_runtime_out_memory;
struct hp1020_udc_ep0 hp1020_usb_runtime_ep0;
struct hp1020_udc_ep0_memory hp1020_usb_runtime_ep0_memory;
struct hp1020_udc_setup hp1020_usb_runtime_setup;
_Alignas(16) uint8_t hp1020_usb_runtime_setup_memory[16];
struct hp1020_udc_program hp1020_usb_runtime_program;
struct hp1020_udc_publish hp1020_usb_runtime_publisher;
struct hp1020_udc_acquire hp1020_usb_runtime_acquirer;
struct hp1020_usb_runtime_provider_type hp1020_usb_runtime_provider;

const struct hp1020_usb_runtime_supplied hp1020_usb_runtime_supplied = {
    .program_initial={1,1,1}, .program={1,1,1,1,1,1,1},
    .publish={1,1,1,1,1,1,1}, .acquire={1,1,1}, .setup={1,1,1},
    .ep0_publish={1,1,1}, .ep0_complete={1,1,1,1,0},
    .ep0_stalls_cleared=1, .receive_quiesced=1, .output_quiesced=1, .transport_reset=1
};
const uint8_t hp1020_usb_runtime_setup_record[16] = {
    0x80,0,0,0,0,0,0,0,0,9,1,0,0,0,0,0
};
static const uint8_t device_descriptor[18] = {
    18,1,0,2,0,0,0,64,0xfe,0xca,0,0x40,0,1,0,0,0,1
};
static const uint8_t configuration[32] = {
    9,2,32,0,1,1,0,0xc0,50,9,4,0,0,2,7,1,2,0,
    7,5,1,2,64,0,0,7,5,0x81,2,64,0,0
};
static const uint8_t language[4] TU_ATTR_ALIGNED(2) = {4,3,9,4};
static const uint8_t minimal_id[2] = {0,2}; /* ID content is outside this profile. */
static const uint32_t receive_dma[4] = {
    HP1020_USB_RUNTIME_RX0_DMA,HP1020_USB_RUNTIME_RX1_DMA,
    HP1020_USB_RUNTIME_RX2_DMA,HP1020_USB_RUNTIME_RX3_DMA
};
/* Supplied read inputs, independent of recorded writes. */
static const uint32_t initial_reads[9][2] = {
    {0x220,0x51},{0x22c,0x80},{0x508,0x100000c1},{0x418,0x00a700a7},
    {0x028,0x40},{0x020,0x51},{0x02c,0x80},{0x50c,0x100000d1},{0x418,0x00a500a7}
};
static const uint32_t packet_reads[5][2] = {
    {0x404,0x34120320},{0x220,0x60},{0x22c,0x40},{0x408,0xa001},{0x220,0x20}
};

static bool fail(enum hp1020_usb_runtime_error error,uint32_t detail) {
    hp1020_usb_runtime_fail(error,detail);return false;
}
static bool healthy(void) { return MW(ERROR)==0; }
static bool same(struct hp1020_tusb_cookie a,struct hp1020_tusb_cookie b) {
    return a.id==b.id && a.epoch==b.epoch && a.generation==b.generation &&
        a.sequence==b.sequence && a.endpoint==b.endpoint;
}
static uint32_t cpu(const void *p) { return (uint32_t)(uintptr_t)p; }
static unsigned slot_of(const uint8_t *p) {
    for(unsigned i=0;i<4;i++)if(p==M.receive.data[i])return i;
    return 4;
}
static void word(uint8_t *p,uint32_t v) {
    p[0]=(uint8_t)(v>>24);p[1]=(uint8_t)(v>>16);p[2]=(uint8_t)(v>>8);p[3]=(uint8_t)v;
}
static uint32_t load_word(const uint8_t *p) {
    return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3];
}
static uint32_t fnv(const void *v,uint32_t count) {
    const uint8_t *p=v;uint32_t h=UINT32_C(2166136261);
    while(count--)h=(h^*p++)*UINT32_C(16777619);
    return h;
}
static bool room(uint32_t count,uint32_t capacity) {
    if(count<capacity)return true;
    MW(BOUNDS_ERRORS)++;return fail(HP1020_USB_RUNTIME_ERROR_LIMIT,capacity);
}
static bool trace(uint32_t kind,uint32_t argument,uint32_t value,uint32_t outcome) {
    const uint32_t n=MW(IO_ROWS);
    if(!room(n,HP1020_USB_RUNTIME_IO_ROWS))return false;
    W.io[n]=(struct hp1020_usb_runtime_io_row){kind,argument,value,outcome};
    MW(IO_ROWS)=n+1;return true;
}

static enum hp1020_udc_program_io_result read32(void *context,uint32_t offset,uint32_t *value) {
    MW(READ_CALLS)++;
    const uint32_t n=P.scope_read_cursor;
    const uint32_t (*script)[2]=P.scope==0?initial_reads:packet_reads;
    const uint32_t count=P.scope==0?9u:5u;
    if(context!=&P || !healthy() || !value || P.scope>HP1020_USB_RUNTIME_BULK_PACKETS || n>=count || script[n][0]!=offset) {
        (void)trace(1,offset,0,HP1020_UDC_PROGRAM_IO_NOT_PERFORMED);
        (void)fail(HP1020_USB_RUNTIME_ERROR_READ_SCRIPT,offset);
        return HP1020_UDC_PROGRAM_IO_NOT_PERFORMED;
    }
    if(!trace(1,offset,script[n][1],HP1020_UDC_PROGRAM_IO_OK))return HP1020_UDC_PROGRAM_IO_NOT_PERFORMED;
    *value=script[n][1];P.scope_read_cursor++;P.read_cursor++;MW(READ_CURSOR)=P.read_cursor;
    return HP1020_UDC_PROGRAM_IO_OK;
}
static enum hp1020_udc_program_io_result write32(void *context,uint32_t offset,uint32_t value) {
    MW(WRITE_CALLS)++;
    return context==&P && healthy() && trace(2,offset,value,0)?
        HP1020_UDC_PROGRAM_IO_OK:HP1020_UDC_PROGRAM_IO_NOT_PERFORMED;
}
static enum hp1020_udc_program_io_result order(void *context) {
    MW(ORDER_CALLS)++;
    return context==&P && healthy() && trace(3,UINT32_MAX,0,0)?
        HP1020_UDC_PROGRAM_IO_OK:HP1020_UDC_PROGRAM_IO_NOT_PERFORMED;
}

/* The actual owner is authoritative even inside prepare_and_publish, before
 * this provider has returned from DCD and installed its own retained record. */
static bool range(void *context,struct hp1020_tusb_cookie cookie,
                  struct hp1020_udc_out_span span,uint32_t kind) {
    const struct hp1020_tusb_owner *owner=&A.owners[2];
    const unsigned slot=slot_of(owner->buffer);
    const bool descriptor=kind==5 || kind==6;
    const bool acquire=kind>=6;
    if(context!=&P || !healthy() || slot>=4 || owner->state!=HP1020_TUSB_OWNER_DCD ||
       owner->auto_status || !same(cookie,owner->cookie) || owner->cookie.endpoint!=1 || owner->length!=64 ||
       !same(O.cookie,owner->cookie) || O.buffer.cpu!=owner->buffer || O.buffer.dma!=receive_dma[slot] ||
       O.buffer.bytes!=64 || O.descriptor.cpu!=OM.descriptor ||
       O.descriptor.dma!=HP1020_USB_RUNTIME_OUT_DESCRIPTOR_DMA || O.descriptor.bytes!=16 ||
       (kind==8 ? span.cpu!=NULL || span.dma || span.bytes :
        span.cpu!=(descriptor?OM.descriptor:owner->buffer) ||
        span.dma!=(descriptor?HP1020_USB_RUNTIME_OUT_DESCRIPTOR_DMA:receive_dma[slot]) ||
        span.bytes!=(descriptor?16u:64u)))
        return fail(HP1020_USB_RUNTIME_ERROR_RANGE,kind);
    if(acquire) {
        if(P.callback_depth || A.busy || A.stack_active || A.prepared || A.delivering_live || !O.busy ||
           O.phase!=HP1020_UDC_OUT_EXPOSED || !P.bulk.live || !same(P.bulk.cookie,owner->cookie) ||
           P.bulk.original!=owner->buffer || P.bulk.requested!=64 || P.bulk.slot!=slot ||
           !P.device_valid || !same(P.image_cookie,owner->cookie) || P.image_slot!=slot)
            return fail(HP1020_USB_RUNTIME_ERROR_OWNER,kind);
    } else {
        if(P.callback_depth!=1 || !A.busy || !A.stack_active || !A.prepared ||
           O.phase!=HP1020_UDC_OUT_PREPARED || memcmp(owner->buffer,P.callback_before,64) ||
           load_word(OM.descriptor)!=UINT32_C(0x08000000) || load_word(OM.descriptor+4) ||
           load_word(OM.descriptor+8)!=receive_dma[slot] || load_word(OM.descriptor+12))
            return fail(HP1020_USB_RUNTIME_ERROR_OWNER,kind);
    }
    const uint32_t n=MW(RANGE_ROWS);
    if(!room(n,HP1020_USB_RUNTIME_RANGE_ROWS) || !trace(kind,span.dma,span.bytes,0))return false;
    const struct hp1020_tusb_cookie actual=owner->cookie;
    W.ranges[n]=(struct hp1020_usb_runtime_range_row){MW(IO_ROWS),actual.id,actual.epoch,
        actual.generation,actual.sequence,actual.endpoint,cpu(span.cpu),cpu(owner->buffer),owner->length};
    MW(RANGE_ROWS)=n+1;MW(RANGE_CHECKS)++;return true;
}
static enum hp1020_udc_program_io_result rx_before(void *c,struct hp1020_tusb_cookie k,struct hp1020_udc_out_span s) {
    MW(RX_PREPARES)++;return range(c,k,s,4)?HP1020_UDC_PROGRAM_IO_OK:HP1020_UDC_PROGRAM_IO_NOT_PERFORMED;
}
static enum hp1020_udc_program_io_result descriptor_before(void *c,struct hp1020_tusb_cookie k,struct hp1020_udc_out_span s) {
    MW(DESCRIPTOR_PREPARES)++;return range(c,k,s,5)?HP1020_UDC_PROGRAM_IO_OK:HP1020_UDC_PROGRAM_IO_NOT_PERFORMED;
}
static enum hp1020_udc_acquire_io_result descriptor_after(void *c,struct hp1020_tusb_cookie k,struct hp1020_udc_out_span s) {
    MW(DESCRIPTOR_ACQUIRES)++;
    if(!range(c,k,s,6))return HP1020_UDC_ACQUIRE_IO_NOT_PERFORMED;
    memcpy(s.cpu,W.device.descriptor,16);MW(DESCRIPTOR_COPIED)+=16;return HP1020_UDC_ACQUIRE_IO_OK;
}
static enum hp1020_udc_acquire_io_result payload_after(void *c,struct hp1020_tusb_cookie k,struct hp1020_udc_out_span s) {
    MW(PAYLOAD_ACQUIRES)++;
    if(!range(c,k,s,7))return HP1020_UDC_ACQUIRE_IO_NOT_PERFORMED;
    memcpy(s.cpu,W.device.payload,64);MW(PAYLOAD_COPIED)+=64;return HP1020_UDC_ACQUIRE_IO_OK;
}
static enum hp1020_udc_acquire_io_result acquire_order(void *c,struct hp1020_tusb_cookie k) {
    const struct hp1020_udc_out_span none={NULL,0,0};MW(ACQUIRE_ORDERS)++;
    return range(c,k,none,8)?HP1020_UDC_ACQUIRE_IO_OK:HP1020_UDC_ACQUIRE_IO_NOT_PERFORMED;
}

static void request_cancel(void *context,struct hp1020_tusb_cookie cookie) {
    struct hp1020_usb_runtime_retained *r=cookie.endpoint==1?&P.bulk:&P.ep0;
    if(context!=&P || !r->live || !same(r->cookie,cookie)) {
        MW(CALLBACK_ERRORS)++;(void)fail(HP1020_USB_RUNTIME_ERROR_OWNER,cookie.id);return;
    }
    r->cancel_requested=1;MW(CANCEL_REQUESTS)++;
    /* Record only: never call a component recursively or pretend settlement. */
    (void)fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,cookie.id);
}
static bool bind_record(struct hp1020_usb_runtime_retained *r,
                        const struct hp1020_tusb_owner *owner,unsigned slot,
                        const void *descriptor,const void *packet) {
    /* Retain the actual bound owner FIRST, even when a later check fails. */
    r->cookie=owner->cookie;r->original=owner->buffer;r->requested=owner->length;
    r->live=1;r->cancel_requested=owner->cancel_requested;r->slot=(uint8_t)slot;
    const uint32_t n=MW(BIND_ROWS);
    if(!room(n,HP1020_USB_RUNTIME_BINDS))return false;
    W.binds[n]=(struct hp1020_usb_runtime_bind_row){r->cookie.id,r->cookie.epoch,r->cookie.generation,
        r->cookie.sequence,r->cookie.endpoint,cpu(r->original),r->requested,cpu(descriptor),cpu(packet)};
    MW(BIND_ROWS)=n+1;
    if(slot==255)MW(EP0_BINDS)++;else MW(BULK_BINDS)++;
    return true;
}

bool dcd_edpt_xfer(uint8_t rhport,uint8_t endpoint,uint8_t *buffer,uint16_t length,bool is_isr) {
    const bool bulk=endpoint==1;
    const unsigned slot=bulk?slot_of(buffer):255;
    struct hp1020_usb_runtime_retained *retained=bulk?&P.bulk:&P.ep0;
    const unsigned index=bulk?2:1;
    if(rhport || is_isr || !healthy() || P.callback_depth || retained->live ||
       A.owners[index].state!=HP1020_TUSB_OWNER_NONE ||
       (bulk ? slot>=4 || length!=64 || !(P.open_mask&4u) : endpoint!=0x80 || buffer || length) ||
       !room(MW(BIND_ROWS),HP1020_USB_RUNTIME_BINDS) ||
       !hp1020_udc_publish_submission_allowed(&hp1020_usb_runtime_publisher))
        return fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,endpoint);
    P.callback_depth=1;MW(CALLBACK_DEPTH)=1;
    struct hp1020_tusb_cookie bound={0};uint32_t result;
    if(bulk) {
        memcpy(P.callback_before,buffer,64);
        result=(uint32_t)hp1020_udc_publish_prepare_and_publish(&hp1020_usb_runtime_publisher,
            rhport,endpoint,buffer,length,&bound);
    } else result=(uint32_t)hp1020_udc_ep0_prepare(&E,endpoint,buffer,length,&bound);
    bool retained_ok=false;
    if(A.owners[index].state==HP1020_TUSB_OWNER_DCD) {
        retained_ok=bind_record(retained,&A.owners[index],slot,
            bulk?(const void *)OM.descriptor:(const void *)EM.in_descriptor,
            bulk?(const void *)buffer:(const void *)EM.in_staging);
        if(!same(bound,retained->cookie) || retained->original!=buffer || retained->requested!=length)
            retained_ok=fail(HP1020_USB_RUNTIME_ERROR_OWNER,bound.id);
    }
    P.callback_depth=0;MW(CALLBACK_DEPTH)=0;
    if(result || !retained_ok)return fail(HP1020_USB_RUNTIME_ERROR_API,result);
    return healthy();
}
bool dcd_edpt_open(uint8_t rhport,const tusb_desc_endpoint_t *endpoint) {
    if(!healthy() || !endpoint || P.callback_depth)return fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,0x100);
    const uint32_t r=(uint32_t)hp1020_udc_program_open(&hp1020_usb_runtime_program,rhport,
        (const uint8_t *)(const void *)endpoint,7,hp1020_usb_runtime_supplied.program);
    if(r)return fail(HP1020_USB_RUNTIME_ERROR_API,r);
    P.open_mask|=endpoint->bEndpointAddress==1?4u:8u;MW(OPEN_MASK)=P.open_mask;return healthy();
}
const usbd_class_driver_t *usbd_app_driver_get_cb(uint8_t *count) {
    *count=1;return hp1020_tusb_adapter_driver();
}
bool usbd_app_control_route_cb(uint8_t rhport,const tusb_control_request_t *request,uint8_t *interface_number) {
    return hp1020_tusb_adapter_route(rhport,request,interface_number);
}
const uint8_t *tud_descriptor_device_cb(void) { return device_descriptor; }
const uint8_t *tud_descriptor_configuration_cb(uint8_t index) { return index?NULL:configuration; }
const uint16_t *tud_descriptor_string_cb(uint8_t index,uint16_t lang) {
    (void)lang;return index?NULL:(const uint16_t *)(const void *)language;
}
uint32_t tusb_time_millis_api(void) { return 0; }
bool dcd_init(uint8_t rhport,const tusb_rhport_init_t *config) {
    if(rhport || !config || config->role!=TUSB_ROLE_DEVICE || config->speed!=TUSB_SPEED_FULL ||
       P.open_mask || !healthy())return fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,0x101);
    P.open_mask=3;MW(OPEN_MASK)=3;return true;
}
/* Logical OSAL interrupt brackets are harmless provider no-ops. No physical
 * interrupt, connect, address or endpoint-default action is implemented. */
void dcd_int_enable(uint8_t rhport) { if(rhport)(void)fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,0x102); }
void dcd_int_disable(uint8_t rhport) { if(rhport)(void)fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,0x103); }
void dcd_connect(uint8_t rhport) { if(rhport)(void)fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,0x104); }
void dcd_sof_enable(uint8_t rhport,bool enabled) { if(rhport || enabled)(void)fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,0x105); }
static void unsupported(uint32_t detail) { MW(CALLBACK_ERRORS)++;(void)fail(HP1020_USB_RUNTIME_ERROR_CALLBACK,detail); }
bool dcd_deinit(uint8_t rhport) { (void)rhport;unsupported(0x106);return false; }
void dcd_int_handler(uint8_t rhport) { (void)rhport;unsupported(0x107); }
void dcd_disconnect(uint8_t rhport) { (void)rhport;unsupported(0x108); }
void dcd_remote_wakeup(uint8_t rhport) { (void)rhport;unsupported(0x109); }
void dcd_set_address(uint8_t rhport,uint8_t address) { (void)rhport;(void)address;unsupported(0x10a); }
void dcd_edpt_close(uint8_t rhport,uint8_t endpoint) { (void)rhport;(void)endpoint;unsupported(0x10b); }
void dcd_edpt_close_all(uint8_t rhport) { (void)rhport;unsupported(0x10c); }
void dcd_edpt_stall(uint8_t rhport,uint8_t endpoint) {
    if(!rhport && (endpoint==0 || endpoint==0x80 || endpoint==1 || endpoint==0x81)) {
        P.stall_mask|=1u<<(2u*(endpoint&15u)+(endpoint>>7));MW(STALL_MASK)=P.stall_mask;
    }
    unsupported(0x10d);
}
void dcd_edpt_clear_stall(uint8_t rhport,uint8_t endpoint) { (void)rhport;(void)endpoint;unsupported(0x10e); }
void dcd_edpt0_status_complete(uint8_t rhport,const tusb_control_request_t *request) {
    if(rhport || !request || request->bmRequestType!=0 || request->bRequest!=9 || request->wValue!=1 ||
       request->wIndex || request->wLength || P.ep0.live || MW(STATUS_CALLBACKS)) { unsupported(0x10f);return; }
    MW(STATUS_CALLBACKS)++;
}

static enum hp1020_result output(const struct hp1020_page_plan *plan,struct hp1020_image_ring *ring,void *context) {
    struct hp1020_ring_view view;
    if(context!=&P || plan!=&D.output.plan || ring!=&D.output.ring || P.callback_depth ||
       P.closing || P.finished || A.stack_active || !healthy()) {
        if(P.closing || P.finished)MW(LATE_CALLBACKS)++;
        MW(CALLBACK_ERRORS)++;(void)fail(HP1020_USB_RUNTIME_ERROR_OUTPUT,0);return HP1020_ORDER;
    }
    P.callback_depth=1;MW(CALLBACK_DEPTH)=1;
    if(!room(MW(OUTPUT_CALLBACKS),2) || hp1020_image_ring_peek(ring,&view)!=HP1020_RING_OK ||
       view.index>=4 || !view.rows || !ring->stride || ring->stride!=plan->stride ||
       ring->storage!=M.output.slots || ring->slot_bytes>HP1020_IMAGE_MAX_BAND_BYTES ||
       view.pixels!=ring->storage+view.index*ring->slot_bytes || view.first!=ring->accepted_rows ||
       view.first>ring->rows || view.rows>ring->rows-view.first ||
       MW(PIXEL_BYTES)>HP1020_USB_RUNTIME_PIXEL_BYTES ||
       view.rows>(HP1020_USB_RUNTIME_PIXEL_BYTES-MW(PIXEL_BYTES))/ring->stride)goto bad;
    const uint32_t bytes=view.rows*ring->stride;
    if(bytes>ring->slot_bytes)goto bad;
    MW(OUTPUT_CALLBACKS)++;
    if(hp1020_image_ring_accept(ring,view.index)!=HP1020_RING_OK)goto bad;
    MW(OUTPUT_ACCEPTS)++;
    memcpy(W.pixels+MW(PIXEL_BYTES),view.pixels,bytes);MW(PIXEL_BYTES)+=bytes;
    if(hp1020_image_ring_complete(ring,view.index)!=HP1020_RING_OK)goto bad;
    MW(OUTPUT_COMPLETES)++;P.callback_depth=0;MW(CALLBACK_DEPTH)=0;return HP1020_OK;
bad:
    if(P.closing || P.finished)MW(LATE_CALLBACKS)++;
    MW(CALLBACK_ERRORS)++;P.callback_depth=0;MW(CALLBACK_DEPTH)=0;
    (void)fail(HP1020_USB_RUNTIME_ERROR_OUTPUT,MW(OUTPUT_CALLBACKS));return HP1020_ORDER;
}
static enum hp1020_result document_event(const struct hp1020_usb_document_event *event,void *context) {
    const uint32_t n=MW(DOCUMENT_CALLBACKS);
    if(context!=&P || !event || P.callback_depth || P.closing || P.finished || A.stack_active ||
       !healthy() || !room(n,HP1020_USB_RUNTIME_DOCUMENT_EVENTS)) {
        if(P.closing || P.finished)MW(LATE_CALLBACKS)++;
        MW(CALLBACK_ERRORS)++;(void)fail(HP1020_USB_RUNTIME_ERROR_DOCUMENT,n);return HP1020_ORDER;
    }
    P.callback_depth=1;MW(CALLBACK_DEPTH)=1;
    W.documents[n]=(struct hp1020_usb_runtime_document_row){event->generation,event->document_id,
        event->first_page,event->pages,HP1020_OK};MW(DOCUMENT_CALLBACKS)=n+1;
    P.callback_depth=0;MW(CALLBACK_DEPTH)=0;return HP1020_OK;
}

bool hp1020_usb_runtime_ram_init(void) {
    if(!healthy() || P.initialized || MW(INITIALIZATIONS) || MW(TUSB_INITIALIZATIONS))
        return fail(HP1020_USB_RUNTIME_ERROR_API,0x200);
    /* Root has already scanned every byte and counted its INIT step. */
    uint8_t *const guards[]={W.head_guard,W.io_guard,W.range_guard,W.bind_guard,
        W.device.guard0,W.device.guard1,W.device.guard2,W.device.guard3};
    for(unsigned i=0;i<8;i++)memset(guards[i],HP1020_USB_RUNTIME_GUARD_BYTE,16);
    P.scope=UINT32_MAX;MW(INITIALIZATIONS)++;
    uint32_t r=(uint32_t)hp1020_usb_document_init_documents(&D,&M,output,&P,document_event,&P);
    const struct hp1020_printer_config pc={minimal_id,2,0,0,0};
    const struct hp1020_tusb_config config={0,1,0x81,64};
    const struct hp1020_tusb_ops ops={request_cancel,&P};
    if(!r)r=(uint32_t)hp1020_usb_printer_init(&hp1020_usb_runtime_printer,&D,&pc);
    if(!r)r=(uint32_t)hp1020_tusb_adapter_init(&A,&hp1020_usb_runtime_printer,&config,&ops);
    if(!r)r=(uint32_t)hp1020_udc_setup_init(&hp1020_usb_runtime_setup,&A,HP1020_USB_RUNTIME_SETUP_DMA);
    const struct hp1020_udc_ep0_spans spans={
        {EM.out_descriptor,HP1020_USB_RUNTIME_EP0_OUT_DESCRIPTOR_DMA,16},
        {EM.in_descriptor,HP1020_USB_RUNTIME_EP0_IN_DESCRIPTOR_DMA,16},
        {EM.out_sink,HP1020_USB_RUNTIME_EP0_OUT_PACKET_DMA,64},
        {EM.in_staging,HP1020_USB_RUNTIME_EP0_IN_PACKET_DMA,64}};
    if(!r)r=(uint32_t)hp1020_udc_ep0_init(&E,&A,&spans);
    const struct hp1020_udc_out_span desc={OM.descriptor,HP1020_USB_RUNTIME_OUT_DESCRIPTOR_DMA,16};
    if(!r)r=(uint32_t)hp1020_udc_out_init(&O,&A,desc);
    const struct hp1020_udc_program_io io={read32,write32,order,&P};
    const struct hp1020_udc_program_layout layout={0x508,0x50c,64};
    if(!r)r=(uint32_t)hp1020_udc_program_init(&hp1020_usb_runtime_program,&hp1020_usb_runtime_setup,
        &io,layout,hp1020_usb_runtime_supplied.program_initial);
    const struct hp1020_udc_publish_mapping mapping={{HP1020_USB_RUNTIME_RX0_DMA,HP1020_USB_RUNTIME_RX1_DMA,
        HP1020_USB_RUNTIME_RX2_DMA,HP1020_USB_RUNTIME_RX3_DMA}};
    const struct hp1020_udc_publish_cache cache={rx_before,descriptor_before,&P};
    if(!r)r=(uint32_t)hp1020_udc_publish_init(&hp1020_usb_runtime_publisher,&hp1020_usb_runtime_program,&O,&mapping,&cache);
    const struct hp1020_udc_acquire_hooks acquire={descriptor_after,payload_after,acquire_order,&P};
    if(!r)r=(uint32_t)hp1020_udc_acquire_init(&hp1020_usb_runtime_acquirer,&O,&acquire);
    if(r)return fail(HP1020_USB_RUNTIME_ERROR_API,r);
    const tusb_rhport_init_t usb={.role=TUSB_ROLE_DEVICE,.speed=TUSB_SPEED_FULL};
    MW(TUSB_INITIALIZATIONS)++;
    if(!tusb_init(0,&usb))return fail(HP1020_USB_RUNTIME_ERROR_API,0x201);
    P.initialized=1;return healthy();
}
bool hp1020_usb_runtime_ram_scope(uint32_t scope) {
    if(!healthy() || !P.initialized || P.callback_depth || scope>HP1020_USB_RUNTIME_BULK_PACKETS ||
       (scope==0 ? P.scope!=UINT32_MAX : P.scope!=scope-1 || P.scope_read_cursor!=(P.scope?5u:9u)) ||
       P.bulk.live || O.phase!=HP1020_UDC_OUT_FREE || A.owners[2].state!=HP1020_TUSB_OWNER_NONE)
        return fail(HP1020_USB_RUNTIME_ERROR_API,0x210|scope);
    P.scope=scope;P.packet_sequence=scope;P.scope_read_cursor=0;P.device_valid=0;return true;
}
bool hp1020_usb_runtime_ram_setup_observation(struct hp1020_udc_setup_observation *observation) {
    if(!healthy() || !P.initialized || !observation || P.scope || P.callback_depth ||
       hp1020_usb_runtime_setup.last_sequence!=1 || hp1020_usb_runtime_setup.pending_kind)
        return fail(HP1020_USB_RUNTIME_ERROR_API,0x220);
    memcpy(hp1020_usb_runtime_setup_memory,hp1020_usb_runtime_setup_record,16);
    *observation=(struct hp1020_udc_setup_observation){.sequence=2,.record_dma=HP1020_USB_RUNTIME_SETUP_DMA};
    memcpy(observation->record,hp1020_usb_runtime_setup_memory,16);return true;
}
bool hp1020_usb_runtime_ram_ep0_observation(struct hp1020_udc_ep0_observation *observation) {
    const struct hp1020_tusb_owner *owner=&A.owners[1];
    if(!healthy() || !observation || P.callback_depth || A.busy || A.stack_active ||
       !P.ep0.live || !same(P.ep0.cookie,owner->cookie) || owner->state!=HP1020_TUSB_OWNER_DCD ||
       owner->buffer || owner->length || owner->auto_status || E.slots[1].phase!=HP1020_UDC_EP0_EXPOSED ||
       !same(E.slots[1].cookie,P.ep0.cookie) || E.slots[1].descriptor.cpu!=EM.in_descriptor ||
       E.slots[1].descriptor.dma!=HP1020_USB_RUNTIME_EP0_IN_DESCRIPTOR_DMA || E.slots[1].descriptor.bytes!=16 ||
       E.slots[1].packet.cpu!=EM.in_staging || E.slots[1].packet.dma!=HP1020_USB_RUNTIME_EP0_IN_PACKET_DMA ||
       E.slots[1].packet.bytes!=64 || E.slots[1].original_buffer || E.slots[1].requested ||
       P.ep0.original || P.ep0.requested)
        return fail(HP1020_USB_RUNTIME_ERROR_OWNER,0x230);
    word(EM.in_descriptor,UINT32_C(0x8800ffff));word(EM.in_descriptor+4,0);
    word(EM.in_descriptor+8,HP1020_USB_RUNTIME_EP0_IN_PACKET_DMA);word(EM.in_descriptor+12,0);
    *observation=(struct hp1020_udc_ep0_observation){.cookie=P.ep0.cookie};
    memcpy(observation->descriptor,EM.in_descriptor,16);return true;
}
bool hp1020_usb_runtime_ram_install_bulk(struct hp1020_tusb_cookie original,uint32_t offset,uint32_t count) {
    const struct hp1020_tusb_owner *owner=&A.owners[2];
    const unsigned slot=slot_of(owner->buffer);
    if(!healthy() || !P.initialized || P.callback_depth || A.busy || A.stack_active || A.prepared || A.delivering_live ||
       O.busy || O.phase!=HP1020_UDC_OUT_EXPOSED || !P.bulk.live || !same(original,P.bulk.cookie) ||
       !same(original,owner->cookie) || !same(original,O.cookie) || owner->state!=HP1020_TUSB_OWNER_DCD ||
       owner->auto_status || slot>=4 || P.bulk.slot!=slot || P.bulk.original!=owner->buffer || P.bulk.requested!=64 ||
       owner->length!=64 || O.buffer.cpu!=owner->buffer || O.buffer.dma!=receive_dma[slot] || O.buffer.bytes!=64 ||
       O.descriptor.cpu!=OM.descriptor || O.descriptor.dma!=HP1020_USB_RUNTIME_OUT_DESCRIPTOR_DMA || O.descriptor.bytes!=16 ||
       P.scope<1 || P.scope>HP1020_USB_RUNTIME_BULK_PACKETS || P.device_valid || count>64 || offset>HP1020_USB_RUNTIME_INPUT_BYTES || count>HP1020_USB_RUNTIME_INPUT_BYTES-offset)
        return fail(HP1020_USB_RUNTIME_ERROR_OWNER,0x240);
    word(W.device.descriptor,UINT32_C(0x88000000)|count);word(W.device.descriptor+4,0);
    word(W.device.descriptor+8,receive_dma[slot]);word(W.device.descriptor+12,0);
    for(unsigned i=0;i<64;i++)W.device.payload[i]=i<count?hp1020_usb_runtime_input[offset+i]:
        (uint8_t)(0x80u|((0x69u^(slot*0x1du)^(i*7u))&0x7fu));
    P.image_cookie=original;P.image_slot=slot;P.source_offset=offset;P.source_length=count;P.device_valid=1;
    word(OM.descriptor,UINT32_C(0xc35a0000)|slot);word(OM.descriptor+4,UINT32_C(0x13579bdf));
    word(OM.descriptor+8,UINT32_C(0xfedcba90));word(OM.descriptor+12,UINT32_C(0x2468ace0));
    for(unsigned i=0;i<64;i++)owner->buffer[i]=(uint8_t)(0xd3u^(slot*0x29u)^(i*0x17u));
    MW(DEVICE_INSTALLS)++;MW(POISON_INSTALLS)++;return true;
}
bool hp1020_usb_runtime_ram_retired(struct hp1020_tusb_cookie original) {
    const bool bulk=original.endpoint==1;
    struct hp1020_usb_runtime_retained *retained=bulk?&P.bulk:&P.ep0;
    const struct hp1020_tusb_owner *owner=&A.owners[bulk?2:1];
    if(!healthy() || P.callback_depth || A.busy || A.stack_active || !retained->live ||
       (!bulk && original.endpoint!=0x80) || !same(original,retained->cookie) || !same(original,owner->cookie) ||
       owner->state!=HP1020_TUSB_OWNER_PENDING || owner->buffer!=retained->original || owner->length!=retained->requested ||
       owner->result!=XFER_RESULT_SUCCESS || owner->actual!=(bulk?P.source_length:0) ||
       (bulk?O.phase!=HP1020_UDC_OUT_FREE:E.slots[1].phase!=HP1020_UDC_EP0_FREE))
        return fail(HP1020_USB_RUNTIME_ERROR_OWNER,0x250);
    retained->live=0;return true;
}

bool hp1020_usb_runtime_ram_note(enum hp1020_usb_runtime_checkpoint checkpoint) {
    if(!healthy() || P.callback_depth || !P.initialized)return false;
    if(MW(IO_ROWS)>HP1020_USB_RUNTIME_IO_ROWS || MW(RANGE_ROWS)>HP1020_USB_RUNTIME_RANGE_ROWS ||
       MW(BIND_ROWS)>HP1020_USB_RUNTIME_BINDS)return fail(HP1020_USB_RUNTIME_ERROR_LIMIT,0x261);
    const uint32_t core_busy=usbd_edpt_busy(0,1)?1u:0u;
    if(checkpoint==HP1020_USB_RUNTIME_NOTE_BEFORE_CLOSE) {
        MW(BEFORE_CLOSE_IO)=MW(IO_ROWS);MW(BEFORE_CLOSE_PIXELS)=MW(PIXEL_BYTES);
        MW(BEFORE_CLOSE_DOCUMENTS)=MW(DOCUMENT_CALLBACKS);MW(BEFORE_CLOSE_CORE_BUSY)=core_busy;
    } else if(checkpoint==HP1020_USB_RUNTIME_NOTE_BEFORE_FINAL_SERVICE) {
        MW(AFTER_ACQUIRE_OWNER)=A.owners[2].state;MW(AFTER_ACQUIRE_COUNT)=D.receive.count;
        MW(AFTER_ACQUIRE_CONSUMED)=D.receive.consumed;MW(AFTER_ACQUIRE_OUT_PHASE)=O.phase;
        MW(BEFORE_FINAL_SERVICE_CORE_BUSY)=core_busy;
    } else if(checkpoint!=HP1020_USB_RUNTIME_NOTE_BEFORE_FINISH && checkpoint!=HP1020_USB_RUNTIME_NOTE_FINAL)
        return fail(HP1020_USB_RUNTIME_ERROR_API,0x260);
    MW(CALLBACK_DEPTH)=P.callback_depth;MW(OPEN_MASK)=P.open_mask;MW(STALL_MASK)=P.stall_mask;
    MW(READ_CURSOR)=P.read_cursor;MW(RECOVERY_ID)=P.recovery.recovery_id;MW(RECOVERY_GENERATION)=P.recovery.generation;
    MW(LAST_COOKIE_ID)=P.bulk.cookie.id;MW(LAST_COOKIE_EPOCH)=P.bulk.cookie.epoch;
    MW(LAST_COOKIE_GENERATION)=P.bulk.cookie.generation;MW(LAST_COOKIE_SEQUENCE)=P.bulk.cookie.sequence;
    MW(LAST_COOKIE_ENDPOINT)=P.bulk.cookie.endpoint;MW(LAST_SLOT)=P.bulk.slot;
    MW(RECEIVE_FNV)=fnv(M.receive.data,sizeof(M.receive.data));MW(OUTPUT_FNV)=fnv(M.output.slots,sizeof(M.output.slots));
    MW(PIXELS_FNV)=fnv(W.pixels,sizeof(W.pixels));MW(TRACE_FNV)=fnv(W.io,MW(IO_ROWS)*sizeof(W.io[0]));
    MW(RANGES_FNV)=fnv(W.ranges,MW(RANGE_ROWS)*sizeof(W.ranges[0]));MW(BINDS_FNV)=fnv(W.binds,MW(BIND_ROWS)*sizeof(W.binds[0]));
    MW(RECEIVE_GENERATION)=D.receive.generation;MW(RECEIVE_ISSUED)=D.receive.issued;MW(RECEIVE_CONSUMED)=D.receive.consumed;
    MW(RECEIVE_COUNT)=D.receive.count;MW(RECEIVE_STOPPED)=D.receive.stopped;MW(RECEIVE_QUIESCENT)=D.receive.quiescent;
    MW(RECEIVE_ERROR)=D.receive.error;MW(DOCUMENT_FINISHED)=D.finished;MW(OUTPUT_FINISHED)=D.output.finished;
    MW(OUTPUT_ERROR)=D.output.error;MW(OUTPUT_QUIESCENT)=D.output_quiescent;MW(PAYLOAD_ERROR)=D.payload_error;
    MW(PARSER_DOCUMENTS)=D.output.stream.parser.documents;MW(STREAM_PAGES)=D.output.stream.pages;
    MW(PAGES_DRAINED)=D.output.pages_drained;MW(DOCUMENTS_COMPLETED)=D.output.documents_completed;
    MW(DOCUMENT_FIRST_PAGE)=D.output.document_first_page;MW(INPUT_CLOSED)=A.input_closed;MW(FENCED)=A.fenced;
    MW(CONTROL_EPOCH)=A.control_epoch;MW(ACTIVE_CONTROL_EPOCH)=A.active_control_epoch;
    MW(TRANSPORT_EPOCH)=A.transport_epoch;MW(ACTIVE_TRANSPORT_EPOCH)=A.active_transport_epoch;
    MW(LAST_SUBMISSION_ID)=A.last_submission_id;MW(EP0_OUT_OWNER)=A.owners[0].state;
    MW(EP0_IN_OWNER)=A.owners[1].state;MW(BULK_OWNER)=A.owners[2].state;MW(OUT_PHASE)=O.phase;
    MW(BULK_CORE_BUSY)=core_busy;MW(PROGRAM_FAILED)=hp1020_usb_runtime_program.failed;
    MW(PUBLISH_FAILED)=hp1020_usb_runtime_publisher.failed;MW(ACQUIRE_FAILED)=hp1020_usb_runtime_acquirer.failure_valid;
    MW(PUBLICATION_PREFIX)=hp1020_usb_runtime_publisher.prefix;MW(ACQUISITION_PREFIX)=hp1020_usb_runtime_acquirer.last.prefix;
    return true;
}
