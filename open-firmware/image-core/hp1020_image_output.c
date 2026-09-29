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
    while(!hp1020_image_ring_drained(&s->ring)) {
        enum hp1020_result r=progress(s);
        if(r)return r;
    }
    s->active=0;s->pages_drained++;
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
    memset(s,0,sizeof(*s));
    if(!memory || !consumer)return s->error=HP1020_LIMIT;
    s->memory=memory;s->progress=consumer;s->context=context;
    return s->error=hp1020_image_stream_init(&s->stream,&memory->stream,consume,s);
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
    if(!s->error)s->finished=1;
    return s->error;
}
