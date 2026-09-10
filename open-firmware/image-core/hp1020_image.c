/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_image.h"
#include <string.h>

static uint32_t be32(const uint8_t *p) {
    return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3];
}
static enum hp1020_image_result fail(struct hp1020_image *s,
                                    enum hp1020_image_result error) {
    s->error=error;
    return error;
}
static int row_out(const struct jbg85_dec_state *codec, unsigned char *data,
                   size_t size, unsigned long row, void *context) {
    struct hp1020_image *s=context;
    (void)codec;
    if (s->pending || row!=s->produced || row>=s->rows || size!=s->stride ||
        s->band_rows>=s->chunk_rows) {
        fail(s,HP1020_IMAGE_STATE);
        return 1;
    }
    if (!s->band_rows) s->band_first=s->produced;
    memcpy(s->band+s->band_rows*s->stride,data,size);
    s->band_rows++; s->produced++;
    s->pending=(s->band_rows==s->chunk_rows || s->produced==s->rows);
    return s->pending;
}
static enum hp1020_image_result result(struct hp1020_image *s, int r) {
    s->codec_result=r;
    if (s->error) return s->error;
    if (r==JBG_EOK) {
        if (s->produced!=s->rows) return fail(s,HP1020_IMAGE_FORMAT);
        s->decoded=1;
    } else if (r!=JBG_EAGAIN && r!=JBG_EOK_INTR) {
        return fail(s,(r&0xf0)==JBG_EIMPL ? HP1020_IMAGE_UNSUPPORTED : HP1020_IMAGE_FORMAT);
    }
    if (s->pending) return HP1020_IMAGE_BAND;
    if (r==JBG_EOK_INTR) return fail(s,HP1020_IMAGE_STATE);
    return s->decoded ? HP1020_IMAGE_DONE : HP1020_IMAGE_MORE;
}
enum hp1020_image_result hp1020_image_init(struct hp1020_image *s,
    const uint8_t bih[20], uint8_t *history, size_t history_size,
    uint8_t *band, size_t band_size, uint32_t chunk_rows) {
    uint8_t header[20]; size_t used=0;
    memset(s,0,sizeof(*s));
    if (!bih || !history || !band) return fail(s,HP1020_IMAGE_STATE);
    if (bih[0] || bih[1] || bih[2]!=1 || bih[3] || bih[16]!=16 ||
        bih[17] || bih[18]!=3 || bih[19]!=0x5c)
        return fail(s,HP1020_IMAGE_UNSUPPORTED);
    s->width_bits=be32(bih+4); s->rows=be32(bih+8);
    uint32_t stripe=be32(bih+12);
    if (!s->width_bits || !s->rows || !stripe) return fail(s,HP1020_IMAGE_FORMAT);
    if (s->width_bits>HP1020_IMAGE_MAX_WIDTH_BITS || s->rows>HP1020_IMAGE_MAX_ROWS ||
        stripe>HP1020_IMAGE_MAX_ROWS) return fail(s,HP1020_IMAGE_LIMIT);
    s->stride=(s->width_bits+7)/8;
    if (!chunk_rows || chunk_rows>HP1020_IMAGE_MAX_BAND_BYTES/s->stride ||
        history_size<2*s->stride || band_size<chunk_rows*s->stride)
        return fail(s,HP1020_IMAGE_LIMIT);
    s->band=band; s->chunk_rows=chunk_rows;
    /* D=DL=0 means there is no differential layer: TPDON and DPON are
     * unused. One plane and one layer make the two interleave bits moot.
     * Private prediction tables, variable height and other profiles were
     * rejected above. Preserve all source bytes; change only this copy. */
    memcpy(header,bih,sizeof(header)); header[18]=0; header[19]=0x48;
    jbg85_dec_init(&s->codec,history,2*s->stride,row_out,s);
    int r=jbg85_dec_in(&s->codec,header,sizeof(header),&used);
    if (r!=JBG_EAGAIN || used!=sizeof(header)) return fail(s,HP1020_IMAGE_STATE);
    return HP1020_IMAGE_MORE;
}
enum hp1020_image_result hp1020_image_feed(struct hp1020_image *s,
    const uint8_t *data, size_t size, size_t *used) {
    uint8_t empty=0;
    if (!used) return fail(s,HP1020_IMAGE_STATE);
    *used=0;
    if (s->error) return s->error;
    if (s->pending) return HP1020_IMAGE_BAND;
    if (s->decoded) return HP1020_IMAGE_DONE;
    if (s->ending || (!data && size)) return fail(s,HP1020_IMAGE_STATE);
    /* Upstream takes a mutable pointer but does not modify input. */
    return result(s,jbg85_dec_in(&s->codec,
                  size ? (unsigned char *)data : &empty,size,used));
}
enum hp1020_image_result hp1020_image_release(struct hp1020_image *s) {
    if (s->error) return s->error;
    if (!s->pending) return fail(s,HP1020_IMAGE_STATE);
    s->pending=0; s->band_rows=0;
    return s->decoded ? HP1020_IMAGE_DONE : HP1020_IMAGE_MORE;
}
enum hp1020_image_result hp1020_image_finish(struct hp1020_image *s) {
    uint8_t empty=0; size_t used=0;
    if (s->error) return s->error;
    if (s->pending) return HP1020_IMAGE_BAND;
    if (s->decoded) return HP1020_IMAGE_DONE;
    s->ending=1;
    /* Same end signal as jbg85_dec_end, with a nonnull empty input span. */
    s->codec.end_of_bie=1;
    enum hp1020_image_result r=result(s,jbg85_dec_in(&s->codec,&empty,0,&used));
    return r==HP1020_IMAGE_MORE ? fail(s,HP1020_IMAGE_TRUNCATED) : r;
}
