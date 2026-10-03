/* SPDX-License-Identifier: GPL-2.0-or-later
 * Unexecuted after-device acquisition fixture. Separate synthetic device images
 * and explicit CPU poison are test inputs, never physical DMA/cache behavior.
 * One actual composed TinyUSB DCD/owner ledger; no replacement queue or owner.
 */
#include "hp1020_udc_acquire.h"

static uint32_t acquire_fixture_init(uint32_t);
static void acquire_fixture_check(void);
static void acquire_fixture_snapshot(void);
static uint32_t acquire_fixture_step(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);
static void acquire_fixture_callback_probe(struct hp1020_tusb_cookie);

#define HP1020_COMPOSED_ACQUIRE 1
#include "udc-publish-test/fixture.c"

uint32_t hp1020_acquire_fixture_stats[80];
/* descriptor guard/data/guard, then payload guard/data/guard. No C padding. */
_Alignas(16) uint8_t hp1020_acquire_fixture_images[144];
static uint8_t acquire_image_shadow[144];
static struct hp1020_udc_acquire acquirer;
static struct {
    struct hp1020_tusb_cookie image_cookie, hook_owner;
    uint32_t result, calls[3], checked, violations, image_writes, poison_writes;
    uint32_t slot, mode, callback_probes, hook_probes, probe_result, probe_unchanged;
    uint32_t image_refusals, packet_calls, accepted, faults, stale;
    uint32_t next_kind, entry_completions, entry_cancel_requests, entry_pixels;
    uint32_t entry_documents, entry_wire, entry_issued, entry_consumed, entry_count;
    uint32_t entry_fault;
    uint8_t facts[3], initialized, image_valid, active;
} acquire_state;

static void acquire_violation(void) {
    acquire_state.violations++; state.violations++;
}
static bool acquire_guards(void) {
    for (uint32_t i=0;i<16;i++)
        if (hp1020_acquire_fixture_images[i] != state.fill ||
            hp1020_acquire_fixture_images[32+i] != state.fill ||
            hp1020_acquire_fixture_images[48+i] != state.fill ||
            hp1020_acquire_fixture_images[128+i] != state.fill) return false;
    return true;
}
static void acquire_fixture_check(void) {
    if (!acquire_state.initialized) return;
    if (!acquire_guards() || memcmp(hp1020_acquire_fixture_images,acquire_image_shadow,144) ||
        acquire_state.checked != acquire_state.calls[0]+acquire_state.calls[1]+acquire_state.calls[2] ||
        !acquire_state.probe_unchanged) acquire_violation();
}
static uint32_t acquire_owner_slot(const struct hp1020_tusb_owner *owner) {
    for (uint32_t i=0;i<HP1020_RX_SLOTS;i++)
        if (owner->buffer == memory.data.receive.data[i]) return i;
    return UINT32_MAX;
}
static bool acquire_original_owner(struct hp1020_tusb_cookie cookie, uint32_t *slot) {
    const struct hp1020_tusb_owner owner=adapter.owners[2];
    *slot=acquire_owner_slot(&owner);
    return cookie.id && cookie.endpoint == 1 && *slot < HP1020_RX_SLOTS &&
        owner.state == HP1020_TUSB_OWNER_DCD && owner.length == 64 &&
        same_cookie(owner.cookie,cookie) && packets[2].live &&
        packets[2].length == 64 && packets[2].buffer == owner.buffer &&
        same_cookie(packets[2].cookie,cookie) && composed_out_current(cookie) &&
        composed_out.buffer.cpu == owner.buffer && composed_out.buffer.bytes == 64 &&
        composed_out.buffer.dma == COMPOSED_RX_DMA + COMPOSED_RX_STEP*(*slot) &&
        composed_out.descriptor.cpu == composed_out_memory.descriptor &&
        composed_out.descriptor.dma == COMPOSED_OUT_DMA &&
        composed_out.descriptor.bytes == 16;
}
static struct hp1020_udc_acquire_facts acquire_facts(void) {
    const struct hp1020_udc_acquire_facts f={acquire_state.facts[0],
        acquire_state.facts[1],acquire_state.facts[2]};
    return f;
}

static void acquire_busy_probe(struct hp1020_tusb_cookie cookie, bool from_hook) {
    /* A real active callback supplies the busy condition; no owned field is
     * modified to manufacture reentry. Byte comparisons cover all API metadata
     * and the current borrowed ranges. Existing full-storage guards remain. */
    uint8_t adapter_before[sizeof(adapter)], receive_before[sizeof(document.receive)];
    uint8_t out_before[sizeof(composed_out)], acquire_before[sizeof(acquirer)];
    uint8_t publisher_before[sizeof(publisher)], program_before[sizeof(program)];
    uint8_t io_before[sizeof(program_state)], state_before[sizeof(state)];
    uint8_t fixture_before[sizeof(acquire_state)], descriptor_before[16], buffer_before[64];
    uint8_t images_before[144];
    uint32_t slot;
    if (!acquire_original_owner(cookie,&slot) ||
        (from_hook ? !composed_out.busy : (!adapter.busy || !adapter.stack_active))) {
        acquire_violation(); return;
    }
    memcpy(adapter_before,&adapter,sizeof(adapter_before));
    memcpy(receive_before,&document.receive,sizeof(receive_before));
    memcpy(out_before,&composed_out,sizeof(out_before));
    memcpy(acquire_before,&acquirer,sizeof(acquire_before));
    memcpy(publisher_before,&publisher,sizeof(publisher_before));
    memcpy(program_before,&program,sizeof(program_before));
    memcpy(io_before,&program_state,sizeof(io_before));
    memcpy(state_before,&state,sizeof(state_before));
    memcpy(fixture_before,&acquire_state,sizeof(fixture_before));
    memcpy(descriptor_before,composed_out_memory.descriptor,16);
    memcpy(buffer_before,memory.data.receive.data[slot],64);
    memcpy(images_before,hp1020_acquire_fixture_images,144);
    const struct hp1020_udc_acquire_facts facts={1,1,1};
    const uint32_t r=(uint32_t)hp1020_udc_acquire_packet(&acquirer,cookie,0,facts);
    const bool unchanged=!memcmp(adapter_before,&adapter,sizeof(adapter_before)) &&
        !memcmp(receive_before,&document.receive,sizeof(receive_before)) &&
        !memcmp(out_before,&composed_out,sizeof(out_before)) &&
        !memcmp(acquire_before,&acquirer,sizeof(acquire_before)) &&
        !memcmp(publisher_before,&publisher,sizeof(publisher_before)) &&
        !memcmp(program_before,&program,sizeof(program_before)) &&
        !memcmp(io_before,&program_state,sizeof(io_before)) &&
        !memcmp(state_before,&state,sizeof(state_before)) &&
        !memcmp(fixture_before,&acquire_state,sizeof(fixture_before)) &&
        !memcmp(descriptor_before,composed_out_memory.descriptor,16) &&
        !memcmp(buffer_before,memory.data.receive.data[slot],64) &&
        !memcmp(images_before,hp1020_acquire_fixture_images,144);
    acquire_state.probe_result=r;
    acquire_state.probe_unchanged=(uint32_t)unchanged;
    if (r != HP1020_UDC_OUT_WAIT || !unchanged) acquire_violation();
    if (from_hook) acquire_state.hook_probes++; else acquire_state.callback_probes++;
}
static void acquire_fixture_callback_probe(struct hp1020_tusb_cookie cookie) {
    if (!acquire_state.initialized) { acquire_violation(); return; }
    acquire_busy_probe(cookie,false);
}

static enum hp1020_udc_acquire_io_result acquire_hook(void *context,
    uint32_t kind, struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_span span) {
    composed_check();
    const struct hp1020_tusb_owner owner=adapter.owners[2];
    acquire_state.hook_owner=owner.cookie; /* Actual owner, not diagnostic output. */
    if (kind < 6 || kind > 8) { acquire_violation(); return HP1020_UDC_ACQUIRE_IO_UNKNOWN; }
    acquire_state.calls[kind-6]++;
    uint32_t slot;
    bool valid=context == &acquire_state && acquire_state.active &&
        acquire_state.next_kind == kind && acquire_original_owner(cookie,&slot) &&
        composed_out.phase == HP1020_UDC_OUT_EXPOSED && composed_out.busy &&
        !adapter.busy && !adapter.stack_active && acquire_state.image_valid &&
        same_cookie(acquire_state.image_cookie,owner.cookie) && acquire_state.slot == slot &&
        state.completions == acquire_state.entry_completions &&
        state.cancel_requests == acquire_state.entry_cancel_requests &&
        state.pixel_bytes == acquire_state.entry_pixels &&
        state.document_calls == acquire_state.entry_documents &&
        state.wire_bytes == acquire_state.entry_wire &&
        document.receive.issued == acquire_state.entry_issued &&
        document.receive.consumed == acquire_state.entry_consumed &&
        document.receive.count == acquire_state.entry_count &&
        composed_out.fault_reason == acquire_state.entry_fault;
    if (valid && kind == 6) valid=span.cpu == composed_out_memory.descriptor &&
        span.dma == COMPOSED_OUT_DMA && span.bytes == 16;
    if (valid && kind == 7) valid=span.cpu == memory.data.receive.data[slot] &&
        span.dma == COMPOSED_RX_DMA + COMPOSED_RX_STEP*slot && span.bytes == 64;
    if (valid && kind == 8) valid=!span.cpu && !span.dma && !span.bytes;
    if (valid) acquire_state.checked++; else acquire_violation();
    if (valid) acquire_busy_probe(owner.cookie,true);
    uint32_t result=program_injected_result(kind,
        valid ? HP1020_UDC_ACQUIRE_IO_OK : HP1020_UDC_ACQUIRE_IO_UNKNOWN);
    result=program_record(kind,span.dma,span.bytes,result);
    acquire_state.next_kind=result == HP1020_UDC_ACQUIRE_IO_OK ? kind+1u : 0;
    if (valid && kind != 8) {
        const uint32_t length=kind == 6 ? 16u : 64u;
        const uint32_t n=result == HP1020_UDC_ACQUIRE_IO_OK ? length :
            result == HP1020_UDC_ACQUIRE_IO_UNKNOWN ? length/2u : 0u;
        const uint32_t offset=kind == 6 ? 16u : 64u;
        if (n && kind == 6) {
            memcpy(composed_out_memory.descriptor,hp1020_acquire_fixture_images+offset,n);
            memcpy(composed_out_shadow,acquire_image_shadow+offset,n);
        } else if (n) {
            memcpy(memory.data.receive.data[slot],hp1020_acquire_fixture_images+offset,n);
            memcpy(packets[2].shadow,acquire_image_shadow+offset,n);
            memcpy(protected_memory.receive.data[slot],acquire_image_shadow+offset,n);
        }
    }
    /* The independently permitted shadows include UNKNOWN partial effects.
     * Check them now, while the original fixture packet is still live. */
    composed_check();
    return (enum hp1020_udc_acquire_io_result)result;
}
static enum hp1020_udc_acquire_io_result acquire_descriptor(void *context,
    struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_span span) {
    return acquire_hook(context,6,cookie,span);
}
static enum hp1020_udc_acquire_io_result acquire_payload(void *context,
    struct hp1020_tusb_cookie cookie, struct hp1020_udc_out_span span) {
    return acquire_hook(context,7,cookie,span);
}
static enum hp1020_udc_acquire_io_result acquire_order(void *context,
    struct hp1020_tusb_cookie cookie) {
    const struct hp1020_udc_out_span none={0};
    return acquire_hook(context,8,cookie,none);
}

static uint32_t acquire_fixture_init(uint32_t fill) {
    memset(&acquirer,0,sizeof(acquirer));
    memset(&acquire_state,0,sizeof(acquire_state));
    memset(hp1020_acquire_fixture_images,(int)(fill & 255u),144);
    memset(acquire_image_shadow,(int)(fill & 255u),144);
    memset(acquire_state.facts,1,sizeof(acquire_state.facts));
    acquire_state.slot=acquire_state.mode=UINT32_MAX;
    acquire_state.probe_result=UINT32_MAX; acquire_state.probe_unchanged=1;
    const struct hp1020_udc_acquire_hooks hooks={acquire_descriptor,acquire_payload,
        acquire_order,&acquire_state};
    const uint32_t r=(uint32_t)hp1020_udc_acquire_init(&acquirer,&composed_out,&hooks);
    acquire_state.initialized=1; acquire_state.result=r;
    return r;
}
static uint32_t acquire_device_image(uint32_t token,uint32_t mode,uint32_t c,uint32_t d) {
    if (mode > 1 || c || d) return HP1020_UDC_OUT_INVALID;
    struct hp1020_tusb_cookie cookie;
    uint32_t slot;
    if (!ep0_history(token,&cookie) || !acquire_original_owner(cookie,&slot))
        return HP1020_UDC_OUT_STALE;
    if (composed_out.phase != HP1020_UDC_OUT_EXPOSED)
        return HP1020_UDC_OUT_INVALID;
    /* All authority checks precede every source-image/CPU mutation. */
    memcpy(hp1020_acquire_fixture_images+16,hp1020_bulk_fixture_input,16);
    memcpy(acquire_image_shadow+16,hp1020_bulk_fixture_input,16);
    memcpy(hp1020_acquire_fixture_images+64,hp1020_bulk_fixture_input+16,64);
    memcpy(acquire_image_shadow+64,hp1020_bulk_fixture_input+16,64);
    acquire_state.image_cookie=cookie; acquire_state.slot=slot;
    acquire_state.mode=mode; acquire_state.image_valid=1; acquire_state.image_writes++;
    uint8_t descriptor[16], payload[64];
    composed_put32(descriptor,mode ? UINT32_C(0x88000040) : UINT32_C(0xc35a0000) | slot);
    composed_put32(descriptor+4,mode ? 0 : UINT32_C(0x13579bdf));
    composed_put32(descriptor+8,mode ? COMPOSED_RX_DMA + COMPOSED_RX_STEP*slot : UINT32_C(0xfedcba90));
    composed_put32(descriptor+12,mode ? 0 : UINT32_C(0x2468ace0));
    for (uint32_t i=0;i<64;i++) payload[i]=(uint8_t)(UINT32_C(0xd3) ^ (slot*UINT32_C(0x29)) ^ (i*UINT32_C(0x17)));
    memcpy(composed_out_memory.descriptor,descriptor,16);
    memcpy(composed_out_shadow,descriptor,16);
    memcpy(memory.data.receive.data[slot],payload,64);
    memcpy(packets[2].shadow,payload,64);
    memcpy(protected_memory.receive.data[slot],payload,64);
    acquire_state.poison_writes++;
    composed_check();
    return HP1020_UDC_OUT_OK;
}
static uint32_t acquire_packet(uint32_t token,uint32_t mutation,uint32_t fault,uint32_t d) {
    if (mutation > 5 || d) return HP1020_UDC_OUT_INVALID;
    acquire_state.packet_calls++;
    struct hp1020_tusb_cookie cookie;
    if (!ep0_history(token,&cookie)) {
        acquire_state.stale++; return HP1020_UDC_OUT_STALE;
    }
    cookie=ep0_mutate(cookie,mutation);
    acquire_state.active=1; acquire_state.next_kind=6;
    acquire_state.entry_completions=state.completions;
    acquire_state.entry_cancel_requests=state.cancel_requests;
    acquire_state.entry_pixels=state.pixel_bytes;
    acquire_state.entry_documents=state.document_calls;
    acquire_state.entry_wire=state.wire_bytes;
    acquire_state.entry_issued=document.receive.issued;
    acquire_state.entry_consumed=document.receive.consumed;
    acquire_state.entry_count=document.receive.count;
    acquire_state.entry_fault=composed_out.fault_reason;
    const uint32_t r=(uint32_t)hp1020_udc_acquire_packet(&acquirer,cookie,fault,acquire_facts());
    /* Ownership must still be witnessed BEFORE this fixture clears its live
     * flag. Actual adapter completion may only have changed DCD to PENDING. */
    composed_check();
    acquire_state.active=0;
    if (r == HP1020_UDC_OUT_OK) {
        if (!packets[2].live || !same_cookie(packets[2].cookie,cookie) ||
            adapter.owners[2].state != HP1020_TUSB_OWNER_PENDING ||
            !same_cookie(adapter.owners[2].cookie,cookie) ||
            composed_out.phase != HP1020_UDC_OUT_FREE) acquire_violation();
        packets[2].live=0; state.completions++; composed_out_state.completions++;
        acquire_state.accepted++;
    } else if (r == HP1020_UDC_OUT_STALE) {
        state.stale++; composed_out_state.stale++; acquire_state.stale++;
    } else if (r == HP1020_UDC_OUT_FAULT) acquire_state.faults++;
    composed_out_state.result=r;
    return r;
}
static uint32_t acquire_fixture_step(uint32_t op,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    uint32_t r=HP1020_UDC_OUT_INVALID;
    if (op == 140) {
        r=acquire_device_image(a,b,c,d);
        if (r != HP1020_UDC_OUT_OK) acquire_state.image_refusals++;
    } else if (op == 141 && !a && !b && !c && !d) {
        memcpy(acquire_state.facts,hp1020_bulk_fixture_input,3);
        r=HP1020_UDC_OUT_OK;
    } else if (op == 142) r=acquire_packet(a,b,c,d);
    else if (op == 143 && a >= 6 && a <= 8 && b > program_state.trace_count &&
        b <= PROGRAM_TRACE_CAPACITY && (c == 1 || c == 2) && !d) {
        if (program_state.injection_armed) r=HP1020_UDC_OUT_WAIT;
        else {
            program_state.injection_kind=a; program_state.injection_ordinal=b;
            program_state.injection_result=c; program_state.injection_armed=1;
            r=HP1020_UDC_OUT_OK;
        }
    }
    acquire_state.result=r;
    return r;
}
static void acquire_diagnostic_words(uint32_t *out,const struct hp1020_udc_acquire_diagnostic *d) {
    ep0_cookie_words(out,d->cookie);
    out[5]=d->prefix; out[6]=d->dma; out[7]=d->bytes; out[8]=d->io_result;
    out[9]=d->reason; out[10]=(uint32_t)d->result; out[11]=d->operation; out[12]=d->snapshot_valid;
    for (uint32_t i=0;i<4;i++) out[13+i]=ep0_be32(d->snapshot+4*i);
}
static void acquire_fixture_snapshot(void) {
    uint32_t *o=hp1020_acquire_fixture_stats;
    memset(o,0,sizeof(hp1020_acquire_fixture_stats));
    o[0]=acquire_state.result; o[1]=acquirer.initialized; o[2]=acquirer.failure_valid;
    for (uint32_t i=0;i<3;i++) o[3+i]=acquire_state.calls[i];
    o[6]=acquire_state.checked; o[7]=acquire_state.violations; o[8]=(uint32_t)acquire_guards();
    o[9]=acquire_state.image_writes; o[10]=acquire_state.poison_writes;
    o[11]=((uint32_t)acquire_state.facts[0]<<16) | ((uint32_t)acquire_state.facts[1]<<8) | acquire_state.facts[2];
    o[12]=acquire_state.slot; o[13]=acquire_state.mode; ep0_cookie_words(o+14,acquire_state.hook_owner);
    o[19]=acquire_state.image_valid; ep0_cookie_words(o+20,acquire_state.image_cookie);
    acquire_diagnostic_words(o+25,&acquirer.last); acquire_diagnostic_words(o+42,&acquirer.first_failure);
    o[59]=(uint32_t)sizeof(acquirer); o[60]=acquire_state.callback_probes; o[61]=acquire_state.hook_probes;
    o[62]=acquire_state.probe_result; o[63]=acquire_state.probe_unchanged; o[64]=acquire_state.image_refusals;
    o[65]=acquire_state.packet_calls; o[66]=acquire_state.accepted; o[67]=acquire_state.faults; o[68]=acquire_state.stale;
    for (uint32_t i=0;i<4;i++) o[69+i]=ep0_be32(hp1020_acquire_fixture_images+16+4*i);
    o[77]=fnv(hp1020_acquire_fixture_images+16,16); o[78]=fnv(hp1020_acquire_fixture_images+64,64);
}
uint8_t *hp1020_acquire_fixture_device_storage(void) { return hp1020_acquire_fixture_images; }
uint32_t hp1020_acquire_fixture_device_storage_bytes(void) { return sizeof(hp1020_acquire_fixture_images); }
uint32_t hp1020_acquire_fixture_component_bytes(void) { return sizeof(acquirer); }
