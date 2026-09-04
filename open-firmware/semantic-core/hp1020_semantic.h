#ifndef HP1020_SEMANTIC_H
#define HP1020_SEMANTIC_H
#include <stddef.h>
#include <stdint.h>

/* Host-tested portable semantic component. No device addresses or I/O hooks. */
#define HP1020_MAX_PAGES 16u
#define HP1020_MAX_RASTERS 128u
#define HP1020_METADATA_BYTES 4096u
#define HP1020_MAX_CHUNK_BYTES 0x01000000u

enum hp1020_result {
    HP1020_OK, HP1020_FORMAT, HP1020_ORDER, HP1020_LIMIT,
    HP1020_UNSUPPORTED, HP1020_TRUNCATED, HP1020_FINISHED
};

struct hp1020_page {
    uint32_t copies, nbie, resolution_x, resolution_y;
    uint32_t host_video_x, host_video_y, host_video_bpp;
    uint32_t raster_x, raster_y, item_present;
    uint32_t bih_xd, bih_yd, bih_l0;
    uint32_t first_raster, raster_count, compressed_bytes;
    uint8_t bih_options, complete;
    /* Direct START_PAGE item builder: low16(VIDEO_Y/RET/ECONOMODE).
       Source knowledge is not hardware calibration or permission to print. */
    uint16_t work_remaining_units, work_ret, work_economode;
    uint32_t item_values[24]; /* Preserve supported metadata, including offsets. */
    uint8_t video_sideband_known, stock_metadata_bounded;
};
struct hp1020_raster { uint32_t page, offset, length; };
struct hp1020_semantic {
    struct hp1020_page pages[HP1020_MAX_PAGES];
    struct hp1020_raster rasters[HP1020_MAX_RASTERS];
    uint8_t *arena;
    uint32_t arena_capacity, arena_used, page_count, raster_count, documents;
    enum hp1020_result error;
    uint32_t magic, header_used, remaining, payload_size, payload_used;
    uint32_t chunk_type, item_count, reserved, phase;
    uint8_t header[16], metadata[HP1020_METADATA_BYTES];
    uint8_t framing, finalized, document_open;
};

void hp1020_semantic_init(struct hp1020_semantic *, uint8_t *arena, uint32_t capacity);
enum hp1020_result hp1020_semantic_feed(struct hp1020_semantic *, const uint8_t *, size_t);
enum hp1020_result hp1020_semantic_finish(struct hp1020_semantic *);
#endif
