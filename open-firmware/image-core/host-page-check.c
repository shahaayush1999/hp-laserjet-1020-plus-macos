/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_page_input[131072];
extern uint32_t hp1020_page_stats[24];
uint32_t hp1020_page_run(uint32_t,uint32_t,uint32_t,uint32_t);
static FILE *capture;
void hp1020_page_observe(const uint8_t *p,uint32_t size) {
    if(fwrite(p,1,size,capture)!=size)exit(6);
}
int main(int argc,char **argv) {
    if(argc!=6)return 2;
    FILE *f=fopen(argv[1],"rb");if(!f)return 3;
    size_t n=fread(hp1020_page_input,1,131072,f);
    if(ferror(f) || fgetc(f)!=EOF)return 4;
    fclose(f);capture=fopen(argv[5],"wb");if(!capture)return 5;
    hp1020_page_run((uint32_t)n,(uint32_t)strtoul(argv[2],0,0),
        (uint32_t)strtoul(argv[3],0,0),(uint32_t)strtoul(argv[4],0,0));
    if(fclose(capture))return 6;
    putchar('[');for(unsigned i=0;i<24;i++)printf("%s%u",i?",":"",hp1020_page_stats[i]);puts("]");
    return 0;
}
