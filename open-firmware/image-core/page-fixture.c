/* SPDX-License-Identifier: GPL-2.0-or-later
 * Complete-file software fixture. No device output, boot or scheduler. */
#include "hp1020_image_page.h"
#include <string.h>
uint8_t hp1020_page_input[131072],hp1020_page_capture[65536];
uint32_t hp1020_page_stats[24];
static struct hp1020_semantic parser;
static struct hp1020_image_page page;
static uint8_t arena[131072],history[4096+32],band[8192+32];
#ifdef HP1020_IMAGE_HOST_CHECK
void hp1020_page_observe(const uint8_t *,uint32_t);
#endif
static uint32_t hash(uint32_t h,const uint8_t *p,uint32_t n) {
    while(n--) h=(h^*p++)*16777619u;
    return h;
}
uint32_t hp1020_page_run(uint32_t length,uint32_t fragment,uint32_t quantum,uint32_t flags) {
    uint32_t *o=hp1020_page_stats; uint8_t fill=(uint8_t)flags;
    memset(o,0,24*sizeof(*o)); memset(history,fill,sizeof(history)); memset(band,fill,sizeof(band));
    memset(hp1020_page_capture,fill,sizeof(hp1020_page_capture));
    o[7]=o[13]=2166136261u; o[14]=sizeof(page);
    if(length>sizeof(hp1020_page_input) || !fragment || !quantum) return o[1]=HP1020_IMAGE_LIMIT;
    hp1020_semantic_init(&parser,arena,sizeof(arena));
    for(uint32_t pos=0;pos<length;) {
        uint32_t n=length-pos; if(n>fragment)n=fragment;
        if(hp1020_semantic_feed(&parser,hp1020_page_input+pos,n))break;
        pos+=n;
    }
    o[0]=(flags&0x100) ? parser.error : hp1020_semantic_finish(&parser);
    o[3]=parser.raster_count; o[12]=parser.arena_used; o[18]=parser.page_count;
    if(o[0])return o[0];
    o[1]=HP1020_IMAGE_DONE;
    if((flags&0x200) && parser.raster_count) parser.rasters[0].offset=UINT32_MAX;
    if((flags&0x400) && parser.raster_count) parser.rasters[0].page=UINT32_MAX;
    if((flags&0x800) && parser.page_count) parser.pages[0].bih[7]^=32;
    for(uint32_t index=0;index<parser.page_count;index++) {
        const struct hp1020_page *p=&parser.pages[index];
        o[13]=hash(o[13],p->bih,20);
        enum hp1020_image_result r=hp1020_image_page_init(&page,&parser,index,
            history+16,4096,band+16,8192);
        uint32_t row=0;
        while(r==HP1020_IMAGE_MORE || r==HP1020_IMAGE_BAND) {
            r=hp1020_image_page_next(&page,quantum);
            if(r!=HP1020_IMAGE_BAND)break;
            if(hp1020_image_page_next(&page,quantum)!=HP1020_IMAGE_BAND || page.image.band_first!=row)o[10]++;
            o[19]++; row+=page.image.band_rows;
            uint32_t bytes=page.image.band_rows*page.image.stride;
#ifdef HP1020_IMAGE_HOST_CHECK
            hp1020_page_observe(page.image.band,bytes);
#endif
            o[7]=hash(o[7],page.image.band,bytes);
            for(uint32_t i=0;i<bytes && o[6]+i<sizeof(hp1020_page_capture);i++)
                hp1020_page_capture[o[6]+i]=page.image.band[i];
            o[4]+=page.image.band_rows;o[5]++;o[6]+=bytes;
            r=hp1020_image_page_release(&page);
        }
        o[1]=r;
        if(r!=HP1020_IMAGE_DONE) {
            o[17]=(hp1020_image_page_next(&page,quantum)==r && hp1020_image_page_release(&page)==r);
            break;
        }
        if(row!=p->bih_yd || hp1020_image_page_next(&page,quantum)!=HP1020_IMAGE_DONE)o[10]++;
        o[2]++;o[8]+=page.plan.copies;o[9]+=page.padding;
    }
    o[11]=1;
    for(uint32_t i=0;i<16;i++)if(history[i]!=fill || history[4112+i]!=fill || band[i]!=fill || band[8208+i]!=fill)o[11]=0;
    return o[1];
}
