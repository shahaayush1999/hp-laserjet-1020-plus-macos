/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_STREAM_H
#define HP1020_IMAGE_STREAM_H
#include "hp1020_image_page.h"

/* foo2zjs uses at most 65536 compressed bytes in a BID; its final BID may add
 * default zero padding through byte 65552. No full compressed page is kept. */
#define HP1020_STREAM_CHUNK_BYTES 65552u
struct hp1020_image_stream_memory {
    uint8_t compressed[HP1020_STREAM_CHUNK_BYTES];
    uint8_t history[4096];
    uint8_t band[8192];
};
typedef enum hp1020_result (*hp1020_band_consumer)(const struct hp1020_page_plan *,
    const struct hp1020_image *,uint32_t page_index,void *context);
enum hp1020_stream_boundary {
    HP1020_STREAM_PAGE_END = 1, HP1020_STREAM_DOCUMENT_END
};
/* Optional synchronous validated-boundary consumer. document_id is one-based;
 * pages is the cumulative completed-page count in this stream, not copies.
 * PAGE_END follows valid decoding/padding and END_PAGE. DOCUMENT_END follows
 * each valid END_DOC, before any bytes of the next document are parsed.
 * No plan/input pointer is lent here. The shared consumer context must remain
 * valid; do not re-enter/mutate this pipeline. An error is sticky and prevents
 * subsequent chunks from being read; already delivered output is not rolled back. */
typedef enum hp1020_result (*hp1020_stream_boundary_consumer)(
    enum hp1020_stream_boundary,uint32_t document_id,uint32_t pages,void *context);
struct hp1020_image_stream {
    struct hp1020_semantic parser;
    struct hp1020_image image;
    struct hp1020_page_plan plan;
    struct hp1020_image_stream_memory *memory;
    hp1020_band_consumer consume_band;
    hp1020_stream_boundary_consumer consume_boundary;
    void *consumer_context;
    uint32_t pages, bands, rows, payload_consumed, padding, peak_compressed_chunk;
    enum hp1020_image_result image_result;
    enum hp1020_result output_error;
    uint8_t active, jbig_ended;
};
/* All objects/buffers must remain valid, stationary and nonoverlapping.
 * The consumer synchronously consumes/copies each band before returning OK.
 * It may block outside this component; no scheduler or asynchronous queue is
 * implemented here. A consumer error aborts the stream and remains sticky.
 * No input pointer survives feed. Bands precede page/document validation and
 * may be followed by late errors. A boundary certifies only its validated
 * prefix, never physical printing or successful future input. */
enum hp1020_result hp1020_image_stream_init(struct hp1020_image_stream *,
    struct hp1020_image_stream_memory *,hp1020_band_consumer,void *context);
/* The original initializer is a wrapper with no boundary consumer. */
enum hp1020_result hp1020_image_stream_init_boundaries(struct hp1020_image_stream *,
    struct hp1020_image_stream_memory *,hp1020_band_consumer,
    hp1020_stream_boundary_consumer,void *context);
enum hp1020_result hp1020_image_stream_feed(struct hp1020_image_stream *,const uint8_t *,size_t);
enum hp1020_result hp1020_image_stream_finish(struct hp1020_image_stream *);
#endif
