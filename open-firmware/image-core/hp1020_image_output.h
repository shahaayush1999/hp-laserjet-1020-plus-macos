/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_OUTPUT_H
#define HP1020_IMAGE_OUTPUT_H
#include "hp1020_image_stream.h"
#include "hp1020_image_ring.h"

struct hp1020_image_output_memory {
    struct hp1020_image_stream_memory stream;
    uint8_t slots[HP1020_IMAGE_RING_SLOTS * HP1020_IMAGE_MAX_BAND_BYTES];
};

/* Called synchronously when space or validated END_PAGE requires output progress.
 * Use only ring_peek/accept/complete on the ring. Returning OK must advance
 * acceptance or completion. Waiting, timeout and cancellation belong to the
 * consumer; they must not be reported as successful completion. The consumer
 * must not re-enter this pipeline. The plan includes copies as metadata only:
 * this component decodes each page once and does not implement copy replay. */
typedef enum hp1020_result (*hp1020_output_progress)(
    const struct hp1020_page_plan *, struct hp1020_image_ring *, void *context);

struct hp1020_output_document {
    uint32_t document_id; /* One-based, within this output lifetime. */
    uint32_t first_page;  /* Zero-based cumulative encoded-page offset. */
    uint32_t pages;       /* Zero for empty documents; copies are not replayed. */
};
/* Optional synchronous notification after valid END_DOC and software completion
 * of every prior page. The event is borrowed only during this call: copy its
 * values if retaining it. Returning OK accepts the notification; only then is
 * documents_completed advanced. Error stops input with no retry or rollback.
 * This is not a physical page/job completion or a quiescence promise. */
typedef enum hp1020_result (*hp1020_output_document_consumer)(
    const struct hp1020_output_document *,void *context);

struct hp1020_image_output {
    struct hp1020_image_stream stream;
    struct hp1020_image_ring ring;
    struct hp1020_page_plan plan;
    struct hp1020_image_output_memory *memory;
    hp1020_output_progress progress;
    void *context;
    hp1020_output_document_consumer consume_document;
    void *document_context;
    uint32_t page_index, pages_drained;
    uint32_t documents_completed, document_first_page;
    enum hp1020_result error;
    uint8_t active, finished;
};

/* Single-context, caller-owned stationary nonoverlapping objects and input.
 * No allocation, scheduler, device I/O or retained full page. Reinitialization
 * requires the previous consumer to be quiescent and old output drained or
 * explicitly abandoned. An error preserves outstanding slot ownership; it does
 * not cancel real transfers or make their memory safe to reuse. */
enum hp1020_result hp1020_image_output_init(struct hp1020_image_output *,
    struct hp1020_image_output_memory *, hp1020_output_progress, void *context);
/* Original initializer wraps this with NULL document notification. Both drain
 * pages at validated END_PAGE and count every validated/completed END_DOC.
 * END_DOC keeps admission open; callbacks may inspect but must not re-enter or
 * mutate the component. The two callback contexts are independently supplied. */
enum hp1020_result hp1020_image_output_init_documents(struct hp1020_image_output *,
    struct hp1020_image_output_memory *,hp1020_output_progress,void *progress_context,
    hp1020_output_document_consumer,void *document_context);
enum hp1020_result hp1020_image_output_feed(struct hp1020_image_output *,
    const uint8_t *, size_t);

/* Explicit whole-input EOF only, not needed after normal END_DOC. Requires valid
 * framing and completion of all pages/documents. A valid page may already have
 * drained before missing END_DOC is discovered here; no document completion is
 * invented. Success is software consumption, never printing. Successful finish
 * is idempotent; feeding afterwards is a sticky FINISHED. */
enum hp1020_result hp1020_image_output_finish(struct hp1020_image_output *);
#endif
