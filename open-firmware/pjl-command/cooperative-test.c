/* SPDX-License-Identifier: GPL-2.0-or-later
 * Existing USB/DCD/reply fixture, with external software output advancement.
 * No peripheral operations or physical reset/completion observations. */
#define HP1020_DOCUMENT_COOPERATIVE 1
#include "test.c"
uint8_t hp1020_cooperative_job[65536];
uint32_t hp1020_cooperative_stats[8];
static struct hp1020_usb_document paused_document;
static struct hp1020_usb_document_memory paused_memory;
static const uint8_t after_query[]="\x1b%-12345X@PJL ECHO AFTER\r\n";
static const uint8_t after_reply[]="@PJL ECHO AFTER\r\n\f";

static uint32_t output_step(void) {
    if(!document.pump.active)return 0;
    struct hp1020_ring_view view;
    enum hp1020_ring_result r=hp1020_image_ring_peek(&document.pump.ring,&view);
    CHECK(r!=HP1020_RING_INVALID);
    if(state.inflight || r==HP1020_RING_OK)
        CHECK(progress(&document.pump.plan,&document.pump.ring,NULL)==HP1020_OK);
    return 0;
}
static enum hp1020_rx_result step(uint32_t mode) {
    return mode==5?hp1020_tusb_adapter_pump(&adapter):hp1020_pjl_command_pump(&commands);
}
static uint32_t held_control(uint32_t mode) {
    paused_document=document;memcpy(&paused_memory,&memory.data,sizeof(paused_memory));
    const uint32_t offset=commands.offset;
    for(unsigned i=0;i<8;i++) {
        CHECK(step(mode)==HP1020_RX_WAIT);
        CHECK(commands.offset==offset && !memcmp(&document,&paused_document,sizeof(document)));
        CHECK(!memcmp(&memory.data,&paused_memory,sizeof(paused_memory)));
    }
    /* A genuine TinyUSB EP0 round trip while decoded output remains blocked. */
    const uint8_t get_config[8]={0x80,8,0,0,0,0,1,0};
    TRY(setup(get_config));
    CHECK(packets[1].live && packets[1].length==1 && packets[1].buffer[0]==1);
    TRY(settle(packets[1].cookie,XFER_RESULT_SUCCESS,1));
    CHECK(packets[0].live && !packets[0].length);
    TRY(settle(packets[0].cookie,XFER_RESULT_SUCCESS,0));
    CHECK(!memcmp(&document,&paused_document,sizeof(document)));
    CHECK(!memcmp(&memory.data,&paused_memory,sizeof(paused_memory)));
    return 0;
}
uint32_t hp1020_cooperative_check(uint32_t mode,uint32_t fill,uint32_t length) {
    CHECK(mode<=5 && length && length<=sizeof(hp1020_cooperative_job));
    TRY(command_start(fill));CHECK(document.cooperative);
    memset(hp1020_cooperative_stats,0,sizeof(hp1020_cooperative_stats));
    if(mode!=5)TRY(command_write(query,sizeof(query)-1,64));
    uint32_t offset=0,tail=0,holding=1,checked=0,recovered=0,old_generation=document.receive.generation;
    if(mode==4)state.document_fail_at=0;
    enum hp1020_rx_result r=HP1020_RX_OK;
    for(unsigned iterations=0;iterations<30000;iterations++) {
        hp1020_cooperative_stats[0]++;
        if(document.receive.count<4) {
            if(offset<length) {
                uint32_t n=length-offset;if(n>64)n=64;
                TRY(command_input(hp1020_cooperative_job+offset,n));offset+=n;
            } else if((mode==0 || mode==1 || mode==4) && !tail) {
                TRY(command_input(after_query,sizeof(after_query)-1));tail=1;
            }
        }
        r=step(mode);
        if(r==HP1020_RX_PAYLOAD)break;
        CHECK(r==HP1020_RX_OK || r==HP1020_RX_WAIT);
        struct hp1020_image_ring *ring=&document.pump.ring;
        if(holding && document.pump.image.pending &&
            ring->copied_rows-ring->completed_rows==4*ring->capacity_rows) {
            /* One further step must actually hit output pressure. */
            CHECK(step(mode)==HP1020_RX_WAIT);TRY(held_control(mode));checked++;
            if(mode==1 && !recovered) {
                TRY(output_step());CHECK(state.inflight==1);
                struct hp1020_tusb_cookie old=commands.in_cookie;
                const uint8_t reset[8]={0x21,2,0,0,0,0,0,0};
                TRY(setup(reset));
                CHECK(document.receive.stopped && hp1020_usb_document_restart(&document)==HP1020_RX_ORDER);
                CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_STOPPED && commands.inflight);
                CHECK(!memcmp(commands.reply,answer,sizeof(answer)-1));
                uint32_t index=ring->completion;
                CHECK(ring->slots[index].state==2);
                CHECK(hp1020_image_ring_complete(ring,index)==HP1020_RING_OK);
                state.inflight--;state.completed++;
                TRY(command_cancel(old));
                /* Remaining unsubmitted bands are explicitly abandoned by
                 * the fixture's existing separate output-quiescence promise. */
                TRY(recover());CHECK(document.cooperative && document.receive.generation==old_generation+1);
                CHECK(!document.pump.pages_completed && !document.pump.pending_chunk);
                CHECK(hp1020_pjl_command_pump(&commands)==HP1020_RX_OK);
                CHECK(!commands.have_input && !commands.offset);
                offset=tail=0;recovered=1;
                TRY(command_write(query,sizeof(query)-1,64));
                continue;
            }
            if(mode!=5)TRY(command_reply(answer,sizeof(answer)-1));
            holding=0;
        }
        if(!holding)TRY(output_step());
        if(commands.inflight && commands.reply_length==sizeof(after_reply)-1 &&
            !memcmp(commands.reply,after_reply,sizeof(after_reply)-1))
            TRY(command_reply(after_reply,sizeof(after_reply)-1));
        if(offset==length && !document.receive.count && !commands.inflight &&
            (mode==2 || mode==3 || mode==5 || tail))break;
    }
    CHECK(checked && hp1020_cooperative_stats[0]<30000);
    if(mode==2 || mode==4) {
        CHECK(r==HP1020_RX_PAYLOAD && document.receive.stopped);
        CHECK(document.payload_error==(mode==2?HP1020_FORMAT:HP1020_ORDER));
        CHECK(!commands.inflight && !state.documents_completed);
        CHECK(state.document_calls==(mode==4?1u:0u));
    } else {
        CHECK(offset==length && !document.receive.count && !commands.inflight && !state.inflight);
        CHECK(hp1020_tusb_adapter_close_input(&adapter)==HP1020_TUSB_OK);
        r=hp1020_tusb_adapter_finish(&adapter);
        if(mode==3)CHECK(r==HP1020_RX_PAYLOAD && document.payload_error==HP1020_TRUNCATED && !state.document_calls);
        else {
            CHECK(r==HP1020_RX_OK && document.finished && state.documents_completed==1);
            CHECK(hp1020_bulk_fixture_documents[0][0]==document.receive.generation);
            CHECK(hp1020_bulk_fixture_documents[0][1]==1 && hp1020_bulk_fixture_documents[0][2]==0 &&
                hp1020_bulk_fixture_documents[0][3]==2);
        }
    }
    if(mode==1)CHECK(recovered && checked==2);
    check_owned();CHECK(!state.violations);
    hp1020_cooperative_stats[1]=state.pixel_bytes;
    hp1020_cooperative_stats[2]=document.pump.pages_completed;
    hp1020_cooperative_stats[3]=state.documents_completed;
    hp1020_cooperative_stats[4]=document.receive.generation;
    hp1020_cooperative_stats[5]=document.payload_error;
    hp1020_cooperative_stats[6]=checked;
    hp1020_cooperative_stats[7]=state.document_calls;
    return 0;
}
