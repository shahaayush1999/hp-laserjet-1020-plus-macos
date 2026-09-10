/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_IMAGE_PAGE_H
#define HP1020_IMAGE_PAGE_H
#include "hp1020_image.h"
#include "hp1020_semantic.h"
#include "hp1020_page_plan.h"

/* Bridge from a successfully finalized semantic parse to packed image bands.
 * Parser, its compressed arena and this state must remain valid/stationary.
 * This bridge retains compressed input; only decoded image storage streams. */
struct hp1020_image_page {
    struct hp1020_image image;
    struct hp1020_page_plan plan;
    const struct hp1020_semantic *parser;
    uint32_t node, end_node, offset, consumed, padding;
    enum hp1020_image_result error;
    uint8_t done;
};
enum hp1020_image_result hp1020_image_page_init(struct hp1020_image_page *,
    const struct hp1020_semantic *, uint32_t page_index,
    uint8_t *history,size_t history_size,uint8_t *band,size_t band_size);
/* A positive input_quantum bounds each decoder feed, including split BIDs.
 * On BAND, consume state.image.band, then call hp1020_image_page_release.
 * DONE includes exact validation of the default foo2zjs 16–19 zero pad bytes.
 * Each page is decoded once; plan.copies remains metadata for a future engine. */
enum hp1020_image_result hp1020_image_page_next(struct hp1020_image_page *,size_t input_quantum);
enum hp1020_image_result hp1020_image_page_release(struct hp1020_image_page *);
#endif
