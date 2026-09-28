/* Independent libcups extraction used to compare with the upstream CLI. */
#include <cups/raster.h>
#include <stdio.h>
#include <unistd.h>
int main(void) {
    cups_raster_t *r=cupsRasterOpen(0,CUPS_RASTER_READ);
    cups_page_header2_t h;
    unsigned char row[1280];
    if(!r||!cupsRasterReadHeader2(r,&h)||h.cupsBytesPerLine>sizeof(row))return 1;
    printf("P4\n%u %u\n",h.cupsWidth,h.cupsHeight);
    for(unsigned y=0;y<h.cupsHeight;y++) {
        if(cupsRasterReadPixels(r,row,h.cupsBytesPerLine)!=h.cupsBytesPerLine)return 2;
        fwrite(row,1,h.cupsBytesPerLine,stdout);
    }
    cupsRasterClose(r);
    return 0;
}
