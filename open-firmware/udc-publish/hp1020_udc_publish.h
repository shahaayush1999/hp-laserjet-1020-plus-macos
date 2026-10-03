/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_PUBLISH_H
#define HP1020_UDC_PUBLISH_H

#include "hp1020_udc_program.h"
#include "hp1020_udc_out.h"

/* One synchronous OUT1/full-speed64/BE PPBNDU publication.
 * No peripheral binding, mapping formula, cache primitive, receive acquisition,
 * completion, IRQ producer, owner allocator or recovery promise is supplied.
 * All calls/hooks are serialized and nonreentrant. Hooks cannot admit ingress,
 * invoke TinyUSB/the adapter, defer work, change mappings or settle ownership.
 * Objects/arguments are stationary, valid and mutually nonaliasing; init is
 * first use only and may never erase retained command or ownership history. */
enum hp1020_udc_publish_result {
    HP1020_UDC_PUBLISH_OK = 0, HP1020_UDC_PUBLISH_WAIT,
    HP1020_UDC_PUBLISH_STALE, HP1020_UDC_PUBLISH_INVALID,
    HP1020_UDC_PUBLISH_FAULT, HP1020_UDC_PUBLISH_ADAPTER_ERROR,
    /* A nonmutating preflight read failed BEFORE any receive reservation or
     * binding. No sticky packet failure/cookie is manufactured in this case. */
    HP1020_UDC_PUBLISH_PREFLIGHT_ERROR
};

/* Four fixed explicit DMA labels for the existing receive queue's64-byte
 * slot prefixes. CPU identities are the actual receive.memory->data[i].
 * Neither CPU pointers nor DMA labels are translated by bit manipulation.
 * Alignment/nonwrap/numerical disjointness are checked; physical mapping and
 * cache-line/alias safety remain the separately supplied lease below. */
struct hp1020_udc_publish_mapping { uint32_t receive_dma[HP1020_RX_SLOTS]; };

/* Mandatory synchronous range hooks, with original identity and exact span.
 * rx_before_device prepares64 bytes for DEVICE WRITES. descriptor_before_device
 * makes the newly built16 bytes ready for DEVICE READ/WRITE (bidirectional).
 * The provider owns real architecture operations, safe line rounding and
 * ordering under the lease. OK is its documented CPU-operation guarantee,
 * never a DMA-stop/USB-completion/ACK fact. No weak no-op fallback is supplied.
 * A justified coherent/uncached implementation is possible only as a separate
 * physical capability, not inferred from a hook returning OK. NOT_PERFORMED
 * and UNKNOWN both stop publication; partial effects must not be hidden. */
struct hp1020_udc_publish_cache {
    enum hp1020_udc_program_io_result (*rx_before_device)(void *,
        struct hp1020_tusb_cookie, struct hp1020_udc_out_span);
    enum hp1020_udc_program_io_result (*descriptor_before_device)(void *,
        struct hp1020_tusb_cookie, struct hp1020_udc_out_span);
    void *context;
};

/* Every field is exactly0/1. Unknown required facts WAIT before any reservation.
 * io_profile: supplied logical classic single-RX-FIFO semantics and compatible
 *   full-speed64/BE packet capability; read bits alone cannot establish it.
 * receive_dma_idle: old DMA/accesses are actually settled BEFORE wrapper entry
 *   and cannot reach rebuilt memory until the final RDE request. Existing
 *   prepare writes HOST_READY, so a later RDE0 observation is insufficient.
 * register_window_stable: sampled preserved fields/type/halt and all hardware
 *   and software RDE/register writers remain controlled through publication.
 * global_receive_ready: safe/visible SETUP SUBPTR, prior SETUP already captured,
 *   and every other OUT path prepared/gated before GLOBAL RDE may be requested.
 * cnak_window_safe: RX FIFO remains empty at CNAK (only required for NAK1).
 * mapping_lease: descriptor and all possible selected receive-prefix mappings
 *   and aliases are valid/stationary/exclusive before prepare and throughout
 *   their ownership; no in-flight address may be replaced after this call.
 * cache_range_safe: real maintenance capability or justified coherent mapping,
 *   valid nonwrapping rounding, exclusively owned whole-line envelopes for both
 *   exact ranges.16-byte alignment alone does not prove a larger granule safe.
 * None of these supplies RECEIVE/TRANSPORT/OUTPUT recovery acknowledgement. */
struct hp1020_udc_publish_facts {
    uint8_t io_profile, receive_dma_idle, register_window_stable;
    uint8_t global_receive_ready, cnak_window_safe, mapping_lease, cache_range_safe;
};

enum hp1020_udc_publish_operation {
    HP1020_UDC_PUBLISH_RX_CACHE = 1, HP1020_UDC_PUBLISH_DESCRIPTOR_CACHE,
    HP1020_UDC_PUBLISH_ORDER, HP1020_UDC_PUBLISH_TAKE,
    HP1020_UDC_PUBLISH_WRITE, HP1020_UDC_PUBLISH_READ,
    HP1020_UDC_PUBLISH_READBACK
};
/* Each prefix bit reports a successful SOFTWARE step, not hardware acceptance.
 * CNAK bits are absent on the no-CNAK path; expose does not imply DESPTR reached
 * a device. A failure also records the possibly uncertain next operation. */
enum hp1020_udc_publish_prefix {
    HP1020_UDC_PUBLISH_PREPARED = 1u,
    HP1020_UDC_PUBLISH_RX_READY = 2u,
    HP1020_UDC_PUBLISH_DESCRIPTOR_READY = 4u,
    HP1020_UDC_PUBLISH_MEMORY_ORDERED = 8u,
    HP1020_UDC_PUBLISH_EXPOSED = 16u,
    HP1020_UDC_PUBLISH_DESPTR_WRITTEN = 32u,
    HP1020_UDC_PUBLISH_DESPTR_ORDERED = 64u,
    HP1020_UDC_PUBLISH_CNAK_WRITTEN = 128u,
    HP1020_UDC_PUBLISH_CNAK_ORDERED = 256u,
    HP1020_UDC_PUBLISH_NAK_CLEARED = 512u,
    HP1020_UDC_PUBLISH_RDE_WRITTEN = 1024u,
    HP1020_UDC_PUBLISH_RDE_ORDERED = 2048u
};
struct hp1020_udc_publish_failure {
    struct hp1020_tusb_cookie cookie;
    uint32_t prefix, offset, attempted_value, dma, bytes;
    uint8_t operation, io_result, exposed, out_result;
};
/* No cookie is attached to a preflight diagnostic. refused distinguishes a
 * valid read with unsupported state from a hook failure. Failed reads retain
 * no alleged observed value. */
struct hp1020_udc_publish_preflight {
    uint32_t offset, value;
    uint8_t io_result, refused;
};
struct hp1020_udc_publish {
    struct hp1020_udc_program *program;
    struct hp1020_udc_out *out;
    struct hp1020_udc_publish_mapping mapping;
    struct hp1020_udc_publish_cache cache;
    struct hp1020_udc_publish_failure failure;
    struct hp1020_udc_publish_preflight preflight;
    uint32_t saved_devctl, saved_outctl, prefix;
    uint32_t arm_control_epoch, arm_transport_epoch, arm_generation, arm_ingress_sequence;
    enum hp1020_tusb_result last_adapter_result;
    enum hp1020_udc_program_result last_program_result;
    enum hp1020_udc_out_result last_out_result;
    uint8_t initialized, busy, arming, window, servicing, failed;
};

enum hp1020_udc_publish_result hp1020_udc_publish_init(
    struct hp1020_udc_publish *, struct hp1020_udc_program *, struct hp1020_udc_out *,
    const struct hp1020_udc_publish_mapping *, const struct hp1020_udc_publish_cache *);

/* The sole public arm path. Checks full combined readiness, exact lease facts
 * and nonmutating register preflight BEFORE adapter_arm_out reserves a receive
 * slot. Installs one synchronous callback window and clears it on every exit.
 * An unsupported snapshot is WAIT; a failed preflight read is PREFLIGHT_ERROR.
 * Both leave every owner, receive counter, descriptor and peripheral unchanged.
 * The existing adapter remains authoritative about actual reservation/admission. */
enum hp1020_udc_publish_result hp1020_udc_publish_arm_out(
    struct hp1020_udc_publish *, struct hp1020_udc_publish_facts);

/* Actual dcd_edpt_xfer callback ONLY. Direct/out-of-window/duplicate calls reject
 * before prepare or any hook. An accepted window is consumed once, then actual
 * udc_out_prepare binds the original cookie. cookie_out is unchanged before
 * binding and receives that cookie IMMEDIATELY afterward, even if a later step
 * fails. The DCD must retain its packet/history ledger on those failures before
 * returning false; never lose a borrowed buffer because the result is non-OK.
 * Cache/order -> take once -> immediate DESPTR/order/CNAK/order/readback/RDE/order.
 * No submission proposal escapes. Return true to TinyUSB ONLY on OK. After-bind
 * errors become sticky; adapter_arm_out fences on false AFTER this unwinds.
 * No fault/completion/cancellation/stack call is made reentrantly here. */
enum hp1020_udc_publish_result hp1020_udc_publish_prepare_and_publish(
    struct hp1020_udc_publish *, uint8_t rhport, uint8_t endpoint,
    uint8_t *buffer, uint16_t length, struct hp1020_tusb_cookie *cookie_out);

/* Replace normal program_service/progress/submission_allowed integration with
 * these combined wrappers. Every ordinary pump/finish/finish_reset, independent
 * EP0 publication must also obey full combined progress. Program selection/grant
 * must reject local publication failed/busy/arming/servicing, then retain their
 * existing admission checks: complete_selection can legitimately need the
 * program's SERVICE-only state to establish binding readiness. Existing program-
 * failure cleanup keeps its own stopped/exact-ticket rules and must not
 * substitute for, or clear, a publication failure. Exact-cookie observation/cancel settlement
 * and actual-reset ingress remain available. A sticky publication failure
 * allows service ONLY for an already admitted inactive actual bus reset; the
 * program's unready-binding SERVICE bit is not that exception. */
uint32_t hp1020_udc_publish_progress(const struct hp1020_udc_publish *);
enum hp1020_udc_publish_result hp1020_udc_publish_service(struct hp1020_udc_publish *);
bool hp1020_udc_publish_submission_allowed(struct hp1020_udc_publish *);

enum hp1020_udc_publish_result hp1020_udc_publish_pending_cleanup(
    const struct hp1020_udc_publish *, struct hp1020_udc_publish_failure *);
/* Exact ORIGINAL failure cookie, even after reset/generation supersession.
 * Requires supplied completed physical cleanup, stopped/unmounted software,
 * OUT FREE and no DCD/PENDING/prepared/delivering/response owner. The receive
 * queue's fenced old reservation accounting stays unchanged until its ordinary
 * three-promise restart; cleanup neither consumes it nor grants those promises.
 * No I/O, retry, descriptor mutation, reconfiguration or program-failure clear.
 * Diagnostic failure bytes survive success; a later failure rejects this cookie. */
enum hp1020_udc_publish_result hp1020_udc_publish_ack_cleanup(
    struct hp1020_udc_publish *, struct hp1020_tusb_cookie, uint8_t physically_clean);

#endif
