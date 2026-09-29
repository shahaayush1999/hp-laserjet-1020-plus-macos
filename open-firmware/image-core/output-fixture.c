/* SPDX-License-Identifier: GPL-2.0-or-later
 * Serialized software consumer, not a USB transport or a physical engine. */
#include "hp1020_image_output.h"
#include <string.h>

uint8_t hp1020_output_input[65552],hp1020_output_capture[262144];
uint32_t hp1020_output_stats[40],hp1020_output_writes[256][5];
uint32_t hp1020_output_pages[64][7];
static struct hp1020_image_output state;
static struct { uint8_t before[16];struct hp1020_image_output_memory data;uint8_t after[16]; } memory;
static hp1020_band_consumer inner_band;
static hp1020_chunk_consumer inner_chunk;
static uint32_t fill_value,mode,reject_after,inflight,random_state;
static uint32_t owned_hash[4];
#ifdef HP1020_IMAGE_HOST_CHECK
void hp1020_output_observe(const uint8_t *,uint32_t);
#endif
static uint32_t hash(uint32_t h,const uint8_t *p,uint32_t n) {
    while(n--)h=(h^*p++)*16777619u;
    return h;
}
static enum hp1020_result pump(const struct hp1020_page_plan *plan,
    struct hp1020_image_ring *ring,void *context) {
    uint32_t *o=hp1020_output_stats;(void)context;
    if(o[9]++==reject_after)return HP1020_LIMIT;
    if(mode==3)return HP1020_OK; /* Deliberately broken consumer: no progress. */
    uint32_t page=state.page_index;
    if(page>=64)return HP1020_LIMIT;
    uint32_t *p=hp1020_output_pages[page];
    if(plan->stride!=ring->stride || plan->rows!=ring->rows)o[10]++;
    p[0]=plan->stride;p[1]=plan->rows;p[2]=plan->copies;p[3]=plan->chunk_rows;
    struct hp1020_ring_view view;
    enum hp1020_ring_result peek=hp1020_image_ring_peek(ring,&view);
    random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;
    int complete=inflight && (mode==0 || (mode==1 && inflight==3) ||
        (mode==2 && (random_state&1)) || peek!=HP1020_RING_OK);
    if(complete) {
        uint32_t at=ring->completion,rows=ring->slots[at].rows;
        if(owned_hash[at]!=hash(2166136261u,ring->storage+at*ring->slot_bytes,rows*ring->stride))o[10]++;
        if(hp1020_image_ring_complete(ring,at)!=HP1020_RING_OK)return HP1020_ORDER;
        p[6]+=rows;o[8]++;inflight--;
    } else {
        if(peek!=HP1020_RING_OK)return HP1020_ORDER;
        if(view.first!=p[5])o[10]++;
        uint32_t bytes=view.rows*ring->stride;
        owned_hash[view.index]=hash(2166136261u,view.pixels,bytes);
#ifdef HP1020_IMAGE_HOST_CHECK
        hp1020_output_observe(view.pixels,bytes);
#endif
        for(uint32_t i=0;i<bytes && o[5]+i<sizeof(hp1020_output_capture);i++)
            hp1020_output_capture[o[5]+i]=view.pixels[i];
        o[6]=hash(o[6],view.pixels,bytes);o[5]+=bytes;
        if(hp1020_image_ring_accept(ring,view.index)!=HP1020_RING_OK)return HP1020_ORDER;
        if(ring->slots[view.index].state!=2)o[10]++;else o[25]++;
        p[4]++;p[5]+=view.rows;o[7]++;inflight++;
        if(inflight>o[24])o[24]=inflight;
    }
    return HP1020_OK;
}
static enum hp1020_result band_observer(const struct hp1020_page_plan *plan,
    const struct hp1020_image *image,uint32_t index,void *context) {
    uint32_t before=hash(2166136261u,image->band,image->band_rows*image->stride);
    enum hp1020_result r=inner_band(plan,image,index,context);
    uint32_t *o=hp1020_output_stats;
    if(!image->pending || before!=hash(2166136261u,image->band,image->band_rows*image->stride))o[10]++;
    o[27]++;
    if(!r) {
        if(o[20]>=256)return HP1020_LIMIT;
        uint32_t at=o[20]++;
        uint32_t *w=hp1020_output_writes[at];
        w[0]=index;w[1]=image->band_first;w[2]=image->band_rows;
        w[3]=(state.ring.producer+3)&3u;w[4]=image->stride;
        o[4]++;
    }
    return r;
}
static enum hp1020_result chunk_observer(const struct hp1020_semantic *parser,
    const uint8_t *data,uint32_t size,void *context) {
    enum hp1020_result r=inner_chunk(parser,data,size,context);
    if(!r && parser->chunk_type==5) {
        memset(memory.data.stream.compressed,fill_value^255,size);
        hp1020_output_stats[21]++;
    }
    return r;
}
uint32_t hp1020_output_reset(uint32_t fill,uint32_t ordering,uint32_t fail_at) {
    fill_value=fill&255;mode=ordering;reject_after=fail_at;inflight=0;random_state=1020;
    memset(&memory,fill_value,sizeof(memory));memset(hp1020_output_capture,fill_value,sizeof(hp1020_output_capture));
    memset(hp1020_output_stats,0,sizeof(hp1020_output_stats));
    memset(hp1020_output_writes,0,sizeof(hp1020_output_writes));memset(hp1020_output_pages,0,sizeof(hp1020_output_pages));
    hp1020_output_stats[6]=2166136261u;hp1020_output_stats[14]=sizeof(state);
    hp1020_output_stats[15]=sizeof(memory.data);
    uint32_t r=hp1020_image_output_init(&state,&memory.data,pump,0);
    inner_band=state.stream.consume_band;state.stream.consume_band=band_observer;
    inner_chunk=state.stream.parser.consume_chunk;state.stream.parser.consume_chunk=chunk_observer;
    return r;
}
uint32_t hp1020_output_feed(uint32_t length,uint32_t fragment) {
    if(length>sizeof(hp1020_output_input) || !fragment)return HP1020_LIMIT;
    uint32_t r=state.error;
    for(uint32_t pos=0;pos<length;) {
        uint32_t n=length-pos;if(n>fragment)n=fragment;
        r=hp1020_image_output_feed(&state,hp1020_output_input+pos,n);
        if(r)break;
        pos+=n;
    }
    memset(hp1020_output_input,fill_value^255,length);
    return r;
}
uint32_t hp1020_output_finish(void) {
    uint32_t *o=hp1020_output_stats;
    o[0]=hp1020_image_output_finish(&state);o[1]=state.stream.parser.documents;
    o[2]=state.stream.pages;o[3]=state.stream.rows;o[12]=state.stream.image_result;
    o[13]=state.stream.output_error;o[16]=state.stream.image.pending;
    o[17]=state.pages_drained;o[22]=state.active;o[23]=state.finished;
    o[28]=state.stream.parser.page_count;o[31]=state.stream.peak_compressed_chunk;
    for(uint32_t i=0;i<4;i++)o[18]+=state.ring.slots[i].state!=0;
    uint32_t before=hash(2166136261u,(const uint8_t *)&memory,sizeof(memory)),calls=o[9];
    if(o[0]) {
        o[19]=hp1020_image_output_feed(&state,NULL,0)==o[0] && hp1020_image_output_finish(&state)==o[0];
        o[26]=!state.finished;
    } else {
        o[19]=hp1020_image_output_finish(&state)==HP1020_OK &&
            hp1020_image_output_feed(&state,NULL,0)==HP1020_FINISHED &&
            hp1020_image_output_finish(&state)==HP1020_FINISHED;
    }
    if(calls!=o[9] || before!=hash(2166136261u,(const uint8_t *)&memory,sizeof(memory)))o[10]++;
    o[11]=1;
    for(uint32_t i=0;i<16;i++)if(memory.before[i]!=fill_value || memory.after[i]!=fill_value)o[11]=0;
    return o[0];
}
uint8_t *hp1020_output_storage(void) { return memory.data.slots; }
