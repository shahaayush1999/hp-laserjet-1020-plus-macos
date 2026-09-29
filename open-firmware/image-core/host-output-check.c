/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_output_input[65552];
extern uint32_t hp1020_output_stats[40],hp1020_output_writes[256][5],hp1020_output_pages[128][7];
uint32_t hp1020_output_reset(uint32_t,uint32_t,uint32_t);
uint32_t hp1020_output_feed(uint32_t,uint32_t);
uint32_t hp1020_output_seed_counter(uint32_t);
uint32_t hp1020_output_finish(void);
uint8_t *hp1020_output_storage(void);
static FILE *capture;
void hp1020_output_observe(const uint8_t *p,uint32_t size) {
    if(fwrite(p,1,size,capture)!=size)exit(6);
}
static void array(const uint32_t *p,unsigned n) {
    putchar('[');for(unsigned i=0;i<n;i++)printf("%s%u",i?",":"",p[i]);putchar(']');
}
int main(int argc,char **argv) {
    if(argc!=10)return 2;
    uint32_t fragment=(uint32_t)strtoul(argv[2],0,0),packet=(uint32_t)strtoul(argv[3],0,0);
    if(!fragment || !packet || packet>65552)return 2;
    FILE *f=fopen(argv[1],"rb");if(!f)return 3;
    capture=fopen(argv[7],"wb");if(!capture)return 4;
    if(hp1020_output_reset((uint32_t)strtoul(argv[4],0,0),(uint32_t)strtoul(argv[5],0,0),
        (uint32_t)strtoul(argv[6],0,0)))return 5;
    if(hp1020_output_seed_counter((uint32_t)strtoul(argv[9],0,0)))return 5;
    size_t n;
    while((n=fread(hp1020_output_input,1,packet,f)))if(hp1020_output_feed((uint32_t)n,fragment))break;
    if(ferror(f))return 3;
    fclose(f);hp1020_output_finish();if(fclose(capture))return 6;
    f=fopen(argv[8],"wb");if(!f)return 4;
    if(fwrite(hp1020_output_storage(),1,32768,f)!=32768 || fclose(f))return 6;
    printf("{\"stats\":");array(hp1020_output_stats,40);printf(",\"writes\":[");
    for(unsigned i=0;i<hp1020_output_stats[20];i++) { if(i)putchar(',');array(hp1020_output_writes[i],5); }
    printf("],\"pages\":[");
    for(unsigned i=0;i<hp1020_output_stats[28] && i<128;i++) { if(i)putchar(',');array(hp1020_output_pages[i],7); }
    puts("]}");
    return 0;
}
