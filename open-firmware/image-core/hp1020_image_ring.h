/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_RING_H
#define HP1020_IMAGE_RING_H
#include <stdint.h>
#include <stddef.h>

#define HP1020_IMAGE_RING_SLOTS 4u
enum hp1020_ring_result {
    HP1020_RING_OK, HP1020_RING_BLOCKED, HP1020_RING_EMPTY, HP1020_RING_INVALID
};
struct hp1020_ring_slot {
    uint32_t state, first, rows, final;
};
struct hp1020_image_ring {
    uint8_t *storage;
    uint32_t stride, rows, capacity_rows, slot_bytes;
    uint32_t producer, selection, completion;
    uint32_t copied_rows, accepted_rows, completed_rows;
    enum hp1020_ring_result error;
    struct hp1020_ring_slot slots[HP1020_IMAGE_RING_SLOTS];
};
struct hp1020_ring_view {
    const uint8_t *pixels;
    uint32_t index, first, rows, final;
};

/* Single caller/context, no device addresses, interrupts or synchronization.
 * Objects/storage/input must be valid, stationary and nonoverlapping. The
 * four slots use the recovered callback-disabled geometry for aligned widths.
 * This is software ownership, not a memory layout for the original firmware.
 * Reinitialization discards ownership; the caller must first drain/abandon it. */
enum hp1020_ring_result hp1020_image_ring_init(struct hp1020_image_ring *,
    uint32_t width_bits,uint32_t rows,uint8_t *storage,size_t storage_size);

/* Configure the decoder with capacity_rows. Push exactly a full slot or the
 * remaining final rows, in order. BLOCKED copies nothing: retain the decoder
 * band and retry after completion; release the decoder band only after OK. */
enum hp1020_ring_result hp1020_image_ring_push(struct hp1020_image_ring *,
    const uint8_t *pixels,uint32_t first,uint32_t rows);

/* Like the recovered normal descriptor gate, hold back the newest nonfinal
 * slot until another slot is published. Views remain owned through accept;
 * the caller must report actual completion before storage can be reused.
 * Empty/blocked are ordinary states. Mutating API misuse is a sticky INVALID
 * error; peek is read-only (including its invalid null-view argument). */
enum hp1020_ring_result hp1020_image_ring_peek(const struct hp1020_image_ring *,
    struct hp1020_ring_view *);
enum hp1020_ring_result hp1020_image_ring_accept(struct hp1020_image_ring *,uint32_t index);
enum hp1020_ring_result hp1020_image_ring_complete(struct hp1020_image_ring *,uint32_t index);

/* All rows consumed in this RAM experiment. The caller must separately require
 * successful decoder/framing completion. This does not retire a printer page. */
int hp1020_image_ring_drained(const struct hp1020_image_ring *);
#endif
