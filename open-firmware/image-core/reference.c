/* SPDX-License-Identifier: GPL-2.0-or-later
 * Host-only original full JBIG-KIT oracle/encoder. Does not use image-core. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "jbig.h"
static void output(unsigned char *p,size_t n,void *f) {
    if (fwrite(p,1,n,f)!=n) exit(4);
}
int main(int argc,char **argv) {
    if (argc<4) return 2;
    FILE *f=fopen(argv[2],"rb"); if (!f) return 3;
    if (fseek(f,0,SEEK_END)) return 3;
    long length=ftell(f); if (length<0 || length>33554432) return 3;
    rewind(f);
    unsigned char *data=malloc((size_t)length+1); if (!data) return 3;
    if (fread(data,1,length,f)!=(size_t)length) return 3;
    fclose(f);
    FILE *out=fopen(argv[3],"wb"); if (!out) return 3;
    if (!strcmp(argv[1],"encode") && argc==7) {
        unsigned long w=strtoul(argv[4],0,0),h=strtoul(argv[5],0,0),stripe=strtoul(argv[6],0,0);
        if (!w || !h || !stripe || ((w+7)/8)*h!=(unsigned long)length) return 2;
        struct jbg_enc_state s;
        jbg_enc_init(&s,w,h,1,&data,output,out);
        jbg_enc_options(&s,JBG_ILEAVE|JBG_SMID,JBG_LRLTWO|JBG_TPBON|JBG_TPDON|JBG_DPON,stripe,16,0);
        jbg_enc_out(&s); jbg_enc_free(&s);
    } else if (!strcmp(argv[1],"decode") && argc==4) {
        struct jbg_dec_state s; size_t used=0;
        jbg_dec_init(&s);
        int r=jbg_dec_in(&s,data,length,&used);
        if (r!=JBG_EOK) { fprintf(stderr,"full decoder error %d\n",r); return 5; }
        unsigned long size=jbg_dec_getsize(&s);
        output(jbg_dec_getimage(&s,0),size,out);
        printf("{\"consumed\":%zu,\"width\":%lu,\"height\":%lu,\"bytes\":%lu}\n",
            used,jbg_dec_getwidth(&s),jbg_dec_getheight(&s),size);
        jbg_dec_free(&s);
    } else return 2;
    if (fclose(out)) return 4;
    free(data); return 0;
}
