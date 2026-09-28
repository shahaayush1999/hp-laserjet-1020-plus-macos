/* SPDX-License-Identifier: GPL-2.0-or-later
 * Serialized RAM fixture: compressed input -> C decoder -> C output ring.
 * The consumer explicitly accepts/completes slots; no physical output exists. */
#include "hp1020_image.h"
#include "hp1020_image_ring.h"
#include <string.h>
uint8_t hp1020_ring_input[131072],hp1020_ring_capture[262144];
uint8_t hp1020_ring_storage[32768+32];
uint32_t hp1020_ring_stats[24],hp1020_ring_trace[512][18];
static struct hp1020_image image;
static struct hp1020_image_ring ring;
static uint8_t history[4096+32],band[8192+32],fragment_copy[131072],stalled_storage[32768];
#ifdef HP1020_IMAGE_HOST_CHECK
void hp1020_ring_observe(const uint8_t *,uint32_t);
#endif
static void check(int pass) { if(!pass)hp1020_ring_stats[10]++; }
static void trace(uint32_t phase) {
    uint32_t *o=hp1020_ring_stats;
    if(o[13]>=512) { o[10]++;return; }
    uint32_t *t=hp1020_ring_trace[o[13]++];
    t[0]=phase;t[1]=ring.producer;t[2]=ring.selection;t[3]=ring.completion;
    t[4]=ring.rows-ring.copied_rows;t[5]=ring.rows-ring.accepted_rows;
    for(uint32_t i=0;i<4;i++) {
        t[6+i*3]=!!ring.slots[i].state;
        t[7+i*3]=ring.slots[i].final;t[8+i*3]=ring.slots[i].rows;
    }
}
static int guard(const uint8_t *p,uint32_t size,uint8_t fill) {
    for(uint32_t i=0;i<16;i++)if(p[i]!=fill || p[16+size+i]!=fill)return 0;
    return 1;
}
static uint32_t accept(void) {
    struct hp1020_ring_view v;
    if(hp1020_image_ring_peek(&ring,&v)!=HP1020_RING_OK) { check(0);return 4; }
    uint32_t *o=hp1020_ring_stats,bytes=v.rows*ring.stride;
    check(v.first==ring.accepted_rows && v.index<4 && bytes<=ring.slot_bytes);
#ifdef HP1020_IMAGE_HOST_CHECK
    hp1020_ring_observe(v.pixels,bytes);
#endif
    for(uint32_t i=0;i<bytes;i++) {
        uint8_t b=v.pixels[i];o[8]=(o[8]^b)*16777619u;
        if(o[7]<sizeof(hp1020_ring_capture))hp1020_ring_capture[o[7]]=b;
        o[7]++;
    }
    check(hp1020_image_ring_accept(&ring,v.index)==HP1020_RING_OK);
    o[6]++;trace(4);return v.index;
}
static void complete(uint32_t index) {
    check(hp1020_image_ring_complete(&ring,index)==HP1020_RING_OK);trace(6);
}

uint32_t hp1020_ring_run(uint32_t length,uint32_t fragment,uint32_t fill,uint32_t reserved) {
    uint32_t *o=hp1020_ring_stats;uint8_t byte=(uint8_t)fill;(void)reserved;
    memset(o,0,sizeof(hp1020_ring_stats));memset(hp1020_ring_trace,0,sizeof(hp1020_ring_trace));
    memset(&image,byte,sizeof(image));memset(&ring,byte,sizeof(ring));
    memset(history,byte,sizeof(history));memset(band,byte,sizeof(band));
    memset(hp1020_ring_storage,byte,sizeof(hp1020_ring_storage));
    memset(hp1020_ring_capture,byte,sizeof(hp1020_ring_capture));
    o[8]=2166136261u;o[14]=sizeof(image);o[15]=sizeof(ring);
    if(length<20 || length>sizeof(hp1020_ring_input) || !fragment || fragment>sizeof(fragment_copy))
        return o[0]=HP1020_IMAGE_LIMIT;
    const uint8_t *p=hp1020_ring_input;
    uint32_t width=(uint32_t)p[4]<<24 | (uint32_t)p[5]<<16 | (uint32_t)p[6]<<8 | p[7];
    uint32_t rows=(uint32_t)p[8]<<24 | (uint32_t)p[9]<<16 | (uint32_t)p[10]<<8 | p[11];
    if(hp1020_image_ring_init(&ring,width,rows,hp1020_ring_storage+16,32768)!=HP1020_RING_OK)
        return o[1]=HP1020_RING_INVALID;
    enum hp1020_image_result r=hp1020_image_init(&image,p,history+16,2*ring.stride,
        band+16,ring.slot_bytes,ring.capacity_rows);
    o[16]=2*ring.stride+ring.slot_bytes*5;trace(0);
    uint32_t pos=20,iterations=0;
    while(r<HP1020_IMAGE_DONE) {
        if(r==HP1020_IMAGE_BAND) {
            memcpy(stalled_storage,hp1020_ring_storage+16,sizeof(stalled_storage));
            enum hp1020_ring_result sent=hp1020_image_ring_push(&ring,image.band,image.band_first,image.band_rows);
            if(sent==HP1020_RING_BLOCKED) {
                check(!memcmp(stalled_storage,hp1020_ring_storage+16,sizeof(stalled_storage)));
                o[9]++;trace(3);
                struct hp1020_image_ring before=ring;
                size_t used=99;uint32_t first=image.band_first,count=image.band_rows;
                check(hp1020_image_feed(&image,hp1020_ring_input,20,&used)==HP1020_IMAGE_BAND && !used);
                check(hp1020_image_finish(&image)==HP1020_IMAGE_BAND);
                check(image.band_first==first && image.band_rows==count && !memcmp(&ring,&before,sizeof(ring)));
                uint32_t index=accept();if(index>=4)break;
                before=ring;
                check(hp1020_image_ring_push(&ring,image.band,first,count)==HP1020_RING_BLOCKED);
                check(!memcmp(&ring,&before,sizeof(ring)));
                check(!memcmp(stalled_storage,hp1020_ring_storage+16,sizeof(stalled_storage)));trace(5);
                complete(index);
                sent=hp1020_image_ring_push(&ring,image.band,first,count);
            }
            if(sent!=HP1020_RING_OK) { check(0);break; }
            o[5]++;trace(1);
            if(o[5]==1 && !ring.slots[0].final) {
                struct hp1020_ring_view v;
                check(hp1020_image_ring_peek(&ring,&v)==HP1020_RING_BLOCKED);trace(2);
            }
            r=hp1020_image_release(&image);
        } else if(pos<length) {
            size_t size=length-pos,used=0;if(size>fragment)size=fragment;
            memcpy(fragment_copy,hp1020_ring_input+pos,size);
            r=hp1020_image_feed(&image,fragment_copy,size,&used);
            check(used<=size && (r!=HP1020_IMAGE_MORE || used));
            check(!memcmp(fragment_copy,hp1020_ring_input+pos,size));
            memset(fragment_copy,byte^0xff,size);pos+=(uint32_t)used;
        } else r=hp1020_image_finish(&image);
        if(++iterations>length+rows*12u+64u) { check(0);break; }
    }
    if(r==HP1020_IMAGE_DONE) {
        while(ring.completed_rows<rows) {
            uint32_t index=accept();if(index>=4)break;
            complete(index);
        }
        check(hp1020_image_finish(&image)==HP1020_IMAGE_DONE);
        check(hp1020_image_ring_drained(&ring));trace(7);
    }
    o[0]=r;o[1]=ring.error;o[2]=ring.copied_rows;o[3]=ring.accepted_rows;o[4]=ring.completed_rows;
    o[11]=guard(history,2*ring.stride,byte)&&guard(band,ring.slot_bytes,byte)
        && guard(hp1020_ring_storage,32768,byte);
    o[12]=pos;o[17]=image.pending;o[18]=hp1020_image_ring_drained(&ring);
    o[19]=ring.capacity_rows;o[20]=ring.slot_bytes;
    o[21]=ring.producer;o[22]=ring.selection;o[23]=ring.completion;
    return o[0];
}

/* Invalid caller actions must never release an owned slot. These are API
 * rejection controls, distinct from valid image delivery. */
uint32_t hp1020_ring_api_control(uint32_t which) {
    enum hp1020_ring_result r;
    uint32_t width=9600,rows=17,size=32768;
    memset(hp1020_ring_storage,0xcc,sizeof(hp1020_ring_storage));
    memset(band,0x55,sizeof(band));
    if(which==0)width=31;
    if(which==1)width=0xffffffffu;
    if(which==2)rows=0;
    if(which==3)size=19199;
    r=hp1020_image_ring_init(&ring,width,rows,hp1020_ring_storage+16,size);
    if(which>=4) {
        if(r!=HP1020_RING_OK)return 0;
        if(which==4)r=hp1020_image_ring_push(&ring,band,1,4);
        else if(which==5)r=hp1020_image_ring_push(&ring,band,0,3);
        else if(which==6)r=hp1020_image_ring_accept(&ring,0);
        else if(which>=7 && which<=10) {
            if(hp1020_image_ring_push(&ring,band,0,4)!=HP1020_RING_OK)return 0;
            if(which==7)r=hp1020_image_ring_complete(&ring,0);
            else {
                if(hp1020_image_ring_push(&ring,band,4,4)!=HP1020_RING_OK ||
                   hp1020_image_ring_accept(&ring,0)!=HP1020_RING_OK)return 0;
                if(which==8)r=hp1020_image_ring_complete(&ring,0xffffffffu);
                if(which==9)r=hp1020_image_ring_accept(&ring,0);
                if(which==10) {
                    if(hp1020_image_ring_complete(&ring,0)!=HP1020_RING_OK)return 0;
                    r=hp1020_image_ring_complete(&ring,0);
                }
            }
        } else return 0;
    }
    if(r!=HP1020_RING_INVALID || ring.error!=r)return 0;
    struct hp1020_image_ring before=ring;
    memcpy(stalled_storage,hp1020_ring_storage+16,sizeof(stalled_storage));
    struct hp1020_ring_view v;
    if(hp1020_image_ring_push(&ring,band,0,4)!=r || hp1020_image_ring_peek(&ring,&v)!=r ||
       hp1020_image_ring_accept(&ring,0)!=r || hp1020_image_ring_complete(&ring,0)!=r ||
       hp1020_image_ring_drained(&ring))return 0;
    if(memcmp(&before,&ring,sizeof(ring)) ||
       memcmp(stalled_storage,hp1020_ring_storage+16,sizeof(stalled_storage)))return 0;
    if(which>=7 && which<=9 && ring.slots[0].state==0)return 0;
    return guard(hp1020_ring_storage,32768,0xcc);
}
