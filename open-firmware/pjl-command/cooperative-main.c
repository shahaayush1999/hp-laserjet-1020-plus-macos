/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_cooperative_job[65536],hp1020_bulk_fixture_pixels[262144];
extern uint32_t hp1020_cooperative_stats[8];
uint32_t hp1020_cooperative_check(uint32_t,uint32_t,uint32_t);
int main(int argc,char **argv) {
    if(argc!=5)return 2;
    FILE *f=fopen(argv[3],"rb");if(!f)return 2;
    uint32_t n=(uint32_t)fread(hp1020_cooperative_job,1,sizeof(hp1020_cooperative_job),f);
    if(!feof(f) || ferror(f)) { fclose(f);return 2; }fclose(f);
    uint32_t failure=hp1020_cooperative_check((uint32_t)strtoul(argv[1],NULL,0),
        (uint32_t)strtoul(argv[2],NULL,0),n);
    if(failure) { fprintf(stderr,"cooperative-test.c or included fixture:%u\n",failure);return 1; }
    f=fopen(argv[4],"wb");if(!f)return 2;
    n=hp1020_cooperative_stats[1];
    if(fwrite(hp1020_bulk_fixture_pixels,1,n,f)!=n) { fclose(f);return 2; }
    if(fclose(f))return 2;
    printf("[");for(unsigned i=0;i<8;i++)printf("%s%u",i?",":"",hp1020_cooperative_stats[i]);puts("]");
    return 0;
}
