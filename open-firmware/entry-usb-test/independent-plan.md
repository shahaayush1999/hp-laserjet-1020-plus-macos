# Independent acceptance plan: one entry-owned USB lifetime, two documents

2026-10-03, author /root/usb_reference_contract. Frozen before reading or writing the new runtime/provider implementation. This is static specification, not an executed result. No candidate/oracle import, parse, build or execution was performed. The companion literals are /tmp/hp1020-entry-usb-independent-literals-20261003.py; source evidence hashes are saved separately.

## Exact first profile and identities

The target initializes once from its own entry/stack/BSS, then uses unchanged TinyUSB, printer/adapter, SETUP/EP0, OUT/publication/acquisition and production document components. The provider supplies one actual bus-reset observation (ingress sequence1), then one raw SET_CONFIGURATION1 record (sequence2), with original wire bytes **00 09 01 00 00 00 00 00**. This is deliberately the existing **software-delivered raw configuration** profile. No typed SC/SI, CSR_DONE, automatic status pseudo-owner, SET_ADDRESS, class request, additional configuration, synthetic EOF-between-documents or component reinitialization belongs in this first schedule.

Source-derived identity chain, independent of new runtime output:

| Stage | Required identity/state |
|---|---|
| document initialize | receive generation1, issued/consumed/count0 |
| adapter initialize | transport epoch1, active transport epoch1, control epoch0; fenced/input_closed/stopped |
| actual reset admission/service | control epoch1, transport epoch2; no recovery identity allocated |
| raw configuration admission | control epoch2, transport epoch3 |
| genuine configuration IN-status bind | original cookie **(id1, epoch2, generation1, sequence0, endpoint0x80)**, original NULL pointer/length0, real64-byte staging allocation |
| successful endpoint binding | internal recovery ticket **(recovery_id1, generation1)**, class_request_id remains0 |
| original EP0 status settlement/service, then three supplied promises and finish_reset | receive **generation2**, issued/consumed/count0; active transport epoch3; no extra reply/class request |
| bulk reservation k,1..13 | original cookie **(id k+1, epoch3, generation2, sequence k, endpoint1)**; slot=(k−1)%4 |

Derivation: hp1020_usb_receive.c:19–24 initializes generation1; :94–99 restart increments it. Adapter init :380–404 establishes epoch1 without allocating a cookie. Adapter bus_reset :504–517 advances control and fences, while fence :96–110 advances transport. admit_control :444–471 similarly fences a nonzero configuration. driver_open/begin_binding_recovery :184–264 allocates exactly one internal class recovery after successful configuration status binding. bind_submission :519–569 creates the EP0/control vs bulk/binding identities and increments the shared submission ID. usb_printer.c:42–65/173–184/224–260 plus document_restart :61–77 require all three promises and perform the one restart. Neither a reset event nor a new configuration alone establishes quiescence.

The initial EP0 status cookie must settle through the EP0 component **before** the initial three-promise restart in this chosen schedule. Copy original cookies from actual bind callbacks into stationary records; compare them to literals, never synthesize them from a reused endpoint/address or replace their generation after recovery.

## Data, document boundaries and the first actual close

Use the existing352-byte small-black stream, SHA256 **ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d**, twice. The companion file embeds its exact bytes; the previous independent entry oracle separately specifies its chunk/item/BIE construction. Each document uses six data packets **64,64,64,64,64,32**. All successful packets enter through retained OUT acquisition, actual TinyUSB completion/service and production document pump. No direct complete_data shortcut outside the existing class callback is admitted.

Expected actual copied output is **64 literal ff bytes**. Notifications are exactly:

1. **(generation2, document_id1, first_page0, pages1)**;
2. **(generation2, document_id2, first_page1, pages1)**.

The document ID and first-page values are cumulative within the generation: image_output.c:29–56 checks documents_completed+1 and uses prior document_first_page, then updates it to cumulative stream.pages. usb_document.c:4–13 obtains generation from the original receive view during feed; the provider cannot pass an arbitrary callback generation. Prior independent continuous cases validate adjacent boundaries and cumulative page numbering (validate-hp1020-continuous-printer.py:85–124). Output ring state resets for a new page, so two page callbacks do not imply ring accepted_rows16: the last ring has8 rows. Production output storage is32 ff bytes followed by32,736 zero bytes, because the same first slot is reused; the separate output witness accumulates both pages.

Maintain ordinary eager rearm after each successfully consumed data packet. After packet12, arm packet13 in slot0, but do not complete it yet. Observe **the first actual entry to hp1020_tusb_adapter_close_input**, before its first instruction. This is the before-EOF checkpoint, not a later workload marker and not the first finish entry. Required production state includes:

- generation2, issued13, consumed12, count1; receive stopped/quiescent/error0;
- document/output finished0 and errors0; both real END_DOC notifications and64 actual ff bytes already present;
- parser documents2, stream pages2, pages_drained2, documents_completed2, document_first_page2;
- adapter input_closed0/fenced0; no earlier close_input or finish call;
- original cookie **(14,3,2,13,1)** still DCD-owned, OUT EXPOSED, core bulk BUSY; EP0 owners absent;
- publisher/acquisition failure latches0, no outstanding class reset and no class request invented.

Read those fields from actual component storage through independently checked target member offsets; the final mailbox snapshot is not their oracle. The new public layout/header must expose those measurements before its implementation is reviewed. Callback logs must originate from the actual page/event values and reject output/notification during or after final close, rather than constructing the expected tuples or pixels.

## Healthy final drain is a supplied transfer, not cancellation

Adapter close_input :948–953 only sets input_closed. It neither requests cancellation nor consumes the reservation. finish :955–969 returns WAIT while a bulk owner remains. Calling cancelled() without a preceding requested cancellation is an unexpected aborted transfer and fences the stream (complete_locked :649–675); it is not a healthy way to discard the final owner.

Therefore after that first close entry:
1. Supply one explicit successful **zero-length OUT** for the retained cookie14 through ordinary acquisition, with independent settlement/cache/mapping facts. Count0 is a genuine supplied transfer and is **not EOF**.
2. Acquisition frees only OUT transport ownership; the adapter is PENDING and receive count remains1/consumed12. The same reservation and original cookie must survive.
3. Actual adapter/TinyUSB service delivers completion, then document pump releases the empty reservation. Empty views invoke no parser feed (usb_document.c:29–43).
4. With count0/consumed13, no packet owner or pending event, call finish once. It sets document/output finished, stops receive and fences input without advancing either generation or identity.
5. Return to the designated success park, then execute its self-branch twice with no intervening writes/calls.

At park: generation2; issued=consumed13/count0; stopped1/quiescent0/error0; input_closed/fenced1; document/output finished1; control epoch2, transport epoch3, last submission ID14; all owners FREE/NONE and core bulk BUSY clear; no cancellation calls; one close and one finish only. Pixel bytes and two document events are unchanged by the final ZLP/service/pump/finish. No additional packet may be armed after close. Without the supplied final settlement, this profile must not report successful completion.

## Logical I/O and acquisition oracle

The companion file independently freezes the existing endpoint-programming19 rows and the established CNAK publication14 rows; it does not read program-generated labels or expected traces.

For every bulk sequence1..13 use the existing asymmetric labels: descriptor0x579bdf10; receive slots0x24681340,0x24682340,0x24683340,0x24684340. Each publication has independently supplied DEVCTL0x34120320, OUTCTL0x60, MPS64, DEVSTS0xa001; records RX preparation64/descriptor preparation16/order; writes DESPTR; orders; commands CNAK0x120; orders; independently reads NAK-cleared0x20; requests RDE0x34120324; orders. The next stopped/stable window is newly supplied, never inferred from the previous write.

Each acquisition records descriptor-for-CPU16, payload-for-CPU64 and acquire-order before the actual descriptor is copied/decoded. The completion words are **(0x88000000 | supplied_count,0,selected_receive_DMA,0)**; prepared status is0x08000000. The final supplied count is0. Successful prefix values remain publication0xfff and acquisition0xf. Original cookie and exact owned CPU/DMA spans accompany each range hook. These operations cannot reenter the adapter.

Thus **19 +13×14 +13×3 =240 logical hook rows**, with237 before close and3 afterward. Kind counts are read74,write47,order54,RX-before-device13,descriptor-before-device13,descriptor-for-CPU13,payload-for-CPU13,acquire-order13. No CSR_DONE grant or endpoint-close sequence is warranted by this raw configuration/ordinary input close. One genuine configuration status ZLP is submitted and settled; its IN actual length0 is supplied independently of a deliberately arbitrary descriptor low16 (proposed0xffff), and no EP0 register publication is claimed.

These exact logical tables assume the public provider adopts the same fixed DMA labels/profile. Any changed numeric provider profile must receive a **pre-execution independent addendum**, not be accepted from observed runner output. Still awaiting that public contract: mailbox indices, exact CPU/DMA span mapping, event framing, source-padding bytes and hook effects, EP0 visibility/fact encoding, trace storage/encoding, bounded harmless poll counts. Prefer the existing independently specified nonzero padding for short/zero packets so passing the wrong count to the parser cannot be hidden by zeros. Do not infer full receive memory from input lengths until that padding contract is frozen.

## Startup, layout and anti-repair acceptance

Use the accepted split-object layout budget within main10003000..100351e0; preserve entry100167a8 and immutable islands. No contiguous adapter/document aggregate is required. Full document memory remains114704, state13496, four1024-byte receive slots and four8192-byte output slots. Admit all linked TinyUSB globals explicitly: preserve actual linked initialized data29 bytes (including pointer relocations/rhport value) and the256-byte sentinel; zero BSS once before any initializer. Verify pre-C zeroing of every admitted BSS byte, unchanged initialized data/stack paint/code/guards/gaps/islands, exact own SP, privileged PS0xf/INTENABLE0/WB0/WS1/loops0/SAR0. Runtime relocation/field/layout sizes must be checked against the actual linked closure, not imported from the old single-document mailbox.

Use the former three CPU profiles × two BSS/stack paints, but **replace the old active loop endpoints**, which overlapped the new prefix:
- ordinary: PS0,INTENABLE0,WB0,WS1,SAR0,loops0;
- dirty-window3: PS0x70302,INTENABLE1,WB3,WS0x89,SAR37,LBEG0x10035080,LEND0x100350a0,LCOUNT17;
- dirty-window7-excm: PS0x50711,INTENABLE2,WB7,WS0xc1,SAR63,LBEG0x100350c0,LEND0x100350e0,LCOUNT65535.

The two dirty LENDs lie outside the new text budget and entry island, and cannot intercept the prefix before LCOUNT clears. Recheck against emitted normalization addresses before execution. No asynchronous event is supplied. Paint pairs remain(a5,5a)/(cc,96); all32 incoming physical ARs are distinct using the previous formula. Reuse the exact verified QEMU11.1.1 map (INTENABLE110;37 is PREFCTL), seed WB before physical ARs and read back actual physical/current logical aliases. No optional register/cache/TLB initialization is added.

Preserve one initial state load and continuous execution: no call0 helper, stack reseed, hidden CPU reset, host memory write, PC advance or BSS repair between entry and park. Capture pre-normalization, after-normalization, pre-C, **first close-input entry**, park and two true park steps; compare complete paired RAM/CPU snapshots and concrete access/instruction traces. The QEMU ledger must independently bind every command/reply to the initial seed or read-only continuation/capture. The old stack bound784 cannot be reused; audit the new full call graph/indirect targets and actual stack low-water mark before claiming8KiB is sufficient.

## Bounded corruption controls after a real run

Independently reject internally consistent paired evidence that changes second first_page to0, relabels generation2 as1, changes any of64 ff bytes, erases the final DCD/PENDING owner before actual settlement/service, removes or fabricates the final ZLP, moves the first close before both END_DOCs, inserts per-document close/finish/reinitialization, skips a cache/order command while resealing trace counters, damages file-backed initialized data before C, or adds a post-entry debugger repair write. Preserve original evidence and use copied artifacts only; these are future gate controls, not executed checks.

This establishes continuous application-side integration under supplied RAM platform behavior. It establishes no physical USB/controller/cache/settlement/SETUP/IN-ACK/output-engine/loader/cold-boot claim.

