/* SPDX-License-Identifier: GPL-2.0-or-later
 * Host-only bridge: never linked into the open image component. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern uint8_t hp1020_image_input[131072], hp1020_image_capture[65536];
extern uint32_t hp1020_image_stats[24];
uint32_t hp1020_image_run(uint32_t,uint32_t,uint32_t,uint32_t);
static FILE *capture;
void hp1020_image_observe(const uint8_t *p,uint32_t size) {
    if (fwrite(p,1,size,capture)!=size) exit(6);
}
int main(int argc, char **argv) {
    if (argc!=7) return 2;
    FILE *f=fopen(argv[1],"rb"); if (!f) return 3;
    size_t n=fread(hp1020_image_input,1,131072,f);
    if (ferror(f) || fgetc(f)!=EOF) return 4;
    fclose(f);
    capture=fopen(argv[5],"wb"); if (!capture) return 5;
    hp1020_image_run((uint32_t)n,(uint32_t)strtoul(argv[2],0,0),
        (uint32_t)strtoul(argv[3],0,0),(uint32_t)strtoul(argv[4],0,0));
    if (fclose(capture)) return 6;
    /* argv[6] is a reserved fixture-format version. */
    if (strtoul(argv[6],0,0)!=1) return 7;
    putchar('[');
    for (unsigned i=0;i<24;i++) printf("%s%u",i ? "," : "",hp1020_image_stats[i]);
    puts("]"); return 0;
}
