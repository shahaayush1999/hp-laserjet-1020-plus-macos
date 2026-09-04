#include "hp1020_page_plan.h"
#include <string.h>

enum hp1020_plan_result hp1020_plan_page(const struct hp1020_page *page,
    struct hp1020_page_plan *out) {
    struct hp1020_page_plan plan={0};
    memset(out,0,sizeof(*out));
    if (!page->complete || !page->video_sideband_known || !page->stock_metadata_bounded ||
        !page->copies || page->copies>UINT16_MAX || !page->bih_xd ||
        page->bih_xd>UINT32_MAX-31u || !page->host_video_y ||
        page->host_video_y>UINT16_MAX || page->host_video_y!=page->bih_yd ||
        page->work_remaining_units!=page->host_video_y)
        return HP1020_PLAN_INVALID;
    /* Deliberately narrow to aligned rows and the recovered 600dpi callbacks.
       Other stock modes require their own proof; BPP4 yields zero refill rows
       for the generated 2400x600 sample and must not silently look ready. */
    if (page->nbie!=1 || page->resolution_x!=600 || page->resolution_y!=600 ||
        (page->host_video_bpp!=1 && page->host_video_bpp!=2) ||
        (page->host_video_y&3u) || page->work_economode>1 || page->work_ret)
        return HP1020_PLAN_UNSUPPORTED;
    plan.stride=((page->bih_xd+31u)&~31u)>>3;
    plan.chunk_rows=(8192u/plan.stride)&~3u;
    if (!plan.chunk_rows) return HP1020_PLAN_UNSUPPORTED;
    plan.rows=page->host_video_y;
    plan.copies=page->copies;
    plan.window=plan.stride*(page->host_video_bpp==1 ? 2u : 1u);
    plan.callback=page->host_video_bpp==1 ? HP1020_CALLBACK_BPP1_600 : HP1020_CALLBACK_BPP2_600;
    plan.economode=page->work_economode;
    /* stride <= 2048 and rows <= 65535 here, so this cannot overflow u32. */
    plan.total_row_bytes=plan.stride*plan.rows;
    *out=plan;
    return HP1020_PLAN_OK;
}

enum hp1020_plan_result hp1020_plan_next_band(const struct hp1020_page_plan *plan,
    uint32_t *cursor, struct hp1020_band_plan *out) {
    memset(out,0,sizeof(*out));
    if (!plan->stride || plan->stride>2048 || !plan->chunk_rows ||
        plan->chunk_rows!=(8192u/plan->stride&~3u) || !plan->rows ||
        (plan->rows&3u) || plan->rows>UINT16_MAX || *cursor>plan->rows || (*cursor&3u))
        return HP1020_PLAN_INVALID;
    if (*cursor==plan->rows) return HP1020_PLAN_DONE;
    out->first_row=*cursor;
    out->rows=plan->rows-*cursor;
    if (out->rows>plan->chunk_rows) out->rows=plan->chunk_rows;
    out->bytes=out->rows*plan->stride;
    *cursor+=out->rows;
    out->final=*cursor==plan->rows;
    return HP1020_PLAN_OK;
}
