/* SPDX-License-Identifier: GPL-2.0-or-later
 * Reuse the synthetic USB setup, then route real DCD IN1 through the new port.
 * The implementation is included so the existing target builder can exercise
 * this narrow composition without another duplicated build script.
 */
#define dcd_edpt_xfer fixture_base_xfer
#include "../tinyusb-printer-test/bulk-in-check.c"
#undef dcd_edpt_xfer
#include "hp1020_udc_in.c"

static struct hp1020_udc_in port;
static struct {
    _Alignas(16) uint8_t before[16];
    struct hp1020_udc_in_memory data;
    uint8_t after[16];
} in_memory;
static uint8_t descriptor_before[16],packet_before[64];

bool dcd_edpt_xfer(uint8_t rhport,uint8_t endpoint,uint8_t *buffer,uint16_t length,bool in_isr) {
    if(endpoint!=0x81)return fixture_base_xfer(rhport,endpoint,buffer,length,in_isr);
    if(rhport || packets[3].live || !(state.open_mask&endpoint_bit(endpoint))) {
        state.violations++;return false;
    }
    uint32_t fail=state.fail_submission;state.fail_submission=0;
    if(fail==1)return false;
    struct hp1020_tusb_cookie c;
    if(hp1020_udc_in_prepare(&port,endpoint,buffer,length,&c))return false;
    if(!c.id || c.id>=4096) { state.violations++;return false; }
    history[c.id]=c;
    packets[3]=(struct packet){.cookie=c,.buffer=buffer,.length=length,.live=1};
    if(length)memcpy(packets[3].shadow,buffer,length);
    state.submissions++;state.last_id=c.id;state.last_ep=endpoint;state.last_length=length;
    return fail!=2;
}
static uint32_t in_send(uint16_t n,struct hp1020_tusb_cookie *cookie) {
    CHECK(hp1020_tusb_adapter_send_in(&adapter,n?reply:NULL,n,cookie)==HP1020_TUSB_OK);
    CHECK(cookie->id && port.phase==HP1020_UDC_IN_PREPARED && same(port.cookie,*cookie));
    /* Independent one-descriptor oracle. DMA address is explicitly supplied,
     * not derived from the host pointer or stock's numeric alias addition. */
    uint8_t descriptor[16]={0x08,0,0,(uint8_t)n,0,0,0,0,0x30,0x40,0,0,0,0,0,0};
    CHECK(!memcmp(in_memory.data.descriptor,descriptor,16));
    CHECK(!memcmp(in_memory.data.packet,expected,n));
    for(uint32_t i=n;i<64;i++)CHECK(in_memory.data.packet[i]==(uint8_t)state.fill);
    memcpy(descriptor_before,in_memory.data.descriptor,16);
    memcpy(packet_before,in_memory.data.packet,64);
    return 0;
}
static uint32_t publish_in(struct hp1020_tusb_cookie c) {
    struct hp1020_udc_in_submission proposal;
    struct hp1020_udc_in_publish_facts facts={1,1,1};
    CHECK(hp1020_udc_in_take_submission(&port,c,facts,&proposal)==HP1020_UDC_IN_OK);
    CHECK(same(proposal.cookie,c) && proposal.original==port.original && proposal.length==port.length);
    CHECK(proposal.descriptor.cpu==in_memory.data.descriptor && proposal.descriptor.dma==0x30400100);
    CHECK(proposal.packet.cpu==in_memory.data.packet && proposal.packet.dma==0x30400000 && proposal.packet.bytes==64);
    CHECK(hp1020_udc_in_take_submission(&port,c,facts,&proposal)==HP1020_UDC_IN_WAIT);
    CHECK(!memcmp(proposal.packet.cpu,expected,proposal.length));return 0;
}
static struct hp1020_udc_in_observation observation(struct hp1020_tusb_cookie c) {
    /* Supplied immutable DMA_DONE record; low bits deliberately differ from
     * the requested count to ensure they never manufacture actual length. */
    struct hp1020_udc_in_observation o={.cookie=c};
    const uint8_t raw[16]={0x88,0,0x5a,0xa5,0,0,0,0,0x30,0x40,0,0,0,0,0,0};
    memcpy(o.descriptor,raw,16);return o;
}
static uint32_t observe_success(struct hp1020_tusb_cookie c,uint32_t n,uint8_t current_result) {
    struct hp1020_udc_in_observation o=observation(c);
    CHECK(hp1020_udc_in_observe(&port,&o,(struct hp1020_udc_in_completion_facts){1,1,1,n})==HP1020_UDC_IN_OK);
    packets[3].live=0;state.completions++;
    CHECK(hp1020_tusb_adapter_take_in_result(&adapter,&(struct hp1020_tusb_in_result){0})==HP1020_TUSB_WAIT);
    TRY(service());TRY(take(c,XFER_RESULT_SUCCESS,n,current_result));return 0;
}
static uint32_t cancel_in(struct hp1020_tusb_cookie c) {
    CHECK(hp1020_udc_in_request_cancel(&port,c)==HP1020_UDC_IN_OK);
    CHECK(hp1020_udc_in_cancelled(&port,c,0)==HP1020_UDC_IN_WAIT);
    CHECK(hp1020_udc_in_cancelled(&port,c,1)==HP1020_UDC_IN_OK);
    packets[3].live=0;state.cancellations++;
    TRY(service());TRY(take(c,XFER_RESULT_ABORTED,0,0));return 0;
}
uint32_t hp1020_udc_in_check(uint32_t scenario,uint32_t fill) {
    TRY(start(fill));memset(&in_memory,fill,sizeof(in_memory));
    struct hp1020_udc_in_span d={in_memory.data.descriptor,0x30400100,16};
    struct hp1020_udc_in_span p={in_memory.data.packet,0x30400000,64};
    CHECK(hp1020_udc_in_init(&port,&adapter,d,d)==HP1020_UDC_IN_INVALID);
    CHECK(hp1020_udc_in_init(&port,&adapter,d,p)==HP1020_UDC_IN_OK);
    struct hp1020_tusb_cookie c={0};
    struct hp1020_udc_in_submission proposal;
    struct hp1020_udc_in_publish_facts ready={1,1,1};
    const uint8_t soft_reset[8]={0x21,2,0,0,0,0,0,0};
    if(scenario<=2) {
        uint16_t n=scenario==0?0:scenario==1?32:64;
        TRY(in_send(n,&c));
        for(unsigned i=0;i<3;i++) {
            struct hp1020_udc_in_publish_facts f={i!=0,i!=1,i!=2};
            CHECK(hp1020_udc_in_take_submission(&port,c,f,&proposal)==HP1020_UDC_IN_WAIT);
        }
        TRY(publish_in(c));struct hp1020_udc_in_observation o=observation(c);
        for(unsigned i=0;i<3;i++) {
            struct hp1020_udc_in_completion_facts f={i!=0,i!=1,i!=2,n};
            CHECK(hp1020_udc_in_observe(&port,&o,f)==HP1020_UDC_IN_WAIT);
            CHECK(packets[3].live && usbd_edpt_busy(0,0x81));
        }
        TRY(observe_success(c,n,1));
        CHECK(hp1020_udc_in_observe(&port,&o,(struct hp1020_udc_in_completion_facts){1,1,1,n})==HP1020_UDC_IN_STALE);
    } else if(scenario==3 || scenario==4) {
        TRY(in_send(32,&c));
        if(scenario==4)TRY(publish_in(c));
        TRY(setup(soft_reset));
        /* Even before the queued cancellation is forwarded, a stale prepared
         * packet must not yield a new publication proposal. */
        CHECK(hp1020_udc_in_take_submission(&port,c,ready,&proposal)==HP1020_UDC_IN_WAIT);
        TRY(cancel_in(c));TRY(recover());
        memset(in_memory.data.packet,fill,64);
        struct hp1020_tusb_cookie next;TRY(in_send(32,&next));TRY(publish_in(next));
        struct hp1020_udc_in_observation old=observation(c);
        CHECK(hp1020_udc_in_observe(&port,&old,(struct hp1020_udc_in_completion_facts){1,1,1,32})==HP1020_UDC_IN_STALE);
        TRY(observe_success(next,32,1));
    } else if(scenario==5 || scenario==6) {
        TRY(in_send(32,&c));TRY(publish_in(c));
        struct hp1020_udc_in_observation o=observation(c);
        if(scenario==5)o.descriptor[8]^=1;
        CHECK(hp1020_udc_in_observe(&port,&o,(struct hp1020_udc_in_completion_facts){1,1,1,scenario==6?31:32})==HP1020_UDC_IN_FAULT);
        CHECK(port.phase==HP1020_UDC_IN_EXPOSED && packets[3].live && packets[3].cancel_requested);
        TRY(cancel_in(c));
    } else if(scenario==7) {
        state.fail_submission=2;
        CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,32,&c)==HP1020_TUSB_ERROR && c.id);
        CHECK(port.phase==HP1020_UDC_IN_PREPARED && packets[3].cancel_requested);
        memcpy(descriptor_before,in_memory.data.descriptor,16);memcpy(packet_before,in_memory.data.packet,64);
        CHECK(hp1020_udc_in_take_submission(&port,c,ready,&proposal)==HP1020_UDC_IN_WAIT);
        TRY(cancel_in(c));
    } else if(scenario==8) {
        TRY(in_send(32,&c));TRY(publish_in(c));TRY(setup(soft_reset));
        CHECK(packets[3].cancel_requested);
        TRY(observe_success(c,32,0));TRY(recover());
    } else return __LINE__;
    CHECK(!memcmp(in_memory.data.descriptor,descriptor_before,16));
    CHECK(!memcmp(in_memory.data.packet,packet_before,64));
    for(unsigned i=0;i<16;i++)CHECK(in_memory.before[i]==fill && in_memory.after[i]==fill);
    CHECK(!memcmp(reply,expected,64) && reply[64]==0xa7 && !state.violations);
    return 0;
}
