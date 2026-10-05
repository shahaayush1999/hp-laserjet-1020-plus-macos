/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_USB_RUNTIME_CONTRACT_H
#define HP1020_USB_RUNTIME_CONTRACT_H

/* Real two-page public contract, drafted before execution on 2026-10-05. This header
 * declares evidence and stationary storage only; it implements no runtime,
 * controller, cache, DMA mapping or settlement. Validation belongs to reports.
 * See CONTRACT.md before implementing these declarations. */
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
#include "hp1020_tusb_adapter.h"
#include "hp1020_udc_setup.h"
#include "hp1020_udc_ep0.h"
#include "hp1020_udc_publish.h"
#include "hp1020_udc_acquire.h"

#define HP1020_USB_RUNTIME_VERSION 3u
#define HP1020_USB_RUNTIME_MAGIC UINT32_C(0x48505552)
#define HP1020_USB_RUNTIME_DOCUMENT_BYTES 13512u
#define HP1020_USB_RUNTIME_MEMORY_BYTES 114704u
#define HP1020_USB_RUNTIME_MAILBOX_BYTES 1024u
#define HP1020_USB_RUNTIME_SENTINEL_BYTES 256u
#define HP1020_USB_RUNTIME_WITNESS_BYTES 9216u
#define HP1020_USB_RUNTIME_WITNESS_CAP 10176u
#define HP1020_USB_RUNTIME_PROVIDER_CAP 384u
#define HP1020_USB_RUNTIME_INPUT_BYTES 967u
#define HP1020_USB_RUNTIME_DATA_PACKETS 16u
#define HP1020_USB_RUNTIME_BULK_PACKETS 17u
#define HP1020_USB_RUNTIME_BINDS 18u
#define HP1020_USB_RUNTIME_IO_ROWS 308u
#define HP1020_USB_RUNTIME_RANGE_ROWS 85u
#define HP1020_USB_RUNTIME_PIXEL_BYTES 192u
#define HP1020_USB_RUNTIME_DOCUMENT_EVENTS 1u
#define HP1020_USB_RUNTIME_MAX_STEPS 256u
#define HP1020_USB_RUNTIME_GUARD_BYTE 0xa7u

/* Explicit fixture labels. Never derive any label from a CPU pointer. */
#define HP1020_USB_RUNTIME_OUT_DESCRIPTOR_DMA UINT32_C(0x579bdf10)
#define HP1020_USB_RUNTIME_RX0_DMA UINT32_C(0x24681340)
#define HP1020_USB_RUNTIME_RX1_DMA UINT32_C(0x24682340)
#define HP1020_USB_RUNTIME_RX2_DMA UINT32_C(0x24683340)
#define HP1020_USB_RUNTIME_RX3_DMA UINT32_C(0x24684340)
#define HP1020_USB_RUNTIME_SETUP_DMA UINT32_C(0x79bdf130)
#define HP1020_USB_RUNTIME_EP0_OUT_DESCRIPTOR_DMA UINT32_C(0x13579bd0)
#define HP1020_USB_RUNTIME_EP0_IN_DESCRIPTOR_DMA UINT32_C(0xa468ace0)
#define HP1020_USB_RUNTIME_EP0_OUT_PACKET_DMA UINT32_C(0x3579bdf0)
#define HP1020_USB_RUNTIME_EP0_IN_PACKET_DMA UINT32_C(0xb68ace00)

enum hp1020_usb_runtime_status {
    HP1020_USB_RUNTIME_ZERO = 0, HP1020_USB_RUNTIME_RUNNING = 1,
    HP1020_USB_RUNTIME_PASS = 2, HP1020_USB_RUNTIME_FAIL = 3
};
enum hp1020_usb_runtime_phase {
    HP1020_USB_RUNTIME_SCAN = 0, HP1020_USB_RUNTIME_INIT = 1,
    HP1020_USB_RUNTIME_RESET = 2, HP1020_USB_RUNTIME_CONFIGURE = 3,
    HP1020_USB_RUNTIME_EP0_SETTLE = 4, HP1020_USB_RUNTIME_RECOVERY = 5,
    HP1020_USB_RUNTIME_ARM = 6, HP1020_USB_RUNTIME_IMAGE = 7,
    HP1020_USB_RUNTIME_ACQUIRE = 8, HP1020_USB_RUNTIME_SERVICE = 9,
    HP1020_USB_RUNTIME_PUMP = 10, HP1020_USB_RUNTIME_CLOSE = 11,
    HP1020_USB_RUNTIME_FINISH = 12, HP1020_USB_RUNTIME_DONE = 13
};
enum hp1020_usb_runtime_error {
    HP1020_USB_RUNTIME_ERROR_NONE = 0, HP1020_USB_RUNTIME_ERROR_ZERO = 1,
    HP1020_USB_RUNTIME_ERROR_SENTINEL = 2, HP1020_USB_RUNTIME_ERROR_LIMIT = 3,
    HP1020_USB_RUNTIME_ERROR_API = 4, HP1020_USB_RUNTIME_ERROR_OWNER = 5,
    HP1020_USB_RUNTIME_ERROR_RANGE = 6, HP1020_USB_RUNTIME_ERROR_READ_SCRIPT = 7,
    HP1020_USB_RUNTIME_ERROR_CALLBACK = 8, HP1020_USB_RUNTIME_ERROR_OUTPUT = 9,
    HP1020_USB_RUNTIME_ERROR_DOCUMENT = 10, HP1020_USB_RUNTIME_ERROR_FINAL = 11
};
enum hp1020_usb_runtime_result_domain {
    HP1020_USB_RUNTIME_DOMAIN_NONE = 0, HP1020_USB_RUNTIME_DOMAIN_RECEIVE = 1,
    HP1020_USB_RUNTIME_DOMAIN_PRINTER = 2, HP1020_USB_RUNTIME_DOMAIN_ADAPTER = 3,
    HP1020_USB_RUNTIME_DOMAIN_SETUP = 4, HP1020_USB_RUNTIME_DOMAIN_EP0 = 5,
    HP1020_USB_RUNTIME_DOMAIN_PROGRAM = 6, HP1020_USB_RUNTIME_DOMAIN_PUBLISH = 7,
    HP1020_USB_RUNTIME_DOMAIN_OUT = 8, HP1020_USB_RUNTIME_DOMAIN_RING = 9
};

/* Every word is a logical uint32, BE in the admitted target. Do not serialize
 * an arbitrary compiler struct or treat logs as production ownership. The row index is its immutable ordinal minus one. Configuration and
 * bulk scopes are independently reconstructed from the complete ordered calls;
 * no log field is a production transfer/ingress identity. */
struct hp1020_usb_runtime_io_row {
    uint32_t kind, argument, value, outcome;
};
/* ordinal points to one actual kind4..8 trace call. cookie fields below come
 * from adapter.owners[2] at hook entry, independently of the hook argument and
 * component diagnostics. The supplied hook cookie must match ALL five fields
 * before any image copy. span_cpu is the actual hook pointer (zero for kind8);
 * owner_cpu/owner_length are copied from the actual adapter owner. DMA and byte
 * count remain the actual hook arguments in the matching I/O row. */
struct hp1020_usb_runtime_range_row {
    uint32_t ordinal, id, epoch, generation, sequence, endpoint;
    uint32_t span_cpu, owner_cpu, owner_length;
};
/* One append per actual DCD bind, including a bind followed by failure. These
 * records are immutable evidence, not a queue used to recover event identity.
 * EP0 original_cpu is zero for the ZLP; packet_cpu still identifies staging64.
 * No dereference is authorized by these numeric diagnostic addresses. */
struct hp1020_usb_runtime_bind_row {
    uint32_t id, epoch, generation, sequence, endpoint;
    uint32_t original_cpu, requested, descriptor_cpu, packet_cpu;
};
struct hp1020_usb_runtime_document_row {
    uint32_t generation, document_id, first_page, pages, callback_result;
};
struct hp1020_usb_runtime_device_images {
    uint8_t guard0[16], descriptor[16], guard1[16], guard2[16];
    uint8_t payload[64], guard3[16];
};

/* Exact9,216-byte evidence object. Guards become16 bytes of0xa7 after the
 * initial complete zero scan. Padding/reserved bytes stay zero. Arrays beyond
 * their actual append count stay zero. Device images are explicitly supplied
 * RAM sources; they are not a second CPU receive queue or physical DMA model. */
struct hp1020_usb_runtime_witness_type {
    uint8_t head_guard[16];                                      /* +0 */
    struct hp1020_usb_runtime_io_row io[308];                     /* +16 */
    uint8_t io_guard[16];                                        /* +4944 */
    struct hp1020_usb_runtime_range_row ranges[85];               /* +4960 */
    uint8_t range_padding[12], range_guard[16];                   /* +8020,+8032 */
    struct hp1020_usb_runtime_bind_row binds[18];                 /* +8048 */
    uint8_t bind_padding[8], bind_guard[16];                      /* +8696,+8704 */
    struct hp1020_usb_runtime_device_images device;              /* +8720 */
    uint8_t pixels[192];                                         /* +8864 */
    struct hp1020_usb_runtime_document_row documents[1];          /* +9056 */
    uint8_t reserved[140];                                       /* +9076 */
};

/* Mailbox words0..127 are fixed below,128..255 remain zero. Snapshot words are
 * secondary diagnostics: independent acceptance reads original component and
 * private TinyUSB bytes at actual function entries. Live counters are bounded.
 * close/finish counters count returned calls, so both are0 at FIRST close entry.
 * Actual entry-call tracking remains an independent runner obligation. */
enum hp1020_usb_runtime_word {
    HP1020_USB_RUNTIME_W_MAGIC = 0, HP1020_USB_RUNTIME_W_VERSION = 1,
    HP1020_USB_RUNTIME_W_STATUS = 2, HP1020_USB_RUNTIME_W_PHASE = 3,
    HP1020_USB_RUNTIME_W_ERROR = 4, HP1020_USB_RUNTIME_W_ERROR_DETAIL = 5,
    HP1020_USB_RUNTIME_W_FIRST_BAD_ADDRESS = 6, HP1020_USB_RUNTIME_W_BAD_BYTES = 7,
    HP1020_USB_RUNTIME_W_SCANNED_BSS = 8, HP1020_USB_RUNTIME_W_SCANNED_MEMORY = 9,
    HP1020_USB_RUNTIME_W_SCANNED_MAILBOX = 10, HP1020_USB_RUNTIME_W_SCANNED_WITNESS = 11,
    HP1020_USB_RUNTIME_W_SCANNED_SENTINEL = 12, HP1020_USB_RUNTIME_W_DATA_BYTES = 13,
    HP1020_USB_RUNTIME_W_INITIAL_DATA_FNV = 14, HP1020_USB_RUNTIME_W_STEPS = 15,
    HP1020_USB_RUNTIME_W_INITIALIZATIONS = 16, HP1020_USB_RUNTIME_W_TUSB_INITIALIZATIONS = 17,
    HP1020_USB_RUNTIME_W_RESETS_ADMITTED = 18, HP1020_USB_RUNTIME_W_SETUPS_ADMITTED = 19,
    HP1020_USB_RUNTIME_W_SERVICES = 20, HP1020_USB_RUNTIME_W_PUMPS = 21,
    HP1020_USB_RUNTIME_W_ARM_CALLS = 22, HP1020_USB_RUNTIME_W_BULK_BINDS = 23,
    HP1020_USB_RUNTIME_W_EP0_BINDS = 24, HP1020_USB_RUNTIME_W_ACQUIRE_CALLS = 25,
    HP1020_USB_RUNTIME_W_ACQUIRES_ACCEPTED = 26, HP1020_USB_RUNTIME_W_EP0_OBSERVATIONS = 27,
    HP1020_USB_RUNTIME_W_EP0_SETTLED = 28, HP1020_USB_RUNTIME_W_STATUS_CALLBACKS = 29,
    HP1020_USB_RUNTIME_W_RECEIVE_PROMISES = 30, HP1020_USB_RUNTIME_W_OUTPUT_PROMISES = 31,
    HP1020_USB_RUNTIME_W_TRANSPORT_PROMISES = 32, HP1020_USB_RUNTIME_W_RECOVERY_FINISHES = 33,
    HP1020_USB_RUNTIME_W_CLOSE_CALLS = 34, HP1020_USB_RUNTIME_W_FINISH_CALLS = 35,
    HP1020_USB_RUNTIME_W_CANCEL_REQUESTS = 36, HP1020_USB_RUNTIME_W_CANCEL_SETTLEMENTS = 37,
    HP1020_USB_RUNTIME_W_IO_ROWS = 38, HP1020_USB_RUNTIME_W_RANGE_ROWS = 39,
    HP1020_USB_RUNTIME_W_BIND_ROWS = 40, HP1020_USB_RUNTIME_W_DEVICE_INSTALLS = 41,
    HP1020_USB_RUNTIME_W_POISON_INSTALLS = 42, HP1020_USB_RUNTIME_W_PIXEL_BYTES = 43,
    HP1020_USB_RUNTIME_W_OUTPUT_CALLBACKS = 44, HP1020_USB_RUNTIME_W_OUTPUT_ACCEPTS = 45,
    HP1020_USB_RUNTIME_W_OUTPUT_COMPLETES = 46, HP1020_USB_RUNTIME_W_DOCUMENT_CALLBACKS = 47,
    HP1020_USB_RUNTIME_W_CALLBACK_ERRORS = 48, HP1020_USB_RUNTIME_W_LATE_CALLBACKS = 49,
    HP1020_USB_RUNTIME_W_BOUNDS_ERRORS = 50, HP1020_USB_RUNTIME_W_READ_CURSOR = 51,
    HP1020_USB_RUNTIME_W_RANGE_CHECKS = 52, HP1020_USB_RUNTIME_W_CALLBACK_DEPTH = 53,
    HP1020_USB_RUNTIME_W_OPEN_MASK = 54, HP1020_USB_RUNTIME_W_STALL_MASK = 55,
    HP1020_USB_RUNTIME_W_RESULT_DOMAIN = 56, HP1020_USB_RUNTIME_W_RESULT = 57,
    HP1020_USB_RUNTIME_W_PUMP_RESULT = 58, HP1020_USB_RUNTIME_W_FINISH_RESULT = 59,
    HP1020_USB_RUNTIME_W_RECOVERY_ID = 60, HP1020_USB_RUNTIME_W_RECOVERY_GENERATION = 61,
    HP1020_USB_RUNTIME_W_LAST_COOKIE_ID = 62, HP1020_USB_RUNTIME_W_LAST_COOKIE_EPOCH = 63,
    HP1020_USB_RUNTIME_W_LAST_COOKIE_GENERATION = 64, HP1020_USB_RUNTIME_W_LAST_COOKIE_SEQUENCE = 65,
    HP1020_USB_RUNTIME_W_LAST_COOKIE_ENDPOINT = 66, HP1020_USB_RUNTIME_W_LAST_SLOT = 67,
    HP1020_USB_RUNTIME_W_BEFORE_CLOSE_IO = 68, HP1020_USB_RUNTIME_W_BEFORE_CLOSE_PIXELS = 69,
    HP1020_USB_RUNTIME_W_BEFORE_CLOSE_DOCUMENTS = 70, HP1020_USB_RUNTIME_W_AFTER_ACQUIRE_OWNER = 71,
    HP1020_USB_RUNTIME_W_AFTER_ACQUIRE_COUNT = 72, HP1020_USB_RUNTIME_W_AFTER_ACQUIRE_CONSUMED = 73,
    HP1020_USB_RUNTIME_W_AFTER_ACQUIRE_OUT_PHASE = 74, HP1020_USB_RUNTIME_W_RECEIVE_FNV = 75,
    HP1020_USB_RUNTIME_W_OUTPUT_FNV = 76, HP1020_USB_RUNTIME_W_PIXELS_FNV = 77,
    HP1020_USB_RUNTIME_W_TRACE_FNV = 78, HP1020_USB_RUNTIME_W_RANGES_FNV = 79,
    HP1020_USB_RUNTIME_W_BINDS_FNV = 80, HP1020_USB_RUNTIME_W_RECEIVE_GENERATION = 81,
    HP1020_USB_RUNTIME_W_RECEIVE_ISSUED = 82, HP1020_USB_RUNTIME_W_RECEIVE_CONSUMED = 83,
    HP1020_USB_RUNTIME_W_RECEIVE_COUNT = 84, HP1020_USB_RUNTIME_W_RECEIVE_STOPPED = 85,
    HP1020_USB_RUNTIME_W_RECEIVE_QUIESCENT = 86, HP1020_USB_RUNTIME_W_RECEIVE_ERROR = 87,
    HP1020_USB_RUNTIME_W_DOCUMENT_FINISHED = 88, HP1020_USB_RUNTIME_W_OUTPUT_FINISHED = 89,
    HP1020_USB_RUNTIME_W_OUTPUT_ERROR = 90, HP1020_USB_RUNTIME_W_OUTPUT_QUIESCENT = 91,
    HP1020_USB_RUNTIME_W_PAYLOAD_ERROR = 92, HP1020_USB_RUNTIME_W_PARSER_DOCUMENTS = 93,
    HP1020_USB_RUNTIME_W_STREAM_PAGES = 94, HP1020_USB_RUNTIME_W_PAGES_DRAINED = 95,
    HP1020_USB_RUNTIME_W_DOCUMENTS_COMPLETED = 96, HP1020_USB_RUNTIME_W_DOCUMENT_FIRST_PAGE = 97,
    HP1020_USB_RUNTIME_W_INPUT_CLOSED = 98, HP1020_USB_RUNTIME_W_FENCED = 99,
    HP1020_USB_RUNTIME_W_CONTROL_EPOCH = 100, HP1020_USB_RUNTIME_W_ACTIVE_CONTROL_EPOCH = 101,
    HP1020_USB_RUNTIME_W_TRANSPORT_EPOCH = 102, HP1020_USB_RUNTIME_W_ACTIVE_TRANSPORT_EPOCH = 103,
    HP1020_USB_RUNTIME_W_LAST_SUBMISSION_ID = 104, HP1020_USB_RUNTIME_W_EP0_OUT_OWNER = 105,
    HP1020_USB_RUNTIME_W_EP0_IN_OWNER = 106, HP1020_USB_RUNTIME_W_BULK_OWNER = 107,
    HP1020_USB_RUNTIME_W_OUT_PHASE = 108, HP1020_USB_RUNTIME_W_BULK_CORE_BUSY = 109,
    HP1020_USB_RUNTIME_W_PROGRAM_FAILED = 110, HP1020_USB_RUNTIME_W_PUBLISH_FAILED = 111,
    HP1020_USB_RUNTIME_W_ACQUIRE_FAILED = 112, HP1020_USB_RUNTIME_W_PUBLICATION_PREFIX = 113,
    HP1020_USB_RUNTIME_W_ACQUISITION_PREFIX = 114, HP1020_USB_RUNTIME_W_INPUT_CONSUMED = 115,
    HP1020_USB_RUNTIME_W_PAYLOAD_COPIED = 116, HP1020_USB_RUNTIME_W_DESCRIPTOR_COPIED = 117,
    HP1020_USB_RUNTIME_W_READ_CALLS = 118, HP1020_USB_RUNTIME_W_WRITE_CALLS = 119,
    HP1020_USB_RUNTIME_W_ORDER_CALLS = 120, HP1020_USB_RUNTIME_W_RX_PREPARES = 121,
    HP1020_USB_RUNTIME_W_DESCRIPTOR_PREPARES = 122, HP1020_USB_RUNTIME_W_DESCRIPTOR_ACQUIRES = 123,
    HP1020_USB_RUNTIME_W_PAYLOAD_ACQUIRES = 124, HP1020_USB_RUNTIME_W_ACQUIRE_ORDERS = 125,
    HP1020_USB_RUNTIME_W_BEFORE_CLOSE_CORE_BUSY = 126,
    HP1020_USB_RUNTIME_W_BEFORE_FINAL_SERVICE_CORE_BUSY = 127
};
struct hp1020_usb_runtime_mailbox_type { uint32_t words[256]; };

/* Only two actual live DCD records; no transfer history drives execution.
 * Retain cookie/buffer/length after live becomes0 until the next genuine bind.
 * slot is0..3 only for bulk; EP0 uses255. cookie is never reconstructed from
 * current generation, endpoint, descriptor pointer or a diagnostic table. */
struct hp1020_usb_runtime_retained {
    struct hp1020_tusb_cookie cookie;
    uint8_t *original;
    uint32_t requested;
    uint8_t live, cancel_requested, slot, reserved;
};
struct hp1020_usb_runtime_provider_type {
    struct hp1020_usb_runtime_retained ep0, bulk;
    struct hp1020_printer_reset_ticket recovery;
    uint32_t scope, read_cursor, scope_read_cursor, packet_sequence;
    uint32_t callback_depth, open_mask, stall_mask, steps;
    uint32_t source_offset, source_length;
    uint8_t initialized, device_valid, closing, finished;
    uint8_t callback_before[64];
    /* Original identity of the installed source image, copied before poison.
     * New arm scope invalidates device_valid without retagging this identity. */
    struct hp1020_tusb_cookie image_cookie;
    uint32_t image_slot;
};

/* Immutable separately supplied capabilities/facts; every boolean is1 for
 * this first schedule, independent of register reads/descriptor bits. The
 * existing program.dynamic_csr prerequisite is explicit even though request
 * delivery is raw SETUP, with an ordinary EP0 status and no CSR_DONE. */
struct hp1020_usb_runtime_supplied {
    struct hp1020_udc_program_init_facts program_initial;
    struct hp1020_udc_program_facts program;
    struct hp1020_udc_publish_facts publish;
    struct hp1020_udc_acquire_facts acquire;
    struct hp1020_udc_setup_capture_facts setup;
    struct hp1020_udc_ep0_publish_facts ep0_publish;
    struct hp1020_udc_ep0_completion_facts ep0_complete;
    uint8_t ep0_stalls_cleared;
    uint8_t receive_quiesced, output_quiesced, transport_reset;
};

/* Separate global objects; only the five explicit .runtime_* sections below
 * have fixed locations. Others use ordinary BSS, never a giant aggregate. */
extern struct hp1020_usb_document hp1020_usb_runtime_document;
extern struct hp1020_usb_document_memory hp1020_usb_runtime_memory;
extern volatile struct hp1020_usb_runtime_mailbox_type hp1020_usb_runtime_mailbox;
extern uint8_t hp1020_usb_runtime_sentinel[256];
extern struct hp1020_usb_runtime_witness_type hp1020_usb_runtime_witness;
extern struct hp1020_usb_printer hp1020_usb_runtime_printer;
extern struct hp1020_tusb_adapter hp1020_usb_runtime_adapter;
extern struct hp1020_udc_out hp1020_usb_runtime_out;
extern struct hp1020_udc_out_memory hp1020_usb_runtime_out_memory;
extern struct hp1020_udc_ep0 hp1020_usb_runtime_ep0;
extern struct hp1020_udc_ep0_memory hp1020_usb_runtime_ep0_memory;
extern struct hp1020_udc_setup hp1020_usb_runtime_setup;
extern uint8_t hp1020_usb_runtime_setup_memory[16];
extern struct hp1020_udc_program hp1020_usb_runtime_program;
extern struct hp1020_udc_publish hp1020_usb_runtime_publisher;
extern struct hp1020_udc_acquire hp1020_usb_runtime_acquirer;
extern struct hp1020_usb_runtime_provider_type hp1020_usb_runtime_provider;
extern const struct hp1020_usb_runtime_supplied hp1020_usb_runtime_supplied;
extern const uint8_t hp1020_usb_runtime_input[HP1020_USB_RUNTIME_INPUT_BYTES];
extern const uint8_t hp1020_usb_runtime_setup_record[16];

/* Only new execution entry. All transport/control/data actions use existing
 * production APIs and ordinary DCD callbacks. No second event/ownership API. */
void hp1020_usb_runtime_c(void);

/* Cross-file seam only. ram_init is the sole first-use component/TinyUSB
 * initializer. Other helpers never service, acquire/complete, pump, close,
 * restart, acknowledge recovery or invoke a callback on the caller's behalf.
 * The existing production APIs remain explicit orchestration calls.
 * Helpers return false on a retained mailbox failure; they cannot repair it. */
bool hp1020_usb_runtime_ram_init(void);
/* Scope0 before configuration, then1..13 before each actual arm. Consumes no
 * transfer identity; verifies prior read-script exhaustion before moving on. */
bool hp1020_usb_runtime_ram_scope(uint32_t packet_scope);
/* Install/copy the one immutable supplied SETUP16; caller still offers/dispatches. */
bool hp1020_usb_runtime_ram_setup_observation(struct hp1020_udc_setup_observation *);
/* Only after caller takes the real EP0 proposal. Synthetic descriptor write and
 * immutable snapshot with original retained cookie; caller still observes it. */
bool hp1020_usb_runtime_ram_ep0_observation(struct hp1020_udc_ep0_observation *);
/* Only exact retained EXPOSED original ownership. Install separate device images
 * and poison descriptor16/prefix64; no acquisition or completion is implied. */
bool hp1020_usb_runtime_ram_install_bulk(struct hp1020_tusb_cookie original,
    uint32_t input_offset, uint32_t actual_count);
/* After production observe/acquire returned OK. Require component FREE and
 * adapter PENDING with the same cookie before marking the provider nonlive;
 * retained identity remains intact. No adapter state or buffer is modified. */
bool hp1020_usb_runtime_ram_retired(struct hp1020_tusb_cookie original);
enum hp1020_usb_runtime_checkpoint {
    HP1020_USB_RUNTIME_NOTE_BEFORE_CLOSE = 1,
    HP1020_USB_RUNTIME_NOTE_BEFORE_FINAL_SERVICE = 2,
    HP1020_USB_RUNTIME_NOTE_BEFORE_FINISH = 3,
    HP1020_USB_RUNTIME_NOTE_FINAL = 4
};
/* Secondary read-only observations to mailbox; not independent stop markers. */
bool hp1020_usb_runtime_ram_note(enum hp1020_usb_runtime_checkpoint);
bool hp1020_usb_runtime_step(enum hp1020_usb_runtime_phase);
void hp1020_usb_runtime_fail(enum hp1020_usb_runtime_error, uint32_t detail);

/* Future compiler-layout witness: ordinary const rodata, no functions or
 * writable state. Header=[magic,version,word_count,object_count,field_count],
 * then object_count records[id,sizeof,alignof], then field_count records
 * [field_id,object_id,offsetof,width]. CONTRACT.md freezes the named fields.
 * Actual symbol addresses come independently from ELF; no address is in this
 * table. Private TinyUSB offsets require a SEPARATE source-derived table and
 * linked _usbd_dev size check; this public witness cannot name a private type. */
#define HP1020_USB_RUNTIME_LAYOUT_MAGIC UINT32_C(0x4850554c)
#define HP1020_USB_RUNTIME_LAYOUT_OBJECTS 16u
#define HP1020_USB_RUNTIME_LAYOUT_FIELDS 101u
#define HP1020_USB_RUNTIME_LAYOUT_WORDS 457u
enum hp1020_usb_runtime_layout_object {
    HP1020_USB_RUNTIME_LAYOUT_DOCUMENT = 1, HP1020_USB_RUNTIME_LAYOUT_MEMORY = 2,
    HP1020_USB_RUNTIME_LAYOUT_PRINTER = 3, HP1020_USB_RUNTIME_LAYOUT_ADAPTER = 4,
    HP1020_USB_RUNTIME_LAYOUT_OUT = 5, HP1020_USB_RUNTIME_LAYOUT_OUT_MEMORY = 6,
    HP1020_USB_RUNTIME_LAYOUT_EP0 = 7, HP1020_USB_RUNTIME_LAYOUT_EP0_MEMORY = 8,
    HP1020_USB_RUNTIME_LAYOUT_SETUP = 9, HP1020_USB_RUNTIME_LAYOUT_PROGRAM = 10,
    HP1020_USB_RUNTIME_LAYOUT_PUBLISHER = 11, HP1020_USB_RUNTIME_LAYOUT_ACQUIRER = 12,
    HP1020_USB_RUNTIME_LAYOUT_PROVIDER = 13, HP1020_USB_RUNTIME_LAYOUT_MAILBOX = 14,
    HP1020_USB_RUNTIME_LAYOUT_WITNESS = 15, HP1020_USB_RUNTIME_LAYOUT_SETUP_MEMORY = 16
};
extern const uint32_t hp1020_usb_runtime_layout[HP1020_USB_RUNTIME_LAYOUT_WORDS];

_Static_assert(sizeof(uint32_t) == 4, "32-bit diagnostic words");
_Static_assert(sizeof(struct hp1020_usb_runtime_io_row) == 16, "I/O row");
_Static_assert(sizeof(struct hp1020_usb_runtime_range_row) == 36, "range row");
_Static_assert(sizeof(struct hp1020_usb_runtime_bind_row) == 36, "bind row");
_Static_assert(sizeof(struct hp1020_usb_runtime_document_row) == 20, "document row");
_Static_assert(sizeof(struct hp1020_usb_runtime_device_images) == 144, "device images");
_Static_assert(sizeof(struct hp1020_usb_runtime_mailbox_type) == 1024, "mailbox");
_Static_assert(sizeof(struct hp1020_usb_runtime_witness_type) == 9216, "witness");
_Static_assert(sizeof(struct hp1020_usb_runtime_provider_type) <= 384, "provider budget");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,io) == 16, "trace offset");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,ranges) == 4960, "range offset");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,binds) == 8048, "bind offset");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,device) == 8720, "device offset");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,pixels) == 8864, "pixel offset");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,documents) == 9056, "event offset");
_Static_assert(offsetof(struct hp1020_usb_runtime_witness_type,reserved) == 9076, "reserved offset");
#if UINTPTR_MAX == UINT32_MAX
_Static_assert(sizeof(struct hp1020_usb_document) == 13512, "full target document");
_Static_assert(sizeof(struct hp1020_usb_document_memory) == 114704, "full target memory");
_Static_assert(sizeof(struct hp1020_usb_runtime_retained) == 32, "target retained owner");
_Static_assert(sizeof(struct hp1020_usb_runtime_provider_type) == 204, "target provider state");
#endif
#endif
