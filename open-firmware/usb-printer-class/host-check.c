/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_pc_fixture_input[1024],hp1020_pc_fixture_capture[262144],hp1020_pc_fixture_replies[32768];
extern uint32_t hp1020_pc_fixture_stats[64];
uint32_t hp1020_pc_fixture_reset(uint32_t,uint32_t,uint32_t);
uint32_t hp1020_pc_fixture_step(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);
uint8_t *hp1020_pc_fixture_storage(void);
uint8_t *hp1020_pc_fixture_output(void);
static void save(const char *path,const uint8_t *data,uint32_t n) {
    FILE *f=fopen(path,"wb");if(!f || fwrite(data,1,n,f)!=n || fclose(f))exit(5);
}
int main(int argc,char **argv) {
    if(argc!=9)return 2;
    FILE *f=fopen(argv[1],"rb");if(!f)return 3;
    hp1020_pc_fixture_reset((uint32_t)strtoul(argv[2],0,0),(uint32_t)strtoul(argv[3],0,0),
                           (uint32_t)strtoul(argv[4],0,0));
    uint8_t header[24];uint32_t index=0;size_t n;putchar('[');
    while((n=fread(header,1,sizeof(header),f))) {
        if(n!=sizeof(header))return 3;
        uint32_t v[6];
        for(unsigned i=0;i<6;i++)v[i]=((uint32_t)header[4*i]<<24)|((uint32_t)header[4*i+1]<<16)|
            ((uint32_t)header[4*i+2]<<8)|header[4*i+3];
        if(v[5]>1024 || fread(hp1020_pc_fixture_input,1,v[5],f)!=v[5])return 3;
        hp1020_pc_fixture_step(v[0],v[1],v[2],v[3],v[4]);
        if(index++)putchar(',');putchar('[');
        for(unsigned i=0;i<64;i++)printf("%s%u",i?",":"",hp1020_pc_fixture_stats[i]);
        putchar(']');
    }
    if(ferror(f) || fclose(f))return 3;
    puts("]");save(argv[5],hp1020_pc_fixture_capture,hp1020_pc_fixture_stats[26]);
    save(argv[6],hp1020_pc_fixture_storage(),4096);save(argv[7],hp1020_pc_fixture_output(),32768);
    save(argv[8],hp1020_pc_fixture_replies,hp1020_pc_fixture_stats[42]);return 0;
}
