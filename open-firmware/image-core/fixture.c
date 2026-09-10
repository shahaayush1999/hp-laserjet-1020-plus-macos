/* SPDX-License-Identifier: GPL-2.0-or-later
 * RAM-only test fixture shared by sanitized host and compiled Xtensa checks.
 * Output hashes and a bounded byte capture are observations, not device I/O. */
#include "hp1020_image.h"
#include <string.h>

uint8_t hp1020_image_input[131072];
uint8_t hp1020_image_capture[65536];
uint32_t hp1020_image_stats[24];
struct hp1020_image hp1020_image_state;
static uint8_t history[4096+32], band[8192+32];
static uint8_t fragment_copy[131072];
#ifdef HP1020_IMAGE_HOST_CHECK
void hp1020_image_observe(const uint8_t *,uint32_t);
#endif

static int guarded(const uint8_t *p, uint32_t size, uint8_t fill) {
    for (uint32_t i=0;i<16;i++) if (p[i]!=fill || p[16+size+i]!=fill) return 0;
    return 1;
}
static void collect(struct hp1020_image *s, uint32_t *out) {
    /* A stalled consumer must preserve the pending band and consume no input. */
    size_t used=99;
    if (hp1020_image_feed(s,hp1020_image_input,20,&used)!=HP1020_IMAGE_BAND || used ||
        hp1020_image_finish(s)!=HP1020_IMAGE_BAND || s->band_first!=out[1]) out[10]++;
    out[1]+=s->band_rows; out[2]++;
#ifdef HP1020_IMAGE_HOST_CHECK
    hp1020_image_observe(s->band,s->band_rows*s->stride);
#endif
    for (uint32_t i=0;i<s->band_rows*s->stride;i++) {
        uint8_t b=s->band[i];
        out[3]=(out[3]^b)*16777619u;
        if (out[4]<sizeof(hp1020_image_capture)) hp1020_image_capture[out[4]]=b;
        out[4]++;
    }
    if (!s->band_rows) out[10]++;
    if (s->produced==s->rows) { out[7]++; out[8]=s->band_rows; }
    hp1020_image_release(s);
}

/* flags low byte: RAM fill; bit8: one-byte-short history; bit9: short band.
 * BIT10: release before ready; BIT11: null nonempty input.
 * No source pointer survives a feed: its scratch copy is poisoned on return. */
uint32_t hp1020_image_run(uint32_t length, uint32_t fragment,
                        uint32_t chunk_rows, uint32_t flags) {
    uint32_t *o=hp1020_image_stats;
    struct hp1020_image *s=&hp1020_image_state;
    uint8_t fill=(uint8_t)flags;
    memset(o,0,24*sizeof(*o)); memset(s,fill,sizeof(*s));
    memset(history,fill,sizeof(history)); memset(band,fill,sizeof(band));
    memset(hp1020_image_capture,fill,sizeof(hp1020_image_capture));
    o[3]=2166136261u; o[14]=sizeof(*s);
    if (length>sizeof(hp1020_image_input) || !fragment || fragment>sizeof(fragment_copy))
        return o[0]=HP1020_IMAGE_LIMIT;
    if (length<20) return o[0]=HP1020_IMAGE_TRUNCATED;
    uint32_t width=(uint32_t)hp1020_image_input[4]<<24 |
        (uint32_t)hp1020_image_input[5]<<16 | (uint32_t)hp1020_image_input[6]<<8 | hp1020_image_input[7];
    uint32_t stride=width<=HP1020_IMAGE_MAX_WIDTH_BITS ? (width+7)/8 : 2048;
    uint32_t hsize=2*stride, bsize=chunk_rows && chunk_rows<=8192/(stride ? stride : 1) ? chunk_rows*stride : 8192;
    enum hp1020_image_result r=hp1020_image_init(s,hp1020_image_input,
        history+16,hsize-!!((flags&0x100)&&hsize),band+16,bsize-!!((flags&0x200)&&bsize),chunk_rows);
    o[11]=s->stride; o[12]=s->rows; o[13]=hsize+bsize;
    if (r==HP1020_IMAGE_MORE && (flags&0x400)) r=hp1020_image_release(s);
    if (r==HP1020_IMAGE_MORE && (flags&0x800)) { size_t n; r=hp1020_image_feed(s,NULL,1,&n); }
    uint32_t pos=20;
    while (r<HP1020_IMAGE_DONE) {
        if (r==HP1020_IMAGE_BAND) {
            collect(s,o); r=s->decoded ? HP1020_IMAGE_DONE : HP1020_IMAGE_MORE;
        } else if (pos<length) {
            size_t n=length-pos,used=0; if (n>fragment) n=fragment;
            memcpy(fragment_copy,hp1020_image_input+pos,n);
            r=hp1020_image_feed(s,fragment_copy,n,&used);
            if (used>n || (r==HP1020_IMAGE_MORE && !used)) return o[0]=HP1020_IMAGE_STATE;
            /* Upstream is not allowed to change any input byte. */
            if (memcmp(fragment_copy,hp1020_image_input+pos,n)) o[10]++;
            memset(fragment_copy,fill^0xff,n);
            pos+=(uint32_t)used;
        } else r=hp1020_image_finish(s);
        if (++o[9]>length+s->rows*4u+64u) return o[0]=HP1020_IMAGE_STATE;
    }
    o[0]=r; o[5]=pos; o[6]=length-pos; o[15]=(uint32_t)s->codec_result;
    o[16]=guarded(history,hsize,fill)&&guarded(band,bsize,fill);
    if (r>=HP1020_IMAGE_FORMAT) {
        size_t used=99;
        o[17]=(hp1020_image_feed(s,NULL,0,&used)==r && used==0 &&
               hp1020_image_release(s)==r && hp1020_image_finish(s)==r);
    } else o[17]=(hp1020_image_finish(s)==HP1020_IMAGE_DONE);
    return o[0];
}
