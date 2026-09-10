/* SPDX-License-Identifier: GPL-2.0-or-later
 * Incremental host/QEMU fixture. Large source files never live in target RAM. */
#include "hp1020_image_stream.h"
#include <string.h>
uint8_t hp1020_stream_input[65552],hp1020_stream_capture[65536];
uint32_t hp1020_stream_stats[32];
static struct hp1020_image_stream state;
static struct { uint8_t before[16];struct hp1020_image_stream_memory data;uint8_t after[16]; } memory;
static hp1020_chunk_consumer inner_consumer;
static uint32_t fail_after,fill_value;
#ifdef HP1020_IMAGE_HOST_CHECK
void hp1020_stream_observe(const uint8_t *,uint32_t);
#endif
static uint32_t hash(uint32_t h,const uint8_t *p,uint32_t n) {
    while(n--)h=(h^*p++)*16777619u;
    return h;
}
static enum hp1020_result band_out(const struct hp1020_page_plan *plan,
    const struct hp1020_image *image,uint32_t index,void *context) {
    uint32_t *o=hp1020_stream_stats;(void)context;
    if(o[4]>=fail_after)return HP1020_LIMIT;
    if(index!=o[17]) { if(index!=o[17]+1 || image->band_first)o[10]++;o[17]=index;o[18]=0; }
    if(image->band_first!=o[18] || image->stride!=plan->stride)o[10]++;
    o[18]+=image->band_rows;
    uint32_t bytes=image->band_rows*image->stride;
#ifdef HP1020_IMAGE_HOST_CHECK
    hp1020_stream_observe(image->band,bytes);
#endif
    o[6]=hash(o[6],image->band,bytes);
    for(uint32_t i=0;i<bytes && o[5]+i<sizeof(hp1020_stream_capture);i++)
        hp1020_stream_capture[o[5]+i]=image->band[i];
    o[3]+=image->band_rows;o[4]++;o[5]+=bytes;
    return HP1020_OK;
}
static enum hp1020_result chunk_observer(const struct hp1020_semantic *p,
    const uint8_t *data,uint32_t size,void *context) {
    (void)context;
    if(p->chunk_type==4)hp1020_stream_stats[20]=hash(hp1020_stream_stats[20],data,size);
    enum hp1020_result r=inner_consumer(p,data,size,&state);
    /* Poison a successfully consumed BID immediately after the real consumer
     * returns. Its next use must be as fresh parser input, never old history. */
    if(!r && p->chunk_type==5) {
        if(p->arena_used!=size)hp1020_stream_stats[10]++;
        memset(memory.data.compressed,fill_value^0xff,size);
        hp1020_stream_stats[21]++;
    }
    return r;
}
uint32_t hp1020_stream_reset(uint32_t fill,uint32_t reject_after) {
    fill_value=fill&255;fail_after=reject_after;
    memset(&memory,fill_value,sizeof(memory));memset(hp1020_stream_capture,fill_value,sizeof(hp1020_stream_capture));
    memset(hp1020_stream_stats,0,sizeof(hp1020_stream_stats));
    hp1020_stream_stats[6]=hp1020_stream_stats[20]=2166136261u;
    hp1020_stream_stats[14]=sizeof(state);hp1020_stream_stats[15]=sizeof(memory.data);
    uint32_t r=hp1020_image_stream_init(&state,&memory.data,band_out,0);
    inner_consumer=state.parser.consume_chunk;state.parser.consume_chunk=chunk_observer;
    return r;
}
uint32_t hp1020_stream_feed(uint32_t length,uint32_t fragment) {
    uint32_t r=state.parser.error;
    if(length>sizeof(hp1020_stream_input) || !fragment)return HP1020_LIMIT;
    for(uint32_t pos=0;pos<length;) {
        uint32_t n=length-pos;if(n>fragment)n=fragment;
        r=hp1020_image_stream_feed(&state,hp1020_stream_input+pos,n);
        if(r)break;
        pos+=n;
    }
    /* The caller's packet storage is also immediately reusable. */
    memset(hp1020_stream_input,fill_value^0xff,length);
    return r;
}
uint32_t hp1020_stream_finish(void) {
    uint32_t *o=hp1020_stream_stats;
    o[0]=hp1020_image_stream_finish(&state);o[1]=state.parser.documents;o[2]=state.pages;
    o[7]=state.parser.raster_count;o[8]=state.peak_compressed_chunk;o[9]=state.parser.arena_used;
    o[11]=1;
    for(uint32_t i=0;i<16;i++)if(memory.before[i]!=fill_value || memory.after[i]!=fill_value)o[11]=0;
    o[12]=state.image_result;o[13]=state.output_error;
    o[16]=state.image.pending;
    if(o[0])o[19]=(hp1020_image_stream_feed(&state,NULL,0)==o[0] && hp1020_image_stream_finish(&state)==o[0]);
    else o[19]=(hp1020_image_stream_finish(&state)==HP1020_OK);
    for(uint32_t i=0;i<sizeof(state.parser.rasters);i++)if(((uint8_t *)state.parser.rasters)[i])o[10]++;
    if(!o[0] && state.parser.page_count) {
        struct hp1020_image_page bridge;
        o[22]=hp1020_image_page_init(&bridge,&state.parser,0,memory.data.history,sizeof(memory.data.history),
            memory.data.band,sizeof(memory.data.band));
    }
    return o[0];
}
