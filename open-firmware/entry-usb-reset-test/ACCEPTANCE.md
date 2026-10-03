# Continuous SOFT_RESET race: independent acceptance contract

2026-10-03. Static, unexecuted acceptance draft, frozen before any new reset
runtime/provider C. Author: independent source reviewer, not the proposed
runtime author. This review used the retained production APIs, the previously
frozen input bytes, and the public healthy-runtime contract. It did not use
CPU/RAM values from an executed runtime to select these expectations. No source
was imported, built, audited or executed; no hardware was accessed.

The reviewed proposal is `inputs/plan/PLAN.md`, SHA256
`b810f5b58ca52ec96191a09d2ca017b49839348d0fb37f23af41ec1e0b0439ca`.
There is no identified production API blocker. This contract selects one of
the proposal's optional actions: require one stale `out_request_cancel` replay
alongside the stale acquisition at the same exact buffer-reuse cut. No other
matrix is added. Both paints use only the ordinary incoming CPU profile; the
existing six startup profiles remain separate evidence.

## Required behavior, derived from existing APIs

1. The exact 352-byte stream and its 26-byte BIE are retained. After five64-byte
   feeds,320 bytes end precisely after END_JBIG, before END_PAGE/END_DOC. This
   is not a partly copied header: semantic phase4/EXPECT_END_PAGE,
   document_open1, documents1, page_count1 and page.complete0 are required.
   The stream has active1/jbig_ended1, bands1/rows8, pages0, consumed6 encoded
   bytes and padding18. The output has active1, page_index0, pages_drained0,
   documents_completed0. Ring slot0 is READY1, first0/rows8/final1; stride4,
   capacity_rows2048, slot_bytes8192, producer1, selection/completion0,
   copied8/accepted0/completed0. Its32 bytes are FF. The actual output and
   document callbacks have not run. These are requirements, not mailbox claims.
2. Eager old packet6 binds `(7,3,2,6,1)` at slot1. It is still EXPOSED/DCD,
   receive issued6/consumed5/count1, sequence6/capacity64/length0/ready0.
   No old packet6 source-image installation or acquisition precedes reset.
   Preserve this returned cookie by value, plus actual CPU/DMA addresses.
3. Offer immutable sequence3 SETUP16
   `80000000000000002102000000000000`, then dispatch with explicit facts.
   While held, the bridge grants no normal service/arm/pump/publication.
   Successful dispatch advances control2→3 and transport3→4, retains active
   transport3, fences/stops input and queues exactly one request_cancel with
   that original cookie. Neither ownership nor storage is released.
   **Receive.error becomes HP1020_RX_ENDPOINT=7** through the admission fence;
   it remains7 until restart. It is not a failed descriptor acquisition.
4. Outside callbacks, mark the queued original cancellation once. The OUT
   component and adapter then both have cancel_requested1. Actual publisher
   service processes canonical class SOFT_RESET despite the retained bulk
   owner: pending_destructive is0. It creates recovery ticket `(2,2)`, class
   request1, deferred reply epoch3, active control3, reset transport4, parts0.
   Finish while owned and RECEIVE while DCD both return WAIT1 without status
   submission, storage changes, promises or identity advance.
5. The original packet succeeds: supply input[320:352], actual32, independent
   nonzero padding, descriptor image and poisoned CPU prefix; acquire through
   the production hooks. Acquisition returns OK, frees only the OUT record and
   retains adapter PENDING with cookie `(7,3,2,6,1)`, SUCCESS0/actual32,
   cancel_requested1/**expected_cancel0**. Core OUT1 BUSY|CLAIMED stays5.
   RECEIVE still returns WAIT while this callback is pending.
6. The next actual service invokes the genuine TinyUSB bulk callback with that
   original side-ledger identity and SUCCESS32, clears core BUSY/CLAIMED and
   retires the adapter owner. Because input is fenced, it must not call
   `hp1020_usb_receive_complete_data` for `(2,6)`, feed those32 bytes, release
   that reservation or emit any output/document callback. Receive remains
   `(G2,issued6,consumed5,count1,error7,stopped1)` and slot1 remains unready.
   This is real successful settlement followed by deliberate parser discard,
   not a fabricated ABORTED/cancelled event or a receive-completion refusal.
7. Only now acknowledge RECEIVE then OUTPUT on the original `(2,2)` ticket.
   Parts become3, receive.quiescent1 and document.output_quiescent1. A finish
   with TRANSPORT absent must return WAIT, preserve G2 and all memory/owners,
   and create no EP0 owner. Supply TRANSPORT independently, then finish once.
   The **second actual document_restart entry** must still show old READY
   output, G2 and parts7. Restart advances G3 and clears metadata, preserving
   **all114704 document-memory bytes** and both callback/context pairs.
   It does not memset output/receive storage or make the pending page delivered.
8. Successful finish then binds the real deferred EP0 IN status ZLP
   `(8,3,3,0,0x80)`. It uses original NULL/length0 plus stationary64-byte
   staging, no data bytes, and independent supplied IN actual0. Publish,
   observe and service this actual owner; the real status-complete and class
   ACK release its response ownership. Retained historical metadata is not
   erased: class_request_id/current_request_id/last_request_id stay1,
   current_action=ACK4/current_issued1, reset ticket stays `(2,2)` after G3;
   ep0_live/ep0_request_id/response_owned become0. Do not demand all response
   structs or history fields be zero merely because no response is owned.
9. Fresh q1 is consumed, fresh q2 is armed as `(10,4,3,2,1)`. Its actual slot1
   CPU address, DMA `0x24682340`, descriptor CPU address and descriptor DMA
   equal old packet6's. Cookie id, epoch, generation and sequence differ;
   endpoint remains1, as the frozen tuples already specify.
   **Before installing the current source image**, acquire the saved old
   cookie with valid facts and fault0: STALE2 before any cache/order hook,
   descriptor/payload load, snapshot or fault mutation. Then replay the saved
   old request_cancel: STALE2. Neither changes current owner/storage, receive
   metadata, acquisition last/first diagnostics, program/publisher state or
   logical trace. The replay is inert metadata after a truthful earlier drain;
   it is not an undispatched DMA write concealed by the receive promise.
10. Complete the fresh352 bytes normally. Require one actual32-FF-byte consumer
    transfer, one ring acceptance/completion and event `(3,1,0,1)` before any
    close/finish. Document/page numbering restarts with G3 because parser/output
    metadata was rebuilt; no old END_DOC is counted. Arm q7 `(15,4,3,7,1)`.
    The **first actual close_input entry** retains it DCD/EXPOSED, count1 and
    BUSY|CLAIMED5. Close once, acquire its supplied successful ZLP, and do not
    service between close and acquisition. The next actual publisher service
    entry sees PENDING/OUT FREE/count1/consumed6; the first actual adapter_finish
    entry sees callback drained and empty reservation consumed7/count0.
    Finish once and park. ZLP is not EOF; no per-document finish/reinit occurs.

## Independent counts and memory oracle

`literals.py` fixes the complete cookie/fragment/slot schedule and logical hook
rows. Scope1..13 is a diagnostic counter, **not** receive sequence: scopes7..13
use fresh sequences1..7 and slots0,1,2,3,0,1,2. The old healthy profile's
scope-modulo-four DMA oracle cannot be reused. There remain240 logical rows and
65 original-owner range records, but those DMA-bearing rows change.

There are15 genuine binds,13 successful bulk acquisitions plus one inert stale
attempt,704 actual acquired bytes but672 parser-fed bytes. Payload visibility
copies cover832 bytes (all64 bytes for each of13 packets),
and descriptor visibility copies cover208 bytes. These differ deliberately
from actual USB byte counts; no provider counter may conflate them. Actual normalized
receive completion/release calls are12 (old5 + fresh6 + finalZLP); nonempty
image-output/semantic feeds are11. Require real call-entry/argument evidence,
including the forbidden old `(2,6)` completion and late32-byte feed absence.
There are exactly two document restarts, one queued cancellation callback, one
OK plus one STALE OUT cancellation mark, zero cancellation-settlement APIs,
two actual EP0 status completions, one output acceptance/completion/event,
one close and one finish. Four specified WAIT probes and two specified STALE
probes are separate conditional findings, not successful lifecycles.

Final receive allocation: slot0 new input[256:320]; slot1 input[320:352] then
nonzero padding; slot2 all64 padding for the ZLP; slot3 input[192:256]. All four
960-byte tails remain zero. Recovery never clears old storage, so raw before/
after comparisons around restart and stale calls are necessary. Production
output allocation is32 FF followed by32736 zero bytes; witness pixels are32 FF
then32 zeros, first event `(3,1,0,1,0)`, second event allzero. Identical old/new
FF bytes alone cannot prove the old page was discarded; callback lineage and
raw metadata/call ordering must independently establish it.

The final steady state has G3 issued=consumed7/count0, stopped1/quiescent0,
receive/output/parser errors0, document/output finished1; no actual EP0/bulk
owner, delivering_live, class response ownership or active reset; control3,
active control3, transport4, active transport4 and last_submission15. Program
binding/masks remain the original successfully configured ones. No new endpoint
programming, automatic status grant, CSR_DONE or controller-close I/O is added.

## Evidence admission and currently pending details

Retain single-entry execution, all initialized data/sentinel/islands, four BSS
zero spans, complete RAM/code/access bounds,8KiB stack and independent full
model/QEMU snapshots. Two paints must independently agree with these literals.
Keep10M model instructions and120s/4096-command/16MiB QEMU limits unless an
explicitly preserved failure justifies a separately reviewed change. New live
paths need new linked/source/stack admission; prior ceilings are not inherited.

Semantic cuts above must be tied to actual functions and ordinal/original
argument predicates in both engines, not mailbox phase labels or host repair.
Exact stop-selector ABI, amended public header/field offsets, new saved-cookie
provider placement,15-bind witness layout and six refusal-row serialization
remain **pending a separately frozen public amendment**. This contract does not
guess those bytes. Refusal records are secondary; raw state/trace/access evidence
is primary. Natural candidate observations are setup offer, second finish-reset
entry, first old-callback service after acquisition, second document_restart,
reset-status bind, old-cookie acquisition at exact reuse, close, final service,
finish and park. Repeated function entries require source/argument selection,
not a forced PC or an unnoticed extra service call.

Supplied mapping/cache/settlement facts remain external. RECEIVE covers all old
writes and callbacks, OUTPUT covers any consumer access (none accepted here),
TRANSPORT covers conservative bulk-IN/halt/toggle/default requirements. The
recording trace proves no physical DMA stop, successful wire packet, printing,
mechanical behavior or cold boot. This is one serialized recovery lifecycle,
not reset storms, failed cancellation or asynchronous-output coverage.

## Source anchors in the sealed inputs

- `hp1020_semantic.c:65..130,134..188`: exact START_DOC/END_JBIG/END_PAGE state;
  `hp1020_image_stream.c:11..18,49..88`: band delivery and page/document bounds;
  `hp1020_image_output.c:14..55,59..77`: no progress before valid END_PAGE for
  this single nonblocking band; `hp1020_image_ring.c:8..57`: READY vs acceptance.
- `hp1020_tusb_adapter.c:96..110,338..367,421..468`: reset admission/error,
  original callback discard; `503..571,649..680,738..788,812..898`: identity
  allocation, successful old settlement, actual callback drain and class dispatch;
  `948..1040`: close/finish and owner-gated three-promise recovery.
- `hp1020_usb_printer.c:42..64,110..128,161..167,193..249,252..318`:
  distinct request/recovery IDs, deferred ACK and retained historical metadata.
- `hp1020_usb_receive.c:21..31,43..56,69..88` and
  `hp1020_usb_document.c:30..74`: counts, stop/discard, metadata-only restart.
- `hp1020_udc_out.c:53..65,168..239,303..389`: original-cookie check before
  hooks, late success despite cancel request, STALE before diagnostics/bytes.
- `hp1020_udc_setup.c:68..127,252..265`, `hp1020_udc_program.c:221..268`,
  `hp1020_udc_publish.c:175..235`: held-capture progression and no reprogramming
  caused by canonical class reset; per-arm fixed trace remains independently
  supplied. `hp1020_udc_ep0.c:143..202`: real original status ownership.
- Pinned TinyUSB `usbd.c:757..777,899..914` plus the local protocol patch:
  clear BUSY/CLAIMED before genuine callback, successful actual status ACK path.
- The old independent352-byte literal and26-byte fixture are preserved byte for
  byte. Their source-based expected black32x8 pixels are32 FF; no new decoder
  execution was used to write this plan.
