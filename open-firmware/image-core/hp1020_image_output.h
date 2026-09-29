/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_OUTPUT_H
#define HP1020_IMAGE_OUTPUT_H
#include "hp1020_image_stream.h"
#include "hp1020_image_ring.h"

struct hp1020_image_output_memory {
    struct hp1020_image_stream_memory stream;
    uint8_t slots[HP1020_IMAGE_RING_SLOTS * HP1020_IMAGE_MAX_BAND_BYTES];
};

/* Called synchronously when space or final draining requires output progress.
 * Use only ring_peek/accept/complete on the ring. Returning OK must advance
 * acceptance or completion. Waiting, timeout and cancellation belong to the
 * consumer; they must not be reported as successful completion. The consumer
 * must not re-enter this pipeline. The plan includes copies as metadata only:
 * this component decodes each page once and does not implement copy replay. */
typedef enum hp1020_result (*hp1020_output_progress)(
    const struct hp1020_page_plan *, struct hp1020_image_ring *, void *context);

struct hp1020_image_output {
    struct hp1020_image_stream stream;
    struct hp1020_image_ring ring;
    struct hp1020_page_plan plan;
    struct hp1020_image_output_memory *memory;
    hp1020_output_progress progress;
    void *context;
    uint32_t page_index, pages_drained;
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
enum hp1020_result hp1020_image_output_feed(struct hp1020_image_output *,
    const uint8_t *, size_t);

/* Finish requires valid document framing, successful decoding, and consumer
 * completion of every published row. Previously emitted rows remain provisional
 * on late input errors. Success is software consumption, not a printed page.
 * Successful finish is idempotent; feeding afterwards is a sticky FINISHED. */
enum hp1020_result hp1020_image_output_finish(struct hp1020_image_output *);
#endif
