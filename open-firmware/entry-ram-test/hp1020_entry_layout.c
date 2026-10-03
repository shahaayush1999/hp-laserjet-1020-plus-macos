/* SPDX-License-Identifier: GPL-2.0-or-later */
/* UNEXECUTED compiler-layout witness: one ordinary const object, no functions,
 * writable storage, generated input, pointer values or runtime initializers.
 * Production member declarations are the only source of offsets and widths. */
#include "hp1020_entry_layout.h"
#include "hp1020_usb_document.h"
#include <limits.h>
#include <stddef.h>

_Static_assert(CHAR_BIT == 8 && sizeof(uint32_t) == 4,
    "layout witness requires eight-bit bytes and four-byte uint32_t");
_Static_assert(sizeof(void *) == 4 && sizeof(size_t) == 4 &&
    sizeof(unsigned long) == 4 && sizeof(int) == 4 &&
    sizeof(hp1020_usb_document_consumer) == 4,
    "layout witness is for the pinned target32 profile, not a host ABI");
_Static_assert(sizeof(enum hp1020_result) == 4 &&
    sizeof(enum hp1020_rx_result) == 4 &&
    sizeof(enum hp1020_image_result) == 4 &&
    sizeof(enum hp1020_ring_result) == 4,
    "layout witness requires the target profile without short enums");
_Static_assert(HP1020_ENTRY_LAYOUT_WORDS == 65,
    "layout witness schema changed");

#define STATE(member) \
    HP1020_ENTRY_LAYOUT_BASE_STATE, \
    (uint32_t)offsetof(struct hp1020_usb_document, member), \
    (uint32_t)sizeof(((struct hp1020_usb_document *)0)->member)
#define MEMORY(member) \
    HP1020_ENTRY_LAYOUT_BASE_MEMORY, \
    (uint32_t)offsetof(struct hp1020_usb_document_memory, member), \
    (uint32_t)sizeof(((struct hp1020_usb_document_memory *)0)->member)

/* No section attribute: this must remain ordinary rodata in the linked ELF.
 * used preserves the definition at compilation; if section garbage collection
 * is enabled, the integrator must additionally retain this symbol at link time. */
const uint32_t hp1020_entry_layout[HP1020_ENTRY_LAYOUT_WORDS]
    __attribute__((used)) = {
    HP1020_ENTRY_LAYOUT_VERSION,
    HP1020_ENTRY_LAYOUT_WORDS,
    HP1020_ENTRY_LAYOUT_FIELD_COUNT,
    (uint32_t)sizeof(struct hp1020_usb_document),
    (uint32_t)sizeof(struct hp1020_usb_document_memory),
    STATE(receive.generation),
    STATE(receive.issued),
    STATE(receive.consumed),
    STATE(receive.count),
    STATE(receive.stopped),
    STATE(receive.quiescent),
    STATE(finished),
    STATE(output.stream.parser.documents),
    STATE(output.stream.pages),
    STATE(output.pages_drained),
    STATE(output.documents_completed),
    STATE(output_quiescent),
    STATE(payload_error),
    STATE(feed_generation),
    STATE(receive.error),
    STATE(output.finished),
    STATE(output.error),
    MEMORY(receive.data),
    MEMORY(output.slots),
    MEMORY(output.stream)
};

#undef MEMORY
#undef STATE
