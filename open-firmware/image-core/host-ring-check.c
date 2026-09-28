/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_ring_input[131072],hp1020_ring_storage[32800];
extern uint32_t hp1020_ring_stats[24],hp1020_ring_trace[512][18];
uint32_t hp1020_ring_run(uint32_t,uint32_t,uint32_t,uint32_t);
uint32_t hp1020_ring_api_control(uint32_t);
static FILE *capture;
void hp1020_ring_observe(const uint8_t *p,uint32_t size) {
    if(fwrite(p,1,size,capture)!=size)exit(6);
}
int main(int argc,char **argv) {
    if(argc==2) {
        printf("%u\n",hp1020_ring_api_control((uint32_t)strtoul(argv[1],0,0)));
        return 0;
    }
    if(argc!=6)return 2;
    FILE *f=fopen(argv[1],"rb");if(!f)return 3;
    size_t n=fread(hp1020_ring_input,1,sizeof(hp1020_ring_input),f);
    if(ferror(f) || fgetc(f)!=EOF)return 4;
    fclose(f);capture=fopen(argv[4],"wb");if(!capture)return 5;
    hp1020_ring_run((uint32_t)n,(uint32_t)strtoul(argv[2],0,0),(uint32_t)strtoul(argv[3],0,0),0);
    if(fclose(capture))return 6;
    f=fopen(argv[5],"wb");if(!f)return 5;
    if(fwrite(hp1020_ring_storage,1,sizeof(hp1020_ring_storage),f)!=sizeof(hp1020_ring_storage) || fclose(f))return 6;
    printf("{\"stats\":[");
    for(unsigned i=0;i<24;i++)printf("%s%u",i ? "," : "",hp1020_ring_stats[i]);
    printf("],\"trace\":[");
    for(uint32_t i=0;i<hp1020_ring_stats[13] && i<512;i++) {
        printf("%s[",i ? "," : "");
        for(unsigned j=0;j<18;j++)printf("%s%u",j ? "," : "",hp1020_ring_trace[i][j]);
        printf("]");
    }
    puts("]}");return 0;
}
