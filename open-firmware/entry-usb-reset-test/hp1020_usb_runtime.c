/* SPDX-License-Identifier: GPL-2.0-or-later
 * Draft continuous RAM-only partial-document reset and fresh document. The platform observations,
 * cache copies, settlement and output consumption are explicitly supplied.
 * This is not an interrupt/controller/engine implementation or an upload. */
#include "hp1020_usb_runtime_contract.h"

#define W(name) (hp1020_usb_runtime_mailbox.words[HP1020_USB_RUNTIME_W_##name])
#define ALL_PROGRESS (HP1020_UDC_SETUP_ALLOW_SERVICE | HP1020_UDC_SETUP_ALLOW_ARM | HP1020_UDC_SETUP_ALLOW_PUMP)
extern uint8_t __hp1020_entry_state_start[], __hp1020_entry_state_end[];
extern uint8_t __hp1020_entry_data_start[], __hp1020_entry_data_end[];

_Static_assert(sizeof(uintptr_t)==4,"target32 only");
_Static_assert(HP1020_RX_SLOTS==4 && HP1020_RX_CAPACITY==1024,"full receive capacity");
_Static_assert(HP1020_IMAGE_RING_SLOTS==4 && HP1020_IMAGE_MAX_BAND_BYTES==8192,"full output capacity");

void hp1020_usb_runtime_fail(enum hp1020_usb_runtime_error error,uint32_t detail) {
    if(!W(ERROR)) { W(ERROR)=(uint32_t)error;W(ERROR_DETAIL)=detail; }
    W(STATUS)=HP1020_USB_RUNTIME_FAIL;
}

bool hp1020_usb_runtime_step(enum hp1020_usb_runtime_phase phase) {
    if(W(ERROR))return false;
    if(phase>HP1020_USB_RUNTIME_DONE || hp1020_usb_runtime_provider.steps>=HP1020_USB_RUNTIME_MAX_STEPS) {
        hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_LIMIT,(uint32_t)phase);return false;
    }
    hp1020_usb_runtime_provider.steps++;
    W(STEPS)=hp1020_usb_runtime_provider.steps;W(PHASE)=(uint32_t)phase;
    return true;
}

static bool result(enum hp1020_usb_runtime_result_domain domain,uint32_t actual) {
    W(RESULT_DOMAIN)=(uint32_t)domain;W(RESULT)=actual;
    if(actual) { hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_API,((uint32_t)domain<<16)|actual);return false; }
    return W(ERROR)==0;
}

static bool progress(uint32_t needed) {
    const uint32_t actual=hp1020_udc_publish_progress(&hp1020_usb_runtime_publisher);
    if((actual&needed)!=needed) {
        hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_API,UINT32_C(0x10000000)|(needed<<8)|actual);return false;
    }
    return W(ERROR)==0;
}

static void scan_zero(const volatile uint8_t *p,uint32_t size,uint32_t *bad,uint32_t *first) {
    for(uint32_t i=0;i<size;i++)if(p[i]) {
        if(!*bad)*first=(uint32_t)(uintptr_t)(p+i);
        (*bad)++;
    }
}

static bool scan_initial_storage(void) {
    const uint32_t state_bytes=(uint32_t)((uintptr_t)__hp1020_entry_state_end-(uintptr_t)__hp1020_entry_state_start);
    const uint32_t data_bytes=(uint32_t)((uintptr_t)__hp1020_entry_data_end-(uintptr_t)__hp1020_entry_data_start);
    uint32_t bad=0,first=0,sentinel_bad=0,data_hash=UINT32_C(2166136261);
    /* No initializer, guard installation or mailbox write before every scan.
     * These are volatile object-representation reads, including pointer bytes. */
    scan_zero(__hp1020_entry_state_start,state_bytes,&bad,&first);
    scan_zero((const volatile uint8_t *)(const volatile void *)&hp1020_usb_runtime_memory,
        sizeof(hp1020_usb_runtime_memory),&bad,&first);
    scan_zero((const volatile uint8_t *)(const volatile void *)&hp1020_usb_runtime_mailbox,
        sizeof(hp1020_usb_runtime_mailbox),&bad,&first);
    scan_zero((const volatile uint8_t *)(const volatile void *)&hp1020_usb_runtime_witness,
        sizeof(hp1020_usb_runtime_witness),&bad,&first);
    const volatile uint8_t *sentinel=hp1020_usb_runtime_sentinel;
    for(uint32_t i=0;i<sizeof(hp1020_usb_runtime_sentinel);i++) {
        if(sentinel[i]!=(uint8_t)(0x31u+0x21u*(i&15u))) {
            if(!bad)first=(uint32_t)(uintptr_t)(sentinel+i);
            bad++;sentinel_bad++;
        }
    }
    const volatile uint8_t *initialized=__hp1020_entry_data_start;
    for(uint32_t i=0;i<data_bytes;i++)data_hash=(data_hash^initialized[i])*UINT32_C(16777619);
    W(MAGIC)=HP1020_USB_RUNTIME_MAGIC;W(VERSION)=HP1020_USB_RUNTIME_VERSION;
    W(STATUS)=HP1020_USB_RUNTIME_RUNNING;W(PHASE)=HP1020_USB_RUNTIME_SCAN;
    W(FIRST_BAD_ADDRESS)=first;W(BAD_BYTES)=bad;
    W(SCANNED_BSS)=state_bytes;W(SCANNED_MEMORY)=sizeof(hp1020_usb_runtime_memory);
    W(SCANNED_MAILBOX)=sizeof(hp1020_usb_runtime_mailbox);W(SCANNED_WITNESS)=sizeof(hp1020_usb_runtime_witness);
    W(SCANNED_SENTINEL)=sizeof(hp1020_usb_runtime_sentinel);
    W(DATA_BYTES)=data_bytes;W(INITIAL_DATA_FNV)=data_hash;
    if(bad) {
        hp1020_usb_runtime_fail(sentinel_bad==bad ? HP1020_USB_RUNTIME_ERROR_SENTINEL : HP1020_USB_RUNTIME_ERROR_ZERO,bad);
        return false;
    }
    return true;
}

static bool service(void) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_SERVICE) || !progress(HP1020_UDC_SETUP_ALLOW_SERVICE))return false;
    const enum hp1020_udc_publish_result r=hp1020_udc_publish_service(&hp1020_usb_runtime_publisher);
    W(SERVICES)++;
    return result(HP1020_USB_RUNTIME_DOMAIN_PUBLISH,(uint32_t)r);
}

static bool pump(uint32_t consumed_bytes) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_PUMP) || !progress(HP1020_UDC_SETUP_ALLOW_PUMP))return false;
    const enum hp1020_rx_result r=hp1020_tusb_adapter_pump(&hp1020_usb_runtime_adapter);
    W(PUMPS)++;W(PUMP_RESULT)=(uint32_t)r;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_RECEIVE,(uint32_t)r))return false;
    W(INPUT_CONSUMED)+=consumed_bytes;
    return true;
}

static bool arm(uint32_t sequence) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_ARM) || !progress(HP1020_UDC_SETUP_ALLOW_ARM) ||
       !hp1020_usb_runtime_ram_scope(sequence))return false;
    const enum hp1020_udc_publish_result r=hp1020_udc_publish_arm_out(
        &hp1020_usb_runtime_publisher,hp1020_usb_runtime_supplied.publish);
    W(ARM_CALLS)++;
    return result(HP1020_USB_RUNTIME_DOMAIN_PUBLISH,(uint32_t)r);
}

static bool acquire(uint32_t offset,uint32_t count) {
    /* The original cookie comes from the genuine DCD callback, not from this
     * packet's loop index, current generation, endpoint or diagnostic rows. */
    const struct hp1020_tusb_cookie original=hp1020_usb_runtime_provider.bulk.cookie;
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_IMAGE) ||
       !hp1020_usb_runtime_ram_install_bulk(original,offset,count) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_ACQUIRE))return false;
    W(ACQUIRE_CALLS)++;
    const enum hp1020_udc_out_result r=hp1020_udc_acquire_packet(&hp1020_usb_runtime_acquirer,
        original,0,hp1020_usb_runtime_supplied.acquire);
    if(!result(HP1020_USB_RUNTIME_DOMAIN_OUT,(uint32_t)r))return false;
    W(ACQUIRES_ACCEPTED)++;
    return hp1020_usb_runtime_ram_retired(original);
}

static bool settle_status(void) {
    if(!progress(ALL_PROGRESS) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_EP0_SETTLE))return false;
    const struct hp1020_tusb_cookie original=hp1020_usb_runtime_provider.ep0.cookie;
    struct hp1020_udc_ep0_submission publication;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_EP0,(uint32_t)hp1020_udc_ep0_take_submission(
        &hp1020_usb_runtime_ep0,original,hp1020_usb_runtime_supplied.ep0_publish,&publication)))return false;
    if(publication.original_buffer || publication.requested || publication.allocation_bytes!=64 ||
       publication.endpoint!=0x80 || publication.descriptor_cpu!=hp1020_usb_runtime_ep0_memory.in_descriptor ||
       publication.packet_cpu!=hp1020_usb_runtime_ep0_memory.in_staging ||
       publication.descriptor_dma!=HP1020_USB_RUNTIME_EP0_IN_DESCRIPTOR_DMA ||
       publication.packet_dma!=HP1020_USB_RUNTIME_EP0_IN_PACKET_DMA) {
        hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_OWNER,1);return false;
    }
    struct hp1020_udc_ep0_observation observation;
    if(!hp1020_usb_runtime_ram_ep0_observation(&observation) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_EP0_SETTLE))return false;
    W(EP0_OBSERVATIONS)++;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_EP0,(uint32_t)hp1020_udc_ep0_observe(
        &hp1020_usb_runtime_ep0,&observation,hp1020_usb_runtime_supplied.ep0_complete)))return false;
    W(EP0_SETTLED)++;
    if(!hp1020_usb_runtime_ram_retired(original) || !service())return false;
    return true;
}

static bool configure(void) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RESET))return false;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_SETUP,(uint32_t)hp1020_udc_setup_bus_reset(
        &hp1020_usb_runtime_setup,1,TUSB_SPEED_FULL)))return false;
    W(RESETS_ADMITTED)++;
    if(!service() || !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_CONFIGURE) ||
       !hp1020_usb_runtime_ram_scope(0))return false;
    struct hp1020_udc_setup_observation setup;
    if(!hp1020_usb_runtime_ram_setup_observation(&setup) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_CONFIGURE) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_SETUP,(uint32_t)hp1020_udc_setup_offer(
           &hp1020_usb_runtime_setup,&setup)) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_CONFIGURE) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_SETUP,(uint32_t)hp1020_udc_setup_dispatch(
           &hp1020_usb_runtime_setup,setup.sequence,hp1020_usb_runtime_supplied.setup,
           hp1020_usb_runtime_supplied.ep0_stalls_cleared)))return false;
    W(SETUPS_ADMITTED)++;
    return service() && settle_status();
}

static bool recover_initial_binding(void) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_pending_reset(
           &hp1020_usb_runtime_adapter,&hp1020_usb_runtime_provider.recovery)))return false;
    const struct hp1020_printer_reset_ticket original=hp1020_usb_runtime_provider.recovery;
    W(RECOVERY_ID)=original.recovery_id;W(RECOVERY_GENERATION)=original.generation;
    /* Each promise is separately supplied. No descriptor, empty software queue
     * or successful programming write proves any of these physical facts. */
    if(hp1020_usb_runtime_supplied.receive_quiesced!=1 ||
       hp1020_usb_runtime_supplied.output_quiesced!=1 ||
       hp1020_usb_runtime_supplied.transport_reset!=1) {
        hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_API,UINT32_C(0x20000000));return false;
    }
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_ack_reset(
           &hp1020_usb_runtime_adapter,original,HP1020_PRINTER_RECEIVE_QUIESCED)))return false;
    W(RECEIVE_PROMISES)++;
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_ack_reset(
           &hp1020_usb_runtime_adapter,original,HP1020_PRINTER_OUTPUT_QUIESCED)))return false;
    W(OUTPUT_PROMISES)++;
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_ack_reset(
           &hp1020_usb_runtime_adapter,original,HP1020_PRINTER_TRANSPORT_RESET)))return false;
    W(TRANSPORT_PROMISES)++;
    if(!progress(ALL_PROGRESS) || !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_finish_reset(
           &hp1020_usb_runtime_adapter,original)))return false;
    W(RECOVERY_FINISHES)++;
    return true;
}

/* Record the actual returned enum without turning WAIT into success. These
 * bounded rows are secondary witnesses; the observer checks real calls/state. */
static bool checked_reset(enum hp1020_usb_runtime_check operation,
    enum hp1020_printer_result actual,struct hp1020_printer_reset_ticket ticket,
    uint32_t detail) {
    W(RESULT_DOMAIN)=HP1020_USB_RUNTIME_DOMAIN_PRINTER;W(RESULT)=(uint32_t)actual;
    const struct hp1020_usb_runtime_check_row row={
        (uint32_t)operation,HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)actual,
        {ticket.recovery_id,ticket.generation,0,0,0},detail};
    return hp1020_usb_runtime_ram_check(&row);
}

static bool checked_cookie(enum hp1020_usb_runtime_check operation,
    enum hp1020_udc_out_result actual,struct hp1020_tusb_cookie original) {
    W(RESULT_DOMAIN)=HP1020_USB_RUNTIME_DOMAIN_OUT;W(RESULT)=(uint32_t)actual;
    const struct hp1020_usb_runtime_check_row row={
        (uint32_t)operation,HP1020_USB_RUNTIME_DOMAIN_OUT,(uint32_t)actual,
        {original.id,original.epoch,original.generation,
         original.sequence,original.endpoint},0};
    return hp1020_usb_runtime_ram_check(&row);
}

static bool wait_finish(struct hp1020_printer_reset_ticket original,
    enum hp1020_usb_runtime_check operation) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY))return false;
    const enum hp1020_printer_result r=hp1020_tusb_adapter_finish_reset(
        &hp1020_usb_runtime_adapter,original);
    return checked_reset(operation,r,original,0);
}

static bool wait_receive(struct hp1020_printer_reset_ticket original,
    enum hp1020_usb_runtime_check operation) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY))return false;
    const enum hp1020_printer_result r=hp1020_tusb_adapter_ack_reset(
        &hp1020_usb_runtime_adapter,original,HP1020_PRINTER_RECEIVE_QUIESCED);
    return checked_reset(operation,r,original,HP1020_PRINTER_RECEIVE_QUIESCED);
}

static bool acknowledge(struct hp1020_printer_reset_ticket original,
    enum hp1020_printer_reset_part part) {
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY))return false;
    const enum hp1020_printer_result r=hp1020_tusb_adapter_ack_reset(
        &hp1020_usb_runtime_adapter,original,part);
    if(!result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)r))return false;
    if(part==HP1020_PRINTER_RECEIVE_QUIESCED)W(RECEIVE_PROMISES)++;
    else if(part==HP1020_PRINTER_OUTPUT_QUIESCED)W(OUTPUT_PROMISES)++;
    else if(part==HP1020_PRINTER_TRANSPORT_RESET)W(TRANSPORT_PROMISES)++;
    else {hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_API,(uint32_t)part);return false;}
    return true;
}

static bool reset_partial_document(void) {
    /* The old page is READY, but has never been accepted by an output consumer.
     * The eager sixth OUT remains genuinely owned; the helper supplies only
     * raw SETUP bytes/ingress3 and the existing APIs perform admission. */
    struct hp1020_udc_setup_observation setup;
    if(!hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_RESET_CUT) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_CONFIGURE) ||
       !hp1020_usb_runtime_ram_reset_observation(&setup) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_SETUP,(uint32_t)hp1020_udc_setup_offer(
           &hp1020_usb_runtime_setup,&setup)) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_CONFIGURE) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_SETUP,(uint32_t)hp1020_udc_setup_dispatch(
           &hp1020_usb_runtime_setup,setup.sequence,hp1020_usb_runtime_supplied.setup,
           hp1020_usb_runtime_supplied.ep0_stalls_cleared)))return false;
    W(SETUPS_ADMITTED)++;
    /* The real transport callback has already retained the historical original
     * cookie. Request cancellation after dispatch unwinds; this is not proof
     * of settlement and never invokes a cancelled-completion shortcut. */
    if(!hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY))return false;
    const struct hp1020_tusb_cookie saved=hp1020_usb_runtime_provider.reset_cookie;
    const enum hp1020_udc_out_result cancelled=hp1020_udc_out_request_cancel(
        &hp1020_usb_runtime_out,saved);
    W(CANCEL_API_CALLS)++;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_OUT,(uint32_t)cancelled) || !service() ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_pending_reset(
           &hp1020_usb_runtime_adapter,&hp1020_usb_runtime_provider.recovery)))return false;
    const struct hp1020_printer_reset_ticket ticket=hp1020_usb_runtime_provider.recovery;
    W(RECOVERY_ID)=ticket.recovery_id;W(RECOVERY_GENERATION)=ticket.generation;
    if(!hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_RESET_HELD) ||
       !wait_finish(ticket,HP1020_USB_RUNTIME_CHECK_FINISH_OWNED) ||
       !wait_receive(ticket,HP1020_USB_RUNTIME_CHECK_RECEIVE_DCD))return false;
    /* This supplied late SUCCESS belongs to the still-live old writer. Its
     * actual queued TinyUSB callback must drain before a receive promise. */
    if(!acquire(320,32) ||
       !wait_receive(ticket,HP1020_USB_RUNTIME_CHECK_RECEIVE_PENDING) ||
       !hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_LATE_PENDING) ||
       !service() || !hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_OLD_DRAINED))return false;
    /* Three distinct platform facts remain explicitly supplied. No empty
     * software counter, descriptor or requested cancellation proves them. */
    if(hp1020_usb_runtime_supplied.receive_quiesced!=1 ||
       hp1020_usb_runtime_supplied.output_quiesced!=1 ||
       hp1020_usb_runtime_supplied.transport_reset!=1) {
        hp1020_usb_runtime_fail(HP1020_USB_RUNTIME_ERROR_API,UINT32_C(0x20000000));return false;
    }
    if(!acknowledge(ticket,HP1020_PRINTER_RECEIVE_QUIESCED) ||
       !acknowledge(ticket,HP1020_PRINTER_OUTPUT_QUIESCED) ||
       !wait_finish(ticket,HP1020_USB_RUNTIME_CHECK_FINISH_MISSING_TRANSPORT) ||
       !acknowledge(ticket,HP1020_PRINTER_TRANSPORT_RESET) ||
       !hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_BEFORE_RESTART) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY) ||
       !result(HP1020_USB_RUNTIME_DOMAIN_PRINTER,(uint32_t)hp1020_tusb_adapter_finish_reset(
           &hp1020_usb_runtime_adapter,ticket)))return false;
    W(RECOVERY_FINISHES)++;
    /* The successful reset creates the real deferred class-status owner. */
    return settle_status();
}

static bool stale_original_at_reuse(void) {
    const struct hp1020_tusb_cookie saved=hp1020_usb_runtime_provider.reset_cookie;
    if(!hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_REUSE_BEFORE) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_ACQUIRE))return false;
    W(ACQUIRE_CALLS)++;
    const enum hp1020_udc_out_result acquired=hp1020_udc_acquire_packet(
        &hp1020_usb_runtime_acquirer,saved,0,hp1020_usb_runtime_supplied.acquire);
    if(!checked_cookie(HP1020_USB_RUNTIME_CHECK_STALE_ACQUIRE_REUSE,acquired,saved) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_RECOVERY))return false;
    const enum hp1020_udc_out_result cancelled=hp1020_udc_out_request_cancel(
        &hp1020_usb_runtime_out,saved);
    W(CANCEL_API_CALLS)++;
    if(!checked_cookie(HP1020_USB_RUNTIME_CHECK_STALE_CANCEL_REUSE,cancelled,saved))return false;
    return hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_REUSE_AFTER);
}

void hp1020_usb_runtime_c(void) {
    if(!scan_initial_storage() || !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_INIT) ||
       !hp1020_usb_runtime_ram_init() || !configure() || !recover_initial_binding() || !arm(1))return;
    for(uint32_t packet=0;packet<5u;packet++) {
        if(!acquire(packet*64u,64) || !service() || !pump(64) || !arm(packet+2u))return;
    }
    if(!reset_partial_document() || !arm(7) || !acquire(0,64) ||
       !service() || !pump(64) || !arm(8) || !stale_original_at_reuse())return;
    for(uint32_t packet=1;packet<6u;packet++) {
        const uint32_t bytes=packet==5u ? 32u : 64u;
        if(!acquire(packet*64u,bytes) || !service() || !pump(bytes) || !arm(packet+8u))return;
    }
    if(!progress(ALL_PROGRESS) || !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_CLOSE))return;
    hp1020_usb_runtime_provider.closing=1;
    if(!hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_BEFORE_CLOSE))return;
    const enum hp1020_tusb_result closed=hp1020_tusb_adapter_close_input(&hp1020_usb_runtime_adapter);
    W(CLOSE_CALLS)++;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_ADAPTER,(uint32_t)closed))return;
    /* No service between close and final acquisition. A genuine supplied ZLP
     * settles the retained owner; it neither invents EOF nor cancels anything. */
    if(!acquire(352,0) || !hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_BEFORE_FINAL_SERVICE) ||
       !service() || !pump(0) || !progress(ALL_PROGRESS) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_FINISH) ||
       !hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_BEFORE_FINISH))return;
    const enum hp1020_rx_result finished=hp1020_tusb_adapter_finish(&hp1020_usb_runtime_adapter);
    W(FINISH_CALLS)++;W(FINISH_RESULT)=(uint32_t)finished;
    if(!result(HP1020_USB_RUNTIME_DOMAIN_RECEIVE,(uint32_t)finished))return;
    hp1020_usb_runtime_provider.finished=1;
    if(!hp1020_usb_runtime_ram_note(HP1020_USB_RUNTIME_NOTE_FINAL) ||
       !hp1020_usb_runtime_step(HP1020_USB_RUNTIME_DONE))return;
    W(STATUS)=HP1020_USB_RUNTIME_PASS;
}
