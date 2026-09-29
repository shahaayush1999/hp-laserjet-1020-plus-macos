/* SPDX-License-Identifier: GPL-2.0-or-later
 * Host codec. Same event and output ABI as the EP0 fixture,
 * with 48 OUT + 40 SETUP words appended and separately guarded RAM captures.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hp1020_usb_document.h"

extern uint8_t hp1020_bulk_fixture_input[1024], hp1020_bulk_fixture_pixels[262144];
extern uint8_t hp1020_bulk_fixture_wire[32768];
extern uint32_t hp1020_bulk_fixture_stats[96], hp1020_ep0_fixture_stats[104];
extern uint32_t hp1020_composed_out_stats[48], hp1020_composed_setup_stats[40];
extern uint32_t hp1020_bulk_fixture_documents[512][5];
uint32_t hp1020_bulk_fixture_reset(uint32_t,uint32_t,uint32_t,uint32_t);
uint32_t hp1020_bulk_fixture_step(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);
uint8_t *hp1020_bulk_fixture_receive_storage(void);
uint8_t *hp1020_bulk_fixture_output_storage(void);
uint8_t *hp1020_ep0_fixture_storage(void);
uint32_t hp1020_ep0_fixture_storage_bytes(void);
uint8_t *hp1020_composed_fixture_out_storage(void);
uint8_t *hp1020_composed_fixture_setup_storage(void);
uint32_t hp1020_composed_fixture_out_storage_bytes(void);
uint32_t hp1020_composed_fixture_setup_storage_bytes(void);

static void print_stats(void) {
    putchar('[');
    for (unsigned i = 0; i < 96; i++) printf("%s%u", i ? "," : "", hp1020_bulk_fixture_stats[i]);
    for (unsigned i = 0; i < 104; i++) printf(",%u", hp1020_ep0_fixture_stats[i]);
    for (unsigned i = 0; i < 48; i++) printf(",%u", hp1020_composed_out_stats[i]);
    for (unsigned i = 0; i < 40; i++) printf(",%u", hp1020_composed_setup_stats[i]);
    puts("]"); fflush(stdout);
}
static int save(const char *path, const void *data, size_t length) {
    FILE *file = fopen(path, "wb");
    if (!file) return 0;
    const int ok = fwrite(data, 1, length, file) == length;
    return fclose(file) == 0 && ok;
}
static int save_extra(const char *output_path, const char *suffix, const void *data, size_t bytes) {
    const size_t length = strlen(output_path), tail = strlen(suffix) + 1u;
    if (length > SIZE_MAX - tail) return 0;
    char *path = malloc(length + tail);
    if (!path) return 0;
    memcpy(path, output_path, length); memcpy(path + length, suffix, tail);
    const int ok = save(path, data, bytes); free(path); return ok;
}
int main(int argc, char **argv) {
    if (argc != 9 && argc != 10) return 2;
    hp1020_bulk_fixture_reset((uint32_t)strtoul(argv[1], NULL, 0), (uint32_t)strtoul(argv[2], NULL, 0),
        (uint32_t)strtoul(argv[3], NULL, 0), (uint32_t)strtoul(argv[4], NULL, 0));
    print_stats();
    uint8_t header[24]; size_t n;
    while ((n = fread(header, 1, sizeof(header), stdin))) {
        if (n != sizeof(header)) return 3;
        uint32_t word[6];
        for (unsigned i = 0; i < 6; i++) word[i] = ((uint32_t)header[4*i] << 24) |
            ((uint32_t)header[4*i+1] << 16) | ((uint32_t)header[4*i+2] << 8) | header[4*i+3];
        if (word[5] > sizeof(hp1020_bulk_fixture_input) ||
            fread(hp1020_bulk_fixture_input, 1, word[5], stdin) != word[5]) return 3;
        if ((word[0] == 44 && word[5] != 20) || (word[0] == 48 && word[5] != 4) ||
            ((word[0] == 46 || word[0] == 65) && word[5] != word[4]) ||
            ((word[0] == 62 || word[0] == 80) && word[5] != 16)) return 3;
        hp1020_bulk_fixture_step(word[0], word[1], word[2], word[3], word[4]); print_stats();
    }
    if (ferror(stdin)) return 3;
    if (!save(argv[5], hp1020_bulk_fixture_pixels, hp1020_bulk_fixture_stats[50]) ||
        !save(argv[6], hp1020_bulk_fixture_wire, hp1020_bulk_fixture_stats[24]) ||
        !save(argv[7], hp1020_bulk_fixture_receive_storage(), sizeof(((struct hp1020_rx_memory *)0)->data)) ||
        !save(argv[8], hp1020_bulk_fixture_output_storage(), sizeof(((struct hp1020_image_output_memory *)0)->slots)) ||
        !save_extra(argv[8], ".ep0-descriptors", hp1020_ep0_fixture_storage(), hp1020_ep0_fixture_storage_bytes()) ||
        !save_extra(argv[8], ".udc-descriptor", hp1020_composed_fixture_out_storage(), hp1020_composed_fixture_out_storage_bytes()) ||
        !save_extra(argv[8], ".setup-record", hp1020_composed_fixture_setup_storage(), hp1020_composed_fixture_setup_storage_bytes())) return 4;
    if (argc == 10) {
        FILE *documents = fopen(argv[9], "wb");
        if (!documents) return 4;
        for (uint32_t i = 0; i < hp1020_bulk_fixture_stats[90]; i++) for (uint32_t j = 0; j < 5; j++) {
            const uint32_t value = hp1020_bulk_fixture_documents[i][j];
            const uint8_t bytes[4] = {(uint8_t)(value >> 24), (uint8_t)(value >> 16),
                (uint8_t)(value >> 8), (uint8_t)value};
            if (fwrite(bytes, 1, 4, documents) != 4) { fclose(documents); return 4; }
        }
        if (fclose(documents)) return 4;
    }
    return 0;
}
