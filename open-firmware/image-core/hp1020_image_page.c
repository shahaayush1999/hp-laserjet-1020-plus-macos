/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image_page.h"
#include <string.h>
static enum hp1020_image_result fail(struct hp1020_image_page *s,enum hp1020_image_result e) {
    s->error=e; return e;
}
enum hp1020_image_result hp1020_image_page_init(struct hp1020_image_page *s,
    const struct hp1020_semantic *parser,uint32_t page_index,
    uint8_t *history,size_t history_size,uint8_t *band,size_t band_size) {
    memset(s,0,sizeof(*s));
    if (!parser || !parser->finalized || parser->error || page_index>=parser->page_count ||
        parser->page_count>HP1020_MAX_PAGES || parser->raster_count>HP1020_MAX_RASTERS ||
        !parser->arena || parser->arena_used>parser->arena_capacity)
        return fail(s,HP1020_IMAGE_STATE);
    const struct hp1020_page *p=&parser->pages[page_index];
    enum hp1020_plan_result pr=hp1020_plan_page(p,&s->plan);
    if (pr!=HP1020_PLAN_OK) return fail(s,pr==HP1020_PLAN_INVALID ? HP1020_IMAGE_FORMAT : HP1020_IMAGE_UNSUPPORTED);
    /* The existing planner rounds stride to 32 bits. Until an explicit row
     * padding adapter exists, require the decoder's packed rows to match it. */
    if (p->bih_xd&31u) return fail(s,HP1020_IMAGE_UNSUPPORTED);
    if (p->first_raster>=parser->raster_count || !p->raster_count ||
        p->raster_count>parser->raster_count-p->first_raster)
        return fail(s,HP1020_IMAGE_STATE);
    s->node=p->first_raster; s->end_node=s->node+p->raster_count; s->parser=parser;
    uint32_t bytes=0;
    for (uint32_t i=s->node;i<s->end_node;i++) {
        const struct hp1020_raster *r=&parser->rasters[i];
        if (r->page!=page_index || !r->length || r->offset>parser->arena_used ||
            r->length>parser->arena_used-r->offset || r->length>UINT32_MAX-bytes)
            return fail(s,HP1020_IMAGE_STATE);
        bytes+=r->length;
    }
    if (bytes!=p->compressed_bytes) return fail(s,HP1020_IMAGE_STATE);
    enum hp1020_image_result r=hp1020_image_init(&s->image,p->bih,history,history_size,
        band,band_size,s->plan.chunk_rows);
    if (r!=HP1020_IMAGE_MORE) return fail(s,r);
    if (s->image.width_bits!=p->bih_xd || s->image.rows!=s->plan.rows || s->image.stride!=s->plan.stride)
        return fail(s,HP1020_IMAGE_STATE);
    return HP1020_IMAGE_MORE;
}
enum hp1020_image_result hp1020_image_page_next(struct hp1020_image_page *s,size_t quantum) {
    if (s->error) return s->error;
    if (!quantum || !s->parser) return fail(s,HP1020_IMAGE_STATE);
    if (s->done) return HP1020_IMAGE_DONE;
    if (s->image.pending) return HP1020_IMAGE_BAND;
    while (s->node<s->end_node) {
        const struct hp1020_raster *r=&s->parser->rasters[s->node];
        size_t n=r->length-s->offset; if (n>quantum) n=quantum;
        const uint8_t *data=s->parser->arena+r->offset+s->offset;
        size_t used=0;
        enum hp1020_image_result result=HP1020_IMAGE_DONE;
        if (!s->image.decoded) {
            result=hp1020_image_feed(&s->image,data,n,&used);
            s->consumed+=(uint32_t)used;
        } else {
            if (n>19-s->padding) return fail(s,HP1020_IMAGE_FORMAT);
            for (size_t i=0;i<n;i++) if (data[i]) return fail(s,HP1020_IMAGE_FORMAT);
            s->padding+=(uint32_t)n; used=n;
        }
        if (used>n) return fail(s,HP1020_IMAGE_STATE);
        s->offset+=(uint32_t)used;
        if (s->offset==r->length) { s->offset=0; s->node++; }
        if (result==HP1020_IMAGE_BAND) return result;
        if (result>=HP1020_IMAGE_FORMAT) return fail(s,result);
        if (result==HP1020_IMAGE_MORE && !used) return fail(s,HP1020_IMAGE_STATE);
    }
    enum hp1020_image_result r=hp1020_image_finish(&s->image);
    if (r==HP1020_IMAGE_BAND) return r;
    if (r!=HP1020_IMAGE_DONE) return fail(s,r);
    if (s->padding!=16+((0u-s->consumed)&3u)) return fail(s,HP1020_IMAGE_FORMAT);
    s->done=1; return HP1020_IMAGE_DONE;
}
enum hp1020_image_result hp1020_image_page_release(struct hp1020_image_page *s) {
    if (s->error) return s->error;
    enum hp1020_image_result r=hp1020_image_release(&s->image);
    return r>=HP1020_IMAGE_FORMAT ? fail(s,r) : HP1020_IMAGE_MORE;
}
