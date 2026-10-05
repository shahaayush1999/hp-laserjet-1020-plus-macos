/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
uint32_t hp1020_udc_in_check(uint32_t,uint32_t);
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    uint32_t failure=hp1020_udc_in_check((uint32_t)strtoul(argv[1],NULL,0),
        (uint32_t)strtoul(argv[2],NULL,0));
    if(failure)fprintf(stderr,"udc-in/test.c or included bulk-in-check.c:%u\n",failure);
    return failure?1:0;
}
