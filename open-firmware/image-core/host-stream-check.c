/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_stream_input[65552];
extern uint32_t hp1020_stream_stats[32];
uint32_t hp1020_stream_reset(uint32_t,uint32_t);
uint32_t hp1020_stream_feed(uint32_t,uint32_t);
uint32_t hp1020_stream_finish(void);
static FILE *capture;
void hp1020_stream_observe(const uint8_t *p,uint32_t size) {
    if(fwrite(p,1,size,capture)!=size)exit(6);
}
int main(int argc,char **argv) {
    if(argc!=8)return 2;
    uint32_t fragment=(uint32_t)strtoul(argv[2],0,0),packet=(uint32_t)strtoul(argv[3],0,0);
    if(!fragment || !packet || packet>65552)return 2;
    FILE *f=fopen(argv[1],"rb");if(!f)return 3;
    capture=fopen(argv[6],"wb");if(!capture)return 4;
    if(hp1020_stream_reset((uint32_t)strtoul(argv[4],0,0),(uint32_t)strtoul(argv[5],0,0)))return 5;
    size_t n;
    while((n=fread(hp1020_stream_input,1,packet,f)))if(hp1020_stream_feed((uint32_t)n,fragment))break;
    if(ferror(f))return 3;
    fclose(f);hp1020_stream_finish();if(fclose(capture))return 6;
    if(strtoul(argv[7],0,0)!=1)return 2;
    putchar('[');for(unsigned i=0;i<32;i++)printf("%s%u",i?",":"",hp1020_stream_stats[i]);puts("]");
    return 0;
}
