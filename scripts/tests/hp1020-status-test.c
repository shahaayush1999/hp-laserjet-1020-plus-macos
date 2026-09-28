/* Exercise the actual status parser, never start a transport. */
#define main hp_backend_main
#include "../../files/macos/hp1020-backend.c"
#undef main
#include <assert.h>
static void feed(Transport *t,const char *s) {
    for(size_t i=0;s[i];i++)back_data(t,(const unsigned char*)s+i,1);
}
int main(void) {
    Transport t={.pages=3,.reason=-1};strcpy(t.token,"current-job");
    feed(&t,"@PJL USTATUS DEVICE\r\nCODE=41001\r\n\f");assert(t.reason==0&&t.attention);
    feed(&t,"@PJL INFO STATUS\nCODE=bad\n\f");assert(t.reason==0);
    feed(&t,"@PJL INFO STATUS\nCODE=99999\n\f");assert(t.reason==0);
    feed(&t,"@PJL USTATUS DEVICE\nCODE=40021\n\f");assert(t.reason==2);
    feed(&t,"@PJL USTATUS DEVICE\nCODE=40022\n\f");assert(t.reason==1);
    feed(&t,"@PJL USTATUS DEVICE\nCODE=40600\n\f");assert(t.reason==3);
    feed(&t,"@PJL USTATUS JOB\nEND\nNAME=\"old-job\"\nPAGES=3\n\f");assert(!t.completed);
    feed(&t,"@PJL USTATUS JOB\nEND\nNAME=\"current-job\"\nPAGES=2\n\f");assert(!t.completed);
    for(int i=0;i<1000000;i++)back_data(&t,(const unsigned char*)"x",1);
    assert(t.used<=FRAME);
    feed(&t,"@PJL INFO STATUS\nCODE=10001\n\f");assert(t.reason==3);
    feed(&t,"@PJL INFO STATUS\nCODE=10001\n\f");assert(!t.attention);
    feed(&t,"@PJL USTATUS JOB\nEND\nNAME=\"current-job\"\nPAGES=3\n\f");assert(t.completed);
    return 0;
}
