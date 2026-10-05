/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_PJL_COMMAND_H
#define HP1020_PJL_COMMAND_H
#include "hp1020_tusb_adapter.h"

/* Bounded uppercase ECHO/INFO STATUS. One reply is always a short USB packet.
 * ECHO permits at most50 printable text bytes. No job/page status is generated. */
#define HP1020_PJL_LINE_BYTES 60u
struct hp1020_pjl_status {
    uint32_t epoch,generation,code;
    uint8_t online;
};
/* Return a current, coherent observation for this binding, or false when it is
 * unavailable. Fill every field; online is 0 or 1 and code is 0..99999. Negative
 * or wrapped stock arithmetic is outside this wire profile. This is a read-only,
 * nonreentrant callback: it must not service/mutate the adapter or pump input.
 * Physical observation, expiry and conversion to a PJL code belong to the
 * provider. Decoding a page, USB mount or an empty queue is not ready/completed
 * printer evidence. The pump checks identity, but cannot verify sensor truth. */
typedef bool (*hp1020_pjl_status_read_fn)(void *,uint32_t,uint32_t,
    struct hp1020_pjl_status *);
struct hp1020_pjl_command {
    struct hp1020_tusb_adapter *adapter;
    hp1020_pjl_status_read_fn read_status;
    void *status_context;
    struct hp1020_rx_ticket input;
    struct hp1020_tusb_cookie in_cookie;
    uint32_t epoch,generation,offset;
    uint8_t line[HP1020_PJL_LINE_BYTES],reply[HP1020_PJL_LINE_BYTES+3];
    uint8_t line_used,line_invalid,line_overflow,uel_match,reply_length;
    uint8_t initialized,busy,have_input,queued,inflight,terminal;
    enum hp1020_tusb_result last_send;
};
/* One stationary caller-owned instance, first use only, nonaliasing storage.
 * Takes exclusive ownership of bulk-IN submission/result collection and the
 * document's input pump. Do not also call the ordinary adapter/document pump.
 * Control service, OUT admission, original-cookie completion and printer reset
 * remain with their existing APIs and controller gates. This layer supplies no
 * controller facts and cannot clear their failures. */
enum hp1020_rx_result hp1020_pjl_command_init(struct hp1020_pjl_command *,
    struct hp1020_tusb_adapter *,hp1020_pjl_status_read_fn,void *);
/* Serialized and nonreentrant, outside adapter/DCD callbacks. Output/document
 * callbacks must obey their existing no-reentry contracts. Retains an original
 * receive-ticket cursor when a second ECHO waits for the first reply's storage.
 * Binary spans go through the existing decoder, never the command lexer.
 * Reset discards partial commands/unsent replies, but cannot erase a borrowed
 * reply until its original result is collected. A short OUT/ZLP is not EOF.
 * This continuous pump does not finalize a command-only query as a document.
 * Missing/unavailable/stale status consumes INFO STATUS without a reply, so a
 * query cannot indefinitely block pages. Reply bytes are a snapshot taken when
 * storage becomes available; later status changes cannot mutate borrowed data.
 * DISPLAY is empty in this profile, as in the original local initial buffer. */
enum hp1020_rx_result hp1020_pjl_command_pump(struct hp1020_pjl_command *);
/* Recovery-only collection is also allowed when controller gates prohibit
 * pumping. Synchronizes the binding and collects only this command's original
 * IN result, if available. Never consumes input, calls a status provider or
 * submits another reply. OK may mean no result was available yet; inflight
 * remains set until the actual matching result is collected. */
enum hp1020_rx_result hp1020_pjl_command_reap(struct hp1020_pjl_command *);
#endif
