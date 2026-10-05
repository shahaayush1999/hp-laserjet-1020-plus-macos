/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_PUMP_H
#define HP1020_IMAGE_PUMP_H
#include "../image-core/hp1020_image_stream.h"
#include "../image-core/hp1020_image_ring.h"

/* Cooperative successor to the synchronous output composition. It reuses the
 * semantic parser, page planner, JBIG decoder and output ring. No progress hook
 * can block inside decoding: the outer loop owns all output advancement. */
#define HP1020_PUMP_INPUT_QUANTUM 64u
enum hp1020_pump_result {
    HP1020_PUMP_MORE, HP1020_PUMP_WAIT_OUTPUT, HP1020_PUMP_PAGE,
    HP1020_PUMP_DOCUMENT, HP1020_PUMP_DONE, HP1020_PUMP_ERROR, HP1020_PUMP_STOPPED
};
struct hp1020_image_pump_memory {
    struct hp1020_image_stream_memory decode;
    uint8_t slots[HP1020_IMAGE_RING_SLOTS*HP1020_IMAGE_MAX_BAND_BYTES];
};
struct hp1020_pump_event {
    enum hp1020_pump_result kind;
    uint32_t document_id, first_page, pages;
};
struct hp1020_image_pump {
    struct hp1020_semantic parser;
    struct hp1020_image image;
    struct hp1020_image_ring ring;
    struct hp1020_page_plan plan;
    struct hp1020_image_pump_memory *memory;
    struct hp1020_pump_event event;
    uint32_t chunk_offset, payload_consumed, padding;
    uint32_t pages_completed, documents_completed, document_first_page;
    enum hp1020_result error;
    enum hp1020_image_result image_error;
    uint8_t initialized, pending_chunk, active, jbig_ended, finished, stopped;
};

/* Zero state before first init. State, memory and input must be nonoverlapping
 * and stationary. Serialized calls; no re-entry, allocation or I/O. Reinit is
 * rejected: discarding state is allowed only after independently settling or
 * abandoning all old consumer ownership. Copies remain plan metadata. */
enum hp1020_pump_result hp1020_image_pump_init(struct hp1020_image_pump *,
    struct hp1020_image_pump_memory *);

/* One bounded step: at most64 input bytes OR one decoder call producing at most
 * one <=8192-byte band. A pending band may be copied into the ring first. No
 * loop waits for output. MORE permits the next step. While pending_chunk is set,
 * another step processes owned data and consumes no input; otherwise MORE needs
 * more input. Passing zero input is valid and does not signal end-of-input.
 * Always honor *used, including ERROR. Bytes beyond it remain with the caller;
 * no input pointer is retained. WAIT_OUTPUT consumes no new input. Advance the
 * exposed ring using its ordinary peek/accept/complete operations, with separate
 * actual completion. Acceptance alone cannot release storage. The plan remains
 * stable until the PAGE event is acknowledged. No clock/throughput guarantee. */
enum hp1020_pump_result hp1020_image_pump_feed(struct hp1020_image_pump *,
    const uint8_t *,size_t,size_t *used);

/* PAGE requires validated END_PAGE, decoding/padding and drained software rows.
 * DOCUMENT requires valid END_DOC and every page drained. Neither means paper
 * printed or physical engine completion. Events are retained and block all new
 * input until acknowledged; acknowledgement alone cannot advance output.
 * Read s->event by value. Wrong-kind acknowledgement is a sticky ORDER error. */
enum hp1020_pump_result hp1020_image_pump_ack(struct hp1020_image_pump *,enum hp1020_pump_result);

/* Explicit end-of-input, never a USB short packet/ZLP. Processes one pending
 * step, or returns the retained event/wait, before checking final framing.
 * A late failure cannot retract already consumed rows or prior PAGE events. */
enum hp1020_pump_result hp1020_image_pump_finish(struct hp1020_image_pump *);
/* Fences new work while retaining decoder, chunk, event and all ring ownership.
 * Does not cancel transfers, prove quiescence, release memory or permit restart. */
void hp1020_image_pump_stop(struct hp1020_image_pump *);
#endif
