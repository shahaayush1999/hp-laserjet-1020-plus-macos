/* Host-emulation fixture only: synthetic link addresses, no boot or USB path. */
#include "hp1020_semantic.h"
#include "hp1020_page_plan.h"
#include <string.h>
uint8_t hp1020_test_input[65536];
uint32_t hp1020_test_output[32];
static uint8_t arena[65536];
static struct hp1020_semantic parser;

uint32_t hp1020_target_run(uint32_t length, uint32_t fragment) {
    uint32_t *o=hp1020_test_output;
    memset(o,0,32*sizeof(*o));
    if (length>sizeof(hp1020_test_input) || !fragment) return 0xffffffffu;
    hp1020_semantic_init(&parser,arena,sizeof(arena));
    uint32_t pos=0;
    while (pos<length) {
        uint32_t n=length-pos;if(n>fragment)n=fragment;
        if(hp1020_semantic_feed(&parser,hp1020_test_input+pos,n))break;
        pos+=n;
    }
    o[0]=hp1020_semantic_finish(&parser);
    o[1]=parser.documents;o[2]=parser.page_count;o[3]=parser.raster_count;o[4]=parser.arena_used;
    uint32_t hash=2166136261u;
    for(uint32_t i=0;i<parser.arena_used;i++)hash=(hash^arena[i])*16777619u;
    o[5]=hash;
    if(parser.page_count) {
        const struct hp1020_page *p=&parser.pages[0];
        o[6]=p->copies;o[7]=p->nbie;o[8]=p->resolution_x;o[9]=p->resolution_y;
        o[10]=p->host_video_x;o[11]=p->host_video_y;o[12]=p->host_video_bpp;
        o[13]=p->bih_xd;o[14]=p->bih_yd;o[15]=p->bih_l0;o[16]=p->bih_options;
        o[17]=p->compressed_bytes;o[18]=p->complete;o[19]=p->work_remaining_units;
        o[20]=p->work_ret;o[21]=p->work_economode;o[22]=p->stock_metadata_bounded;
        if(!o[0]) {
            struct hp1020_page_plan plan;
            o[23]=hp1020_plan_page(p,&plan);
            if(!o[23]) {
                o[24]=plan.stride;o[25]=plan.window;o[26]=plan.chunk_rows;
                uint32_t cursor=0;struct hp1020_band_plan band;
                while(hp1020_plan_next_band(&plan,&cursor,&band)==HP1020_PLAN_OK) {
                    o[27]++;o[28]+=band.bytes;o[29]+=band.final;
                }
            }
        }
    }
    return o[0];
}
