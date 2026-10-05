/* SPDX-License-Identifier: GPL-2.0-or-later
 * One existing RAM-only controller fixture, now with both directions and PJL.
 * Register values, cache leases and physical settlements are supplied inputs.
 */
#include "hp1020_usb_service.h"

static struct hp1020_usb_service coordinator;
static struct hp1020_udc_in in_port;
static struct hp1020_udc_in_publish in_publisher;
static struct hp1020_pjl_command commands;
static uint32_t service_progress(const struct hp1020_udc_publish *);
static enum hp1020_udc_publish_result service_control(struct hp1020_udc_publish *);
static bool service_submission(struct hp1020_udc_publish *);
static enum hp1020_udc_publish_result service_arm(struct hp1020_udc_publish *,
    struct hp1020_udc_publish_facts);
static bool service_in_xfer(uint8_t,uint8_t,uint8_t *,uint16_t,bool);
static enum hp1020_udc_program_result service_selection(struct hp1020_udc_program *,
    struct hp1020_udc_program_facts);
static enum hp1020_udc_program_result service_grant(struct hp1020_udc_program *,uint32_t,
    struct hp1020_tusb_cookie,struct hp1020_udc_program_grant_facts);

/* Redirect only the old fixture's platform calls. The production modules are
 * separately compiled, so their own internal calls retain their real names. */
#define hp1020_udc_publish_progress service_progress
#define hp1020_udc_publish_service service_control
#define hp1020_udc_publish_submission_allowed service_submission
#define hp1020_udc_publish_arm_out service_arm
#define hp1020_udc_program_complete_selection service_selection
#define hp1020_udc_program_grant service_grant
#define HP1020_COMPOSED_BULK_IN_XFER service_in_xfer
#include "../udc-publish-test/fixture.c"
#undef hp1020_udc_publish_progress
#undef hp1020_udc_publish_service
#undef hp1020_udc_publish_submission_allowed
#undef hp1020_udc_publish_arm_out
#undef hp1020_udc_program_complete_selection
#undef hp1020_udc_program_grant

#define CHECK(x) do { if(!(x))return __LINE__; } while(0)
#define TRY(x) do { uint32_t failure=(x);if(failure)return failure; } while(0)
uint8_t hp1020_service_job[4096];
uint8_t hp1020_service_reply[64];
uint32_t hp1020_service_reply_length;
static struct hp1020_udc_in_memory in_memory;
static uint32_t status_reads;
static const struct hp1020_udc_in_publish_facts_ext in_facts={1,1,1,1,1};
static const uint8_t echo[]="@PJL ECHO COMBINED\r\n";
static const uint8_t echo_reply[]="@PJL ECHO COMBINED\r\n\f";
static const uint8_t status_query[]="@PJL INFO STATUS\r\n";
static const uint8_t status_reply[]="@PJL INFO STATUS\r\nCODE=10001\r\nDISPLAY=\"\"\r\nONLINE=TRUE\r\n\f";

static uint32_t service_progress(const struct hp1020_udc_publish *p) {
    return p==coordinator.out?hp1020_usb_service_progress(&coordinator):0;
}
static enum hp1020_udc_publish_result service_control(struct hp1020_udc_publish *p) {
    return p==coordinator.out?hp1020_usb_service_control(&coordinator):HP1020_UDC_PUBLISH_INVALID;
}
static bool service_submission(struct hp1020_udc_publish *p) {
    return p==coordinator.out && hp1020_usb_service_submission_allowed(&coordinator);
}
static enum hp1020_udc_publish_result service_arm(struct hp1020_udc_publish *p,
    struct hp1020_udc_publish_facts facts) {
    return p==coordinator.out?hp1020_usb_service_arm_out(&coordinator,facts):HP1020_UDC_PUBLISH_INVALID;
}
static enum hp1020_udc_program_result service_selection(struct hp1020_udc_program *p,
    struct hp1020_udc_program_facts facts) {
    if(p!=&program || !hp1020_usb_service_program_allowed(&coordinator))return HP1020_UDC_PROGRAM_WAIT;
    return hp1020_udc_program_complete_selection(p,facts);
}
static enum hp1020_udc_program_result service_grant(struct hp1020_udc_program *p,uint32_t sequence,
    struct hp1020_tusb_cookie cookie,struct hp1020_udc_program_grant_facts facts) {
    if(p!=&program || !hp1020_usb_service_program_allowed(&coordinator))return HP1020_UDC_PROGRAM_WAIT;
    return hp1020_udc_program_grant(p,sequence,cookie,facts);
}
static bool service_in_xfer(uint8_t rhport,uint8_t endpoint,uint8_t *buffer,uint16_t length,bool in_isr) {
    (void)in_isr;
    if(rhport || endpoint!=0x81 || packets[3].live || !hp1020_usb_service_submission_allowed(&coordinator))return false;
    struct hp1020_tusb_cookie cookie;
    if(hp1020_udc_in_prepare(&in_port,endpoint,buffer,length,&cookie)!=HP1020_UDC_IN_OK)return false;
    if(!cookie.id || cookie.id>=4096) { state.violations++;return false; }
    history[cookie.id]=cookie;
    packets[3]=(struct packet){.cookie=cookie,.buffer=buffer,.length=length,.live=1};
    if(length)memcpy(packets[3].shadow,buffer,length);
    state.submissions++;state.last_id=cookie.id;state.last_ep=endpoint;state.last_length=length;
    return true;
}
static bool status_read(void *context,uint32_t epoch,uint32_t generation,struct hp1020_pjl_status *value) {
    if(context!=&status_reads) { state.violations++;return false; }
    status_reads++;*value=(struct hp1020_pjl_status){epoch,generation,10001,1};return true;
}

/* Short no-CNAK IN trace. Writes do not generate subsequent observations. */
static const uint32_t in_trace[][3]={
    {1,0x404,0x228},{1,0x20,0x20},{1,0x2c,64},{1,0x28,16},{1,0x418,0xa5a7a5a7},
    {4,0x30400000,64},{4,0x30400100,16},{3,0,0},{2,0x34,0x30400100},
    {3,0,0},{2,0x418,0xa5a7a5a5},{3,0,0},{2,0x20,0x28},{3,0,0}
};
static struct { uint32_t at,fail,ready_calls; } in_io;
static bool in_record(void *context,uint32_t kind,uint32_t offset,uint32_t value,uint32_t *read_value) {
    if(context!=&in_io || in_io.at>=sizeof(in_trace)/sizeof(in_trace[0])) { state.violations++;return false; }
    uint32_t at=in_io.at++;const uint32_t *expected=in_trace[at];
    if(expected[0]!=kind || expected[1]!=offset || (kind!=1 && expected[2]!=value)) { state.violations++;return false; }
    if(at==in_io.fail)return false;
    if(read_value)*read_value=expected[2];
    return true;
}
static bool in_ready(void *context,struct hp1020_tusb_cookie cookie) {
    if(context!=&in_io)return false;
    in_io.ready_calls++;
    return hp1020_usb_service_in_ready(&coordinator,cookie);
}
static bool in_read(void *c,uint32_t o,uint32_t *v) { return in_record(c,1,o,0,v); }
static bool in_write(void *c,uint32_t o,uint32_t v) { return in_record(c,2,o,v,NULL); }
static bool in_order(void *c) { return in_record(c,3,0,0,NULL); }
static bool in_visible(void *c,struct hp1020_udc_in_span span) {
    if(span.cpu!=(span.bytes==16?in_memory.descriptor:in_memory.packet)) { state.violations++;return false; }
    return in_record(c,4,span.dma,span.bytes,NULL);
}
static void in_trace_start(uint32_t fail) { in_io=(__typeof__(in_io)){.fail=fail}; }
static uint32_t reads(const uint32_t words[][2],uint32_t count) {
    CHECK(count<=85);
    for(uint32_t i=0;i<count;i++) {
        composed_put32(hp1020_bulk_fixture_input+12*i,words[i][0]);
        composed_put32(hp1020_bulk_fixture_input+12*i+4,words[i][1]);
        composed_put32(hp1020_bulk_fixture_input+12*i+8,0);
    }
    CHECK(hp1020_bulk_fixture_step(120,count,0,0,0)==HP1020_UDC_PROGRAM_OK);return 0;
}
static uint32_t control(void) {
    CHECK(hp1020_bulk_fixture_step(1,0,0,0,0)==HP1020_UDC_PUBLISH_OK);return 0;
}
static uint32_t fresh(uint32_t fill) {
    CHECK(hp1020_bulk_fixture_reset(fill,64,0,UINT32_MAX)==HP1020_TUSB_OK);
    memset(&in_memory,fill,sizeof(in_memory));
    CHECK(hp1020_udc_in_init(&in_port,&adapter,
        (struct hp1020_udc_in_span){in_memory.descriptor,0x30400100,16},
        (struct hp1020_udc_in_span){in_memory.packet,0x30400000,64})==HP1020_UDC_IN_OK);
    const struct hp1020_udc_in_publish_io io={in_ready,in_read,in_write,in_order,in_visible,&in_io};
    CHECK(hp1020_udc_in_publish_init(&in_publisher,&in_port,&io)==HP1020_IN_PUBLISH_OK);
    CHECK(hp1020_pjl_command_init(&commands,&adapter,status_read,&status_reads)==HP1020_RX_OK);
    CHECK(hp1020_usb_service_init(&coordinator,&publisher,&in_publisher,&commands));
    CHECK(!hp1020_usb_service_init(&coordinator,&publisher,&in_publisher,&commands));
    CHECK(hp1020_bulk_fixture_step(83,1,TUSB_SPEED_FULL,0,0)==HP1020_UDC_SETUP_OK);
    TRY(control());return 0;
}
static uint32_t offer_configuration(void) {
    CHECK(hp1020_bulk_fixture_step(100,2,1,0x10000,0)==HP1020_UDC_SETUP_OK);
    CHECK(hp1020_bulk_fixture_step(101,2,0x01010101,0,0)==HP1020_UDC_SETUP_OK);return 0;
}
static const uint32_t configuration_reads[][2]={
    {0x220,0x51},{0x22c,128},{0x508,0x100000c1},{0x418,0xa700a7},
    {0x28,64},{0x20,0x51},{0x2c,128},{0x50c,0x100000d1},{0x418,0xa500a7}
};
static uint32_t recover_document(void) {
    CHECK(hp1020_bulk_fixture_step(10,0,0,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(11,0,1,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(11,0,2,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(15,0,0,0,0)==HP1020_TUSB_OK);
    CHECK(hp1020_bulk_fixture_step(11,0,4,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(12,0,0,0,0)==HP1020_PRINTER_OK);return 0;
}
static uint32_t grant(uint32_t sequence) {
    static const uint32_t grant_read[][2]={{0x404,0x34120320}};
    TRY(reads(grant_read,1));memset(hp1020_bulk_fixture_input,1,5);
    CHECK(hp1020_bulk_fixture_step(124,sequence,packets[1].cookie.id,0,0)==HP1020_UDC_PROGRAM_OK);return 0;
}
static uint32_t configured(uint32_t fill) {
    TRY(fresh(fill));TRY(offer_configuration());TRY(reads(configuration_reads,9));TRY(control());
    CHECK(program.binding_ready && hp1020_usb_service_progress(&coordinator)==7);
    TRY(grant(2));TRY(recover_document());return 0;
}
static const uint32_t out_reads[][2]={{0x404,0xa55a0228},{0x220,0x20},{0x22c,64},{0x408,0xa001}};
static uint32_t input(const uint8_t *data,uint32_t count) {
    CHECK(count<=64);TRY(reads(out_reads,4));
    CHECK(hp1020_bulk_fixture_step(6,0,0,0,0)==HP1020_UDC_PUBLISH_OK);
    uint32_t id=packets[2].cookie.id;
    memcpy(hp1020_bulk_fixture_input,data,count);
    CHECK(hp1020_bulk_fixture_step(65,id,1,0,count)==HP1020_UDC_OUT_OK);
    memcpy(hp1020_bulk_fixture_input,composed_out_memory.descriptor,16);
    composed_put32(hp1020_bulk_fixture_input,0x88000000u|count);
    CHECK(hp1020_bulk_fixture_step(62,id,0x010101,0,0)==HP1020_UDC_OUT_OK);
    TRY(control());return 0;
}
static uint32_t pump(void) {
    enum hp1020_rx_result r=hp1020_usb_service_pump(&coordinator);
    CHECK(r==HP1020_RX_OK || r==HP1020_RX_WAIT);return 0;
}
static uint32_t publish_reply(const uint8_t *wanted,uint32_t count) {
    CHECK(commands.inflight && commands.reply_length==count && count<64);
    CHECK(!memcmp(commands.reply,wanted,count) && !memcmp(in_memory.packet,wanted,count));
    memcpy(hp1020_service_reply,in_memory.packet,count);hp1020_service_reply_length=count;
    in_trace_start(UINT32_MAX);
    CHECK(hp1020_usb_service_publish_in(&coordinator,commands.in_cookie,in_facts)==HP1020_IN_PUBLISH_OK);
    CHECK(in_io.at==14 && in_io.ready_calls==1 && in_port.phase==HP1020_UDC_IN_EXPOSED);return 0;
}
static uint32_t reply_done(void) {
    struct hp1020_udc_in_observation o={.cookie=commands.in_cookie};
    memcpy(o.descriptor,in_memory.descriptor,16);composed_put32(o.descriptor,0x88005aa5);
    CHECK(hp1020_udc_in_observe(&in_port,&o,
        (struct hp1020_udc_in_completion_facts){1,1,1,commands.reply_length})==HP1020_UDC_IN_OK);
    packets[3].live=0;state.completions++;TRY(control());return 0;
}
static uint32_t reply(const uint8_t *wanted,uint32_t count) {
    TRY(publish_reply(wanted,count));TRY(reply_done());TRY(pump());return 0;
}
static uint32_t check_blocked(struct hp1020_tusb_cookie cookie) {
    uint32_t submitted=state.submissions,read_count=status_reads,offset=commands.offset;
    uint32_t hooks=program_state.trace_count,in_hooks=in_io.at;
    CHECK(!hp1020_usb_service_progress(&coordinator));
    CHECK(!hp1020_usb_service_submission_allowed(&coordinator));
    CHECK(!hp1020_usb_service_in_ready(&coordinator,cookie));
    CHECK(hp1020_usb_service_control(&coordinator)==HP1020_UDC_PUBLISH_WAIT);
    CHECK(hp1020_usb_service_arm_out(&coordinator,publish_facts())==HP1020_UDC_PUBLISH_WAIT);
    CHECK(hp1020_usb_service_publish_in(&coordinator,cookie,in_facts)==HP1020_IN_PUBLISH_WAIT);
    CHECK(hp1020_usb_service_pump(&coordinator)==HP1020_RX_WAIT);
    CHECK(state.submissions==submitted && status_reads==read_count && commands.offset==offset);
    CHECK(program_state.trace_count==hooks && in_io.at==in_hooks);return 0;
}
static uint32_t reset_drain(void) {
    CHECK(hp1020_bulk_fixture_step(83,4,TUSB_SPEED_FULL,0,0)==HP1020_UDC_SETUP_OK);
    CHECK(hp1020_usb_service_progress(&coordinator)==HP1020_UDC_SETUP_ALLOW_SERVICE);
    CHECK(!hp1020_usb_service_submission_allowed(&coordinator));
    if(packets[1].live)CHECK(hp1020_bulk_fixture_step(103,packets[1].cookie.id,1,0,0)==HP1020_TUSB_OK);
    if(packets[2].live)CHECK(hp1020_bulk_fixture_step(64,packets[2].cookie.id,1,0,0)==HP1020_UDC_OUT_OK);
    TRY(control());return 0;
}
uint32_t hp1020_usb_service_check(uint32_t scenario,uint32_t fill,uint32_t job_length) {
    if(scenario==4) {
        TRY(fresh(fill));TRY(offer_configuration());TRY(reads(configuration_reads,9));
        CHECK(hp1020_bulk_fixture_step(121,2,2,HP1020_UDC_PROGRAM_IO_UNKNOWN,0)==HP1020_UDC_PROGRAM_OK);
        CHECK(hp1020_bulk_fixture_step(1,0,0,0,0)==HP1020_UDC_PUBLISH_FAULT);
        CHECK(program.failed && !publisher.failed && !in_publisher.failed);
        TRY(check_blocked((struct hp1020_tusb_cookie){0}));
        TRY(reset_drain());CHECK(program.failed);return state.violations?__LINE__:0;
    }
    TRY(configured(fill));
    if(scenario==0) {
        TRY(input(echo,sizeof(echo)-1));TRY(pump());TRY(reply(echo_reply,sizeof(echo_reply)-1));
        TRY(input(status_query,sizeof(status_query)-1));TRY(pump());TRY(reply(status_reply,sizeof(status_reply)-1));
        CHECK(status_reads==1 && job_length && job_length<=sizeof(hp1020_service_job));
        for(uint32_t at=0;at<job_length;) {
            uint32_t n=job_length-at;if(n>64)n=64;
            TRY(input(hp1020_service_job+at,n));TRY(pump());at+=n;
        }
        CHECK(document.output.documents_completed==1 && document.output.pages_drained==2 && state.pixel_bytes==128);
        CHECK(!commands.inflight && !document.receive.count);
    } else if(scenario==1 || scenario==2) {
        TRY(input(echo,sizeof(echo)-1));TRY(pump());
        if(scenario==2) { TRY(publish_reply(echo_reply,sizeof(echo_reply)-1));TRY(reply_done()); }
        TRY(input(status_query,sizeof(status_query)-1));
        CHECK(hp1020_bulk_fixture_step(100,3,2,0x10000,0)==HP1020_UDC_SETUP_OK);
        CHECK(document.receive.count==1 && !status_reads);
        TRY(check_blocked(commands.in_cookie));
        CHECK(commands.inflight==(scenario==1));
        CHECK(document.receive.count==1 && !status_reads && !commands.have_input);
    } else if(scenario==3 || scenario==7) {
        TRY(input(echo,sizeof(echo)-1));TRY(pump());
        const struct hp1020_tusb_cookie cookie=commands.in_cookie;
        in_trace_start(12); /* Uncertain actual POLL command. */
        CHECK(hp1020_usb_service_publish_in(&coordinator,cookie,in_facts)==HP1020_IN_PUBLISH_FAULT);
        CHECK(in_publisher.failed && !publisher.failed && packets[3].cancel_requested);
        CHECK(!hp1020_usb_service_program_allowed(&coordinator));
        TRY(check_blocked(cookie));
        if(scenario==7) {
            /* Gate-only mutation: distinguish unready-binding SERVICE from an
             * admitted inactive actual reset. No hardware claim uses it. */
            program.binding_ready=0;
            CHECK(hp1020_udc_program_progress(&program)==HP1020_UDC_SETUP_ALLOW_SERVICE);
            CHECK(hp1020_udc_setup_progress(&composed_setup)==7);
            TRY(check_blocked(cookie));
        }
        CHECK(hp1020_udc_in_request_cancel(&in_port,cookie)==HP1020_UDC_IN_OK);
        CHECK(hp1020_udc_in_cancelled(&in_port,cookie,1)==HP1020_UDC_IN_OK);
        packets[3].live=0;state.cancellations++;
        CHECK(hp1020_udc_in_publish_clear(&in_publisher,cookie,1)==HP1020_IN_PUBLISH_WAIT);
        TRY(reset_drain());
        CHECK(in_publisher.failed && commands.inflight);
        CHECK(hp1020_usb_service_pump(&coordinator)==HP1020_RX_WAIT);
        CHECK(!commands.inflight && !adapter.in_result_pending && !status_reads);
        struct hp1020_tusb_cookie stale=cookie;stale.id++;
        CHECK(hp1020_udc_in_publish_clear(&in_publisher,stale,1)==HP1020_IN_PUBLISH_STALE);
        CHECK(hp1020_udc_in_publish_clear(&in_publisher,cookie,1)==HP1020_IN_PUBLISH_OK);
    } else if(scenario==5) {
        TRY(input(echo,sizeof(echo)-1));TRY(pump());
        const struct hp1020_tusb_cookie cookie=commands.in_cookie;
        TRY(reads(out_reads,4));
        CHECK(hp1020_bulk_fixture_step(131,4,program_state.trace_count+5,HP1020_UDC_PROGRAM_IO_UNKNOWN,0)==HP1020_UDC_PUBLISH_OK);
        CHECK(hp1020_bulk_fixture_step(6,0,0,0,0)==HP1020_UDC_PUBLISH_FAULT);
        CHECK(publisher.failed && !program.failed && !in_publisher.failed);
        CHECK(!hp1020_usb_service_program_allowed(&coordinator));TRY(check_blocked(cookie));
        CHECK(hp1020_udc_in_request_cancel(&in_port,cookie)==HP1020_UDC_IN_OK);
        CHECK(hp1020_udc_in_cancelled(&in_port,cookie,1)==HP1020_UDC_IN_OK);
        packets[3].live=0;state.cancellations++;
        TRY(reset_drain());CHECK(publisher.failed);
        CHECK(hp1020_usb_service_pump(&coordinator)==HP1020_RX_WAIT);
        CHECK(!commands.inflight && !adapter.in_result_pending);
    } else if(scenario==8) {
        const uint32_t old_status=packets[1].cookie.id;
        CHECK(hp1020_bulk_fixture_step(100,3,2,0x10000,0)==HP1020_UDC_SETUP_OK);
        CHECK(hp1020_bulk_fixture_step(101,3,0x01010101,0,0)==HP1020_UDC_SETUP_OK);
        CHECK(hp1020_bulk_fixture_step(103,old_status,1,0,0)==HP1020_TUSB_OK);
        TRY(control());
        CHECK(!program.binding_ready && hp1020_usb_service_progress(&coordinator)==HP1020_UDC_SETUP_ALLOW_SERVICE);
        CHECK(hp1020_usb_service_program_allowed(&coordinator));
        static const uint32_t selection_reads[][2]={
            {0x220,0x61},{0x22c,64},{0x508,0x020000c1},{0x418,0xa500a5},
            {0x28,64},{0x20,0x61},{0x2c,64},{0x50c,0x020000d1},{0x418,0xa500a5}
        };
        TRY(reads(selection_reads,9));
        CHECK(hp1020_bulk_fixture_step(123,0,0,0,0)==HP1020_UDC_PROGRAM_OK);
        CHECK(program.binding_ready && hp1020_usb_service_progress(&coordinator)==7);
        TRY(grant(3));TRY(recover_document());
        TRY(input(echo,sizeof(echo)-1));TRY(pump());TRY(reply(echo_reply,sizeof(echo_reply)-1));
    } else if(scenario==6) {
        TRY(input(echo,sizeof(echo)-1));TRY(pump());
        const struct hp1020_tusb_cookie cookie=commands.in_cookie;
        uint8_t *flags[]={&publisher.busy,&publisher.arming,&publisher.servicing,&in_publisher.busy,&commands.busy};
        for(unsigned i=0;i<sizeof(flags)/sizeof(flags[0]);i++) {
            *flags[i]=1; /* Explicit gate-only, not an injected physical failure. */
            CHECK(!hp1020_usb_service_program_allowed(&coordinator));
            CHECK(!hp1020_usb_service_progress(&coordinator));
            CHECK(hp1020_usb_service_pump(&coordinator)==HP1020_RX_WAIT);
            if(i!=3)CHECK(!hp1020_usb_service_in_ready(&coordinator,cookie));
            else CHECK(hp1020_usb_service_in_ready(&coordinator,cookie));
            *flags[i]=0;
        }
        commands.terminal=1; /* Gate-only stopped command contract. */
        CHECK(!hp1020_usb_service_progress(&coordinator));
        CHECK(!hp1020_usb_service_program_allowed(&coordinator));
        CHECK(!hp1020_usb_service_submission_allowed(&coordinator));
        CHECK(!hp1020_usb_service_in_ready(&coordinator,cookie));
        CHECK(hp1020_usb_service_pump(&coordinator)==HP1020_RX_ORDER);
        commands.terminal=0;
        struct hp1020_tusb_cookie stale=cookie;stale.epoch++;
        CHECK(!hp1020_usb_service_in_ready(&coordinator,stale));
        struct hp1020_tusb_adapter other=adapter;
        in_port.adapter=&other;CHECK(!hp1020_usb_service_progress(&coordinator));
        CHECK(!hp1020_usb_service_in_ready(&coordinator,cookie));
        in_port.adapter=&adapter;TRY(reply(echo_reply,sizeof(echo_reply)-1));
    } else return __LINE__;
    composed_check();CHECK(!state.violations && !program_state.violations && !publish_state.violations);
    CHECK(program_state.cursor==program_state.queued);return 0;
}
