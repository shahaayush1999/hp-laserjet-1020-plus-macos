/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_PJL_COMMAND_H
#define HP1020_PJL_COMMAND_H
#include "hp1020_tusb_adapter.h"

/* First bounded PJL profile: uppercase @PJL ECHO plus printable ASCII text,
 * at most50 text bytes. Replies end CR/LF/FF and are always short USB packets.
 * Other PJL lines are ignored; no physical/job/page status is fabricated. */
#define HP1020_PJL_LINE_BYTES 60u
struct hp1020_pjl_command {
    struct hp1020_tusb_adapter *adapter;
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
    struct hp1020_tusb_adapter *);
/* Serialized and nonreentrant, outside adapter/DCD callbacks. Output/document
 * callbacks must obey their existing no-reentry contracts. Retains an original
 * receive-ticket cursor when a second ECHO waits for the first reply's storage.
 * Binary spans go through the existing decoder, never the command lexer.
 * Reset discards partial commands/unsent replies, but cannot erase a borrowed
 * reply until its original result is collected. A short OUT/ZLP is not EOF.
 * This continuous pump does not finalize a command-only query as a document. */
enum hp1020_rx_result hp1020_pjl_command_pump(struct hp1020_pjl_command *);
#endif
