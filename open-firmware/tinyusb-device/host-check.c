/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern uint8_t hp1020_tusb_fixture_input[1024],hp1020_tusb_fixture_capture[32768];
extern uint32_t hp1020_tusb_fixture_stats[72];
uint32_t hp1020_tusb_fixture_reset(uint32_t,uint32_t,uint32_t,uint32_t);
uint32_t hp1020_tusb_fixture_step(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);

static void print_stats(void) {
    putchar('[');
    for(unsigned i=0;i<72;i++)printf("%s%u",i?",":"",hp1020_tusb_fixture_stats[i]);
    puts("]");fflush(stdout);
}
int main(int argc,char **argv) {
    if(argc!=6)return 2;
    hp1020_tusb_fixture_reset((uint32_t)strtoul(argv[1],NULL,0),(uint32_t)strtoul(argv[2],NULL,0),
                             (uint32_t)strtoul(argv[3],NULL,0),(uint32_t)strtoul(argv[4],NULL,0));
    print_stats();
    uint8_t header[24];size_t n;
    while((n=fread(header,1,sizeof(header),stdin))) {
        if(n!=sizeof(header))return 3;
        uint32_t word[6];
        for(unsigned i=0;i<6;i++)word[i]=((uint32_t)header[4*i]<<24)|((uint32_t)header[4*i+1]<<16)|
            ((uint32_t)header[4*i+2]<<8)|header[4*i+3];
        if(word[5]>sizeof(hp1020_tusb_fixture_input) ||
            fread(hp1020_tusb_fixture_input,1,word[5],stdin)!=word[5])return 3;
        hp1020_tusb_fixture_step(word[0],word[1],word[2],word[3],word[4]);print_stats();
    }
    if(ferror(stdin))return 3;
    FILE *output=fopen(argv[5],"wb");
    uint32_t size=hp1020_tusb_fixture_stats[13];
    if(!output || fwrite(hp1020_tusb_fixture_capture,1,size,output)!=size || fclose(output))return 4;
    return 0;
}
