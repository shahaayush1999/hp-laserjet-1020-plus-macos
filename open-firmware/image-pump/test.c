/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image_pump.h"
#include <string.h>
#define CHECK(x) do { if(!(x))return __LINE__; } while(0)
uint8_t hp1020_pump_job[65536],hp1020_pump_pixels[262144];
uint32_t hp1020_pump_stats[8];
static struct hp1020_image_pump state;
static struct hp1020_image_pump_memory memory;
static uint8_t packet[511],held_band[8192],held_slots[32768];
static struct hp1020_image_pump held_state;
static uint32_t queue[4],hashes[4],sizes[4],head,count;
static const uint8_t *pointers[4];
static uint32_t hash(const uint8_t *p,uint32_t size) {
    uint32_t h=2166136261u;
    for(uint32_t i=0;i<size;i++)h=(h^p[i])*16777619u;
    return h;
}
static uint32_t accept(void) {
    struct hp1020_ring_view v;
    enum hp1020_ring_result r=hp1020_image_ring_peek(&state.ring,&v);
    if(r==HP1020_RING_EMPTY || r==HP1020_RING_BLOCKED)return 0;
    CHECK(r==HP1020_RING_OK && count<4 && v.index<4);
    uint32_t bytes=v.rows*state.plan.stride;
    CHECK(hp1020_pump_stats[0]+bytes<=sizeof(hp1020_pump_pixels));
    memcpy(hp1020_pump_pixels+hp1020_pump_stats[0],v.pixels,bytes);
    hp1020_pump_stats[0]+=bytes;
    pointers[v.index]=v.pixels;sizes[v.index]=bytes;hashes[v.index]=hash(v.pixels,bytes);
    queue[(head+count)%4]=v.index;count++;
    CHECK(hp1020_image_ring_accept(&state.ring,v.index)==HP1020_RING_OK);
    return 0;
}
static uint32_t complete(void) {
    CHECK(count);
    uint32_t index=queue[head];
    CHECK(hash(pointers[index],sizes[index])==hashes[index]);
    CHECK(hp1020_image_ring_complete(&state.ring,index)==HP1020_RING_OK);
    head=(head+1)%4;count--;return 0;
}
static uint32_t held(enum hp1020_pump_result result,uint32_t repetitions) {
    held_state=state;
    memcpy(held_band,memory.decode.band,sizeof(held_band));
    memcpy(held_slots,memory.slots,sizeof(held_slots));
    uint32_t compressed=hash(memory.decode.compressed,sizeof(memory.decode.compressed));
    for(uint32_t i=0;i<repetitions;i++) {
        size_t used=123;
        CHECK(hp1020_image_pump_feed(&state,packet,sizeof(packet),&used)==result && !used);
        CHECK(!memcmp(&state,&held_state,sizeof(state)));
        CHECK(!memcmp(held_band,memory.decode.band,sizeof(held_band)));
        CHECK(!memcmp(held_slots,memory.slots,sizeof(held_slots)));
        CHECK(hash(memory.decode.compressed,sizeof(memory.decode.compressed))==compressed);
    }
    return 0;
}
uint32_t hp1020_image_pump_check(uint32_t mode,uint32_t fill,uint32_t length) {
    CHECK(length && length<=sizeof(hp1020_pump_job));
    memset(&state,0,sizeof(state));memset(&memory,fill,sizeof(memory));
    memset(hp1020_pump_stats,0,sizeof(hp1020_pump_stats));head=count=0;
    CHECK(hp1020_image_pump_init(&state,&memory)==HP1020_PUMP_MORE);
    CHECK(hp1020_image_pump_init(&state,&memory)==HP1020_PUMP_ERROR);
    uint32_t offset=0,holding=mode==1 || mode==3,wait_checked=0;
    enum hp1020_pump_result r=HP1020_PUMP_MORE;
    while(hp1020_pump_stats[4]++<30000) {
        size_t used=0;
        if(offset<length) {
            uint32_t n=length-offset;
            if(n>sizeof(packet))n=sizeof(packet);
            if(mode==7)n=1;
            memcpy(packet,hp1020_pump_job+offset,n);
            r=hp1020_image_pump_feed(&state,packet,n,&used);
            CHECK(used<=n && used<=HP1020_PUMP_INPUT_QUANTUM);
            offset+=(uint32_t)used;
            memset(packet,fill^255,sizeof(packet));
        } else r=hp1020_image_pump_finish(&state);
        if(r==HP1020_PUMP_ERROR || r==HP1020_PUMP_DONE)break;
        CHECK(r!=HP1020_PUMP_STOPPED);
        if(r==HP1020_PUMP_WAIT_OUTPUT) {
            CHECK(!used);hp1020_pump_stats[3]++;
            if(holding && !wait_checked) {
                uint32_t failure=held(r,32);CHECK(!failure);
                wait_checked=1;
                if(mode==3) {
                    CHECK(!accept() && count==1);
                    hp1020_image_pump_stop(&state);
                    CHECK(!held(HP1020_PUMP_STOPPED,8));
                    CHECK(hp1020_image_pump_finish(&state)==HP1020_PUMP_STOPPED);
                    CHECK(!complete() && state.ring.copied_rows>state.ring.completed_rows);
                    CHECK(!state.pages_completed && !state.documents_completed);
                    hp1020_pump_stats[5]=1;return 0;
                }
                holding=0;
            }
        }
        if(r==HP1020_PUMP_PAGE || r==HP1020_PUMP_DOCUMENT) {
            CHECK(!used && !count);
            CHECK(state.event.kind==r);
            if(mode==6)CHECK(!held(r,8));
            if(mode==8) {
                CHECK(r==HP1020_PUMP_PAGE);
                CHECK(hp1020_image_pump_ack(&state,HP1020_PUMP_DOCUMENT)==HP1020_PUMP_ERROR);
                CHECK(state.error==HP1020_ORDER && state.event.kind==r);
                CHECK(hp1020_image_pump_feed(&state,packet,1,&used)==HP1020_PUMP_ERROR && !used);
                hp1020_pump_stats[6]=HP1020_ORDER;return 0;
            }
            if(r==HP1020_PUMP_PAGE) {
                CHECK(state.event.first_page==hp1020_pump_stats[1] && state.event.pages==1);
                CHECK(hp1020_image_ring_drained(&state.ring));hp1020_pump_stats[1]++;
            } else {
                CHECK(state.event.document_id==hp1020_pump_stats[2]+1);
                CHECK(state.event.first_page+state.event.pages==hp1020_pump_stats[1]);
                hp1020_pump_stats[2]++;
            }
            CHECK(hp1020_image_pump_ack(&state,r)==HP1020_PUMP_MORE);
        }
        if(state.active && !holding) {
            CHECK(!accept());
            if(count>hp1020_pump_stats[5])hp1020_pump_stats[5]=count;
            if(count && (mode!=2 || count>=2 ||
                state.ring.accepted_rows==state.ring.rows))CHECK(!complete());
        }
    }
    CHECK(hp1020_pump_stats[4]<30000);
    hp1020_pump_stats[6]=state.error;
    hp1020_pump_stats[7]=(uint32_t)(sizeof(state)+sizeof(memory));
    if(mode==4 || mode==5) {
        CHECK(r==HP1020_PUMP_ERROR && state.error==(mode==4?HP1020_FORMAT:HP1020_TRUNCATED));
        CHECK(!state.documents_completed);
        size_t used=123;
        CHECK(hp1020_image_pump_feed(&state,packet,1,&used)==HP1020_PUMP_ERROR && !used);
    } else {
        CHECK(r==HP1020_PUMP_DONE && offset==length && !count);
        CHECK(hp1020_image_pump_finish(&state)==HP1020_PUMP_DONE);
        CHECK(state.pages_completed==hp1020_pump_stats[1]);
        CHECK(state.documents_completed==hp1020_pump_stats[2]);
        if(mode==1)CHECK(wait_checked && hp1020_pump_stats[3]);
        if(mode==2)CHECK(hp1020_pump_stats[5]>=2);
    }
    return 0;
}
