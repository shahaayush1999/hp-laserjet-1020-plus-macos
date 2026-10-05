/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_ENTRY_WORKLOAD_H
#define HP1020_ENTRY_WORKLOAD_H

/* UNEXECUTED RAM-only workload. Named words are serialized as target BE u32.
 * No USB, device, DMA/cache, controller, engine or physical output is supplied. */
#include <stdint.h>
#include "hp1020_usb_document.h"

#define HP1020_ENTRY_STATE_BYTES 13512u
#define HP1020_ENTRY_MEMORY_BYTES 114704u
#define HP1020_ENTRY_MAILBOX_BYTES 1024u
#define HP1020_ENTRY_DATA_BYTES 256u
#define HP1020_ENTRY_MAILBOX_WORDS 64u
#define HP1020_ENTRY_PIXEL_BYTES 32u
#define HP1020_ENTRY_PIXEL_OFFSET 256u
#define HP1020_ENTRY_MAILBOX_MAGIC UINT32_C(0x48503130)
#define HP1020_ENTRY_ABI_VERSION 1u
#define HP1020_ENTRY_FRAGMENT_BYTES 64u
#define HP1020_ENTRY_INPUT_MAX_BYTES 1024u

enum hp1020_entry_status {
    HP1020_ENTRY_UNREPORTED = 0, HP1020_ENTRY_RUNNING = 1,
    HP1020_ENTRY_PASS = 2, HP1020_ENTRY_FAIL = 3
};
enum hp1020_entry_stage {
    HP1020_ENTRY_STAGE_SCAN = 1, HP1020_ENTRY_STAGE_INIT = 2,
    HP1020_ENTRY_STAGE_FEED = 3, HP1020_ENTRY_STAGE_FINISH = 4,
    HP1020_ENTRY_STAGE_DONE = 5
};
enum hp1020_entry_error {
    HP1020_ENTRY_ERROR_NONE = 0, HP1020_ENTRY_ERROR_ZERO = 1,
    HP1020_ENTRY_ERROR_DATA = 2, HP1020_ENTRY_ERROR_INPUT = 3,
    HP1020_ENTRY_ERROR_INIT = 4, HP1020_ENTRY_ERROR_RESERVE = 5,
    HP1020_ENTRY_ERROR_TICKET = 6, HP1020_ENTRY_ERROR_COMPLETE = 7,
    HP1020_ENTRY_ERROR_PUMP = 8, HP1020_ENTRY_ERROR_FINISH = 9,
    HP1020_ENTRY_ERROR_OUTPUT = 10, HP1020_ENTRY_ERROR_DOCUMENT = 11,
    HP1020_ENTRY_ERROR_LIMIT = 12, HP1020_ENTRY_ERROR_FINAL = 13,
    HP1020_ENTRY_ERROR_DATA_FINAL = 14
};

/* Counts are software observations, never physical completion promises.
 * ZERO_BAD/DATA_BAD count bytes; FIRST fields are target addresses or zero.
 * STAGE stays at the first failure; ERROR_DETAIL is local bounded context.
 * Input hash and both storage hashes are FNV1a32. PIXEL_FNV covers only actual
 * PIXEL_BYTES; pixel bytes are copied from the borrowed actual output view.
 * DOCUMENT_* copy the original event by value, never today's generation.
 * RING_RESULT records the last ring operation (final complete OK, no terminal
 * peek); IMAGE_ERROR is output.error. RECEIVE_FNV covers all4096 receive bytes,
 * OUTPUT_FNV all32768 output-slot bytes. Fields22..28,40..47,54..60 are read-only
 * production snapshots taken at end.
 * Scan-failure return writes only words0..13/61; no initializer is called. */
enum hp1020_entry_word {
    HP1020_ENTRY_W_MAGIC = 0, HP1020_ENTRY_W_ABI = 1,
    HP1020_ENTRY_W_STATUS = 2, HP1020_ENTRY_W_ERROR = 3,
    HP1020_ENTRY_W_STAGE = 4, HP1020_ENTRY_W_RX_RESULT = 5,
    HP1020_ENTRY_W_PAYLOAD_RESULT = 6, HP1020_ENTRY_W_RING_RESULT = 7,
    HP1020_ENTRY_W_ZERO_BAD = 8, HP1020_ENTRY_W_ZERO_FIRST = 9,
    HP1020_ENTRY_W_DATA_BAD = 10, HP1020_ENTRY_W_DATA_FIRST = 11,
    HP1020_ENTRY_W_ZERO_SCANNED = 12, HP1020_ENTRY_W_DATA_SCANNED = 13,
    HP1020_ENTRY_W_INPUT_BYTES = 14, HP1020_ENTRY_W_INPUT_FNV = 15,
    HP1020_ENTRY_W_FED_BYTES = 16, HP1020_ENTRY_W_COPY_CALLS = 17,
    HP1020_ENTRY_W_RESERVE_CALLS = 18, HP1020_ENTRY_W_COMPLETE_CALLS = 19,
    HP1020_ENTRY_W_PUMP_CALLS = 20, HP1020_ENTRY_W_FINISH_CALLS = 21,
    HP1020_ENTRY_W_GENERATION = 22, HP1020_ENTRY_W_ISSUED = 23,
    HP1020_ENTRY_W_CONSUMED = 24, HP1020_ENTRY_W_RX_COUNT = 25,
    HP1020_ENTRY_W_STOPPED = 26, HP1020_ENTRY_W_QUIESCENT = 27,
    HP1020_ENTRY_W_FINISHED = 28, HP1020_ENTRY_W_OUTPUT_CALLS = 29,
    HP1020_ENTRY_W_OUTPUT_ACCEPTS = 30, HP1020_ENTRY_W_OUTPUT_COMPLETES = 31,
    HP1020_ENTRY_W_PIXEL_BYTES = 32, HP1020_ENTRY_W_PIXEL_FNV = 33,
    HP1020_ENTRY_W_DOCUMENT_CALLS = 34, HP1020_ENTRY_W_DOCUMENT_GENERATION = 35,
    HP1020_ENTRY_W_DOCUMENT_ID = 36, HP1020_ENTRY_W_DOCUMENT_FIRST_PAGE = 37,
    HP1020_ENTRY_W_DOCUMENT_PAGES = 38, HP1020_ENTRY_W_DOCUMENT_RESULT = 39,
    HP1020_ENTRY_W_PARSER_DOCUMENTS = 40, HP1020_ENTRY_W_STREAM_PAGES = 41,
    HP1020_ENTRY_W_PAGES_DRAINED = 42, HP1020_ENTRY_W_DOCUMENTS_COMPLETED = 43,
    HP1020_ENTRY_W_COPIED_ROWS = 44, HP1020_ENTRY_W_ACCEPTED_ROWS = 45,
    HP1020_ENTRY_W_COMPLETED_ROWS = 46, HP1020_ENTRY_W_NONFREE_OUTPUT_SLOTS = 47,
    HP1020_ENTRY_W_TICKET_GENERATION = 48, HP1020_ENTRY_W_TICKET_SEQUENCE = 49,
    HP1020_ENTRY_W_LAST_FRAGMENT = 50, HP1020_ENTRY_W_OUTPUT_FINAL = 51,
    HP1020_ENTRY_W_OUTPUT_ROWS = 52, HP1020_ENTRY_W_OUTPUT_STRIDE = 53,
    HP1020_ENTRY_W_RX_ERROR = 54, HP1020_ENTRY_W_IMAGE_ERROR = 55,
    HP1020_ENTRY_W_RING_ERROR = 56, HP1020_ENTRY_W_RECEIVE_FNV = 57,
    HP1020_ENTRY_W_OUTPUT_FNV = 58, HP1020_ENTRY_W_STATE_BYTES = 59,
    HP1020_ENTRY_W_MEMORY_BYTES = 60, HP1020_ENTRY_W_ERROR_DETAIL = 61,
    HP1020_ENTRY_W_FINAL_DATA_BAD = 62, HP1020_ENTRY_W_FINAL_DATA_FIRST = 63
};

struct hp1020_entry_mailbox_type {
    uint32_t words[HP1020_ENTRY_MAILBOX_WORDS];
    uint8_t pixels[HP1020_ENTRY_PIXEL_BYTES];
    uint8_t reserved[HP1020_ENTRY_MAILBOX_BYTES - HP1020_ENTRY_PIXEL_OFFSET - HP1020_ENTRY_PIXEL_BYTES];
};

extern struct hp1020_usb_document hp1020_entry_state;
extern struct hp1020_usb_document_memory hp1020_entry_memory;
extern volatile struct hp1020_entry_mailbox_type hp1020_entry_mailbox;
extern uint8_t hp1020_entry_data[HP1020_ENTRY_DATA_BYTES];

/* Exactly one call by startup after its own stack and three BSS clears.
 * Return goes to the startup's terminal park, never to an inherited caller. */
void hp1020_entry_c(void);

/* Build-time const input contract, included by implementation only:
 * hp1020_entry_input.h provides HP1020_ENTRY_INPUT_BYTES (1..1024) and
 * static const uint8_t hp1020_entry_input[HP1020_ENTRY_INPUT_BYTES] = {...};
 * The planned352-byte stream is derived from the unchanged checked fixture
 * builder; no new input header has been generated/frozen by this draft.
 * Six64-byte reservations carry lengths64,64,64,64,64,32 and original G1 tickets
 * 1..6; each is copied/completed/pumped before the next. Exactly one explicit
 * finish follows the already observed32-byte page and original END_DOC event.
 * That array belongs only to read-only text/rodata; no additional writable
 * objects or input-generating code are added to the workload. */
#endif
