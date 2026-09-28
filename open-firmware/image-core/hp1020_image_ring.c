/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image_ring.h"
#include <string.h>
enum { FREE, READY, ACCEPTED };
static enum hp1020_ring_result invalid(struct hp1020_image_ring *r) {
    return r->error=HP1020_RING_INVALID;
}
enum hp1020_ring_result hp1020_image_ring_init(struct hp1020_image_ring *r,
    uint32_t width,uint32_t rows,uint8_t *storage,size_t size) {
    memset(r,0,sizeof(*r));
    if(!storage || !width || width>16384 || (width&31u) || !rows || rows>16384)
        return invalid(r);
    r->stride=width/8;r->rows=rows;
    r->capacity_rows=(8192u/r->stride)&~3u;
    r->slot_bytes=r->capacity_rows*r->stride;
    if(size<HP1020_IMAGE_RING_SLOTS*r->slot_bytes)return invalid(r);
    r->storage=storage;
    return HP1020_RING_OK;
}
enum hp1020_ring_result hp1020_image_ring_push(struct hp1020_image_ring *r,
    const uint8_t *pixels,uint32_t first,uint32_t rows) {
    if(r->error)return r->error;
    uint32_t n=r->rows-r->copied_rows;
    if(n>r->capacity_rows)n=r->capacity_rows;
    if(!pixels || !n || first!=r->copied_rows || rows!=n)return invalid(r);
    struct hp1020_ring_slot *s=&r->slots[r->producer];
    if(s->state!=FREE)return HP1020_RING_BLOCKED;
    memcpy(r->storage+r->producer*r->slot_bytes,pixels,rows*r->stride);
    s->first=first;s->rows=rows;s->final=first+rows==r->rows;s->state=READY;
    r->copied_rows+=rows;r->producer=(r->producer+1)&3u;
    return HP1020_RING_OK;
}
enum hp1020_ring_result hp1020_image_ring_peek(const struct hp1020_image_ring *r,
    struct hp1020_ring_view *view) {
    if(r->error)return r->error;
    if(!view)return HP1020_RING_INVALID;
    const struct hp1020_ring_slot *s=&r->slots[r->selection];
    if(s->state!=READY)return HP1020_RING_EMPTY;
    if(((r->selection+1)&3u)==r->producer && !s->final)return HP1020_RING_BLOCKED;
    view->pixels=r->storage+r->selection*r->slot_bytes;
    view->index=r->selection;view->first=s->first;view->rows=s->rows;view->final=s->final;
    return HP1020_RING_OK;
}
enum hp1020_ring_result hp1020_image_ring_accept(struct hp1020_image_ring *r,uint32_t index) {
    if(r->error)return r->error;
    struct hp1020_ring_view view;
    if(hp1020_image_ring_peek(r,&view)!=HP1020_RING_OK || index!=view.index)return invalid(r);
    r->slots[index].state=ACCEPTED;r->accepted_rows+=view.rows;
    r->selection=(r->selection+1)&3u;
    return HP1020_RING_OK;
}
enum hp1020_ring_result hp1020_image_ring_complete(struct hp1020_image_ring *r,uint32_t index) {
    if(r->error)return r->error;
    if(index!=r->completion || r->slots[index].state!=ACCEPTED)return invalid(r);
    r->completed_rows+=r->slots[index].rows;r->slots[index].state=FREE;
    r->completion=(r->completion+1)&3u;
    return HP1020_RING_OK;
}
int hp1020_image_ring_drained(const struct hp1020_image_ring *r) {
    return !r->error && r->rows && r->completed_rows==r->rows;
}
