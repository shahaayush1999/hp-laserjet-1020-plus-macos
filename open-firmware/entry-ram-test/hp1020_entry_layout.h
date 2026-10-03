/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_ENTRY_LAYOUT_H
#define HP1020_ENTRY_LAYOUT_H

/* UNEXECUTED compiler-layout witness. No workload or generated input is used.
 * The target stores these uint32_t words in ordinary read-only data. The runner
 * must verify every word against separately derived target32 expectations
 * before using an offset to inspect production memory. This is layout metadata,
 * not an observed document result or a physical-memory mapping contract. */
#include <stdint.h>

#define HP1020_ENTRY_LAYOUT_VERSION 1u
#define HP1020_ENTRY_LAYOUT_HEADER_WORDS 5u
#define HP1020_ENTRY_LAYOUT_RECORD_WORDS 3u

enum hp1020_entry_layout_header_word {
    HP1020_ENTRY_LAYOUT_W_VERSION = 0,
    HP1020_ENTRY_LAYOUT_W_WORD_COUNT = 1,
    HP1020_ENTRY_LAYOUT_W_FIELD_COUNT = 2,
    HP1020_ENTRY_LAYOUT_W_STATE_BYTES = 3,
    HP1020_ENTRY_LAYOUT_W_MEMORY_BYTES = 4
};

/* Each record has [base, byte offset from that object, byte width].
 * No target pointer is stored. State means the actual hp1020_entry_state;
 * memory means the actual hp1020_entry_memory, independently located by symbol.
 * A flag width is one byte; never read the adjacent flags as a single u32. */
enum hp1020_entry_layout_base {
    HP1020_ENTRY_LAYOUT_BASE_STATE = 1,
    HP1020_ENTRY_LAYOUT_BASE_MEMORY = 2
};
enum hp1020_entry_layout_record_word {
    HP1020_ENTRY_LAYOUT_R_BASE = 0,
    HP1020_ENTRY_LAYOUT_R_OFFSET = 1,
    HP1020_ENTRY_LAYOUT_R_WIDTH = 2
};
enum hp1020_entry_layout_field {
    HP1020_ENTRY_LAYOUT_RECEIVE_GENERATION = 0,
    HP1020_ENTRY_LAYOUT_RECEIVE_ISSUED = 1,
    HP1020_ENTRY_LAYOUT_RECEIVE_CONSUMED = 2,
    HP1020_ENTRY_LAYOUT_RECEIVE_COUNT = 3,
    HP1020_ENTRY_LAYOUT_RECEIVE_STOPPED = 4,
    HP1020_ENTRY_LAYOUT_RECEIVE_QUIESCENT = 5,
    HP1020_ENTRY_LAYOUT_DOCUMENT_FINISHED = 6,
    HP1020_ENTRY_LAYOUT_PARSER_DOCUMENTS = 7,
    HP1020_ENTRY_LAYOUT_STREAM_PAGES = 8,
    HP1020_ENTRY_LAYOUT_PAGES_DRAINED = 9,
    HP1020_ENTRY_LAYOUT_DOCUMENTS_COMPLETED = 10,
    HP1020_ENTRY_LAYOUT_OUTPUT_QUIESCENT = 11,
    HP1020_ENTRY_LAYOUT_PAYLOAD_ERROR = 12,
    HP1020_ENTRY_LAYOUT_FEED_GENERATION = 13,
    HP1020_ENTRY_LAYOUT_RECEIVE_ERROR = 14,
    HP1020_ENTRY_LAYOUT_OUTPUT_FINISHED = 15,
    HP1020_ENTRY_LAYOUT_OUTPUT_ERROR = 16,
    HP1020_ENTRY_LAYOUT_MEMORY_RECEIVE_DATA = 17,
    HP1020_ENTRY_LAYOUT_MEMORY_OUTPUT_SLOTS = 18,
    HP1020_ENTRY_LAYOUT_MEMORY_STREAM = 19,
    HP1020_ENTRY_LAYOUT_FIELD_COUNT = 20
};

#define HP1020_ENTRY_LAYOUT_WORDS \
    (HP1020_ENTRY_LAYOUT_HEADER_WORDS + \
     HP1020_ENTRY_LAYOUT_RECORD_WORDS * HP1020_ENTRY_LAYOUT_FIELD_COUNT)
#define HP1020_ENTRY_LAYOUT_RECORD(field) \
    (HP1020_ENTRY_LAYOUT_HEADER_WORDS + \
     HP1020_ENTRY_LAYOUT_RECORD_WORDS * (field))

extern const uint32_t hp1020_entry_layout[HP1020_ENTRY_LAYOUT_WORDS];
#endif
