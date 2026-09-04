#ifndef HP1020_PAGE_PLAN_H
#define HP1020_PAGE_PLAN_H
#include "hp1020_semantic.h"

enum hp1020_plan_result { HP1020_PLAN_OK, HP1020_PLAN_INVALID,
    HP1020_PLAN_UNSUPPORTED, HP1020_PLAN_DONE };
enum hp1020_callback { HP1020_CALLBACK_BPP1_600, HP1020_CALLBACK_BPP2_600 };
struct hp1020_page_plan {
    uint32_t stride, window, chunk_rows, rows, copies, total_row_bytes;
    uint32_t callback, economode;
};
struct hp1020_band_plan { uint32_t first_row, rows, bytes, final; };
/* Produces RAM-only arithmetic plans. It never authorizes hardware output.
   The parser supplies the declared-metadata bounds flag in the page object. */
enum hp1020_plan_result hp1020_plan_page(const struct hp1020_page *,
    struct hp1020_page_plan *);
enum hp1020_plan_result hp1020_plan_next_band(const struct hp1020_page_plan *,
    uint32_t *row_cursor, struct hp1020_band_plan *);
#endif
