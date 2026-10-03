# Separate entry-USB reset profile: public amendment

2026-10-03. **Unexecuted public header/layout proposal only.** No new runtime,
provider or layout C is supplied; no compiler, import, parser, audit, validator,
Machine/QEMU or hardware operation was run. The current entry-usb-test profile,
its contract, sources and accepted evidence are unchanged. Root must approve this
amendment and the independent author must freeze its matching addendum before C.

The proposed sibling directory is `open-firmware/entry-usb-reset-test/`. Retain
the three existing C basenames, `hp1020_usb_runtime_contract.h`, all exported
runtime/object names and the existing startup/linker section names. It builds a
separate ELF/report/capture with public version2. This lets unchanged production
code and strict helpers be reused without treating a new schedule as old evidence.

`inputs/reset-plan.md` supplies the proposed sequence. This amendment closes its
provider/storage questions and incorporates independent pre-implementation source
review: reset admission leaves receive.error=HP1020_RX_ENDPOINT(7) until restart;
after the actual class status completes, current/last/class request IDs remain1,
current_action is ACK4 and current_issued remains1, while response ownership is
gone. Those historical values are not pending ownership or permission to ACK again.

## Fixed scope and memory

One canonical SOFT_RESET during one partial document; one original late successful
completion; one new document; one inert stale acquisition and one inert stale
cancellation request at exact buffer reuse. Two ordinary CPU cases use the old
ordinary-privilege seed and paints `(a5,5a)` and `(cc,96)` from the preserved CPU
oracle. All32 physical AR seeds remain `8a000001 + i*00010101`, i=0..31; no dirty
CPU cross-product is added. The startup still independently normalizes state and
uses its own stack. This is not a reset/fault/malformed-request matrix.

All production objects/APIs and full capacities remain unchanged. Fixed spans
remain document13496 at10010000, memory114704 at10016800, mailbox1024 at10016060,
sentinel256 at10016500, witness9216 at10032830 and stack8192 at10014020..10016020.
Generic BSS must still end no later than10013fe0; code/rodata cap remains53216
bytes at10003000..1000ffe0; initialized data remains within96 bytes at100164a0.
Witness cap remains10176 and provider cap384. No old accepted stack bound is a
substitute for reviewing the newly emitted call graph/frames. Actual BSS extent
comes from the new ELF, not an assumed old extent plus20.

Only two types change: provider204→224 and witness members within its existing
9216. The same16 stationary object IDs remain; no new mutable global or owner
queue is added. The extra immutable reset record consumes16 ordinary rodata bytes.
Startup still clears the actual four zero spans, preserving all loaded data,
sentinel, stack and gaps. C still scans the whole four spans and sentinel/data
before any initializer or mailbox write. Every custom NOLOAD initializer remains
zero-only and must be independently checked in retained input objects.

## Retained original identity and cancellation

Append `struct hp1020_tusb_cookie reset_cookie` at provider offset204. Its fields
are id204, epoch208, generation212, sequence216 (four bytes each), endpoint220
(one byte); padding221..223 stays startup-zero. The provider's old204 bytes and
offsets are unchanged. This is an immutable historical identity, not a third live
DCD record or a buffer-lifetime authority.

The genuine adapter request_cancel callback validates context, bulk endpoint,
live original retained owner, and all five supplied cookie fields against the
actual adapter DCD owner **before** copying those semantic fields once into
reset_cookie and setting the existing `bulk.cancel_requested`. Preserve the
existing real callback count. Any other or duplicate cancellation is a bounded
profile failure. Never reconstruct saved fields from current generation, scope,
descriptor address, slot or diagnostic bind rows. Do not copy indeterminate C
padding from an argument into the saved object's initialized representation.

The callback only records work; it must not reenter the adapter/OUT component,
settle a packet, clear BUSY, satisfy a promise or modify the descriptor/payload.
The adapter may be busy in its legitimate admission callback, and its current
transport epoch is already4 while the actual retained old cookie's epoch is3.
Neither circumstance is an excuse to reject or retag this original callback.
After callback/dispatch unwinds the orchestrator calls the real
`hp1020_udc_out_request_cancel(saved_cookie)` once and records its actual OK.
Later, at exact slot1 reuse, a second direct call with that same saved cookie
returns STALE. Thus:

- CANCEL_REQUESTS: one actual queued transport callback;
- CANCEL_API_CALLS: two returned OUT API attempts, one OK and one STALE;
- CANCEL_SETTLEMENTS: zero; no `out_cancelled` or adapter cancelled call occurs.

Old callback settlement is the explicitly supplied late SUCCESS plus actual
TinyUSB service. The later stale replay is inert metadata, not an undispatched
DMA writer falsely declared quiescent. Both live records still come only from
genuine DCD binding and retain their original pointers/cookies after retirement.

## Immutable requests and cross-file seams

Retain the existing initial configuration record/sequence2 exactly. Add const
`hp1020_usb_runtime_reset_record[16]` in ordinary rodata:

`80 00 00 00 00 00 00 00 21 02 00 00 00 00 00 00`

Its original external ingress sequence is3; the wire request is the last8 bytes.
Only the dedicated setup-memory16 is overwritten by the new helper before the
real offer copies it. No fabricated typed SC/SI, status grant, bus reset, class
request identity, endpoint reprogramming or CSR_DONE is introduced.

Retain all prior helper prototypes and add only:

```
bool hp1020_usb_runtime_ram_reset_observation(struct hp1020_udc_setup_observation *);
bool hp1020_usb_runtime_ram_check(const struct hp1020_usb_runtime_check_row *);
```

The reset observation helper admits exactly this second supplied observation
after320 old bytes are consumed and packet6 is still owned. It checks the actual
current ownership, setup sequence2/no pending capture, initialization and absence
of callback reentry. It copies the immutable record and original sequence3 only;
the orchestrator still explicitly offers/dispatches it. It neither changes read
scope nor fences, queues cancellation, services or promises anything.

The checked-return helper runs immediately **after** the named production call.
The orchestrator supplies the actual returned value and actual original saved
ticket/cookie; the helper validates bounded order/schema/result and appends the
row. It has no production side effects, hidden retry or authority to call the API
again. A mismatch records the first profile failure and stops. Existing `result`
handling remains strict for all ordinary OK calls; no general acceptance of
nonzero returns is introduced. The independent gate must tie rows to actual
calls/returns and raw state, not accept a row as proof of a return.

`ram_note` may use the added named note tags for the same secondary read-only
snapshots. Notes are not new checkpoint functions or host-controlled transitions.
`ram_init` still runs once, after root's scans; no component reinitialization,
extra stack seed or storage clearing occurs during recovery.

The existing status callback must accept exactly the real initial configuration
status and then the real SOFT_RESET status after recovery. Validate rhport, all
six standard setup fields and request order against the two exact requests;
check the genuine original EP0 owner was retired. It records no status callback
on reset admission, deferred service, failed finish or a stale replay. Class
reply lifetime remains governed by existing production APIs.

## Exact checked-return schema

Each row contains nine logical uint32 words,36 bytes, BE on target:
`operation, domain, result, identity[5], detail`. Domain is the **return enum**.
Identity kind is separately fixed by operation: RESET_TICKET for1..4, with
`(recovery_id,generation,0,0,0)`; ORIGINAL_COOKIE for5..6, with
`(id,epoch,generation,sequence,endpoint)`. Never format a reset ticket as a cookie.

| Row / operation | Production call and cut | Domain / actual return | Identity | detail |
|---|---|---|---|---:|
|1 FINISH_OWNED|finish_reset after class reset service, old DCD owner retained|PRINTER2 / WAIT1|2,2,0,0,0|0|
|2 RECEIVE_DCD|ack_reset RECEIVE while old DCD owner retained|PRINTER2 / WAIT1|2,2,0,0,0|1|
|3 RECEIVE_PENDING|ack_reset RECEIVE after late acquire but before service|PRINTER2 / WAIT1|2,2,0,0,0|1|
|4 FINISH_MISSING_TRANSPORT|finish_reset after successful RECEIVE+OUTPUT only|PRINTER2 / WAIT1|2,2,0,0,0|0|
|5 STALE_ACQUIRE_REUSE|acquire_packet(old, fault0, supplied facts), new slot1 owned|OUT8 / STALE2|7,3,2,6,1|0|
|6 STALE_CANCEL_REUSE|out_request_cancel(old), same new owner|OUT8 / STALE2|7,3,2,6,1|0|

The four WAIT calls preserve production memory, ownership, receive counts,
generation, reset parts and borrowed bytes, except the adapter's documented
last_class_result diagnostic. Transient enter/leave busy stores are permitted;
stable bytes before/after remain identical. No WAIT increments an accepted
promise or successful recovery count. Both stale calls preserve all owner,
buffer, descriptor and acquisition last/first diagnostic bytes and run no
visibility hook, copy, completion, fault or cancellation callback. Their own
profile counters/rows and ordinary call stack may change. Raw comparison and
access/entry evidence remain mandatory; numeric rows do not replace them.

## Manual storage/layout delta

`draft/.../layout-objects.tsv` and `layout-fields.tsv` are hand-derived target32
tables, not compiler output. The actual const witness must later use genuine
sizeof/alignof/offsetof and be independently compared against them. Object IDs
and field IDs1..101 are preserved; fields102..118 make original cancellation,
refusal diagnostics and retained class metadata directly readable. Table header
is `[4850554c,2,525,16,118]`, then16 triples and118 quadruples (2100 bytes rodata).
It contains no runtime addresses or instructions.

| Witness member | Offset | Bytes |
|---|---:|---:|
|head_guard|0|16|
|io240|16|5760|
|io_guard|5776|16|
|ranges65|5792|2340|
|range_padding / range_guard|8132 /8144|12 /16|
|binds15|8160|540|
|bind_padding / bind_guard|8700 /8704|4 /16|
|device images|8720|144|
|pixels|8864|64|
|documents2|8928|40|
|checks6|8968|216|
|reserved|9184|32|

Guard bytes remain16 copies of a7. All padding, unused rows and reserved bytes
remain zero. The144-byte device sublayout and its four guards are unchanged.
The second32 pixel bytes and second document row remain zero in this profile;
exactly one new-generation32-byte page/event is permitted. Both old output
storage and new storage may contain32 FF, so actual callbacks/generation/data
admission must distinguish a discarded READY page from a delivered page.

Mailbox words0..127 preserve their meanings. Word128 CHECK_ROWS is the number of
successfully appended checked-return rows, final6. Word129 CANCEL_API_CALLS counts
returned direct OUT cancellation API calls, final2. Words130..255 remain zero.
No new mailbox expected-state fields or writable witness shadow is added.

## Scopes, CPU/device writes and literal counts

The same13 monotonically increasing bulk scopes label the supplied read/trace
schedule; they are **not** receive reservation sequence numbers across restart.
Scopes1..6 use old G2 q1..6, slots0,1,2,3,0,1. Scopes7..13 use new G3 q1..7,
slots0,1,2,3,0,1,2. The actual receive owner pointer identifies the slot; every
cache hook independently validates it, its exact DMA/span and original cookie.
DMA-bearing literal trace rows therefore differ from the healthy profile after
scope6 even though counts remain240 I/O rows and65 range rows.

Read observations remain nine initial programming reads then five per arm;
completion/recovery adds no register read/write/order or program operation.
Kinds1..8 keep the original ordered schema and counts. Kind3's argument remains
ffffffff; kind8 argument/value remain0. Binding rows now include initial status,
old bulk6, genuine SOFT_RESET status and new bulk7:15 total.

For the final zero-length source only, this profile supplies input_offset352,
actual_count0. This is a legal one-past source index with no input dereference;
all64 source bytes are padding. It differs from the healthy profile's offset0
only as explicit source metadata, not as payload bytes or EOF inference.

Device padding remains `0x80 | ((0x69 ^ slot*0x1d ^ i*7) &0x7f)` for i after
actual_count through63, with slot0..3 and uint32 arithmetic. Descriptor poison
stays `(c35a0000|slot,13579bdf,fedcba90,2468ace0)` and prefix poison byte remains
`(d3 ^ slot*29 ^ i*17)&ff` with hexadecimal29/17 and i0..63. No poison is installed
for either stale probe. Every genuine acquisition synthetically installs its
guarded source, poisons only descriptor16/actual prefix64, then copies16, copies64
and orders through existing hooks. Payload tails64..1024 remain untouched.

Successful supplied completion lengths total704, but full-prefix visibility
copies total832 (13*64), so PAYLOAD_COPIED remains832. DESCRIPTOR_COPIED208;
successful acquisitions13, attempted acquisitions14 including the inert stale
probe. Only12 normalized receive completions/releases and11 nonempty feeds occur:
old5+new6 feeds admit672 bytes, while the old late32 bytes never reach the parser.
The final empty completion releases a reservation without starting/ending a doc.
No manual release or cancellation settlement erases the old unready reservation.

## Required event/checkpoint meanings

Independent acceptance selects actual call entries/returns by original
arguments, ordinal and state, never a mailbox note alone. Existing normalized,
pre-C, first close, next post-close publisher-service, first adapter-finish and
park boundaries retain their meanings. The reset-specific cuts are:

| Meaning | Concrete call boundary and evidence |
|---|---|
|Reset cut|Second `hp1020_udc_setup_offer` entry, sequence3; old320 consumed, oldq6 retained, no image6 installed; old READY page unaccepted, no output/event.|
|Admitted cancellation|First `hp1020_udc_out_request_cancel` entry, after the real queued callback copied oldcookie; receive stopped/error7, old DCD ownership retained. This call marks OUT cancellation only.|
|Held class reset|First finish_reset entry with original ticket2,2, after actual class service; parts0, deferred reply, no new EP0 owner; returned WAIT becomes row1.|
|Late pending|Publisher-service entry after late original acquire and row3; OUT FREE, adapter PENDING with SUCCESS32, actual core BUSY plus CLAIMED remains05; RX6/5/count1 and old READY page still retained.|
|Old callback drained|First successful RECEIVE acknowledgment entry for ticket2,2, after that actual service; no live/pending owner or BUSY, but unready reservation6/count1 and error7 still present; no old tail feed/output/event.|
|Before actual restart|Second `hp1020_usb_document_restart` entry, reached only after all three independent promises; old state/storage retained until this call. Successful restart resets metadata toG3, not all storage.|
|Before stale pair|Eighth actual acquire_packet entry: savedoldcookie supplied, current newq2/slot1 genuinely retained; exact descriptor/CPU/DMA address reuse must be proved independently.|
|After stale pair|Next existing `ram_install_bulk(newcookie,64,64)` entry, before any image or poison store; both stale calls returned, rows5/6 recorded, raw production and acquisition bytes unchanged from pre-stale (apart from ordinary stack).|

The last boundary is an existing useful source-installation operation, not a new
marker function. A harness may instead capture the exact returned-call sites
provided it proves the same state before any subsequent write; it must not fix
PC or inject calls. Four WAIT return comparisons and both stale comparisons also
need their actual entry/return values and bounded write/access evidence, not just
the larger snapshots. The exact capture-name/entry-ledger schema is a separate
pre-execution harness amendment, not an already executed result.

At reset admission receive.error7 is expected. It persists through late callback
drain and all promises until actual generation restart clears it. At park receive
G3 issued=consumed7/count0/stopped1/quiescent0/error0, one event `(3,1,0,1)`,32 FF
witness bytes, no active reset or owned status/bulk. The original ticket remains
2,2 in provider history. Class last/current/class request IDs remain1 with
current_actionACK4/current_issued1; class ep0_live/ep0_request_id and adapter
response_owned/deferred are0. Historical request IDs are not ownership.

Final eager OUT still settles only after first close through an explicitly
supplied successful ZLP, with no service poll between close and acquisition.
Before the next service it is PENDING and BUSY, then service/pump empties the
reservation before the sole finish. Keep two actual self-park iterations and
all external host no-repair, raw pair/seal/initial-load obligations unchanged.

## Truthful boundary and remaining work

RECEIVE is supplied only after every old writer and actual callback has drained;
the pre-drain attempts merely test refusal. OUTPUT is separately supplied because
no external consumer accepted the old READY page. TRANSPORT remains an explicit
platform promise about the required bulk-IN/default/toggle/halt state, not a
deduction from RAM counters, CNAK, error7 or a class request. No physical mapping,
cache, reset, IRQ or printing result is claimed. The stale calls are inert saved
metadata and cannot justify ignoring a real writer after a false promise.

Before implementation: root/independent review must agree this header and manual
layout; freeze amended literal traces/cookies/storage/checkpoint predictions.
Then author only the separate experimental profile, reuse production APIs and
full buffers, preserve old sources, freshly admit inputs/ELF/stack/callbacks and
run the two cases sequentially. No production API gap is asserted by this draft.
