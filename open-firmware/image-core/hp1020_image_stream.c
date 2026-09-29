/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image_stream.h"
#include <string.h>
static enum hp1020_result image_error(struct hp1020_image_stream *s,enum hp1020_image_result r) {
    s->image_result=r;
    if(r==HP1020_IMAGE_LIMIT)return HP1020_LIMIT;
    if(r==HP1020_IMAGE_UNSUPPORTED)return HP1020_UNSUPPORTED;
    if(r==HP1020_IMAGE_TRUNCATED)return HP1020_TRUNCATED;
    return HP1020_FORMAT;
}
static enum hp1020_result band_out(struct hp1020_image_stream *s) {
    if(!s->image.pending)return HP1020_OK;
    if(s->bands==UINT32_MAX || s->image.band_rows>UINT32_MAX-s->rows)return HP1020_LIMIT;
    enum hp1020_result r=s->consume_band(&s->plan,&s->image,s->parser.page_count-1,s->consumer_context);
    if(r) { s->output_error=r; return r; }
    s->bands++;s->rows+=s->image.band_rows;
    enum hp1020_image_result ir=hp1020_image_release(&s->image);
    return ir>=HP1020_IMAGE_FORMAT ? image_error(s,ir) : HP1020_OK;
}
static enum hp1020_result boundary_out(struct hp1020_image_stream *s,
    enum hp1020_stream_boundary boundary) {
    if(!s->consume_boundary)return HP1020_OK;
    enum hp1020_result r=s->consume_boundary(boundary,s->parser.documents,
        s->pages,s->consumer_context);
    if(r)s->output_error=r;
    return r;
}
static enum hp1020_result chunk_in(const struct hp1020_semantic *parser,
    const uint8_t *data,uint32_t size,void *context) {
    struct hp1020_image_stream *s=context;
    enum hp1020_image_result r;
    switch(parser->chunk_type) {
    case 4: {
        /* Planning now precedes END_PAGE. Only a local copy is marked complete
         * for geometry admission; the real parser/page remains unfinished. */
        const struct hp1020_page *current=hp1020_semantic_current_page(parser);
        if(!current)return HP1020_ORDER;
        struct hp1020_page p=*current;p.complete=1;
        enum hp1020_plan_result pr=hp1020_plan_page(&p,&s->plan);
        if(pr!=HP1020_PLAN_OK)return pr==HP1020_PLAN_INVALID ? HP1020_FORMAT : HP1020_UNSUPPORTED;
        if(p.bih_xd&31u)return HP1020_UNSUPPORTED;
        r=hp1020_image_init(&s->image,p.bih,s->memory->history,sizeof(s->memory->history),
            s->memory->band,sizeof(s->memory->band),s->plan.chunk_rows);
        if(r!=HP1020_IMAGE_MORE)return image_error(s,r);
        s->payload_consumed=0;s->padding=0;s->jbig_ended=0;s->active=1;
        s->image_result=r;
        break;
    }
    case 5: {
        if(!s->active || s->jbig_ended)return HP1020_ORDER;
        if(size>s->peak_compressed_chunk)s->peak_compressed_chunk=size;
        size_t pos=0;
        while(pos<size) {
            size_t used=0;
            if(s->image.decoded) {
                if(size-pos>19-s->padding)return HP1020_FORMAT;
                while(pos<size) { if(data[pos++])return HP1020_FORMAT; s->padding++; }
                break;
            }
            r=hp1020_image_feed(&s->image,data+pos,size-pos,&used);
            if(used>size-pos)return HP1020_FORMAT;
            pos+=used;s->payload_consumed+=(uint32_t)used;s->image_result=r;
            if(r>=HP1020_IMAGE_FORMAT)return image_error(s,r);
            enum hp1020_result out=band_out(s);if(out)return out;
            if(r==HP1020_IMAGE_MORE && !used)return HP1020_FORMAT;
        }
        break;
    }
    case 6:
        do {
            r=hp1020_image_finish(&s->image);s->image_result=r;
            if(r>=HP1020_IMAGE_FORMAT)return image_error(s,r);
            enum hp1020_result out=band_out(s);if(out)return out;
        } while(r==HP1020_IMAGE_BAND);
        if(r!=HP1020_IMAGE_DONE || s->padding!=16+((0u-s->payload_consumed)&3u))return HP1020_FORMAT;
        s->jbig_ended=1;
        break;
    case 3:
        if(!s->active || !s->jbig_ended)return HP1020_ORDER;
        if(s->pages==UINT32_MAX)return HP1020_LIMIT;
        if(parser->page_count!=s->pages+1)return HP1020_ORDER;
        s->active=0;s->pages++;
        return boundary_out(s,HP1020_STREAM_PAGE_END);
    case 1:
        /* The semantic parser already validated END_DOC and closed its
         * framing. Observe it now, before the next START_DOC shares this feed. */
        if(s->active || s->pages!=parser->page_count)return HP1020_ORDER;
        return boundary_out(s,HP1020_STREAM_DOCUMENT_END);
    default: break;
    }
    return HP1020_OK;
}
enum hp1020_result hp1020_image_stream_init(struct hp1020_image_stream *s,
    struct hp1020_image_stream_memory *memory,hp1020_band_consumer consume,void *context) {
    return hp1020_image_stream_init_boundaries(s,memory,consume,NULL,context);
}
enum hp1020_result hp1020_image_stream_init_boundaries(struct hp1020_image_stream *s,
    struct hp1020_image_stream_memory *memory,hp1020_band_consumer consume,
    hp1020_stream_boundary_consumer boundary,void *context) {
    memset(s,0,sizeof(*s));
    if(!memory || !consume)return s->parser.error=HP1020_LIMIT;
    s->memory=memory;s->consume_band=consume;s->consumer_context=context;
    s->consume_boundary=boundary;
    hp1020_semantic_init_streaming(&s->parser,memory->compressed,sizeof(memory->compressed),chunk_in,s);
    return s->parser.error;
}
enum hp1020_result hp1020_image_stream_feed(struct hp1020_image_stream *s,const uint8_t *data,size_t size) {
    return hp1020_semantic_feed(&s->parser,data,size);
}
enum hp1020_result hp1020_image_stream_finish(struct hp1020_image_stream *s) {
    return hp1020_semantic_finish(&s->parser);
}
