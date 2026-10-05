/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "../udc-in-publish/test.c"
#include "hp1020_pjl_command.c"
static struct hp1020_pjl_command commands;
uint8_t hp1020_command_job[4096];
static const uint8_t query[]="\x1b%-12345X@PJL ECHO HP1020_STATUS_PROBE\r\n\x1b%-12345X";
static const uint8_t answer[]="@PJL ECHO HP1020_STATUS_PROBE\r\n\f";

static uint32_t command_start(uint32_t fill) {
    TRY(start(fill));memset(&in_memory,fill,sizeof(in_memory));
    CHECK(hp1020_udc_in_init(&port,&adapter,
        (struct hp1020_udc_in_span){in_memory.data.descriptor,0x30400100,16},
        (struct hp1020_udc_in_span){in_memory.data.packet,0x30400000,64})==HP1020_UDC_IN_OK);
    struct hp1020_udc_in_publish_io io={pub_ready,pub_read,pub_write,pub_order,pub_visible,&io_state};
    CHECK(hp1020_udc_in_publish_init(&publisher,&port,&io)==HP1020_IN_PUBLISH_OK);
    CHECK(hp1020_pjl_command_init(&commands,&adapter)==HP1020_RX_OK);return 0;
}
static uint32_t command_input(const uint8_t *data,uint32_t n) {
    CHECK(n<=64 && hp1020_tusb_adapter_arm_out(&adapter)==HP1020_TUSB_OK);
    if(n)memcpy(hp1020_bulk_fixture_input,data,n);
    CHECK(hp1020_bulk_fixture_step(3,packets[2].cookie.id,n,0,0)==HP1020_TUSB_OK);
    TRY(settle(packets[2].cookie,XFER_RESULT_SUCCESS,n));return 0;
}
static uint32_t command_write(const uint8_t *data,uint32_t n,uint32_t fragment) {
    for(uint32_t at=0;at<n;) {
        uint32_t count=n-at;if(count>fragment)count=fragment;
        TRY(command_input(data+at,count));at+=count;
        enum hp1020_rx_result r=hp1020_pjl_command_pump(&commands);
        CHECK(r==HP1020_RX_OK || r==HP1020_RX_WAIT);
    }
    return 0;
}
static uint32_t command_publish(const uint8_t *wanted,uint32_t n) {
    CHECK(commands.inflight && commands.queued && commands.reply_length==n && n<64);
    CHECK(!memcmp(commands.reply,wanted,n) && !memcmp(in_memory.data.packet,wanted,n));
    CHECK(packets[3].live && packets[3].buffer==commands.reply && packets[3].length==n);
    const uint8_t descriptor[16]={0x08,0,0,(uint8_t)n,0,0,0,0,0x30,0x40,0,0,0,0,0};
    CHECK(!memcmp(in_memory.data.descriptor,descriptor,16));
    memcpy(descriptor_before,in_memory.data.descriptor,16);memcpy(packet_before,in_memory.data.packet,64);
    TRY(publish_success(commands.in_cookie,true));return 0;
}
static uint32_t command_memory_done(struct hp1020_tusb_cookie c,uint32_t n) {
    struct hp1020_udc_in_observation o=observation(c);
    CHECK(hp1020_udc_in_observe(&port,&o,(struct hp1020_udc_in_completion_facts){1,1,1,n})==HP1020_UDC_IN_OK);
    packets[3].live=0;state.completions++;TRY(service());return 0;
}
static uint32_t command_reply(const uint8_t *wanted,uint32_t n) {
    TRY(command_publish(wanted,n));TRY(command_memory_done(commands.in_cookie,n));
    CHECK(commands.inflight && !memcmp(commands.reply,wanted,n));
    enum hp1020_rx_result r=hp1020_pjl_command_pump(&commands);
    CHECK(r==HP1020_RX_OK || r==HP1020_RX_WAIT);return 0;
}
static uint32_t command_cancel(struct hp1020_tusb_cookie c) {
    CHECK(hp1020_udc_in_request_cancel(&port,c)==HP1020_UDC_IN_OK);
    CHECK(hp1020_udc_in_cancelled(&port,c,0)==HP1020_UDC_IN_WAIT);
    CHECK(hp1020_udc_in_cancelled(&port,c,1)==HP1020_UDC_IN_OK);
    packets[3].live=0;state.cancellations++;TRY(service());
    CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_STOPPED);
    CHECK(!commands.inflight && !commands.queued);return 0;
}
uint32_t hp1020_pjl_command_check(uint32_t scenario,uint32_t fill,uint32_t job_length) {
    TRY(command_start(fill));
    const uint8_t reset[8]={0x21,2,0,0,0,0,0,0};
    if(scenario<=2) {
        TRY(command_write(query,sizeof(query)-1,scenario==0?64:scenario==1?1:7));
        CHECK(!document.output.documents_completed && !document.finished);
        TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==3) {
        const uint8_t text[]="@PJL ECHO JZJZ JZJZ\r\n";
        const uint8_t response[]="@PJL ECHO JZJZ JZJZ\r\n\f";
        TRY(command_write(text,sizeof(text)-1,2));
        CHECK(!document.output.stream.parser.framing);
        TRY(command_reply(response,sizeof(response)-1));
    } else if(scenario==4) {
        const uint8_t two[]="@PJL ECHO FIRST\r\n@PJL ECHO SECOND\r\n";
        TRY(command_write(two,sizeof(two)-1,64));
        struct hp1020_tusb_cookie first=commands.in_cookie;
        CHECK(document.receive.count==1 && commands.have_input);
        for(unsigned i=0;i<3;i++)CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_WAIT);
        TRY(command_reply((const uint8_t *)"@PJL ECHO FIRST\r\n\f",18));
        CHECK(commands.inflight && commands.in_cookie.id!=first.id);
        TRY(command_reply((const uint8_t *)"@PJL ECHO SECOND\r\n\f",19));
    } else if(scenario==5) {
        TRY(command_write(query,sizeof(query)-1,64));TRY(command_input(NULL,0));
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_WAIT && !document.finished);
        TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==6 || scenario==7) {
        uint8_t line[64];memcpy(line,"@PJL ECHO ",10);memset(line+10,'A',51);
        uint32_t n=scenario==6?60:61;line[n++]='\r';line[n++]='\n';
        TRY(command_input(line,n));
        if(scenario==7) {
            CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_PAYLOAD);
            CHECK(document.payload_error==HP1020_LIMIT && document.receive.stopped && !commands.inflight);
            return state.violations?__LINE__:0;
        }
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_WAIT);
        line[62]='\f';TRY(command_reply(line,63));
    } else if(scenario==8) {
        uint8_t unknown[256];memset(unknown,'A',sizeof(unknown));
        memcpy(unknown,"@PJL JOB NAME=",14);unknown[254]='\r';unknown[255]='\n';
        TRY(command_write(unknown,sizeof(unknown),64));
        CHECK(!commands.inflight && !document.output.documents_completed);
        TRY(command_write(query,sizeof(query)-1,64));TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==9) {
        TRY(command_write((const uint8_t *)"@PJL ECHO OLD",13,3));
        TRY(setup(reset));TRY(recover());
        TRY(command_write(query,sizeof(query)-1,7));TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==10 || scenario==11 || scenario==13) {
        TRY(command_input(query,sizeof(query)-1));
        if(scenario==13)state.fail_submission=2;
        CHECK(hp1020_pjl_command_pump(&commands)==(scenario==13?HP1020_RX_STOPPED:HP1020_RX_WAIT));
        struct hp1020_tusb_cookie old=commands.in_cookie;
        if(scenario==11)TRY(command_publish(answer,sizeof(answer)-1));
        TRY(setup(reset));
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_STOPPED);
        CHECK(commands.inflight && !memcmp(commands.reply,answer,sizeof(answer)-1));
        if(scenario==11) {
            TRY(command_memory_done(old,sizeof(answer)-1));
            CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_STOPPED && !commands.inflight);
        } else TRY(command_cancel(old));
        TRY(recover());TRY(command_write(query,sizeof(query)-1,7));
        CHECK(commands.in_cookie.id!=old.id);
        trace(old,true);
        CHECK(hp1020_udc_in_publish_packet(&publisher,old,all_facts)==HP1020_IN_PUBLISH_STALE && !io_state.cursor);
        TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==12) {
        TRY(command_input(query,sizeof(query)-1));state.fail_submission=1;
        uint32_t submissions=state.submissions;
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_WAIT);
        CHECK(commands.queued && !commands.inflight && state.submissions==submissions && !adapter.fenced);
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_WAIT);
        TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==14) {
        uint8_t binary[52]={'J','Z','J','Z',0,0,0,48,0,0,0,0,0,0,0,0,0,0,0x5a,0x5a};
        memcpy(binary+20,"@PJL ECHO BINARY MUST NOT REPLY\r\n",32);
        TRY(command_input(binary,20));CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_OK);
        TRY(command_input(binary+20,32));
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_PAYLOAD);
        CHECK(!commands.inflight && !commands.queued && !packets[3].live);
        return state.violations?__LINE__:0;
    } else if(scenario==15) {
        CHECK(job_length && job_length<=sizeof(hp1020_command_job));
        const uint8_t before[]="@PJL INFO STATUS\r\n@PJL ECHO BEFORE\r\n@PJL ENTER LANGUAGE=ZJS\r\n";
        const uint8_t after[]="\x1b%-12345X@PJL ECHO AFTER\r\n";
        TRY(command_write(before,sizeof(before)-1,7));
        TRY(command_write(hp1020_command_job,job_length,7));
        TRY(command_write(after,sizeof(after)-1,7));
        CHECK(document.output.documents_completed==1 && document.output.pages_drained==2 && state.pixel_bytes==128);
        TRY(command_reply((const uint8_t *)"@PJL ECHO BEFORE\r\n\f",19));
        TRY(command_reply((const uint8_t *)"@PJL ECHO AFTER\r\n\f",18));
    } else if(scenario==16) {
        TRY(command_input(query,sizeof(query)-1));state.fail_submission=1;
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_WAIT && commands.queued && !commands.inflight);
        TRY(setup(reset));
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_STOPPED && !commands.queued);
        TRY(recover());TRY(command_write(query,sizeof(query)-1,7));
        TRY(command_reply(answer,sizeof(answer)-1));
    } else if(scenario==17) {
        TRY(command_write(query,sizeof(query)-1,64));
        struct hp1020_tusb_cookie old=commands.in_cookie;
        memcpy(descriptor_before,in_memory.data.descriptor,16);memcpy(packet_before,in_memory.data.packet,64);
        trace(old,true);io_state.fail_at=16; /* Uncertain POLL write. */
        CHECK(hp1020_udc_in_publish_packet(&publisher,old,all_facts)==HP1020_IN_PUBLISH_FAULT);
        CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_STOPPED && commands.inflight);
        CHECK(!memcmp(commands.reply,answer,sizeof(answer)-1));
        TRY(command_cancel(old));
        CHECK(hp1020_udc_in_publish_clear(&publisher,old,1)==HP1020_IN_PUBLISH_OK);
        TRY(setup(reset));TRY(recover());TRY(command_write(query,sizeof(query)-1,7));
        TRY(command_reply(answer,sizeof(answer)-1));
    } else return __LINE__;
    CHECK(!commands.inflight && !commands.queued && !commands.have_input && !document.receive.count);
    CHECK(!state.violations && !document.receive.stopped);
    for(unsigned i=0;i<16;i++)CHECK(in_memory.before[i]==fill && in_memory.after[i]==fill);
    return 0;
}
