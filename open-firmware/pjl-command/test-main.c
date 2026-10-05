/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_command_job[4096],hp1020_bulk_fixture_pixels[262144];
extern uint8_t hp1020_command_last_reply[64];
extern uint32_t hp1020_command_last_length;
uint32_t hp1020_pjl_command_check(uint32_t,uint32_t,uint32_t);
int main(int argc,char **argv) {
    if(argc!=5)return 2;
    FILE *file=fopen(argv[3],"rb");if(!file)return 2;
    uint32_t n=(uint32_t)fread(hp1020_command_job,1,sizeof(hp1020_command_job),file);
    if(!feof(file) || ferror(file)) { fclose(file);return 2; } fclose(file);
    uint32_t scenario=(uint32_t)strtoul(argv[1],NULL,0);
    uint32_t failure=hp1020_pjl_command_check(scenario,(uint32_t)strtoul(argv[2],NULL,0),n);
    if(failure)fprintf(stderr,"pjl-command/test.c or included fixture:%u\n",failure);
    if(!failure) {
        file=fopen(argv[4],"wb");if(!file)return 2;
        const uint8_t *out=scenario==15?hp1020_bulk_fixture_pixels:hp1020_command_last_reply;
        n=scenario==15?128:hp1020_command_last_length;
        if(fwrite(out,1,n,file)!=n) { fclose(file);return 2; }
        if(fclose(file))return 2;
    }
    return failure?1:0;
}
