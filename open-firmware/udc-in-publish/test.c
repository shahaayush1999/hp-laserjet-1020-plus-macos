/* SPDX-License-Identifier: GPL-2.0-or-later
 * Real adapter/DCD/descriptor path; immutable supplied register observations.
 * A recorded write never changes a subsequent read or proves hardware state.
 */
#include "../udc-in/test.c"
#include "hp1020_udc_in_publish.c"

enum { READ_OP=1, WRITE_OP, ORDER_OP, VISIBLE_OP };
struct operation { uint32_t kind,offset,value; };
static const struct operation nak_trace[]={
    {READ_OP,0x404,0x22c},{READ_OP,0x20,0x60},{READ_OP,0x2c,64},
    {READ_OP,0x28,16},{READ_OP,0x418,0xa5a7a5a7},{READ_OP,0x408,0x8000},
    {VISIBLE_OP,0x30400000,64},{VISIBLE_OP,0x30400100,16},{ORDER_OP,0,0},
    {WRITE_OP,0x34,0x30400100},{ORDER_OP,0,0},{WRITE_OP,0x418,0xa5a7a5a5},
    {ORDER_OP,0,0},{WRITE_OP,0x20,0x120},{ORDER_OP,0,0},
    {READ_OP,0x20,0x20},{WRITE_OP,0x20,0x28},{ORDER_OP,0,0}
};
static const struct operation clear_trace[]={
    {READ_OP,0x404,0x228},{READ_OP,0x20,0x20},{READ_OP,0x2c,64},
    {READ_OP,0x28,16},{READ_OP,0x418,0xa5a7a5a7},
    {VISIBLE_OP,0x30400000,64},{VISIBLE_OP,0x30400100,16},{ORDER_OP,0,0},
    {WRITE_OP,0x34,0x30400100},{ORDER_OP,0,0},{WRITE_OP,0x418,0xa5a7a5a5},
    {ORDER_OP,0,0},{WRITE_OP,0x20,0x28},{ORDER_OP,0,0}
};
static struct hp1020_udc_in_publish publisher;
static struct {
    const struct operation *expected;
    uint32_t count,cursor,fail_at,changed_at,changed_value;
    struct hp1020_tusb_cookie cookie;
    bool ready;
} io_state;
static const struct hp1020_udc_in_publish_facts_ext all_facts={1,1,1,1,1};

static bool record(uint32_t kind,uint32_t offset,uint32_t value,uint32_t *read_value) {
    if(io_state.cursor>=io_state.count) { state.violations++;return false; }
    uint32_t i=io_state.cursor++;
    const struct operation *e=&io_state.expected[i];
    if(e->kind!=kind || e->offset!=offset || (kind!=READ_OP && e->value!=value)) {
        state.violations++;return false;
    }
    if(i==io_state.fail_at)return false;
    if(read_value)*read_value=i==io_state.changed_at?io_state.changed_value:e->value;
    return true;
}
static bool pub_ready(void *context,struct hp1020_tusb_cookie c) {
    if(context!=&io_state || !same(c,io_state.cookie)) { state.violations++;return false; }
    return io_state.ready;
}
static bool pub_read(void *context,uint32_t offset,uint32_t *value) {
    if(context!=&io_state)return false;
    return record(READ_OP,offset,0,value);
}
static bool pub_write(void *context,uint32_t offset,uint32_t value) {
    if(context!=&io_state)return false;
    return record(WRITE_OP,offset,value,NULL);
}
static bool pub_order(void *context) {
    if(context!=&io_state)return false;
    return record(ORDER_OP,0,0,NULL);
}
static bool pub_visible(void *context,struct hp1020_udc_in_span s) {
    if(context!=&io_state)return false;
    if(s.cpu!=(s.bytes==16?in_memory.data.descriptor:in_memory.data.packet) ||
        memcmp(in_memory.data.descriptor,descriptor_before,16) ||
        memcmp(in_memory.data.packet,packet_before,64)) { state.violations++;return false; }
    return record(VISIBLE_OP,s.dma,s.bytes,NULL);
}
static void trace(struct hp1020_tusb_cookie c,bool nak) {
    io_state=(__typeof__(io_state)){
        .expected=nak?nak_trace:clear_trace,.count=nak?18:14,
        .fail_at=UINT32_MAX,.changed_at=UINT32_MAX,.cookie=c,.ready=true};
}
static uint32_t publish_success(struct hp1020_tusb_cookie c,bool nak) {
    trace(c,nak);
    CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_OK);
    CHECK(io_state.cursor==io_state.count && !publisher.failed && port.phase==HP1020_UDC_IN_EXPOSED);
    CHECK(packets[3].live && usbd_edpt_busy(0,0x81));
    CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_WAIT);
    CHECK(io_state.cursor==io_state.count);return 0;
}
uint32_t hp1020_udc_in_publish_check(uint32_t scenario,uint32_t fill) {
    TRY(start(fill));memset(&in_memory,fill,sizeof(in_memory));
    CHECK(hp1020_udc_in_init(&port,&adapter,
        (struct hp1020_udc_in_span){in_memory.data.descriptor,0x30400100,16},
        (struct hp1020_udc_in_span){in_memory.data.packet,0x30400000,64})==HP1020_UDC_IN_OK);
    struct hp1020_udc_in_publish_io io={pub_ready,pub_read,pub_write,pub_order,pub_visible,&io_state};
    CHECK(hp1020_udc_in_publish_init(&publisher,&port,&io)==HP1020_IN_PUBLISH_OK);
    struct hp1020_tusb_cookie c;
    uint16_t length=scenario==0?64:scenario==2?0:32;
    TRY(in_send(length,&c));trace(c,true);
    if(scenario<=2) {
        TRY(publish_success(c,scenario!=0));TRY(observe_success(c,length,1));
    } else if(scenario==3) {
        for(unsigned i=0;i<5;i++) {
            struct hp1020_udc_in_publish_facts_ext f={i!=0,i!=1,i!=2,i!=3,i!=4};
            trace(c,true);
            CHECK(hp1020_udc_in_publish_packet(&publisher,c,f)==HP1020_IN_PUBLISH_WAIT);
            CHECK(io_state.cursor==(i==4?5u:0u) && port.phase==HP1020_UDC_IN_PREPARED);
        }
        TRY(publish_success(c,true));TRY(observe_success(c,length,1));
    } else if(scenario==4) {
        static const uint32_t refused[][2]={{0,0x220},{0,0x23c},{0,0x26c},{0,0x122c},
            {0,0x422c},{1,0x28},{1,0x61},{2,63},{3,15},{5,0}};
        for(unsigned i=0;i<sizeof(refused)/sizeof(refused[0]);i++) {
            trace(c,true);io_state.changed_at=refused[i][0];io_state.changed_value=refused[i][1];
            CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_WAIT);
            CHECK(io_state.cursor==io_state.changed_at+1 && !publisher.failed);
        }
        TRY(publish_success(c,true));TRY(observe_success(c,length,1));
    } else if(scenario>=5 && scenario<=17) {
        /* Every mutating-hook prefix and the post-CNAK read, including an
         * uncertain POLL write/order. No failed attempt is ever replayed. */
        if(scenario==5) { io_state.changed_at=15;io_state.changed_value=0x60; }
        else io_state.fail_at=scenario; /* indices6..17 in immutable trace */
        CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_FAULT);
        CHECK(publisher.failed && same(publisher.failure_cookie,c));
        CHECK(io_state.cursor==(scenario==5?16:scenario+1));
        CHECK(packets[3].live && packets[3].cancel_requested && port.cancel_requested);
        uint32_t cursor=io_state.cursor;
        CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_FAULT);
        CHECK(io_state.cursor==cursor);
        struct hp1020_tusb_cookie wrong=c;wrong.id++;
        CHECK(hp1020_udc_in_publish_clear(&publisher,wrong,1)==HP1020_IN_PUBLISH_STALE);
        CHECK(hp1020_udc_in_publish_clear(&publisher,c,1)==HP1020_IN_PUBLISH_WAIT);
        TRY(cancel_in(c));
        CHECK(hp1020_udc_in_publish_clear(&publisher,c,0)==HP1020_IN_PUBLISH_WAIT);
        CHECK(hp1020_udc_in_publish_clear(&publisher,c,1)==HP1020_IN_PUBLISH_OK);
        const uint8_t reset[8]={0x21,2,0,0,0,0,0,0};TRY(setup(reset));TRY(recover());
        memset(in_memory.data.packet,fill,64);
        TRY(in_send(32,&c));TRY(publish_success(c,true));TRY(observe_success(c,32,1));
    } else if(scenario==18) {
        for(unsigned i=0;i<6;i++) {
            trace(c,true);io_state.fail_at=i;
            CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_READ_ERROR);
            CHECK(io_state.cursor==i+1 && !publisher.failed && port.phase==HP1020_UDC_IN_PREPARED);
        }
        TRY(publish_success(c,true));TRY(observe_success(c,length,1));
    } else if(scenario==19) {
        io_state.ready=false;
        CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_WAIT && !io_state.cursor);
        TRY(publish_success(c,true));TRY(observe_success(c,length,1));
    } else if(scenario==20) {
        struct hp1020_tusb_cookie wrong=c;wrong.id++;
        CHECK(hp1020_udc_in_publish_packet(&publisher,wrong,all_facts)==HP1020_IN_PUBLISH_STALE);
        const uint8_t reset[8]={0x21,2,0,0,0,0,0,0};TRY(setup(reset));
        CHECK(hp1020_udc_in_publish_packet(&publisher,c,all_facts)==HP1020_IN_PUBLISH_WAIT && !io_state.cursor);
        TRY(cancel_in(c));TRY(recover());
    } else if(scenario==21) {
        TRY(publish_success(c,true));TRY(observe_success(c,length,1));
        memset(in_memory.data.packet,fill,64);TRY(in_send(64,&c));trace(c,false);
        struct hp1020_udc_in_publish_facts_ext f=all_facts;f.tx_idle_fifo_empty=0;
        CHECK(hp1020_udc_in_publish_packet(&publisher,c,f)==HP1020_IN_PUBLISH_WAIT && !io_state.cursor);
        TRY(publish_success(c,false));TRY(observe_success(c,64,1));
    } else return __LINE__;
    CHECK(!memcmp(in_memory.data.descriptor,descriptor_before,16));
    CHECK(!memcmp(in_memory.data.packet,packet_before,64));
    CHECK(!memcmp(reply,expected,64) && reply[64]==0xa7 && !state.violations);
    for(unsigned i=0;i<16;i++)CHECK(in_memory.before[i]==fill && in_memory.after[i]==fill);
    return 0;
}
