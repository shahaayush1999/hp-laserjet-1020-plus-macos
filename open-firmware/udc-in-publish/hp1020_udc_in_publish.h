/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_IN_PUBLISH_H
#define HP1020_UDC_IN_PUBLISH_H
#include "../udc-in/hp1020_udc_in.h"

/* Logical recording hooks, not a physical backend. Calls and hooks are
 * serialized, immediate and nonreentrant. A successful write/order reports a
 * CPU operation, not peripheral arrival or USB acknowledgement. False may mean
 * an uncertain partial operation; after preflight it always poisons this attempt.
 * ready must include current controller programming and all integration gates
 * (including an OUT publication failure), not merely TinyUSB's mounted flag. */
struct hp1020_udc_in_publish_io {
    bool (*ready)(void *, struct hp1020_tusb_cookie);
    bool (*read32)(void *, uint32_t offset, uint32_t *value);
    bool (*write32)(void *, uint32_t offset, uint32_t value);
    bool (*order)(void *);
    bool (*visible)(void *, struct hp1020_udc_in_span);
    void *context;
};
struct hp1020_udc_in_publish_facts_ext {
    /* Exactly 0/1, valid for this entire call and original cookie. TX idle/empty
     * includes completed prior short/ZLP boundaries. TDC/source release alone
     * does not grant it. CNAK requires the RX-empty safe interval if NAK is set.
     * The register lease excludes concurrent software/hardware changes that
     * would invalidate these reads/RMW commands. No DEVCTL write is performed. */
    uint8_t mode_packet64_be, tx_idle_fifo_empty, mapping_cache_lease;
    uint8_t register_window_stable, cnak_window_safe;
};
enum hp1020_udc_in_publish_result {
    HP1020_IN_PUBLISH_OK, HP1020_IN_PUBLISH_WAIT, HP1020_IN_PUBLISH_STALE,
    HP1020_IN_PUBLISH_INVALID, HP1020_IN_PUBLISH_READ_ERROR, HP1020_IN_PUBLISH_FAULT
};
enum hp1020_udc_in_publish_step {
    HP1020_IN_PACKET_VISIBLE = 1, HP1020_IN_DESCRIPTOR_VISIBLE,
    HP1020_IN_MEMORY_ORDER, HP1020_IN_TAKE, HP1020_IN_DESPTR,
    HP1020_IN_DESPTR_ORDER, HP1020_IN_IRQ_MASK, HP1020_IN_IRQ_ORDER,
    HP1020_IN_CNAK, HP1020_IN_CNAK_ORDER, HP1020_IN_NAK_READ,
    HP1020_IN_POLL, HP1020_IN_POLL_ORDER
};
struct hp1020_udc_in_publish {
    struct hp1020_udc_in *port;
    struct hp1020_udc_in_publish_io io;
    struct hp1020_tusb_cookie failure_cookie;
    uint8_t initialized, busy, failed, failure_step;
};

/* First use only, zeroed stationary state; arguments/objects must not alias. */
enum hp1020_udc_in_publish_result hp1020_udc_in_publish_init(
    struct hp1020_udc_in_publish *, struct hp1020_udc_in *,
    const struct hp1020_udc_in_publish_io *);
/* Called after the real DCD submission returns, never inside TinyUSB. One
 * prepared packet -> cache/order -> local proposal -> DESPTR/unmask/CNAK/POLL.
 * No proposal escapes, no IRQ status is acknowledged, no DMA completion is
 * invented. WAIT/read errors before cache work have no mutating hook calls.
 * Later failures retain all owners and request ordinary adapter cancellation.
 * The integration must block new publication/programming while failed; normal
 * original-cookie cancellation and real reset ingress remain available. */
enum hp1020_udc_in_publish_result hp1020_udc_in_publish_packet(
    struct hp1020_udc_in_publish *, struct hp1020_tusb_cookie,
    struct hp1020_udc_in_publish_facts_ext);
/* Original failure identity, drained DCD/callback/result, and independently
 * supplied completed endpoint cleanup. Never retries writes, grants controller
 * reset promises, or clears a separate programming/OUT publication failure. */
enum hp1020_udc_in_publish_result hp1020_udc_in_publish_clear(
    struct hp1020_udc_in_publish *, struct hp1020_tusb_cookie, uint8_t physically_clean);
#endif
