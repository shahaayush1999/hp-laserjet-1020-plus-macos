/* SPDX-License-Identifier: GPL-2.0-or-later
 * Experimental publication fixture. Recording hooks only; no MMIO/cache
 * implementation, DMA simulation, hardware settlement or USB contact.
 */
#include "hp1020_udc_publish.h"

static uint32_t publish_fixture_init(uint32_t);
static uint32_t publish_fixture_service(void);
static uint32_t publish_fixture_progress(void);
static bool publish_fixture_submission_allowed(void);
static bool publish_fixture_program_allowed(void);
static uint32_t publish_fixture_arm_out(void);
static bool publish_fixture_bulk_xfer(uint8_t,uint8_t,uint8_t *,uint16_t,bool);
static void publish_fixture_check(void);
static void publish_fixture_snapshot(void);
static uint32_t publish_fixture_step(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);

#define HP1020_COMPOSED_PUBLISH 1
#define HP1020_FIXTURE_ADAPTER_ARM_OUT(a) publish_fixture_arm_out()
#include "udc-program-test/fixture.c"

uint32_t hp1020_publish_fixture_stats[64];
static struct hp1020_udc_publish publisher;
static struct {
    uint32_t result, rx_calls, descriptor_calls, checked_ranges, violations;
    uint32_t callbacks, cleanups, cleanup_count_before, cleanup_count_after;
    uint32_t duplicate_checked;
    uint32_t direct_calls, direct_unchanged, callback_result, last_slot;
    uint32_t query_result, callback_slot;
    struct hp1020_tusb_cookie cache_owner;
    struct hp1020_udc_publish_failure query;
    uint8_t facts[7], callback_before[64], initialized, in_callback;
} publish_state;

static void publish_violation(void) {
    publish_state.violations++; state.violations++;
}
static void publish_fixture_check(void) {
    if (!publish_state.initialized) return;
    if (publish_state.checked_ranges != publish_state.rx_calls + publish_state.descriptor_calls)
        publish_violation();
    if (!publish_state.in_callback && publish_state.duplicate_checked != publish_state.callbacks)
        publish_violation();
}
static struct hp1020_udc_publish_facts publish_facts(void) {
    const uint8_t *f=publish_state.facts;
    const struct hp1020_udc_publish_facts facts={f[0],f[1],f[2],f[3],f[4],f[5],f[6]};
    return facts;
}

static enum hp1020_udc_program_io_result publish_cache_record(void *context,
    uint32_t kind, struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_span span) {
    if (kind == 4) publish_state.rx_calls++; else publish_state.descriptor_calls++;
    /* The witness comes from the actual adapter owner at hook entry, never
     * from the publication failure object or the supplied hook cookie. */
    const struct hp1020_tusb_owner owner=adapter.owners[2];
    publish_state.cache_owner=owner.cookie;
    const uint32_t slot=publish_state.callback_slot;
    bool valid=context == &publish_state && publish_state.in_callback && slot < HP1020_RX_SLOTS &&
        owner.state == HP1020_TUSB_OWNER_DCD && owner.cookie.id && owner.cookie.endpoint == 1 &&
        owner.length == 64 && same_cookie(owner.cookie,cookie);
    if (valid) {
        uint8_t expected[16];
        const uint32_t dma=COMPOSED_RX_DMA + COMPOSED_RX_STEP*slot;
        composed_put32(expected,UINT32_C(0x08000000)); composed_put32(expected+4,0);
        composed_put32(expected+8,dma); composed_put32(expected+12,0);
        valid=owner.buffer == memory.data.receive.data[slot] &&
            !memcmp(owner.buffer,publish_state.callback_before,64) &&
            !memcmp(composed_out_memory.descriptor,expected,16);
        if (kind == 4) valid=valid && span.cpu == memory.data.receive.data[slot] &&
            span.dma == dma && span.bytes == 64;
        else valid=valid && kind == 5 && span.cpu == composed_out_memory.descriptor &&
            span.dma == COMPOSED_OUT_DMA && span.bytes == 16;
    }
    uint32_t r=HP1020_UDC_PROGRAM_IO_OK;
    if (valid) publish_state.checked_ranges++;
    else { publish_violation(); r=HP1020_UDC_PROGRAM_IO_UNKNOWN; }
    r=program_injected_result(kind,r);
    /* These hooks record intent only. They do not mutate payload/descriptor,
     * set visibility bits, release ownership, or perform an actual cache op. */
    return (enum hp1020_udc_program_io_result)program_record(kind,span.dma,span.bytes,r);
}
static enum hp1020_udc_program_io_result publish_rx_cache(void *context,
    struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_span span) {
    return publish_cache_record(context,4,cookie,span);
}
static enum hp1020_udc_program_io_result publish_descriptor_cache(void *context,
    struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_span span) {
    return publish_cache_record(context,5,cookie,span);
}

static uint32_t publish_fixture_init(uint32_t fill) {
    (void)fill;
    memset(&publish_state,0,sizeof(publish_state));
    memset(&publisher,0,sizeof(publisher));
    memset(&publish_state.query,0xa7,sizeof(publish_state.query));
    memset(publish_state.facts,1,sizeof(publish_state.facts));
    publish_state.query_result=publish_state.callback_result=UINT32_MAX;
    publish_state.last_slot=publish_state.callback_slot=UINT32_MAX;
    publish_state.cleanup_count_before=publish_state.cleanup_count_after=UINT32_MAX;
    publish_state.direct_unchanged=1;
    publish_state.initialized=1;
    const struct hp1020_udc_publish_mapping mapping={{COMPOSED_RX_DMA,
        COMPOSED_RX_DMA+COMPOSED_RX_STEP, COMPOSED_RX_DMA+2*COMPOSED_RX_STEP,
        COMPOSED_RX_DMA+3*COMPOSED_RX_STEP}};
    const struct hp1020_udc_publish_cache cache={publish_rx_cache,publish_descriptor_cache,&publish_state};
    publish_state.result=(uint32_t)hp1020_udc_publish_init(&publisher,&program,&composed_out,&mapping,&cache);
    return publish_state.result;
}
static uint32_t publish_fixture_service(void) {
    publish_state.result=(uint32_t)hp1020_udc_publish_service(&publisher);
    return publish_state.result;
}
static uint32_t publish_fixture_progress(void) { return hp1020_udc_publish_progress(&publisher); }
static bool publish_fixture_submission_allowed(void) {
    return hp1020_udc_publish_submission_allowed(&publisher);
}
static bool publish_fixture_program_allowed(void) {
    /* Keep complete_selection's own SERVICE-only admission. This additional
     * barrier cannot be used to evade a retained publication failure. */
    return publisher.initialized && !publisher.failed && !publisher.busy &&
        !publisher.arming && !publisher.servicing;
}
static uint32_t publish_fixture_arm_out(void) {
    publish_state.result=(uint32_t)hp1020_udc_publish_arm_out(&publisher,publish_facts());
    return publish_state.result;
}

static void publish_duplicate_probe(uint8_t rhport,uint8_t endpoint,uint8_t *buffer,uint16_t length) {
    /* The real callback is still inside arm_out. Probe the consumed one-shot
     * window immediately after its first helper returns, including a faulted
     * first helper, before ledger bookkeeping or the adapter can unwind. */
    if (!publish_state.in_callback || !publisher.arming || publisher.window ||
        publisher.busy || publisher.servicing || !adapter.busy ||
        !adapter.stack_active || !adapter.prepared) {
        publish_violation(); return;
    }
    struct hp1020_tusb_cookie duplicate; memset(&duplicate,0xa7,sizeof(duplicate));
    uint8_t cookie_before[sizeof(duplicate)], adapter_before[sizeof(adapter)];
    uint8_t receive_before[sizeof(document.receive)], descriptor_before[16];
    uint8_t out_before[sizeof(composed_out)], publisher_before[sizeof(publisher)];
    uint8_t program_before[sizeof(program)], io_before[sizeof(program_state)];
    uint8_t fixture_before[sizeof(state)], publish_before[sizeof(publish_state)];
    memcpy(cookie_before,&duplicate,sizeof(cookie_before));
    memcpy(adapter_before,&adapter,sizeof(adapter_before));
    memcpy(receive_before,&document.receive,sizeof(receive_before));
    memcpy(descriptor_before,composed_out_memory.descriptor,sizeof(descriptor_before));
    memcpy(out_before,&composed_out,sizeof(out_before));
    memcpy(publisher_before,&publisher,sizeof(publisher_before));
    memcpy(program_before,&program,sizeof(program_before));
    memcpy(io_before,&program_state,sizeof(io_before));
    memcpy(fixture_before,&state,sizeof(fixture_before));
    memcpy(publish_before,&publish_state,sizeof(publish_before));
    const uint32_t result=(uint32_t)hp1020_udc_publish_prepare_and_publish(&publisher,
        rhport,endpoint,buffer,length,&duplicate);
    /* Whole local metadata snapshots include the original owner and failure,
     * all cache/register counters and injection state, and forward/wire/page/
     * document counters. Do not increment the public out-of-window probe ABI. */
    if (result != HP1020_UDC_PUBLISH_INVALID ||
        memcmp(cookie_before,&duplicate,sizeof(cookie_before)) ||
        memcmp(adapter_before,&adapter,sizeof(adapter_before)) ||
        memcmp(receive_before,&document.receive,sizeof(receive_before)) ||
        memcmp(descriptor_before,composed_out_memory.descriptor,sizeof(descriptor_before)) ||
        memcmp(out_before,&composed_out,sizeof(out_before)) ||
        memcmp(publisher_before,&publisher,sizeof(publisher_before)) ||
        memcmp(program_before,&program,sizeof(program_before)) ||
        memcmp(io_before,&program_state,sizeof(io_before)) ||
        memcmp(fixture_before,&state,sizeof(fixture_before)) ||
        memcmp(publish_before,&publish_state,sizeof(publish_before)))
        publish_violation();
    else publish_state.duplicate_checked++;
}

static bool publish_fixture_bulk_xfer(uint8_t rhport,uint8_t endpoint,uint8_t *buffer,
    uint16_t length,bool in_isr) {
    (void)in_isr;
    composed_check();
    publish_state.callbacks++;
    if (rhport || endpoint != 1 || !buffer || length != 64 || packets[2].live ||
        !(state.open_mask & endpoint_bit(endpoint)) || publish_state.in_callback) {
        publish_violation(); return false;
    }
    uint32_t slot=UINT32_MAX;
    for (uint32_t i=0;i<HP1020_RX_SLOTS;i++) if (buffer == memory.data.receive.data[i]) slot=i;
    if (slot == UINT32_MAX) { publish_violation(); return false; }
    publish_state.callback_slot=slot;
    memcpy(publish_state.callback_before,buffer,64);
    struct hp1020_tusb_cookie cookie={0};
    publish_state.in_callback=1;
    const uint32_t r=(uint32_t)hp1020_udc_publish_prepare_and_publish(&publisher,
        rhport,endpoint,buffer,length,&cookie);
    publish_duplicate_probe(rhport,endpoint,buffer,length);
    publish_state.in_callback=0;
    publish_state.callback_result=r;
    publish_state.result=r;
    composed_out_state.result=r;
    /* Detect binding from the actual adapter owner, not helper success. A
     * post-bind cache/write failure must still enter the cancellation ledger. */
    const struct hp1020_tusb_owner owner=adapter.owners[2];
    if (owner.state == HP1020_TUSB_OWNER_DCD) {
        const uint32_t dma=COMPOSED_RX_DMA + COMPOSED_RX_STEP*slot;
        if (!same_cookie(cookie,owner.cookie) || !owner.cookie.id || owner.cookie.endpoint != endpoint ||
            owner.buffer != buffer || owner.length != length ||
            !same_cookie(composed_out.cookie,owner.cookie) ||
            composed_out.buffer.cpu != buffer || composed_out.buffer.dma != dma ||
            composed_out.buffer.bytes != 64 || composed_out.phase == HP1020_UDC_OUT_FREE)
            publish_violation();
        composed_out_state.last_slot=slot; publish_state.last_slot=slot;
        composed_put32(composed_out_shadow,UINT32_C(0x08000000));
        composed_put32(composed_out_shadow+4,0); composed_put32(composed_out_shadow+8,dma);
        composed_put32(composed_out_shadow+12,0); composed_out_state.preparations++;
        struct packet *p=&packets[2];
        p->cookie=owner.cookie; p->buffer=buffer; p->length=length;
        p->live=1; p->cancel_requested=0;
        memcpy(p->shadow,publish_state.callback_before,64);
        state.submissions++; state.last_id=owner.cookie.id; state.last_ep=endpoint; state.last_length=length;
        if (owner.cookie.id && owner.cookie.id < 4096) history[owner.cookie.id]=owner.cookie;
        else publish_violation();
        if (composed_out.phase == HP1020_UDC_OUT_EXPOSED) {
            /* Independent proposal-equivalent diagnostics. They reflect actual
             * conservative exposure, including failed subsequent register work,
             * and are built from the bound input span, not component output. */
            composed_publication.cookie=owner.cookie;
            composed_publication.descriptor_cpu=composed_out_memory.descriptor;
            composed_publication.buffer_cpu=buffer;
            composed_publication.descriptor_dma=COMPOSED_OUT_DMA;
            composed_publication.buffer_dma=dma; composed_publication.capacity=64;
            composed_publication.endpoint=1;
            memcpy(composed_published_bytes,composed_out_shadow,16);
            composed_out_state.publications++;
        }
#ifdef HP1020_COMPOSED_ACQUIRE
        /* Actual original binding exists, but the initiating adapter/TinyUSB
         * callback has not unwound. Acquisition must refuse without hooks. */
        acquire_fixture_callback_probe(owner.cookie);
#endif
    } else if (r == HP1020_UDC_PUBLISH_OK || cookie.id ||
        composed_out.phase != HP1020_UDC_OUT_FREE) publish_violation();
    composed_check();
    return r == HP1020_UDC_PUBLISH_OK;
}

static void publish_failure_words(uint32_t *out,const struct hp1020_udc_publish_failure *f) {
    ep0_cookie_words(out,f->cookie);
    out[5]=f->prefix; out[6]=f->offset; out[7]=f->attempted_value;
    out[8]=f->dma; out[9]=f->bytes; out[10]=f->operation; out[11]=f->io_result;
    out[12]=f->exposed; out[13]=f->out_result;
}
static uint32_t publish_query_digest(void) {
    uint32_t words[14]; uint8_t bytes[56];
    publish_failure_words(words,&publish_state.query);
    for (uint32_t i=0;i<14;i++) composed_put32(bytes+4*i,words[i]);
    return fnv(bytes,sizeof(bytes));
}
static uint32_t publish_fixture_step(uint32_t op,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    uint32_t r=HP1020_UDC_PUBLISH_INVALID;
    if (op == 130 && !a && !b && !c && !d) {
        memcpy(publish_state.facts,hp1020_bulk_fixture_input,7);
        r=HP1020_UDC_PUBLISH_OK;
    } else if (op == 131 && (a == 4 || a == 5) && b > program_state.trace_count &&
        b <= PROGRAM_TRACE_CAPACITY && (c == 1 || c == 2) && !d) {
        if (program_state.injection_armed) r=HP1020_UDC_PUBLISH_WAIT;
        else {
            program_state.injection_kind=a; program_state.injection_ordinal=b;
            program_state.injection_result=c; program_state.injection_armed=1;
            r=HP1020_UDC_PUBLISH_OK;
        }
    } else if (op == 132 && !a && !b && !c && !d) {
        uint8_t before[sizeof(publish_state.query)]; memcpy(before,&publish_state.query,sizeof(before));
        r=(uint32_t)hp1020_udc_publish_pending_cleanup(&publisher,&publish_state.query);
        if (r != HP1020_UDC_PUBLISH_OK && memcmp(before,&publish_state.query,sizeof(before)))
            publish_violation();
        publish_state.query_result=r;
    } else if (op == 133 && b <= 5 && c <= 255 && !d) {
        struct hp1020_tusb_cookie cookie;
        if (ep0_history(a,&cookie)) {
            cookie=ep0_mutate(cookie,b);
            uint8_t receive_before[sizeof(document.receive)];
            memcpy(receive_before,&document.receive,sizeof(receive_before));
            const uint32_t count_before=document.receive.count;
            const uint8_t reset_active=printer.reset_active, reset_parts=printer.reset_parts;
            const uint8_t output_quiescent=document.output_quiescent;
            uint8_t reset_before[sizeof(printer.reset)];
            memcpy(reset_before,&printer.reset,sizeof(reset_before));
            const uint32_t trace=program_state.trace_count;
            r=(uint32_t)hp1020_udc_publish_ack_cleanup(&publisher,cookie,(uint8_t)c);
            /* Cleanup cannot erase the deliberately retained old reservation or
             * create any of the three separately acknowledged reset promises. */
            if (memcmp(receive_before,&document.receive,sizeof(receive_before)) ||
                reset_active != printer.reset_active || reset_parts != printer.reset_parts ||
                output_quiescent != document.output_quiescent ||
                memcmp(reset_before,&printer.reset,sizeof(reset_before)) ||
                trace != program_state.trace_count) publish_violation();
            if (r == HP1020_UDC_PUBLISH_OK) {
                if (c != 1 || owned_mask() || adapter.owners[0].state || adapter.owners[1].state ||
                    adapter.owners[2].state || adapter.prepared || adapter.delivering_live ||
                    adapter.response_owned || composed_out.phase != HP1020_UDC_OUT_FREE ||
                    !document.receive.stopped || tud_mounted() || !adapter.fenced)
                    publish_violation();
                publish_state.cleanups++;
                publish_state.cleanup_count_before=count_before;
                publish_state.cleanup_count_after=document.receive.count;
            }
        }
    } else if (op == 134 && a <= 255 && b <= 255 && c < HP1020_RX_SLOTS && d <= UINT16_MAX) {
        struct hp1020_tusb_cookie cookie; memset(&cookie,0xa7,sizeof(cookie));
        uint8_t before[sizeof(cookie)]; memcpy(before,&cookie,sizeof(before));
        uint8_t owner_before[sizeof(adapter.owners)], receive_before[sizeof(document.receive)];
        memcpy(owner_before,adapter.owners,sizeof(owner_before));
        memcpy(receive_before,&document.receive,sizeof(receive_before));
        const uint32_t trace_before=program_state.trace_count;
        publish_state.direct_calls++;
        r=(uint32_t)hp1020_udc_publish_prepare_and_publish(&publisher,(uint8_t)a,(uint8_t)b,
            memory.data.receive.data[c],(uint16_t)d,&cookie);
        publish_state.direct_unchanged=!memcmp(before,&cookie,sizeof(before));
        if (r == HP1020_UDC_PUBLISH_OK || !publish_state.direct_unchanged ||
            trace_before != program_state.trace_count ||
            memcmp(owner_before,adapter.owners,sizeof(owner_before)) ||
            memcmp(receive_before,&document.receive,sizeof(receive_before))) publish_violation();
    }
    publish_state.result=r;
    return r;
}
static void publish_fixture_snapshot(void) {
    uint32_t *o=hp1020_publish_fixture_stats;
    memset(o,0,sizeof(hp1020_publish_fixture_stats));
    o[0]=publish_state.result; o[1]=publisher.initialized; o[2]=publisher.busy;
    o[3]=publisher.arming; o[4]=publisher.window; o[5]=publisher.servicing; o[6]=publisher.failed;
    o[7]=hp1020_udc_publish_progress(&publisher); o[8]=publisher.prefix;
    o[9]=publisher.last_adapter_result; o[10]=publisher.last_program_result; o[11]=publisher.last_out_result;
    o[12]=publisher.saved_devctl; o[13]=publisher.saved_outctl;
    o[14]=publisher.arm_control_epoch; o[15]=publisher.arm_transport_epoch;
    o[16]=publisher.arm_generation; o[17]=publisher.arm_ingress_sequence;
    o[18]=publisher.preflight.offset; o[19]=publisher.preflight.value;
    o[20]=publisher.preflight.io_result; o[21]=publisher.preflight.refused;
    publish_failure_words(o+22,&publisher.failure);
    for (uint32_t i=0;i<7;i++) o[36+i]=publish_state.facts[i];
    o[43]=publish_state.query_result; o[44]=publish_query_digest();
    ep0_cookie_words(o+45,publish_state.cache_owner);
    o[50]=publish_state.rx_calls; o[51]=publish_state.descriptor_calls;
    o[52]=publish_state.checked_ranges; o[53]=publish_state.violations;
    o[54]=publish_state.callbacks; o[55]=publish_state.cleanups;
    o[56]=publish_state.cleanup_count_before; o[57]=publish_state.cleanup_count_after;
    o[58]=(uint32_t)sizeof(publisher); o[59]=publish_state.direct_calls;
    o[60]=publish_state.direct_unchanged; o[61]=publish_state.callback_result;
    o[62]=publish_state.last_slot;
}
uint32_t hp1020_publish_fixture_component_bytes(void) { return (uint32_t)sizeof(publisher); }
