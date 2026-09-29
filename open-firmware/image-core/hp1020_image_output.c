/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image_output.h"
#include <string.h>

static enum hp1020_result progress(struct hp1020_image_output *s) {
    uint32_t accepted=s->ring.accepted_rows, completed=s->ring.completed_rows;
    enum hp1020_result r=s->progress(&s->plan,&s->ring,s->context);
    if(r)return r;
    if(s->ring.error || (accepted==s->ring.accepted_rows && completed==s->ring.completed_rows))
        return HP1020_ORDER;
    return HP1020_OK;
}

static enum hp1020_result drain(struct hp1020_image_output *s) {
    if(!s->active)return HP1020_OK;
    if(s->pages_drained==UINT32_MAX)return HP1020_LIMIT;
    /* stream.plan may already belong to a later BIH. Only a validated completed
     * page may drain; progress deliberately continues to use our retained plan. */
    if(s->page_index!=s->pages_drained || s->page_index>=s->stream.pages)
        return HP1020_ORDER;
    while(!hp1020_image_ring_drained(&s->ring)) {
        enum hp1020_result r=progress(s);
        if(r)return r;
    }
    s->active=0;s->pages_drained++;
    return HP1020_OK;
}

static enum hp1020_result boundary(enum hp1020_stream_boundary kind,
    uint32_t document_id,uint32_t pages,void *context) {
    struct hp1020_image_output *s=context;
    if(s->error)return s->error;
    /* Check all counters/identities before further external progress. Parser
     * START_DOC/START_PAGE already guard their own cumulative counters. */
    if(s->documents_completed==UINT32_MAX)return HP1020_LIMIT;
    if(document_id!=s->documents_completed+1 || pages!=s->stream.pages)
        return HP1020_ORDER;
    if(kind==HP1020_STREAM_PAGE_END) {
        if(!s->active)return HP1020_ORDER;
        enum hp1020_result r=drain(s);
        if(r)return r;
        return s->pages_drained==pages ? HP1020_OK : HP1020_ORDER;
    }
    if(kind!=HP1020_STREAM_DOCUMENT_END || s->stream.active)return HP1020_ORDER;
    enum hp1020_result r=drain(s);
    if(r)return r;
    if(s->pages_drained!=pages || s->document_first_page>pages)return HP1020_ORDER;
    const struct hp1020_output_document event={document_id,s->document_first_page,
        pages-s->document_first_page};
    if(s->consume_document) {
        r=s->consume_document(&event,s->document_context);
        if(r)return r; /* No retry or successful-notification count on failure. */
    }
    s->documents_completed++;
    s->document_first_page=pages;
    return HP1020_OK;
}

static enum hp1020_result consume(const struct hp1020_page_plan *plan,
    const struct hp1020_image *image,uint32_t index,void *context) {
    struct hp1020_image_output *s=context;
    if(!s->active || index!=s->page_index) {
        enum hp1020_result r=drain(s);
        if(r)return r;
        if(index!=s->pages_drained || image->band_first)return HP1020_ORDER;
        if(hp1020_image_ring_init(&s->ring,image->width_bits,plan->rows,
            s->memory->slots,sizeof(s->memory->slots))!=HP1020_RING_OK)return HP1020_LIMIT;
        if(plan->stride!=s->ring.stride || plan->chunk_rows!=s->ring.capacity_rows)return HP1020_ORDER;
        s->plan=*plan;s->page_index=index;s->active=1;
    }
    for(;;) {
        enum hp1020_ring_result r=hp1020_image_ring_push(&s->ring,image->band,
            image->band_first,image->band_rows);
        if(r==HP1020_RING_OK)return HP1020_OK;
        if(r!=HP1020_RING_BLOCKED)return HP1020_ORDER;
        enum hp1020_result out=progress(s);
        if(out)return out;
    }
}

enum hp1020_result hp1020_image_output_init(struct hp1020_image_output *s,
    struct hp1020_image_output_memory *memory,hp1020_output_progress consumer,void *context) {
    return hp1020_image_output_init_documents(s,memory,consumer,context,NULL,NULL);
}
enum hp1020_result hp1020_image_output_init_documents(struct hp1020_image_output *s,
    struct hp1020_image_output_memory *memory,hp1020_output_progress consumer,void *context,
    hp1020_output_document_consumer document,void *document_context) {
    memset(s,0,sizeof(*s));
    if(!memory || !consumer)return s->error=HP1020_LIMIT;
    s->memory=memory;s->progress=consumer;s->context=context;
    s->consume_document=document;s->document_context=document_context;
    return s->error=hp1020_image_stream_init_boundaries(&s->stream,&memory->stream,consume,boundary,s);
}

enum hp1020_result hp1020_image_output_feed(struct hp1020_image_output *s,const uint8_t *data,size_t size) {
    if(s->error)return s->error;
    if(s->finished)return s->error=HP1020_FINISHED;
    return s->error=hp1020_image_stream_feed(&s->stream,data,size);
}

enum hp1020_result hp1020_image_output_finish(struct hp1020_image_output *s) {
    if(s->error)return s->error;
    if(s->finished)return HP1020_OK;
    s->error=hp1020_image_stream_finish(&s->stream);
    if(!s->error)s->error=drain(s);
    if(!s->error && (s->pages_drained!=s->stream.pages ||
        s->documents_completed!=s->stream.parser.documents))s->error=HP1020_ORDER;
    if(!s->error)s->finished=1;
    return s->error;
}
