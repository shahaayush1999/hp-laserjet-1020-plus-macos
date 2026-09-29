/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_USB_RECEIVE_H
#define HP1020_USB_RECEIVE_H
#include <stdint.h>

#define HP1020_RX_SLOTS 4u
#define HP1020_RX_CAPACITY 1024u
enum hp1020_rx_result {
    HP1020_RX_OK, HP1020_RX_WAIT, HP1020_RX_STALE, HP1020_RX_STOPPED,
    HP1020_RX_ORDER, HP1020_RX_LIMIT, HP1020_RX_STATUS, HP1020_RX_ENDPOINT,
    HP1020_RX_PAYLOAD
};
struct hp1020_rx_ticket { uint32_t generation, sequence; };
struct hp1020_rx_slot { uint32_t sequence, capacity, length, ready; };
struct hp1020_rx_memory { _Alignas(16) uint8_t data[HP1020_RX_SLOTS][HP1020_RX_CAPACITY]; };
struct hp1020_usb_receive {
    struct hp1020_rx_memory *memory;
    struct hp1020_rx_slot slots[HP1020_RX_SLOTS];
    uint32_t generation, issued, consumed, count;
    enum hp1020_rx_result error;
    uint8_t stopped, quiescent;
};
struct hp1020_rx_view {
    struct hp1020_rx_ticket ticket;
    const uint8_t *data;
    uint32_t length;
};

/* Single serialized context, stationary nonoverlapping objects. Init is for
 * first use only. IRQs must be marshalled by a future controller adapter.
 * No register access, descriptors, cache maintenance or actual DMA is supplied.
 * Reserve gives an external transport exclusive write ownership until clean
 * completion. A full queue applies backpressure without changing any storage.
 * Tickets never wrap; a consumed/stale ticket cannot affect another transfer. */
enum hp1020_rx_result hp1020_usb_receive_init(struct hp1020_usb_receive *, struct hp1020_rx_memory *);
enum hp1020_rx_result hp1020_usb_receive_reserve(struct hp1020_usb_receive *, uint32_t capacity,
    struct hp1020_rx_ticket *, uint8_t **buffer);

/* The adapter must establish an immutable CPU-visible status/data snapshot and
 * report endpoint errors (including BNA/HE) independently. Any nonzero fault
 * fences the stream. Owner 2 comes from stock execution; RX==0, L==1 and bounded
 * count are our conservative single-descriptor software profile, not proof of
 * successful HP transfers. Other owners mean WAIT, never permission to reuse.
 * Zero count is a consumed empty transfer, not end-of-document or end-of-input.
 * A recognized but invalid completion stops without releasing any buffer. */
enum hp1020_rx_result hp1020_usb_receive_complete(struct hp1020_usb_receive *,
    struct hp1020_rx_ticket, uint32_t descriptor_status, uint32_t endpoint_fault);
/* Normalized successful transport completion, without stock descriptor bits.
 * The caller promises this exact reservation's transfer ended, all its writes
 * are CPU-visible and length is the actual data count. Report transport faults
 * independently before pumping any READY data. This is not an all-generation
 * quiescence promise and does not settle late callbacks. Zero length is a
 * consumed empty transfer, never EOF. Stale/stopped/size checks are shared with
 * the raw descriptor-policy wrapper; invalid recognized counts keep ownership. */
enum hp1020_rx_result hp1020_usb_receive_complete_data(struct hp1020_usb_receive *,
    struct hp1020_rx_ticket, uint32_t length);
/* Endpoint-wide events need no live ticket. Report them before consuming any
 * queued data, even when the queue is empty or the descriptor is already ready.
 * Old-generation events are stale; any current nonzero fault fences the stream. */
enum hp1020_rx_result hp1020_usb_receive_fault(struct hp1020_usb_receive *,uint32_t generation,uint32_t fault);
enum hp1020_rx_result hp1020_usb_receive_peek(const struct hp1020_usb_receive *, struct hp1020_rx_view *);
enum hp1020_rx_result hp1020_usb_receive_release(struct hp1020_usb_receive *, struct hp1020_rx_ticket);
void hp1020_usb_receive_stop(struct hp1020_usb_receive *);

/* Stop fences all new reservations and consumption but preserves memory.
 * Quiesced is an assertion supplied by the external adapter: old writes and
 * callbacks can no longer touch this storage. It is not inferred from owner
 * bits, an empty queue, reset or a timeout. Restart requires that assertion and
 * advances generation before any reuse. The caller must also quiesce consumers. */
enum hp1020_rx_result hp1020_usb_receive_quiesced(struct hp1020_usb_receive *, uint32_t generation);
enum hp1020_rx_result hp1020_usb_receive_restart(struct hp1020_usb_receive *);
#endif
