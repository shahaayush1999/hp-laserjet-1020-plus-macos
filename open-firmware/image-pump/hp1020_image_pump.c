/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image_pump.h"
#include <string.h>

static enum hp1020_pump_result fail(struct hp1020_image_pump *s,enum hp1020_result r) {
    s->error=r;return HP1020_PUMP_ERROR;
}
static enum hp1020_pump_result image_fail(struct hp1020_image_pump *s,enum hp1020_image_result r) {
    s->image_error=r;
    return fail(s,r==HP1020_IMAGE_LIMIT?HP1020_LIMIT:r==HP1020_IMAGE_UNSUPPORTED?
        HP1020_UNSUPPORTED:r==HP1020_IMAGE_TRUNCATED?HP1020_TRUNCATED:HP1020_FORMAT);
}
static enum hp1020_pump_result gate(struct hp1020_image_pump *s) {
    if(!s || !s->initialized)return HP1020_PUMP_ERROR;
    if(s->stopped)return HP1020_PUMP_STOPPED;
    if(s->error)return HP1020_PUMP_ERROR;
    if(s->ring.error)return fail(s,HP1020_ORDER);
    if(s->event.kind)return s->event.kind;
    return s->finished?HP1020_PUMP_DONE:HP1020_PUMP_MORE;
}
static enum hp1020_result chunk(const struct hp1020_semantic *parser,
    const uint8_t *data,uint32_t size,void *context) {
    struct hp1020_image_pump *s=context;
    (void)data;(void)size;
    if(parser!=&s->parser || s->pending_chunk)return HP1020_ORDER;
    /* Semantic completion releases its arena accounting. The bytes are still
     * ours: no further feed is admitted until this pending chunk is consumed. */
    s->pending_chunk=1;s->chunk_offset=0;return HP1020_OK;
}
enum hp1020_pump_result hp1020_image_pump_init(struct hp1020_image_pump *s,
    struct hp1020_image_pump_memory *m) {
    if(!s || s->initialized || !m)return HP1020_PUMP_ERROR;
    memset(s,0,sizeof(*s));s->memory=m;s->initialized=1;
    hp1020_semantic_init_streaming(&s->parser,m->decode.compressed,
        sizeof(m->decode.compressed),chunk,s);
    return HP1020_PUMP_MORE;
}
static enum hp1020_pump_result publish_band(struct hp1020_image_pump *s) {
    if(!s->image.pending)return HP1020_PUMP_MORE;
    enum hp1020_ring_result r=hp1020_image_ring_push(&s->ring,s->image.band,
        s->image.band_first,s->image.band_rows);
    if(r==HP1020_RING_BLOCKED)return HP1020_PUMP_WAIT_OUTPUT;
    if(r!=HP1020_RING_OK)return fail(s,HP1020_ORDER);
    enum hp1020_image_result released=hp1020_image_release(&s->image);
    return released>=HP1020_IMAGE_FORMAT?image_fail(s,released):HP1020_PUMP_MORE;
}
static enum hp1020_pump_result pending(struct hp1020_image_pump *s) {
    enum hp1020_pump_result out=publish_band(s);
    if(out!=HP1020_PUMP_MORE)return out;
    const uint32_t size=s->parser.payload_size;
    enum hp1020_image_result r;
    switch(s->parser.chunk_type) {
    case 4: {
        const struct hp1020_page *current=hp1020_semantic_current_page(&s->parser);
        if(!current || s->active || s->pages_completed!=s->parser.page_count-1)
            return fail(s,HP1020_ORDER);
        struct hp1020_page page=*current;page.complete=1;
        enum hp1020_plan_result pr=hp1020_plan_page(&page,&s->plan);
        if(pr!=HP1020_PLAN_OK)return fail(s,pr==HP1020_PLAN_INVALID?HP1020_FORMAT:HP1020_UNSUPPORTED);
        if(page.bih_xd&31u)return fail(s,HP1020_UNSUPPORTED);
        r=hp1020_image_init(&s->image,page.bih,s->memory->decode.history,
            sizeof(s->memory->decode.history),s->memory->decode.band,
            sizeof(s->memory->decode.band),s->plan.chunk_rows);
        if(r!=HP1020_IMAGE_MORE)return image_fail(s,r);
        if(hp1020_image_ring_init(&s->ring,page.bih_xd,s->plan.rows,
            s->memory->slots,sizeof(s->memory->slots))!=HP1020_RING_OK)
            return fail(s,HP1020_LIMIT);
        if(s->plan.stride!=s->ring.stride || s->plan.chunk_rows!=s->ring.capacity_rows)
            return fail(s,HP1020_ORDER);
        s->payload_consumed=0;s->padding=0;s->jbig_ended=0;s->active=1;
        break;
    }
    case 5: {
        if(!s->active || s->jbig_ended || s->chunk_offset>size)return fail(s,HP1020_ORDER);
        if(s->chunk_offset==size)break;
        const uint8_t *data=s->memory->decode.compressed;
        if(s->image.decoded) {
            if(size-s->chunk_offset>19-s->padding)return fail(s,HP1020_FORMAT);
            while(s->chunk_offset<size) {
                if(data[s->chunk_offset++])return fail(s,HP1020_FORMAT);
                s->padding++;
            }
            break;
        }
        size_t used=0;
        r=hp1020_image_feed(&s->image,data+s->chunk_offset,size-s->chunk_offset,&used);
        if(used>size-s->chunk_offset || used>UINT32_MAX-s->payload_consumed)
            return fail(s,HP1020_LIMIT);
        s->chunk_offset+=(uint32_t)used;s->payload_consumed+=(uint32_t)used;
        if(r>=HP1020_IMAGE_FORMAT)return image_fail(s,r);
        if(r==HP1020_IMAGE_MORE && !used)return fail(s,HP1020_FORMAT);
        /* Publish on a later step. Its data and unconsumed compressed tail
         * remain stable while the outer loop services other work. */
        return HP1020_PUMP_MORE;
    }
    case 6:
        if(!s->active || s->jbig_ended)return fail(s,HP1020_ORDER);
        r=hp1020_image_finish(&s->image);
        if(r>=HP1020_IMAGE_FORMAT)return image_fail(s,r);
        if(r==HP1020_IMAGE_BAND)return HP1020_PUMP_MORE;
        if(r!=HP1020_IMAGE_DONE || s->padding!=16+((0u-s->payload_consumed)&3u))
            return fail(s,HP1020_FORMAT);
        s->jbig_ended=1;break;
    case 3:
        if(!s->active || !s->jbig_ended || s->pages_completed==UINT32_MAX ||
            s->pages_completed+1!=s->parser.page_count)return fail(s,HP1020_ORDER);
        if(!hp1020_image_ring_drained(&s->ring))return HP1020_PUMP_WAIT_OUTPUT;
        s->event=(struct hp1020_pump_event){HP1020_PUMP_PAGE,s->parser.documents,s->pages_completed,1};
        s->pages_completed++;s->active=0;break;
    case 1:
        if(s->active || s->pages_completed!=s->parser.page_count ||
            s->documents_completed==UINT32_MAX || s->documents_completed+1!=s->parser.documents ||
            s->document_first_page>s->pages_completed)return fail(s,HP1020_ORDER);
        s->event=(struct hp1020_pump_event){HP1020_PUMP_DOCUMENT,s->parser.documents,
            s->document_first_page,s->pages_completed-s->document_first_page};
        s->documents_completed++;s->document_first_page=s->pages_completed;break;
    default:break;
    }
    s->pending_chunk=0;
    return s->event.kind?s->event.kind:HP1020_PUMP_MORE;
}
enum hp1020_pump_result hp1020_image_pump_feed(struct hp1020_image_pump *s,
    const uint8_t *data,size_t size,size_t *used) {
    if(!used)return s && s->initialized?fail(s,HP1020_FORMAT):HP1020_PUMP_ERROR;
    *used=0;
    enum hp1020_pump_result g=gate(s);
    if(g!=HP1020_PUMP_MORE)return g;
    if(!data && size)return fail(s,HP1020_FORMAT);
    if(s->pending_chunk)return pending(s);
    size_t budget=size<HP1020_PUMP_INPUT_QUANTUM?size:HP1020_PUMP_INPUT_QUANTUM;
    while(*used<budget) {
        size_t n=1; /* Scan only until framing is known. */
        if(s->parser.framing==1)n=16-s->parser.header_used;
        else if(s->parser.framing==2)n=s->parser.remaining;
        if(n>budget-*used)n=budget-*used;
        /* This span ends at the current header/payload boundary. The semantic
         * parser cannot reach a second completed chunk in the same feed. */
        enum hp1020_result r=hp1020_semantic_feed(&s->parser,data+*used,n);
        *used+=n;
        if(r)return fail(s,r);
        if(s->pending_chunk)break;
    }
    return HP1020_PUMP_MORE;
}
enum hp1020_pump_result hp1020_image_pump_ack(struct hp1020_image_pump *s,enum hp1020_pump_result kind) {
    enum hp1020_pump_result g=gate(s);
    if(g==HP1020_PUMP_ERROR || g==HP1020_PUMP_STOPPED || g==HP1020_PUMP_DONE)return g;
    if((kind!=HP1020_PUMP_PAGE && kind!=HP1020_PUMP_DOCUMENT) || s->event.kind!=kind)
        return fail(s,HP1020_ORDER);
    s->event=(struct hp1020_pump_event){0};return HP1020_PUMP_MORE;
}
enum hp1020_pump_result hp1020_image_pump_finish(struct hp1020_image_pump *s) {
    enum hp1020_pump_result g=gate(s);
    if(g!=HP1020_PUMP_MORE)return g;
    if(s->pending_chunk)return pending(s);
    enum hp1020_result r=hp1020_semantic_finish(&s->parser);
    if(r)return fail(s,r);
    if(s->active || s->pages_completed!=s->parser.page_count ||
        s->documents_completed!=s->parser.documents)return fail(s,HP1020_ORDER);
    s->finished=1;return HP1020_PUMP_DONE;
}
void hp1020_image_pump_stop(struct hp1020_image_pump *s) {
    if(s && s->initialized)s->stopped=1;
}
