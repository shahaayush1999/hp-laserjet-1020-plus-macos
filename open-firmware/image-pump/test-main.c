/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_pump_job[65536],hp1020_pump_pixels[262144];
extern uint32_t hp1020_pump_stats[8];
extern uint32_t hp1020_image_pump_check(uint32_t,uint32_t,uint32_t);
int main(int argc,char **argv) {
    if(argc!=5)return 2;
    FILE *f=fopen(argv[3],"rb");if(!f)return 2;
    size_t length=fread(hp1020_pump_job,1,sizeof(hp1020_pump_job),f);
    if(ferror(f) || fgetc(f)!=EOF || fclose(f))return 2;
    uint32_t failure=hp1020_image_pump_check((uint32_t)strtoul(argv[1],NULL,0),
        (uint32_t)strtoul(argv[2],NULL,0),(uint32_t)length);
    if(failure) { fprintf(stderr,"image-pump/test.c:%u\n",failure);return 1; }
    f=fopen(argv[4],"wb");if(!f)return 2;
    if(fwrite(hp1020_pump_pixels,1,hp1020_pump_stats[0],f)!=hp1020_pump_stats[0] || fclose(f))return 2;
    printf("[");for(unsigned i=0;i<8;i++)printf("%s%u",i?",":"",hp1020_pump_stats[i]);puts("]");
    return 0;
}
