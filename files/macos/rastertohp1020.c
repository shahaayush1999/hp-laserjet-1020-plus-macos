/* Native CUPS raster adapter, linked to the preserved GPL foo2zjs encoder.
 * Apple renders/collates/layouts pages. We accept only the advertised monochrome
 * geometry, then supply one PBM page at a time to the original encoder.
 * No new compression or printer protocol implementation is introduced here.
 */
#include "hp1020-common.h"
#include <cups/raster.h>
#include <math.h>

/* Deliberately narrow interface to unchanged foo2zjs.c (main renamed at build). */
extern int Model, ResX, ResY, Bpp, PaperCode, LogicalClip, OutputStartPlane;
extern void start_doc(FILE *), end_doc(FILE *), do_one(FILE *);

int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts("HP1020 native CUPS driver 3"); return 0; }
    if (argc < 6 || argc > 7) return 1;
    hp_signals();
    if (!hp_options(argv[5])) return 1;
    int fd = argc == 7 ? open(argv[6], O_RDONLY | O_CLOEXEC) : STDIN_FILENO;
    cups_raster_t *raster = fd >= 0 ? cupsRasterOpen(fd, CUPS_RASTER_READ) : NULL;
    if (!raster) { fputs("ERROR: Cannot open rendered document.\n", stderr); return 1; }
    cups_page_header2_t header;
    unsigned pages = 0;
    int failed = 0;
    Model = 1; ResX = ResY = 600; Bpp = 2;
    LogicalClip = 0; OutputStartPlane = 0; /* Same -z1 -r1200x600 -L0 -P as the working wrapper. */
    while (!hp_cancelled && cupsRasterReadHeader2(raster, &header)) {
        /* Imageable area exactly matches the original 192x96 pixel crop.
         * Validate the dimensions, rather than silently stretching or shifting. */
        unsigned width, height;
        if (fabs(header.cupsPageSize[0] - 595.2) < 0.1 && fabs(header.cupsPageSize[1] - 841.92) < 0.1) {
            PaperCode = 9; width = 9536; height = 6824;
        } else if (fabs(header.cupsPageSize[0] - 612) < 0.1 && fabs(header.cupsPageSize[1] - 792) < 0.1) {
            PaperCode = 1; width = 9816; height = 6408;
        } else { fputs("ERROR: Unsupported rendered paper size.\n", stderr); failed = 1; break; }
        if (header.cupsWidth != width || header.cupsHeight != height ||
            header.cupsBitsPerColor != 1 || header.cupsBitsPerPixel != 1 ||
            header.cupsColorSpace != CUPS_CSPACE_K || header.cupsNumColors != 1 ||
            header.cupsColorOrder != CUPS_ORDER_CHUNKED || header.cupsBytesPerLine != (width + 7) / 8 ||
            header.HWResolution[0] != 1200 || header.HWResolution[1] != 600 ||
            header.NumCopies != 1 || header.Duplex || header.Tumble ||
            fabs(header.cupsImagingBBox[0] - 11.52) > 0.02 || fabs(header.cupsImagingBBox[1] - 11.52) > 0.02) {
            fputs("ERROR: Unsupported raster geometry or copies. Document was not completed.\n", stderr);
            failed = 1; break;
        }
        FILE *page = hp_temp();
        if (!page) { failed = 1; break; }
        fprintf(page, "P4\n%u %u\n", width, height);
        unsigned char row[1280];
        for (unsigned y = 0; y < height; y++) {
            if (hp_cancelled || cupsRasterReadPixels(raster, row, header.cupsBytesPerLine) != header.cupsBytesPerLine ||
                fwrite(row, 1, header.cupsBytesPerLine, page) != header.cupsBytesPerLine) {
                failed = 1; break;
            }
        }
        if (fflush(page) || ferror(page)) failed = 1;
        if (!failed) {
            rewind(page);
            if (!pages) start_doc(stdout);
            do_one(page);
            pages++;
            fprintf(stderr, "PAGE: %u 1\nINFO: Prepared page %u.\n", pages, pages);
        }
        fclose(page);
        if (failed || ferror(stdout)) { failed = 1; break; }
    }
    const char *error = cupsRasterErrorString();
    if (error && *error) { fprintf(stderr, "ERROR: Raster read failed: %s\n", error); failed = 1; }
    if (!pages) failed = 1;
    /* Omit END_DOC on any failure: the backend checks the complete document
     * before opening USB, so a truncated filter result cannot print partially. */
    if (!failed && !hp_cancelled) end_doc(stdout);
    cupsRasterClose(raster);
    if (fd != STDIN_FILENO) close(fd);
    if (fflush(stdout)) failed = 1;
    if (failed) fputs("ERROR: Could not prepare the complete document.\n", stderr);
    return hp_cancelled ? 0 : failed;
}
