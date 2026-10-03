/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_UDC_ACQUIRE_H
#define HP1020_UDC_ACQUIRE_H

#include "hp1020_udc_out.h"

/* UNEXECUTED draft. Synchronous CPU acquisition of one already retained OUT1
 * packet. No IRQ/event producer, physical mapping/cache binding, owner, queue,
 * descriptor policy, cancellation implementation or recovery promise is added.
 * All objects/arguments/hooks are stationary, serialized and nonreentrant.
 * Hooks may not invoke the adapter/TinyUSB, admit ingress, change mappings,
 * rebuild memory, defer effects or release ownership. */

/* Same meanings/numeric policy as the recording-program I/O results, kept
 * independent of that higher layer so historical OUT-only builds stay usable.
 * OK guarantees only the documented CPU operation. No return proves physical
 * settlement. A malformed result is also a retained acquisition failure. */
enum hp1020_udc_acquire_io_result {
    HP1020_UDC_ACQUIRE_IO_OK = 0,
    HP1020_UDC_ACQUIRE_IO_NOT_PERFORMED,
    HP1020_UDC_ACQUIRE_IO_UNKNOWN
};

struct hp1020_udc_acquire_hooks {
    /* After-device phase of the retained BIDIRECTIONAL descriptor mapping.
     * The span is exactly16 bytes, never an alternate snapshot/address. */
    enum hp1020_udc_acquire_io_result (*descriptor_for_cpu)(void *,
        struct hp1020_tusb_cookie, struct hp1020_udc_out_span);
    /* After-device phase of the retained DEVICE-WRITE receive mapping.
     * Exactly its owned64-byte prefix, independent of the eventual count. */
    enum hp1020_udc_acquire_io_result (*payload_for_cpu)(void *,
        struct hp1020_tusb_cookie, struct hp1020_udc_out_span);
    /* Complete required maintenance and acquire ordering before CPU loads.
     * A release-only register barrier does not satisfy this contract. */
    enum hp1020_udc_acquire_io_result (*acquire_order)(void *,
        struct hp1020_tusb_cookie);
    void *context;
};

/* Exactly0/1. Missing prerequisites WAIT before any cache hook or data load.
 * transfer_settled: original descriptor/payload accesses have finished and
 *   cannot recur; pending observations still carry their original identities.
 * mapping_lease: original CPU/DMA pairs remain valid, exclusive and stable;
 *   no actor can rebuild/rearm/modify these bytes through the acquisition.
 * cache_range_safe: real maintenance or justified coherent capability, safe
 *   nonwrapping rounding and exclusively owned whole-line envelopes.16-byte
 *   alignment alone does not establish larger-line/alias safety.
 * These are not RECEIVE/TRANSPORT/OUTPUT promises or endpoint-default proof. */
struct hp1020_udc_acquire_facts {
    uint8_t transfer_settled, mapping_lease, cache_range_safe;
};

#define HP1020_UDC_ACQUIRE_REASON_IO UINT32_C(0x80000103)

enum hp1020_udc_acquire_operation {
    HP1020_UDC_ACQUIRE_NONE = 0, HP1020_UDC_ACQUIRE_DESCRIPTOR,
    HP1020_UDC_ACQUIRE_PAYLOAD, HP1020_UDC_ACQUIRE_ORDER
};
enum hp1020_udc_acquire_prefix {
    HP1020_UDC_ACQUIRE_DESCRIPTOR_READY = 1u,
    HP1020_UDC_ACQUIRE_PAYLOAD_READY = 2u,
    HP1020_UDC_ACQUIRE_ORDERED = 4u,
    HP1020_UDC_ACQUIRE_SNAPSHOT_COPIED = 8u
};

/* Evidence only. prefix records successful SOFTWARE operations, not physical
 * completion. dma/bytes describe the most recently attempted range (zero for
 * order). io_result preserves the raw returned value, including malformed
 * values. snapshot is valid only when snapshot_valid==1. A fault-only call
 * contains no fabricated descriptor. Serialize named fields, not C padding. */
struct hp1020_udc_acquire_diagnostic {
    struct hp1020_tusb_cookie cookie;
    uint32_t prefix, dma, bytes, io_result, reason;
    enum hp1020_udc_out_result result;
    uint8_t operation, snapshot_valid;
    uint8_t snapshot[HP1020_UDC_OUT_DESCRIPTOR_BYTES];
};

/* Fixed configuration and diagnostics only; no ownership/admission state.
 * OUT's existing busy/fault/cookie/phase remain authoritative. First failure
 * survives retries, cancellation and reset; a failure of a genuinely later
 * retained cookie may replace it. Successful later calls do not erase it.
 * All fields are read-only to callers after init. */
struct hp1020_udc_acquire {
    struct hp1020_udc_out *out;
    struct hp1020_udc_acquire_hooks hooks;
    struct hp1020_udc_acquire_diagnostic last, first_failure;
    uint8_t initialized, failure_valid;
};

/* Context MUST be zero-initialized stationary storage. First use only, before
 * the adapter's first control epoch/submission; OUT must be FREE/unfaulted and
 * adapter in-flight preparation/owner/response state empty. Receive accounting
 * is untouched; the caller supplies document lifetime/initialization conditions.
 * Every later init rejects,
 * including after retirement/reset. Never zero/reinitialize a context to clear
 * fault evidence or use init as recovery. Inputs/context must not alias each
 * other or any OUT/adapter/document/receive/descriptor/payload allocation. */
enum hp1020_udc_out_result hp1020_udc_acquire_init(struct hp1020_udc_acquire *,
    struct hp1020_udc_out *, const struct hp1020_udc_acquire_hooks *);

/* Only after the initiating callback unwinds. Match the exact retained OUT
 * cookie AND adapter DCD owner before hooks. FREE/PENDING/stale are STALE;
 * normal PREPARED is INVALID; active/reentrant calls WAIT. No current epoch or
 * mounted/progress7 requirement: original settlement must remain possible
 * while newer ingress or a previous programming/publication failure blocks
 * ordinary progress. Such acceptance never clears those failures.
 *
 * Known/local fault -> existing fault path, no hooks/snapshot. Normal path:
 * descriptor16 -> payload64 -> acquire-order -> real descriptor copy -> same
 * locked observe policy as the historical API. No supplied visibility flags
 * or descriptor bytes. Hooks fail -> latch REASON_IO and existing cancellation
 * before returning; retries only deliver that fault, never retry cache work.
 * WAIT/ADAPTER_ERROR from fault reporting must be resolved before normal
 * service/pump. Exact-cookie cancellation remains independently available.
 *
 * Ordinary missing-fact/busy/not-DONE WAIT may retry the WHOLE acquisition with
 * a fresh lease. Success retires only OUT transport ownership; adapter stays
 * PENDING. This function never services/pumps, rearms or supplies reset facts.
 * Stale/invalid/prerequisite/busy refusals leave context diagnostics unchanged. */
enum hp1020_udc_out_result hp1020_udc_acquire_packet(struct hp1020_udc_acquire *,
    struct hp1020_tusb_cookie, uint32_t endpoint_fault,
    struct hp1020_udc_acquire_facts);

#endif
