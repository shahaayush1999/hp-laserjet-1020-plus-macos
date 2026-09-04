#include "hp1020_semantic.h"
#include <string.h>

/* Deliberately no allocation, USB, queues, physical addresses, or output API. */
static uint32_t be32(const uint8_t *p) {
    return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3];
}
static uint32_t be16(const uint8_t *p) { return (uint32_t)p[0]<<8 | p[1]; }
static enum hp1020_result fail(struct hp1020_semantic *s, enum hp1020_result e) {
    s->error=e;
    return e;
}
enum { EXPECT_DOC, EXPECT_PAGE_OR_END, EXPECT_BIH, EXPECT_BID, EXPECT_END_PAGE };

void hp1020_semantic_init(struct hp1020_semantic *s, uint8_t *arena, uint32_t capacity) {
    memset(s,0,sizeof(*s));
    s->arena=arena;
    s->arena_capacity=capacity;
    if (!arena && capacity) s->error=HP1020_LIMIT;
}

static enum hp1020_result items(struct hp1020_semantic *s, struct hp1020_page *page) {
    uint32_t pos=0, seen=0;
    /* The daily foo2zjs path uses uint32 items. The reserved word is not
       authoritative: logical-clip streams add items without increasing it.
       Parse exactly item_count items bounded by the actual chunk size. */
    for (uint32_t i=0;i<s->item_count;i++) {
        if (s->payload_size-pos<12) return fail(s,HP1020_FORMAT);
        const uint8_t *p=s->metadata+pos;
        uint32_t size=be32(p), id=be16(p+4), value=be32(p+8);
        if (size!=12 || p[6]!=1 || p[7]!=0) return fail(s,HP1020_UNSUPPORTED);
        if (id>0x17) return fail(s,HP1020_UNSUPPORTED);
        uint32_t bit=UINT32_C(1)<<id;
        if (seen&bit) return fail(s,HP1020_FORMAT);
        seen|=bit;
        if (page) {
            page->item_values[id]=value;
            switch(id) {
            case 4: page->copies=value; break;
            case 7: page->nbie=value; break;
            case 8: page->resolution_x=value; break;
            case 9: page->resolution_y=value; break;
            case 12: page->raster_x=value; break;
            case 13: page->raster_y=value; break;
            case 16: page->host_video_bpp=value; break;
            case 17: page->host_video_x=value; break;
            case 18: page->host_video_y=value; break;
            default: break; /* Supported metadata outside the current work fields. */
            }
        }
        pos+=size;
    }
    if (pos!=s->payload_size) return fail(s,HP1020_FORMAT);
    if (page) page->item_present=seen;
    return HP1020_OK;
}

static enum hp1020_result complete_chunk(struct hp1020_semantic *s) {
    struct hp1020_page *p=s->page_count ? &s->pages[s->page_count-1] : NULL;
    switch(s->chunk_type) {
    case 0:
        if (items(s,NULL)) return s->error;
        if (s->documents==UINT32_MAX) return fail(s,HP1020_LIMIT);
        s->documents++; s->document_open=1; s->phase=EXPECT_PAGE_OR_END;
        break;
    case 1:
        s->document_open=0; s->phase=EXPECT_DOC; s->framing=0; s->magic=0;
        return HP1020_OK;
    case 2:
        if (s->page_count==HP1020_MAX_PAGES) return fail(s,HP1020_LIMIT);
        p=&s->pages[s->page_count];
        memset(p,0,sizeof(*p)); p->copies=1;
        if (items(s,p)) return s->error;
        if (!p->copies || p->copies>UINT16_MAX || p->nbie!=1 ||
            !p->resolution_x || !p->resolution_y) return fail(s,HP1020_UNSUPPORTED);
        p->work_remaining_units=(uint16_t)p->host_video_y;
        p->work_ret=(uint16_t)p->item_values[22];
        p->work_economode=(uint16_t)p->item_values[23];
        p->video_sideband_known=1;
        p->stock_metadata_bounded=s->reserved>=s->payload_size;
        p->first_raster=s->raster_count;
        s->page_count++; s->phase=EXPECT_BIH;
        break;
    case 3:
        p->complete=1; s->phase=EXPECT_PAGE_OR_END;
        break;
    case 4: {
        const uint8_t *b=s->metadata;
        /* Single-layer, single-plane BIH used by the tested foo2zjs path. */
        if (b[0] || b[1] || b[2]!=1 || b[3]) return fail(s,HP1020_UNSUPPORTED);
        p->bih_xd=be32(b+4); p->bih_yd=be32(b+8); p->bih_l0=be32(b+12);
        p->bih_options=b[19];
        if (!p->bih_xd || p->bih_xd>UINT32_MAX-31u || !p->bih_yd || !p->bih_l0)
            return fail(s,HP1020_FORMAT);
        s->phase=EXPECT_BID;
        break;
    }
    case 5: {
        struct hp1020_raster *node=&s->rasters[s->raster_count++];
        node->page=s->page_count-1;
        node->offset=s->arena_used-s->payload_size;
        node->length=s->payload_size;
        p->raster_count++; p->compressed_bytes+=s->payload_size;
        break;
    }
    case 6:
        if (!p->raster_count) return fail(s,HP1020_ORDER);
        s->phase=EXPECT_END_PAGE;
        break;
    default: return fail(s,HP1020_UNSUPPORTED);
    }
    s->framing=1;
    return HP1020_OK;
}

static enum hp1020_result begin_chunk(struct hp1020_semantic *s) {
    uint32_t size=be32(s->header);
    s->chunk_type=be32(s->header+4); s->item_count=be32(s->header+8);
    s->reserved=be16(s->header+12);
    if (be16(s->header+14)!=0x5a5a || size<16) return fail(s,HP1020_FORMAT);
    if (size>HP1020_MAX_CHUNK_BYTES) return fail(s,HP1020_LIMIT);
    if (s->chunk_type>6) return fail(s,HP1020_UNSUPPORTED);
    s->payload_size=s->remaining=size-16; s->payload_used=0;
    if (s->reserved>s->payload_size) return fail(s,HP1020_FORMAT);
    if ((s->chunk_type==0 && s->phase!=EXPECT_DOC) ||
        (s->chunk_type==1 && s->phase!=EXPECT_PAGE_OR_END) ||
        (s->chunk_type==2 && s->phase!=EXPECT_PAGE_OR_END) ||
        (s->chunk_type==3 && s->phase!=EXPECT_END_PAGE) ||
        (s->chunk_type==4 && s->phase!=EXPECT_BIH) ||
        ((s->chunk_type==5 || s->chunk_type==6) && s->phase!=EXPECT_BID))
        return fail(s,HP1020_ORDER);
    if (s->chunk_type!=0 && s->chunk_type!=2 && (s->item_count || s->reserved)) return fail(s,HP1020_UNSUPPORTED);
    if ((s->chunk_type==1 || s->chunk_type==3 || s->chunk_type==6) && s->payload_size)
        return fail(s,HP1020_FORMAT);
    if (s->chunk_type==4 && s->payload_size!=20) return fail(s,HP1020_FORMAT);
    if (s->chunk_type==5) {
        if (!s->payload_size) return fail(s,HP1020_FORMAT);
        if (s->raster_count==HP1020_MAX_RASTERS || s->payload_size>s->arena_capacity-s->arena_used)
            return fail(s,HP1020_LIMIT);
    } else if (s->payload_size>HP1020_METADATA_BYTES) return fail(s,HP1020_LIMIT);
    s->framing=2;
    return s->remaining ? HP1020_OK : complete_chunk(s);
}

enum hp1020_result hp1020_semantic_feed(struct hp1020_semantic *s,const uint8_t *data,size_t size) {
    if (s->error) return s->error;
    if (s->finalized) return fail(s,HP1020_FINISHED);
    if (!data && size) return fail(s,HP1020_FORMAT);
    for (size_t i=0;i<size;i++) {
        uint8_t b=data[i];
        if (!s->framing) {
            s->magic=(s->magic<<8)|b;
            if (s->magic==UINT32_C(0x4a5a4a5a)) { s->framing=1; s->header_used=0; }
        } else if (s->framing==1) {
            s->header[s->header_used++]=b;
            if (s->header_used==16) {
                s->header_used=0;
                if (begin_chunk(s)) return s->error;
            }
        } else {
            if (s->chunk_type==5) s->arena[s->arena_used++]=b;
            else s->metadata[s->payload_used]=b;
            s->payload_used++;
            if (!--s->remaining && complete_chunk(s)) return s->error;
        }
    }
    return HP1020_OK;
}

enum hp1020_result hp1020_semantic_finish(struct hp1020_semantic *s) {
    if (s->error) return s->error;
    if (s->finalized) return HP1020_OK;
    s->finalized=1;
    if (s->document_open || s->framing || !s->documents) return fail(s,HP1020_TRUNCATED);
    return HP1020_OK;
}
