/* SPDX-License-Identifier: GPL-2.0-or-later
 * UNEXECUTED RAM-only entry workload. Startup owns CPU/stack/BSS setup.
 * The transport copies and immediate output completions below are supplied
 * software actions, not USB/DMA/cache/device or physical-page observations. */
#include "hp1020_entry_workload.h"
#include "hp1020_entry_input.h" /* Generated and frozen externally before build. */
#include <stddef.h>

#define ENTRY_OBJECT(name) __attribute__((section(name),aligned(16),used))
#define ENTRY_WORD(n) (hp1020_entry_mailbox.words[(n)])
#define ENTRY_SENTINEL_ROW \
    0x31,0x52,0x73,0x94,0xb5,0xd6,0xf7,0x18,0x39,0x5a,0x7b,0x9c,0xbd,0xde,0xff,0x20

struct hp1020_usb_document hp1020_entry_state ENTRY_OBJECT(".entry_state");
struct hp1020_usb_document_memory hp1020_entry_memory ENTRY_OBJECT(".entry_memory");
volatile struct hp1020_entry_mailbox_type hp1020_entry_mailbox ENTRY_OBJECT(".entry_mailbox");
uint8_t hp1020_entry_data[HP1020_ENTRY_DATA_BYTES] ENTRY_OBJECT(".entry_data") = {
    ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,
    ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,
    ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,
    ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW,ENTRY_SENTINEL_ROW
};

_Static_assert(sizeof(uint32_t)==4 && sizeof(uintptr_t)==4,"target32 ABI required");
_Static_assert(sizeof(hp1020_entry_state)==HP1020_ENTRY_STATE_BYTES,"unchanged document state size");
_Static_assert(sizeof(hp1020_entry_memory)==HP1020_ENTRY_MEMORY_BYTES,"unchanged full-capacity memory size");
_Static_assert(sizeof(hp1020_entry_mailbox)==HP1020_ENTRY_MAILBOX_BYTES,"fixed mailbox extent");
_Static_assert(offsetof(struct hp1020_entry_mailbox_type,pixels)==HP1020_ENTRY_PIXEL_OFFSET,"pixel offset");
_Static_assert(sizeof(hp1020_entry_data)==HP1020_ENTRY_DATA_BYTES,"file-backed sentinel extent");
_Static_assert(HP1020_ENTRY_INPUT_BYTES>0 && HP1020_ENTRY_INPUT_BYTES<=HP1020_ENTRY_INPUT_MAX_BYTES,"bounded input");
_Static_assert(sizeof(hp1020_entry_input)==HP1020_ENTRY_INPUT_BYTES,"fixed external input extent");
_Static_assert(HP1020_RX_SLOTS==4 && HP1020_RX_CAPACITY==1024,"full receive capacities retained");
_Static_assert(HP1020_IMAGE_RING_SLOTS==4 && HP1020_IMAGE_MAX_BAND_BYTES==8192,"full output capacities retained");

static uint32_t entry_hash(const volatile uint8_t *bytes,uint32_t length) {
    uint32_t result=UINT32_C(2166136261);
    for(uint32_t i=0;i<length;i++)result=(result^bytes[i])*UINT32_C(16777619);
    return result;
}

/* Character access is valid for every object representation. Every byte is a
 * volatile load, including unused mailbox bytes and uninitialized pointer
 * representations in the production state. No field dereference, initializer
 * or mailbox store happens until ALL three spans and the data sentinel pass. */
static void entry_scan_zero(const volatile uint8_t *bytes,uint32_t length,
    uint32_t *bad,uint32_t *first) {
    for(uint32_t i=0;i<length;i++)if(bytes[i]) {
        if(!*bad)*first=(uint32_t)(uintptr_t)(bytes+i);
        (*bad)++;
    }
}
static void entry_scan_data(uint32_t *bad,uint32_t *first) {
    const volatile uint8_t *bytes=hp1020_entry_data;
    for(uint32_t i=0;i<HP1020_ENTRY_DATA_BYTES;i++) {
        const uint8_t expected=(uint8_t)(0x31u+0x21u*(i&15u));
        if(bytes[i]!=expected) {
            if(!*bad)*first=(uint32_t)(uintptr_t)(bytes+i);
            (*bad)++;
        }
    }
}
static void entry_fail(enum hp1020_entry_error error,uint32_t detail) {
    if(!ENTRY_WORD(HP1020_ENTRY_W_ERROR)) {
        ENTRY_WORD(HP1020_ENTRY_W_ERROR)=(uint32_t)error;
        ENTRY_WORD(HP1020_ENTRY_W_ERROR_DETAIL)=detail;
    }
    ENTRY_WORD(HP1020_ENTRY_W_STATUS)=HP1020_ENTRY_FAIL;
}
static int entry_count(enum hp1020_entry_word word,uint32_t limit) {
    const uint32_t value=ENTRY_WORD(word);
    if(value>=limit) { entry_fail(HP1020_ENTRY_ERROR_LIMIT,(uint32_t)word);return 0; }
    ENTRY_WORD(word)=value+1;return 1;
}

static enum hp1020_result entry_output(const struct hp1020_page_plan *plan,
    struct hp1020_image_ring *ring,void *context) {
    if(ENTRY_WORD(HP1020_ENTRY_W_ERROR))return HP1020_ORDER;
    if(context!=&hp1020_entry_state || plan!=&hp1020_entry_state.output.plan ||
       ring!=&hp1020_entry_state.output.ring || ENTRY_WORD(HP1020_ENTRY_W_FINISH_CALLS)) {
        entry_fail(HP1020_ENTRY_ERROR_OUTPUT,1);return HP1020_ORDER;
    }
    if(!entry_count(HP1020_ENTRY_W_OUTPUT_CALLS,HP1020_IMAGE_RING_SLOTS))return HP1020_LIMIT;
    if(!ring->stride || ring->stride!=plan->stride || ring->rows!=plan->rows ||
       ring->stride>HP1020_ENTRY_PIXEL_BYTES || ring->rows>8 ||
       ring->storage!=hp1020_entry_memory.output.slots ||
       ring->slot_bytes>HP1020_IMAGE_MAX_BAND_BYTES) {
        entry_fail(HP1020_ENTRY_ERROR_OUTPUT,2);return HP1020_ORDER;
    }
    struct hp1020_ring_view view;
    enum hp1020_ring_result result=hp1020_image_ring_peek(ring,&view);
    ENTRY_WORD(HP1020_ENTRY_W_RING_RESULT)=(uint32_t)result;
    if(result!=HP1020_RING_OK) {
        entry_fail(HP1020_ENTRY_ERROR_OUTPUT,3);return HP1020_ORDER;
    }
    const uint32_t before=ENTRY_WORD(HP1020_ENTRY_W_PIXEL_BYTES);
    if(view.index>=HP1020_IMAGE_RING_SLOTS || !view.rows || view.final>1 ||
       view.first!=ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_ROWS) ||
       view.rows>HP1020_ENTRY_PIXEL_BYTES/ring->stride ||
       before>HP1020_ENTRY_PIXEL_BYTES ||
       view.rows*ring->stride>HP1020_ENTRY_PIXEL_BYTES-before ||
       view.pixels!=ring->storage+view.index*ring->slot_bytes) {
        entry_fail(HP1020_ENTRY_ERROR_OUTPUT,4);return HP1020_LIMIT;
    }
    const uint32_t bytes=view.rows*ring->stride;
    result=hp1020_image_ring_accept(ring,view.index);
    ENTRY_WORD(HP1020_ENTRY_W_RING_RESULT)=(uint32_t)result;
    if(result!=HP1020_RING_OK) {
        entry_fail(HP1020_ENTRY_ERROR_OUTPUT,5);return HP1020_ORDER;
    }
    if(!entry_count(HP1020_ENTRY_W_OUTPUT_ACCEPTS,HP1020_IMAGE_RING_SLOTS))return HP1020_LIMIT;
    /* Read the actual accepted slot before immediate software completion. No
     * expected pixel pattern or independently generated page is copied here. */
    for(uint32_t i=0;i<bytes;i++)hp1020_entry_mailbox.pixels[before+i]=view.pixels[i];
    ENTRY_WORD(HP1020_ENTRY_W_PIXEL_BYTES)=before+bytes;
    ENTRY_WORD(HP1020_ENTRY_W_PIXEL_FNV)=entry_hash(hp1020_entry_mailbox.pixels,before+bytes);
    ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_ROWS)=view.first+view.rows;
    ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_STRIDE)=ring->stride;
    ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_FINAL)=view.final;
    result=hp1020_image_ring_complete(ring,view.index);
    ENTRY_WORD(HP1020_ENTRY_W_RING_RESULT)=(uint32_t)result;
    if(result!=HP1020_RING_OK) {
        entry_fail(HP1020_ENTRY_ERROR_OUTPUT,6);return HP1020_ORDER;
    }
    if(!entry_count(HP1020_ENTRY_W_OUTPUT_COMPLETES,HP1020_IMAGE_RING_SLOTS))return HP1020_LIMIT;
    return HP1020_OK;
}

static enum hp1020_result entry_document(const struct hp1020_usb_document_event *event,
    void *context) {
    if(ENTRY_WORD(HP1020_ENTRY_W_ERROR))return HP1020_ORDER;
    if(context!=&hp1020_entry_state || !event || ENTRY_WORD(HP1020_ENTRY_W_FINISH_CALLS)) {
        entry_fail(HP1020_ENTRY_ERROR_DOCUMENT,1);return HP1020_ORDER;
    }
    /* A second notification fails before it can overwrite the original one. */
    if(!entry_count(HP1020_ENTRY_W_DOCUMENT_CALLS,1))return HP1020_LIMIT;
    ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_GENERATION)=event->generation;
    ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_ID)=event->document_id;
    ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_FIRST_PAGE)=event->first_page;
    ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_PAGES)=event->pages;
    if(event->generation!=1 || event->generation!=hp1020_entry_state.feed_generation ||
       event->document_id!=1 || event->first_page || event->pages!=1 ||
       ENTRY_WORD(HP1020_ENTRY_W_PIXEL_BYTES)!=HP1020_ENTRY_PIXEL_BYTES ||
       ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_ACCEPTS)!=ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_COMPLETES)) {
        ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_RESULT)=HP1020_ORDER;
        entry_fail(HP1020_ENTRY_ERROR_DOCUMENT,2);return HP1020_ORDER;
    }
    ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_RESULT)=HP1020_OK;
    return HP1020_OK;
}

static void entry_snapshot(void) {
    const struct hp1020_usb_receive *receive=&hp1020_entry_state.receive;
    const struct hp1020_image_output *output=&hp1020_entry_state.output;
    const struct hp1020_image_ring *ring=&output->ring;
    ENTRY_WORD(HP1020_ENTRY_W_PAYLOAD_RESULT)=(uint32_t)hp1020_entry_state.payload_error;
    ENTRY_WORD(HP1020_ENTRY_W_GENERATION)=receive->generation;
    ENTRY_WORD(HP1020_ENTRY_W_ISSUED)=receive->issued;
    ENTRY_WORD(HP1020_ENTRY_W_CONSUMED)=receive->consumed;
    ENTRY_WORD(HP1020_ENTRY_W_RX_COUNT)=receive->count;
    ENTRY_WORD(HP1020_ENTRY_W_STOPPED)=receive->stopped;
    ENTRY_WORD(HP1020_ENTRY_W_QUIESCENT)=receive->quiescent;
    ENTRY_WORD(HP1020_ENTRY_W_FINISHED)=hp1020_entry_state.finished;
    ENTRY_WORD(HP1020_ENTRY_W_PARSER_DOCUMENTS)=output->stream.parser.documents;
    ENTRY_WORD(HP1020_ENTRY_W_STREAM_PAGES)=output->stream.pages;
    ENTRY_WORD(HP1020_ENTRY_W_PAGES_DRAINED)=output->pages_drained;
    ENTRY_WORD(HP1020_ENTRY_W_DOCUMENTS_COMPLETED)=output->documents_completed;
    ENTRY_WORD(HP1020_ENTRY_W_COPIED_ROWS)=ring->copied_rows;
    ENTRY_WORD(HP1020_ENTRY_W_ACCEPTED_ROWS)=ring->accepted_rows;
    ENTRY_WORD(HP1020_ENTRY_W_COMPLETED_ROWS)=ring->completed_rows;
    uint32_t nonfree=0;
    for(uint32_t i=0;i<HP1020_IMAGE_RING_SLOTS;i++)nonfree+=(ring->slots[i].state!=0);
    ENTRY_WORD(HP1020_ENTRY_W_NONFREE_OUTPUT_SLOTS)=nonfree;
    ENTRY_WORD(HP1020_ENTRY_W_RX_ERROR)=(uint32_t)receive->error;
    ENTRY_WORD(HP1020_ENTRY_W_IMAGE_ERROR)=(uint32_t)output->error;
    ENTRY_WORD(HP1020_ENTRY_W_RING_ERROR)=(uint32_t)ring->error;
    ENTRY_WORD(HP1020_ENTRY_W_RECEIVE_FNV)=entry_hash(
        (const volatile uint8_t *)hp1020_entry_memory.receive.data,sizeof(hp1020_entry_memory.receive.data));
    ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_FNV)=entry_hash(
        hp1020_entry_memory.output.slots,sizeof(hp1020_entry_memory.output.slots));
    ENTRY_WORD(HP1020_ENTRY_W_STATE_BYTES)=sizeof(hp1020_entry_state);
    ENTRY_WORD(HP1020_ENTRY_W_MEMORY_BYTES)=sizeof(hp1020_entry_memory);
}

void hp1020_entry_c(void) {
    uint32_t zero_bad=0,zero_first=0,data_bad=0,data_first=0;
    entry_scan_zero((const volatile uint8_t *)&hp1020_entry_state,sizeof(hp1020_entry_state),&zero_bad,&zero_first);
    entry_scan_zero((const volatile uint8_t *)&hp1020_entry_mailbox,sizeof(hp1020_entry_mailbox),&zero_bad,&zero_first);
    entry_scan_zero((const volatile uint8_t *)&hp1020_entry_memory,sizeof(hp1020_entry_memory),&zero_bad,&zero_first);
    entry_scan_data(&data_bad,&data_first);
    /* Compiler-only barrier: no emitted cache, device or architecture operation.
     * The externally checked pre-C stop separately verifies startup clearing. */
    __asm__ __volatile__("" ::: "memory");
    ENTRY_WORD(HP1020_ENTRY_W_MAGIC)=HP1020_ENTRY_MAILBOX_MAGIC;
    ENTRY_WORD(HP1020_ENTRY_W_ABI)=HP1020_ENTRY_ABI_VERSION;
    ENTRY_WORD(HP1020_ENTRY_W_STATUS)=HP1020_ENTRY_RUNNING;
    ENTRY_WORD(HP1020_ENTRY_W_ERROR)=HP1020_ENTRY_ERROR_NONE;
    ENTRY_WORD(HP1020_ENTRY_W_STAGE)=HP1020_ENTRY_STAGE_SCAN;
    ENTRY_WORD(HP1020_ENTRY_W_RX_RESULT)=0;
    ENTRY_WORD(HP1020_ENTRY_W_PAYLOAD_RESULT)=0;
    ENTRY_WORD(HP1020_ENTRY_W_RING_RESULT)=0;
    ENTRY_WORD(HP1020_ENTRY_W_ZERO_BAD)=zero_bad;
    ENTRY_WORD(HP1020_ENTRY_W_ZERO_FIRST)=zero_first;
    ENTRY_WORD(HP1020_ENTRY_W_DATA_BAD)=data_bad;
    ENTRY_WORD(HP1020_ENTRY_W_DATA_FIRST)=data_first;
    ENTRY_WORD(HP1020_ENTRY_W_ZERO_SCANNED)=sizeof(hp1020_entry_state)+sizeof(hp1020_entry_mailbox)+sizeof(hp1020_entry_memory);
    ENTRY_WORD(HP1020_ENTRY_W_DATA_SCANNED)=sizeof(hp1020_entry_data);
    ENTRY_WORD(HP1020_ENTRY_W_ERROR_DETAIL)=0;
    if(zero_bad || data_bad) {
        entry_fail(zero_bad?HP1020_ENTRY_ERROR_ZERO:HP1020_ENTRY_ERROR_DATA,
                   zero_bad?zero_first:data_first);
        return;
    }
    ENTRY_WORD(HP1020_ENTRY_W_INPUT_BYTES)=sizeof(hp1020_entry_input);
    ENTRY_WORD(HP1020_ENTRY_W_INPUT_FNV)=entry_hash(hp1020_entry_input,sizeof(hp1020_entry_input));
    ENTRY_WORD(HP1020_ENTRY_W_PIXEL_FNV)=UINT32_C(2166136261);
    if(sizeof(hp1020_entry_input)!=352u) { entry_fail(HP1020_ENTRY_ERROR_INPUT,sizeof(hp1020_entry_input));return; }

    ENTRY_WORD(HP1020_ENTRY_W_STAGE)=HP1020_ENTRY_STAGE_INIT;
    enum hp1020_rx_result result=hp1020_usb_document_init_documents(&hp1020_entry_state,
        &hp1020_entry_memory,entry_output,&hp1020_entry_state,entry_document,&hp1020_entry_state);
    ENTRY_WORD(HP1020_ENTRY_W_RX_RESULT)=(uint32_t)result;
    if(result!=HP1020_RX_OK) { entry_fail(HP1020_ENTRY_ERROR_INIT,(uint32_t)result);goto done; }
    ENTRY_WORD(HP1020_ENTRY_W_STAGE)=HP1020_ENTRY_STAGE_FEED;
    const uint32_t packets=(HP1020_ENTRY_INPUT_BYTES+HP1020_ENTRY_FRAGMENT_BYTES-1)/HP1020_ENTRY_FRAGMENT_BYTES;
    uint32_t offset=0;
    for(uint32_t packet=0;packet<packets;packet++) {
        struct hp1020_rx_ticket ticket;
        uint8_t *buffer=NULL;
        const uint32_t remaining=HP1020_ENTRY_INPUT_BYTES-offset;
        const uint32_t length=remaining<HP1020_ENTRY_FRAGMENT_BYTES?remaining:HP1020_ENTRY_FRAGMENT_BYTES;
        if(!entry_count(HP1020_ENTRY_W_RESERVE_CALLS,HP1020_ENTRY_INPUT_MAX_BYTES/HP1020_ENTRY_FRAGMENT_BYTES))goto done;
        result=hp1020_usb_receive_reserve(&hp1020_entry_state.receive,HP1020_ENTRY_FRAGMENT_BYTES,&ticket,&buffer);
        ENTRY_WORD(HP1020_ENTRY_W_RX_RESULT)=(uint32_t)result;
        if(result!=HP1020_RX_OK) { entry_fail(HP1020_ENTRY_ERROR_RESERVE,(uint32_t)result);goto done; }
        ENTRY_WORD(HP1020_ENTRY_W_TICKET_GENERATION)=ticket.generation;
        ENTRY_WORD(HP1020_ENTRY_W_TICKET_SEQUENCE)=ticket.sequence;
        ENTRY_WORD(HP1020_ENTRY_W_LAST_FRAGMENT)=length;
        if(ticket.generation!=1 || ticket.sequence!=packet+1 ||
           buffer!=hp1020_entry_memory.receive.data[packet%HP1020_RX_SLOTS] || !length) {
            entry_fail(HP1020_ENTRY_ERROR_TICKET,packet);goto done;
        }
        if(!entry_count(HP1020_ENTRY_W_COPY_CALLS,HP1020_ENTRY_INPUT_MAX_BYTES/HP1020_ENTRY_FRAGMENT_BYTES))goto done;
        for(uint32_t i=0;i<length;i++)buffer[i]=hp1020_entry_input[offset+i];
        if(!entry_count(HP1020_ENTRY_W_COMPLETE_CALLS,HP1020_ENTRY_INPUT_MAX_BYTES/HP1020_ENTRY_FRAGMENT_BYTES))goto done;
        result=hp1020_usb_receive_complete_data(&hp1020_entry_state.receive,ticket,length);
        ENTRY_WORD(HP1020_ENTRY_W_RX_RESULT)=(uint32_t)result;
        if(result!=HP1020_RX_OK) { entry_fail(HP1020_ENTRY_ERROR_COMPLETE,(uint32_t)result);goto done; }
        if(!entry_count(HP1020_ENTRY_W_PUMP_CALLS,HP1020_ENTRY_INPUT_MAX_BYTES/HP1020_ENTRY_FRAGMENT_BYTES))goto done;
        result=hp1020_usb_document_pump(&hp1020_entry_state);
        ENTRY_WORD(HP1020_ENTRY_W_RX_RESULT)=(uint32_t)result;
        if(result!=HP1020_RX_OK) { entry_fail(HP1020_ENTRY_ERROR_PUMP,(uint32_t)result);goto done; }
        offset+=length;ENTRY_WORD(HP1020_ENTRY_W_FED_BYTES)=offset;
        if(hp1020_entry_state.receive.generation!=1 || hp1020_entry_state.receive.count ||
           hp1020_entry_state.receive.consumed!=packet+1) {
            entry_fail(HP1020_ENTRY_ERROR_TICKET,packet);goto done;
        }
    }
    /* The locally finite sender has now closed admission. END_DOC has already
     * notified during pumping; a short last fragment is never treated as EOF. */
    if(offset!=sizeof(hp1020_entry_input) || ENTRY_WORD(HP1020_ENTRY_W_DOCUMENT_CALLS)!=1 ||
       ENTRY_WORD(HP1020_ENTRY_W_PIXEL_BYTES)!=HP1020_ENTRY_PIXEL_BYTES ||
       hp1020_entry_state.output.documents_completed!=1 || hp1020_entry_state.output.pages_drained!=1) {
        entry_fail(HP1020_ENTRY_ERROR_FINAL,1);goto done;
    }
    ENTRY_WORD(HP1020_ENTRY_W_STAGE)=HP1020_ENTRY_STAGE_FINISH;
    if(!entry_count(HP1020_ENTRY_W_FINISH_CALLS,1))goto done;
    result=hp1020_usb_document_finish(&hp1020_entry_state);
    ENTRY_WORD(HP1020_ENTRY_W_RX_RESULT)=(uint32_t)result;
    if(result!=HP1020_RX_OK) { entry_fail(HP1020_ENTRY_ERROR_FINISH,(uint32_t)result);goto done; }
    if(hp1020_entry_state.receive.generation!=1 || hp1020_entry_state.receive.issued!=packets ||
       hp1020_entry_state.receive.consumed!=packets || hp1020_entry_state.receive.count ||
       !hp1020_entry_state.receive.stopped || hp1020_entry_state.receive.quiescent ||
       !hp1020_entry_state.finished || hp1020_entry_state.output_quiescent ||
       hp1020_entry_state.payload_error || hp1020_entry_state.receive.error ||
       hp1020_entry_state.output.stream.parser.documents!=1 || hp1020_entry_state.output.stream.pages!=1 ||
       hp1020_entry_state.output.pages_drained!=1 || hp1020_entry_state.output.documents_completed!=1 ||
       !hp1020_entry_state.output.finished || !hp1020_image_ring_drained(&hp1020_entry_state.output.ring) ||
       ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_CALLS)!=1 || ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_ACCEPTS)!=1 ||
       ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_COMPLETES)!=1 || ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_ROWS)!=8 ||
       ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_STRIDE)!=4 || ENTRY_WORD(HP1020_ENTRY_W_OUTPUT_FINAL)!=1) {
        entry_fail(HP1020_ENTRY_ERROR_FINAL,2);
    }
done:
    entry_snapshot();
    data_bad=0;data_first=0;entry_scan_data(&data_bad,&data_first);
    ENTRY_WORD(HP1020_ENTRY_W_FINAL_DATA_BAD)=data_bad;
    ENTRY_WORD(HP1020_ENTRY_W_FINAL_DATA_FIRST)=data_first;
    if(data_bad)entry_fail(HP1020_ENTRY_ERROR_DATA_FINAL,data_first);
    if(!ENTRY_WORD(HP1020_ENTRY_W_ERROR)) {
        ENTRY_WORD(HP1020_ENTRY_W_STAGE)=HP1020_ENTRY_STAGE_DONE;
        ENTRY_WORD(HP1020_ENTRY_W_STATUS)=HP1020_ENTRY_PASS;
    }
}
