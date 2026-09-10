/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_H
#define HP1020_IMAGE_H
#include <stdint.h>
#include <stddef.h>
#include "jbig85.h"

#define HP1020_IMAGE_MAX_WIDTH_BITS 16384u
#define HP1020_IMAGE_MAX_ROWS 16384u
#define HP1020_IMAGE_MAX_BAND_BYTES 8192u

enum hp1020_image_result {
    HP1020_IMAGE_MORE, HP1020_IMAGE_BAND, HP1020_IMAGE_DONE,
    HP1020_IMAGE_FORMAT, HP1020_IMAGE_LIMIT, HP1020_IMAGE_UNSUPPORTED,
    HP1020_IMAGE_TRUNCATED, HP1020_IMAGE_STATE
};

/* All storage belongs to the caller. Do not copy or move an initialized state.
 * No allocation, physical addresses, USB, or output device exists in this API. */
struct hp1020_image {
    struct jbg85_dec_state codec;
    uint8_t *band;
    uint32_t width_bits, rows, stride, chunk_rows, produced;
    uint32_t band_first, band_rows;
    int codec_result;
    enum hp1020_image_result error;
    uint8_t pending, decoded, ending;
};

/* BIH must have DL=D=0, P=1, reserved=0, MX=16, MY=0, order=3,
 * options=0x5c. Only a private header copy is normalized for T.85.
 * History needs 2*ceil(width/8) bytes. Band needs chunk_rows*stride bytes,
 * at most 8192. State, history, band, and input must not overlap.
 * chunk_rows is an explicit caller choice, not inferred engine geometry. */
enum hp1020_image_result hp1020_image_init(struct hp1020_image *s,
    const uint8_t bih[20], uint8_t *history, size_t history_size,
    uint8_t *band, size_t band_size, uint32_t chunk_rows);

/* Feed BID bytes (no BIH or ZjStream framing). Always inspect *used and
 * resubmit the remainder. BAND consumes nothing until release. On DONE,
 * bytes beyond *used belong to the caller (e.g. transport padding).
 * Input need only remain valid during this call. Errors are sticky. */
enum hp1020_image_result hp1020_image_feed(struct hp1020_image *s,
    const uint8_t *data, size_t size, size_t *used);

/* BAND exposes band_rows consecutive packed rows at band_first in s->band.
 * Copy/consume them before release. A final short band is allowed.
 * Output is provisional until DONE: JBIG contains no image checksum. */
enum hp1020_image_result hp1020_image_release(struct hp1020_image *s);

/* Signal the end of BID input, draining pending bands by release/finish.
 * Missing final stripe termination is TRUNCATED, even if rows were produced. */
enum hp1020_image_result hp1020_image_finish(struct hp1020_image *s);
#endif
