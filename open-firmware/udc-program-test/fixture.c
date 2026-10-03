/* SPDX-License-Identifier: GPL-2.0-or-later
 * Experimental register-command fixture. One existing RAM-only DCD;
 * explicit read observations and recorded CPU operation intent, no MMIO.
 */
#include "hp1020_udc_program.h"

static uint32_t program_fixture_init(uint32_t);
static uint32_t program_fixture_service(void);
static uint32_t program_fixture_progress(void);
static bool program_fixture_submission_allowed(void);
static bool program_fixture_open(uint8_t, const uint8_t *, uint32_t);
static bool program_fixture_close_all(uint8_t);
static void program_fixture_begin_event(void);
static void program_fixture_snapshot(void);
static void program_fixture_check(void);
static uint32_t program_fixture_step(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);

#define HP1020_COMPOSED_OFFLOAD 1
#define HP1020_COMPOSED_PROGRAM 1
#define HP1020_FIXTURE_ADAPTER_SERVICE(a) program_fixture_service()
#define HP1020_COMPOSED_PROGRESS() program_fixture_progress()
#include "udc-composed-test/fixture.c"

#define PROGRAM_READ_CAPACITY 256u
#define PROGRAM_TRACE_CAPACITY 1024u
#define PROGRAM_ENTRY_SERVICE 1u
#define PROGRAM_ENTRY_OUT_OPEN 2u
#define PROGRAM_ENTRY_IN_OPEN 3u
#define PROGRAM_ENTRY_CLOSE 4u
#define PROGRAM_ENTRY_SELECTION 5u
#define PROGRAM_ENTRY_GRANT 6u
#define PROGRAM_ENTRY_SUBMISSION 7u

/* Explicit word arrays avoid host/target padding and endian dependencies.
 * The public symbols begin with16 guard bytes. No pointer lives in a capture. */
struct program_read_storage {
    uint32_t before[4], words[PROGRAM_READ_CAPACITY][3], after[4];
};
struct program_trace_storage {
    uint32_t before[4], words[PROGRAM_TRACE_CAPACITY][6], after[4];
};
struct program_read_storage hp1020_program_fixture_reads;
struct program_trace_storage hp1020_program_fixture_trace;
uint32_t hp1020_program_fixture_stats[64];
_Static_assert(sizeof(struct program_read_storage) == 3104, "read capture layout");
_Static_assert(sizeof(struct program_trace_storage) == 24608, "trace capture layout");
static uint32_t program_read_shadow[PROGRAM_READ_CAPACITY][3];
static uint32_t program_trace_shadow[PROGRAM_TRACE_CAPACITY][6];
static struct hp1020_udc_program program;
static struct {
    uint32_t event, result, violations, queued, cursor, trace_count;
    uint32_t reads, writes, orders, injection_kind, injection_ordinal, injection_result;
    uint32_t last_submission, submission_checks, query_result, failure_entries, failure_kind;
    struct hp1020_tusb_programming_ticket failure_entry;
    struct hp1020_udc_program_failure query;
    uint8_t facts[7], grant_facts[5], injection_armed, initialized;
} program_state;

static void program_violation(void) {
    program_state.violations++;
    state.violations++;
}
static uint32_t program_fill_word(void) { return (state.fill & 255u) * UINT32_C(0x01010101); }
static int program_guards(void) {
    const uint32_t fill = program_fill_word();
    for (uint32_t i = 0; i < 4; ++i)
        if (hp1020_program_fixture_reads.before[i] != fill ||
            hp1020_program_fixture_reads.after[i] != fill ||
            hp1020_program_fixture_trace.before[i] != fill ||
            hp1020_program_fixture_trace.after[i] != fill) return 0;
    return 1;
}
static void program_fixture_check(void) {
    if (!program_state.initialized) return;
    if (!program_guards() || program_state.queued > PROGRAM_READ_CAPACITY ||
        program_state.cursor > program_state.queued ||
        program_state.trace_count > PROGRAM_TRACE_CAPACITY ||
        memcmp(hp1020_program_fixture_reads.words, program_read_shadow,
            sizeof(program_read_shadow)) ||
        memcmp(hp1020_program_fixture_trace.words, program_trace_shadow,
            sizeof(program_trace_shadow))) program_violation();
}
static struct hp1020_tusb_programming_ticket program_entry_ticket(void) {
    /* Independently read identities already allocated at actual API entry.
     * Never reconstruct these from the backend's resulting failure object. */
    const struct hp1020_tusb_programming_ticket t = {
        adapter.active_offload.sequence, adapter.active_control_epoch, adapter.transport_epoch};
    return t;
}
struct program_call_entry {
    struct hp1020_tusb_programming_ticket ticket;
    uint32_t witness_count, kind;
    uint8_t was_failed;
};
static struct program_call_entry program_call_begin(uint32_t kind) {
    const struct program_call_entry before = {
        program_entry_ticket(), program_state.failure_entries, kind, program.failed};
    return before;
}
static uint32_t program_call_end(struct program_call_entry before, uint32_t result) {
    if (!before.was_failed && program.failed &&
        before.witness_count == program_state.failure_entries) {
        /* Nested actual DCD callbacks win over their enclosing service call. */
        program_state.failure_entry = before.ticket;
        program_state.failure_kind = before.kind;
        program_state.failure_entries++;
        offload_state.failure = before.ticket;
        offload_state.dirty = 1;
    }
    program_state.result = result;
    program_fixture_check();
    return result;
}
static struct hp1020_udc_program_facts program_facts(void) {
    const uint8_t *f = program_state.facts;
    const struct hp1020_udc_program_facts facts = {f[0],f[1],f[2],f[3],f[4],f[5],f[6]};
    return facts;
}

/* One absolute all-hook ordinal. Read failures come from their own immutable
 * observation; a schedule that accidentally points at a read is a harness bug. */
static uint32_t program_injected_result(uint32_t kind, uint32_t fallback) {
    if (!program_state.injection_armed) return fallback;
    const uint32_t ordinal = program_state.trace_count + 1u;
    if (ordinal < program_state.injection_ordinal) return fallback;
    program_state.injection_armed = 0;
    if (ordinal != program_state.injection_ordinal || kind != program_state.injection_kind) {
        program_violation(); return HP1020_UDC_PROGRAM_IO_UNKNOWN;
    }
    return program_state.injection_result;
}
static uint32_t program_record(uint32_t kind, uint32_t offset, uint32_t value, uint32_t result) {
    if (program_state.trace_count >= PROGRAM_TRACE_CAPACITY) {
        program_violation(); return HP1020_UDC_PROGRAM_IO_UNKNOWN;
    }
    const uint32_t record[6] = {program_state.event, program_state.trace_count + 1u,
        kind, offset, value, result};
    memcpy(hp1020_program_fixture_trace.words[program_state.trace_count], record, sizeof(record));
    memcpy(program_trace_shadow[program_state.trace_count], record, sizeof(record));
    program_state.trace_count++;
    return result;
}
static enum hp1020_udc_program_io_result program_read32(void *context, uint32_t offset,
    uint32_t *value) {
    uint32_t result = HP1020_UDC_PROGRAM_IO_UNKNOWN, observed = 0;
    program_state.reads++;
    if (context != &program_state || !value || program_state.cursor >= program_state.queued) {
        program_violation();
    } else {
        const uint32_t *item = hp1020_program_fixture_reads.words[program_state.cursor++];
        if (item[0] != offset || item[2] > HP1020_UDC_PROGRAM_IO_UNKNOWN)
            program_violation();
        else { result = item[2]; if (result == HP1020_UDC_PROGRAM_IO_OK) observed = item[1]; }
    }
    result = program_injected_result(1, result);
    if (result != HP1020_UDC_PROGRAM_IO_OK) observed = 0;
    result = program_record(1, offset, observed, result);
    if (result == HP1020_UDC_PROGRAM_IO_OK) *value = observed;
    /* On failure the supplied output object remains untouched. */
    return (enum hp1020_udc_program_io_result)result;
}
static enum hp1020_udc_program_io_result program_write32(void *context, uint32_t offset,
    uint32_t value) {
    uint32_t result = HP1020_UDC_PROGRAM_IO_OK;
    program_state.writes++;
    if (context != &program_state) { program_violation(); result = HP1020_UDC_PROGRAM_IO_UNKNOWN; }
    result = program_injected_result(2, result);
    return (enum hp1020_udc_program_io_result)program_record(2, offset, value, result);
}
static enum hp1020_udc_program_io_result program_order(void *context) {
    uint32_t result = HP1020_UDC_PROGRAM_IO_OK;
    program_state.orders++;
    if (context != &program_state) { program_violation(); result = HP1020_UDC_PROGRAM_IO_UNKNOWN; }
    result = program_injected_result(3, result);
    return (enum hp1020_udc_program_io_result)program_record(3, UINT32_MAX, 0, result);
}

static uint32_t program_fixture_init(uint32_t fill) {
    memset(&program_state, 0, sizeof(program_state));
    memset(&program, 0, sizeof(program));
    memset(&hp1020_program_fixture_reads, (int)(fill & 255u), sizeof(hp1020_program_fixture_reads));
    memset(&hp1020_program_fixture_trace, (int)(fill & 255u), sizeof(hp1020_program_fixture_trace));
    memset(program_read_shadow, (int)(fill & 255u), sizeof(program_read_shadow));
    memset(program_trace_shadow, (int)(fill & 255u), sizeof(program_trace_shadow));
    memset(&program_state.query, 0xa7, sizeof(program_state.query));
    memset(program_state.facts, 1, sizeof(program_state.facts));
    program_state.query_result = program_state.last_submission = UINT32_MAX;
    program_state.initialized = 1;
    const struct hp1020_udc_program_io io = {
        program_read32, program_write32, program_order, &program_state};
    const struct hp1020_udc_program_layout layout = {UINT32_C(0x508), UINT32_C(0x50c), 64};
    const struct hp1020_udc_program_init_facts facts = {1,1,1};
    program_state.result = (uint32_t)hp1020_udc_program_init(&program, &composed_setup,
        &io, layout, facts);
#ifdef HP1020_COMPOSED_PUBLISH
    if (!program_state.result) program_state.result = publish_fixture_init(fill);
#endif
    return program_state.result;
}
static uint32_t program_fixture_service(void) {
    const struct program_call_entry before = program_call_begin(PROGRAM_ENTRY_SERVICE);
#ifdef HP1020_COMPOSED_PUBLISH
    return program_call_end(before, publish_fixture_service());
#else
    return program_call_end(before, (uint32_t)hp1020_udc_program_service(&program));
#endif
}
static uint32_t program_fixture_progress(void) {
#ifdef HP1020_COMPOSED_PUBLISH
    return publish_fixture_progress();
#else
    return hp1020_udc_program_progress(&program);
#endif
}
static bool program_fixture_submission_allowed(void) {
    const struct program_call_entry before = program_call_begin(PROGRAM_ENTRY_SUBMISSION);
    program_state.submission_checks++;
#ifdef HP1020_COMPOSED_PUBLISH
    const bool allowed = publish_fixture_submission_allowed();
#else
    const bool allowed = hp1020_udc_program_submission_allowed(&program);
#endif
    program_state.last_submission = allowed ? 1u : 0u;
    (void)program_call_end(before, program.failed ? HP1020_UDC_PROGRAM_FAULT :
        allowed ? HP1020_UDC_PROGRAM_OK : HP1020_UDC_PROGRAM_WAIT);
    return allowed;
}
static bool program_fixture_open(uint8_t rhport, const uint8_t *descriptor, uint32_t length) {
    const struct program_call_entry before = program_call_begin(
        descriptor[2] == 1 ? PROGRAM_ENTRY_OUT_OPEN : PROGRAM_ENTRY_IN_OPEN);
    const uint32_t r = program_call_end(before, (uint32_t)hp1020_udc_program_open(
        &program, rhport, descriptor, length, program_facts()));
    if (r != HP1020_UDC_PROGRAM_OK && !offload_state.dirty) {
        /* Independently record an actual false open, even if a future backend
         * accidentally fails to retain its own programming failure. */
        offload_state.failure = before.ticket; offload_state.dirty = 1;
    }
    return r == HP1020_UDC_PROGRAM_OK;
}
static bool program_fixture_close_all(uint8_t rhport) {
    const struct program_call_entry before = program_call_begin(PROGRAM_ENTRY_CLOSE);
    return program_call_end(before, (uint32_t)hp1020_udc_program_close_all(
        &program, rhport, program_facts())) == HP1020_UDC_PROGRAM_OK;
}
static void program_fixture_begin_event(void) {
    program_fixture_check();
    if (program_state.event == UINT32_MAX) program_violation();
    else program_state.event++;
}

static uint32_t program_fixture_step(uint32_t op, uint32_t a, uint32_t b,
    uint32_t c, uint32_t d) {
    uint32_t r = HP1020_UDC_PROGRAM_INVALID;
    program_fixture_check();
#ifdef HP1020_COMPOSED_PUBLISH
    /* Selection must remain callable while its existing programming barrier
     * awaits completion; a publication failure cannot be bypassed that way. */
    if ((op == 123 || op == 124) && !publish_fixture_program_allowed()) {
        program_state.result = HP1020_UDC_PROGRAM_WAIT;
        return HP1020_UDC_PROGRAM_WAIT;
    }
#endif
    if (op == 120 && !b && !c && !d && a <= sizeof(hp1020_bulk_fixture_input)/12u &&
        a <= PROGRAM_READ_CAPACITY - program_state.queued) {
        bool valid = true;
        for (uint32_t i = 0; i < a; ++i)
            if (ep0_be32(hp1020_bulk_fixture_input + 12*i + 8) > 2) valid = false;
        if (valid) {
            for (uint32_t i = 0; i < a; ++i) for (uint32_t j = 0; j < 3; ++j) {
                const uint32_t value = ep0_be32(hp1020_bulk_fixture_input + 12*i + 4*j);
                hp1020_program_fixture_reads.words[program_state.queued+i][j] = value;
                program_read_shadow[program_state.queued+i][j] = value;
            }
            program_state.queued += a; r = HP1020_UDC_PROGRAM_OK;
        }
    } else if (op == 121 && (a == 2 || a == 3) && b > program_state.trace_count &&
        b <= PROGRAM_TRACE_CAPACITY && (c == 1 || c == 2) && !d) {
        if (program_state.injection_armed) r = HP1020_UDC_PROGRAM_WAIT;
        else {
            program_state.injection_kind = a; program_state.injection_ordinal = b;
            program_state.injection_result = c; program_state.injection_armed = 1;
            r = HP1020_UDC_PROGRAM_OK;
        }
    } else if (op == 122 && !a && !b && !c && !d) {
        memcpy(program_state.facts, hp1020_bulk_fixture_input, 7);
        r = HP1020_UDC_PROGRAM_OK; /* Raw byte values, including malformed2. */
    } else if (op == 123 && !a && !b && !c && !d) {
        const struct program_call_entry before = program_call_begin(PROGRAM_ENTRY_SELECTION);
        r = program_call_end(before, (uint32_t)hp1020_udc_program_complete_selection(
            &program, program_facts()));
    } else if (op == 124 && c <= 5 && !d) {
        struct hp1020_tusb_cookie cookie;
        memcpy(program_state.grant_facts, hp1020_bulk_fixture_input, 5);
        if (ep0_history(b, &cookie)) {
            cookie = ep0_mutate(cookie, c);
            const uint8_t *f = program_state.grant_facts;
            const struct hp1020_udc_program_grant_facts facts = {f[0],f[1],f[2],f[3],f[4]};
            const struct hp1020_tusb_offload original = offload_state.original;
            const struct hp1020_tusb_cookie original_cookie = offload_state.cookie;
            const uint8_t was_granted = adapter.owners[1].auto_granted;
            const struct program_call_entry before = program_call_begin(PROGRAM_ENTRY_GRANT);
            offload_state.grant_facts = ((uint32_t)f[2] << 8) | f[3];
            r = program_call_end(before, (uint32_t)hp1020_udc_program_grant(&program,a,cookie,facts));
            /* Observe actual ownership transition even on a later I/O FAULT.
             * This is permission consumption, never USB status completion. */
            if (!was_granted && adapter.owners[1].auto_granted) {
                if (!offload_state.live || offload_state.granted ||
                    adapter.owners[1].state != HP1020_TUSB_OWNER_DCD ||
                    !same_cookie(adapter.owners[1].cookie, original_cookie) ||
                    !same_cookie(cookie, original_cookie) || a != original.sequence)
                    program_violation();
                offload_state.grant.original = original;
                offload_state.grant.cookie = original_cookie;
                offload_state.granted = 1; offload_state.grants++;
            } else if (r == HP1020_UDC_PROGRAM_OK) program_violation();
            offload_state.result = r;
        }
    } else if (op == 125 && !a && !b && !c && !d) {
        uint8_t previous[sizeof(program_state.query)];
        memcpy(previous, &program_state.query, sizeof(previous));
        r = (uint32_t)hp1020_udc_program_pending_cleanup(&program, &program_state.query);
        if (r != HP1020_UDC_PROGRAM_OK && memcmp(previous, &program_state.query, sizeof(previous)))
            program_violation();
        program_state.query_result = r;
    } else if (op == 126 && d <= 255) {
        const struct hp1020_tusb_programming_ticket original = {a,b,c};
        r = (uint32_t)hp1020_udc_program_ack_cleanup(&program, original, (uint8_t)d);
        if (r == HP1020_UDC_PROGRAM_OK) {
            if (d != 1 || owned_mask() || adapter.owners[0].state || adapter.owners[1].state ||
                adapter.owners[2].state || adapter.prepared || adapter.delivering_live ||
                adapter.response_owned || !offload_state.dirty ||
                a != offload_state.failure.sequence || b != offload_state.failure.control_epoch ||
                c != offload_state.failure.transport_epoch) program_violation();
            /* Independently SUPPLIED cleanup permits these synthetic bookkeeping
             * changes. No read/write hook or fictitious physical reset occurs. */
            state.open_mask &= 3u; state.stall_mask &= 3u;
            offload_state.programmed_mask &= 3u; offload_state.dirty = 0;
            offload_state.cleanups++; offload_state.last_cleanup_sequence = a;
        }
        offload_state.result = r;
    }
    program_state.result = r;
    program_fixture_check();
    return r;
}
static void program_failure_words(uint32_t *out, const struct hp1020_udc_program_failure *f) {
    out[0]=f->ticket.sequence; out[1]=f->ticket.control_epoch; out[2]=f->ticket.transport_epoch;
    out[3]=f->offset; out[4]=f->attempted_value; out[5]=f->operation;
    out[6]=f->io_result; out[7]=f->grant_consumed;
}
static void program_fixture_snapshot(void) {
    uint32_t *o = hp1020_program_fixture_stats;
    memset(o, 0, sizeof(hp1020_program_fixture_stats));
    o[0]=program_state.result; o[1]=program.initialized; o[2]=program.busy; o[3]=program.servicing;
    o[4]=program.failed; o[5]=program.completed_mask; o[6]=program.selection_mask; o[7]=program.binding_ready;
    o[8]=hp1020_udc_program_progress(&program); o[9]=program_state.last_submission;
    o[10]=program.selection.sequence; o[11]=program.selection.control_epoch;
    o[12]=program.selection.transport_epoch; o[13]=program.service_control_epoch;
    o[14]=(uint32_t)program.last_adapter_result; o[15]=(uint32_t)program.last_bridge_result;
    o[16]=program.failure.ticket.sequence; o[17]=program.failure.ticket.control_epoch;
    o[18]=program.failure.ticket.transport_epoch; o[19]=program.failure.operation;
    o[20]=program.failure.offset; o[21]=program.failure.attempted_value;
    o[22]=program.failure.io_result; o[23]=program.failure.grant_consumed;
    o[24]=program_state.queued; o[25]=program_state.cursor; o[26]=program_state.trace_count;
    o[27]=program_state.reads; o[28]=program_state.writes; o[29]=program_state.orders;
    o[30]=(uint32_t)program_guards(); o[31]=program_state.violations;
    o[32]=program_state.injection_kind; o[33]=program_state.injection_ordinal;
    o[34]=program_state.injection_result; o[35]=program_state.injection_armed;
    for (uint32_t i=0;i<7;++i) o[36+i]=program_state.facts[i];
    for (uint32_t i=0;i<5;++i) o[43+i]=program_state.grant_facts[i];
    program_failure_words(o+48,&program_state.query); o[56]=program_state.query_result;
    o[57]=(uint32_t)sizeof(program); o[58]=program_state.failure_entry.sequence;
    o[59]=program_state.failure_entry.control_epoch; o[60]=program_state.failure_entry.transport_epoch;
    o[61]=program_state.failure_kind; o[62]=program_state.failure_entries;
    o[63]=program_state.submission_checks;
#ifdef HP1020_COMPOSED_PUBLISH
    publish_fixture_snapshot();
#endif
}

/* The host codec serializes every word explicitly. The target reader can use
 * the two public symbols directly: data begins at+16; lengths are stats24/26. */
const void *hp1020_program_fixture_read_words(void) {
    return &hp1020_program_fixture_reads.words;
}
const void *hp1020_program_fixture_trace_words(void) {
    return &hp1020_program_fixture_trace.words;
}
const void *hp1020_program_fixture_read_storage_words(void) {
    return &hp1020_program_fixture_reads;
}
const void *hp1020_program_fixture_trace_storage_words(void) {
    return &hp1020_program_fixture_trace;
}
uint32_t hp1020_program_fixture_component_bytes(void) { return (uint32_t)sizeof(program); }
