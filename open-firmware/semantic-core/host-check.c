#include "hp1020_semantic.h"
#include "hp1020_page_plan.h"
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

int main(int argc,char **argv) {
    if (argc!=4) return 2;
    size_t fragment=(size_t)strtoul(argv[2],NULL,10);
    uint32_t capacity=(uint32_t)strtoul(argv[3],NULL,10);
    if (!fragment || fragment>65536 || capacity>16u*1024u*1024u) return 2;
    FILE *f=fopen(argv[1],"rb");
    if (!f) return 2;
    uint8_t *arena=malloc(capacity ? capacity : 1),*buffer=malloc(fragment);
    struct hp1020_semantic *s=malloc(sizeof(*s));
    if (!arena || !buffer || !s) return 2;
    hp1020_semantic_init(s,arena,capacity);
    size_t count;
    while ((count=fread(buffer,1,fragment,f)) && !s->error) hp1020_semantic_feed(s,buffer,count);
    if (ferror(f)) return 2;
    fclose(f);
    enum hp1020_result result=hp1020_semantic_finish(s);
    printf("{\"result\":%u,\"documents\":%" PRIu32 ",\"arena_used\":%" PRIu32 ",\"pages\":[",result,s->documents,s->arena_used);
    for (uint32_t i=0;i<s->page_count;i++) {
        struct hp1020_page *p=&s->pages[i];
        struct hp1020_page_plan plan;
        unsigned plan_result=hp1020_plan_page(p,&plan);
        printf("%s{\"copies\":%" PRIu32 ",\"nbie\":%" PRIu32 ",\"resolution_x\":%" PRIu32 ",\"resolution_y\":%" PRIu32
               ",\"video_x\":%" PRIu32 ",\"video_y\":%" PRIu32 ",\"bpp\":%" PRIu32 ",\"xd\":%" PRIu32
               ",\"yd\":%" PRIu32 ",\"l0\":%" PRIu32 ",\"options\":%u,\"rasters\":%" PRIu32
               ",\"compressed_bytes\":%" PRIu32 ",\"complete\":%u,\"sideband_known\":%u,\"work26\":%u,\"work30\":%u,\"work32\":%u,\"plan_result\":%u}",
               i?",":"",p->copies,p->nbie,p->resolution_x,p->resolution_y,p->host_video_x,p->host_video_y,p->host_video_bpp,
               p->bih_xd,p->bih_yd,p->bih_l0,p->bih_options,p->raster_count,p->compressed_bytes,p->complete,p->video_sideband_known,p->work_remaining_units,p->work_ret,p->work_economode,plan_result);
    }
    printf("],\"rasters\":[");
    for (uint32_t i=0;i<s->raster_count;i++) {
        struct hp1020_raster *r=&s->rasters[i];
        uint32_t hash=UINT32_C(2166136261);
        for (uint32_t j=0;j<r->length;j++) hash=(hash^arena[r->offset+j])*UINT32_C(16777619);
        printf("%s{\"page\":%" PRIu32 ",\"offset\":%" PRIu32 ",\"length\":%" PRIu32 ",\"fnv1a\":%" PRIu32 "}",i?",":"",r->page,r->offset,r->length,hash);
    }
    printf("]}\n");
    free(s);free(buffer);free(arena);
    return 0;
}
