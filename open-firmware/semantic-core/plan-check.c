#include "hp1020_page_plan.h"
#include <stdio.h>
#include <inttypes.h>

int main(void) {
    uint32_t xd,yd,bpp,res,eco,ret,bounded,copies;
    while (scanf("%" SCNu32 " %" SCNu32 " %" SCNu32 " %" SCNu32 " %" SCNu32 " %" SCNu32 " %" SCNu32 " %" SCNu32,
                 &xd,&yd,&bpp,&res,&eco,&ret,&bounded,&copies)==8) {
        struct hp1020_page p={0};
        p.bih_xd=xd;p.bih_yd=yd;p.host_video_y=yd;p.host_video_bpp=bpp;
        p.nbie=1;p.resolution_x=res;p.resolution_y=res;p.work_economode=(uint16_t)eco;
        p.work_ret=(uint16_t)ret;p.copies=copies;p.complete=1;p.video_sideband_known=1;
        p.work_remaining_units=(uint16_t)yd;p.stock_metadata_bounded=bounded!=0;
        struct hp1020_page_plan plan;struct hp1020_band_plan band;
        uint32_t status=hp1020_plan_page(&p,&plan);
        uint32_t cursor=0,count=0,total=0,finals=0,last_rows=0;
        if (status==HP1020_PLAN_OK) {
            enum hp1020_plan_result result;
            while ((result=hp1020_plan_next_band(&plan,&cursor,&band))==HP1020_PLAN_OK) {
                if (!band.rows || band.bytes>8192 || band.first_row+band.rows!=cursor) return 2;
                count++;total+=band.bytes;finals+=band.final;last_rows=band.rows;
            }
            if (result!=HP1020_PLAN_DONE || finals!=1 || cursor!=plan.rows) return 3;
            cursor=plan.rows+4;
            if (hp1020_plan_next_band(&plan,&cursor,&band)!=HP1020_PLAN_INVALID) return 4;
            cursor=1;
            if (hp1020_plan_next_band(&plan,&cursor,&band)!=HP1020_PLAN_INVALID) return 5;
        }
        printf("{\"result\":%" PRIu32 ",\"stride\":%" PRIu32 ",\"window\":%" PRIu32 ",\"chunk_rows\":%" PRIu32
               ",\"bands\":%" PRIu32 ",\"last_rows\":%" PRIu32 ",\"bytes\":%" PRIu32 "}\n",
               status,plan.stride,plan.window,plan.chunk_rows,count,last_rows,total);
    }
    return ferror(stdin) ? 1 : 0;
}
