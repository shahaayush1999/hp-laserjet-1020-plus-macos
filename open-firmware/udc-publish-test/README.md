# Recording bulk-OUT publication fixture

This fixture composes one publication wrapper with the
existing actual TinyUSB, adapter, receive/document pipeline, SETUP bridge,
EP0/OUT descriptor objects and recording register backend. There is still one
DCD and one ownership ledger. No register write, DMA, cache operation, hardware
settlement, USB transfer or physical print is executed by these hooks.

The three optional shared-fixture seams preserve existing variants. The base
fixture's arm macro defaults to its original adapter call. The program fixture
uses combined service/progress/submission wrappers only under
`HP1020_COMPOSED_PUBLISH`. The composed fixture routes only the actual bulk DCD
callback to publication and recognizes the new inputs. Every prior diagnostic
position and the eleven capture pairs remain unchanged;64 words are appended.

Actual op6 calls `hp1020_udc_publish_arm_out`, whose preflight precedes any
receive reservation or descriptor preparation. Only its synchronous real DCD
callback invokes `prepare_and_publish`. The fixture detects binding from the
actual adapter owner, including when the helper returns a post-bind failure.
It records the original packet, history and descriptor shadow **before**
returning false to TinyUSB. Deferred cancellation then sees that same owner.
Descriptor expectations are built from literal BE words and independently
selected receive-slot addresses, never copied from implementation output.

Immediately after every genuine helper returns, while the original arm wrapper
is still active, a private probe retries the same arguments with a separate
poisoned cookie output. This runs after both successful and failed first calls.
It requires INVALID and unchanged output, adapter/receive/OUT/publisher/program
metadata, descriptor bytes, cache/register/injection state and forward counters.
A private checked count must equal genuine callbacks after unwind. This covers
the consumed one-shot window separately from op134's out-of-window probes; it
adds no operation, row word or public direct-probe counter and performs no
expected hook or transfer action.

The existing exposure/publication diagnostics count conservative
`take_submission` exposure, including failures in later register operations.
They do not claim that a DESPTR write occurred or reached hardware. Their
proposal-equivalent fields come from the original bound buffer and fixed mapping.
Original-cookie observation/cancellation and actual reset admission remain
available. Forward service/arm/pump/finish and DCD submissions obey the combined
barrier. Program selection/grant also refuse local publication failure or an
active publication call, while preserving `complete_selection`'s necessary
SERVICE-only admission before it establishes programming readiness.

Only this variant rejects old fail-submission op14, manual publication settings60,
and manual proposal61. The program variant already rejects direct grant102,
independent open-failure106 and adapter-only cleanup107. Thus post-bind failures
must come through the actual cache/register hooks; bypass inputs cannot create
an apparently successful publication outside the new wrapper. The retained old
automatic/publication-fact diagnostics are inert compatibility fields here.

## Fixed spans, hooks and independent guards

The descriptor DMA label is `579bdf10`, with the actual16-byte descriptor CPU
object. Receive prefixes are the actual existing four queue slots,64 bytes each,
at explicit DMA labels `24681340 + slot*1000`. These labels deliberately differ
from CPU pointers. No pointer value or alias conversion is serialized.

Both new cache hooks require the exact current adapter DCD owner and original
cookie. They independently compare the supplied CPU pointer to the selected
queue slot or descriptor allocation, the explicit DMA label and length, the
unchanged64-byte payload shadow and the complete literal descriptor words.
The hook witness is copied from `adapter.owners[2]`, never from the publisher's
failure object or its supplied cookie. Full composed storage checks run after
the helper returns; they are deliberately not called mid-preparation while
the old descriptor shadow is being replaced.

All facts start at1 as explicit test inputs. They are not inferred from these
hooks. Cache-line geometry, safe whole-line envelopes, actual mapping,
receive settlement, SETUP/global readiness and stable register windows remain
external premises. The hooks only record immediate operation intent and return
their separately supplied outcomes. They do not change bytes, produce a
completion, settle ownership or create any recovery promise.

The existing immutable read FIFO and guarded trace are reused. Trace records
remain six BE words:

`(input_event, all_hook_ordinal, kind, offset_or_dma, value_or_length, outcome)`.

Kinds1/2/3 are read/write/order, unchanged. Kind4 is RX preparation for device
writes: DMA=selected receive label,length64. Kind5 is descriptor bidirectional
publication: DMA=`579bdf10`,length16. Each original kind1..3 retains its existing
attempt counter; total trace count additionally includes both cache kinds.
No command changes a queued read observation. The shared single fault schedule
accepts cache kinds only through the new op131, so old op121 behavior is unchanged.
Missing/wrong queued reads, incorrect fault ordinals/kinds, overflow, pointer or
cookie mismatch, or guard/tail changes are harness violations.

## Added input ABI

The existing event header is six BE words: opcode,a,b,c,d,payload length. Inputs
must obey the same envelope on host and target. Publisher results are
OK0,WAIT1,STALE2,INVALID3,FAULT4,ADAPTER_ERROR5,PREFLIGHT_ERROR6. Existing operations
retain their own result domains; a base result is not always an adapter result.

| Op | Arguments | Payload | Operation |
|---|---|---|---|
|130|a/b/c/d=0|Exactly7 bytes|Replace io_profile,receive_dma_idle,register_window_stable,global_receive_ready,cnak_window_safe,mapping_lease,cache_range_safe; malformed bytes pass through to production validation.|
|131|a=kind4 or5;b=future absolute all-hook ordinal;c=outcome1 or2;d=0|None|Arm the same single injection slot used by program op121. A second armed schedule returns WAIT. Ordinal is at most1024.|
|132|a/b/c/d=0|None|Query pending publication cleanup into retained poison-initialized output. Non-OK must preserve every byte.|
|133|a=original history id;b=cookie mutation0..5;c=physical-clean byte;d=0|None|Call publication cleanup with an original by-value cookie or one independently altered field.|
|134|a=rhport byte;b=endpoint byte;c=receive slot0..3;d=length16bit|None|Call the helper outside its synchronous wrapper; no hook, owner/reservation change or output-cookie write is permitted.|

Op133 checks that all receive metadata remains byte-for-byte unchanged, including
nonzero old reserved count. It also preserves the reset ticket, active/part flags
and output-quiescence promise. Successful cleanup requires no actual retained
packet/adapter/prepared/delivering/response owner, OUT FREE, and stopped/unmounted/
fenced software. It emits no I/O, clears no queued input and supplies none of the
three separate generation-restart promises. The original failure cookie must
remain independently testable after newer reset/configuration events.

## Added64 diagnostic words

Append after the unchanged432 words, for496 words per row. The public target
symbol is `hp1020_publish_fixture_stats[64]`. Size is measured separately and
may differ between host and target.

| Relative index | Meaning |
|---|---|
|0|Last publication/helper/fixture operation result|
|1..6|initialized,busy,arming,window,servicing,failed|
|7..8|Combined pure progress,current software prefix|
|9..11|Last adapter/program/OUT results|
|12..13|Saved DEVCTL,OUTCTL|
|14..17|Arm control epoch,transport epoch,generation,shared ingress sequence|
|18..21|Preflight offset,value,I/O outcome,refused flag|
|22..26|Failure original cookie:id,epoch,generation,receive sequence,endpoint|
|27..35|Failure prefix,offset,attempted value,DMA,length,operation,I/O outcome,exposed,OUT result|
|36..42|Seven current raw publication fact bytes|
|43..44|Last query result;FNV32 of query's14 explicit fields serialized as BE words|
|45..49|Latest cache witness from the actual adapter owner:cookie5|
|50..53|RX hook attempts,descriptor hook attempts,successful exact span/cookie checks,violations|
|54..55|Genuine DCD publication-helper calls,successful publication cleanups|
|56..57|Receive count before/after the latest successful cleanup|
|58|sizeof publication object|
|59..60|Direct-helper probes,last output-cookie-unchanged flag|
|61..62|Last genuine helper result,last bound receive slot|
|63|Reserved0|

Query bytes initially equal`a7`, but only explicit fields enter its digest:
the first four cookie words and five32-bit failure words are`a7a7a7a7`; endpoint
and the four final byte fields are`a7`. The FNV uses the existing standard seed
`811c9dc5` and multiplier`01000193`, one byte at a time. Query result, helper
result, bound slot and cleanup counts start`ffffffff` where no event exists;
direct-unchanged starts1, counters and cache witness start0. No padding or CPU
pointer appears in that digest. Existing backend query and size fields are
unchanged.

All original raw captures remain present: events, rows, pixels, wire, receive,
output, document notifications, EP0 descriptor storage, OUT descriptor storage,
SETUP storage, and the program read/trace/storage files as applicable to the
existing eleven paired artifacts. Read storage remains3104 bytes and trace
storage24608; complete combined storage is27712 bytes. Only appended used words
may replace the initialization fill. Host serialization is explicit BE; target
read/trace payloads still start at their original public symbols+16.

The builder retains the pinned compiler-profile gate, exact patched TinyUSB
materializer, freestanding flags, undefined-symbol check and disassembly output.
It adds one separately compiled production unit and includes the existing
recording fixture. The lead's validator must still audit the target before
QEMU. This linker image is synthetic RAM test code, never a boot/upload image.

The first focused experiment passed40 sanitized host/40 audited QEMU cases,
4784 paired event rows and440 paired raw captures. The independently frozen gate
passed unchanged in both report-only and raw-capture modes. The earlier40-host
attempt stopped before target compilation because disposable compiler headers
were missing; that partial run remains separate. No production or scenario
correction was needed after execution. Full sequential validation passed130
consistency checks and both suites; case rows and capture identities are unchanged,
and the raw-capture gate passed again. Ten deliberately corrupted, internally
paired examples were rejected at the intended semantic checks in both gate modes.

Exact sources, fixtures, target and raw captures are preserved under
`analysis/usb-path/udc-publish/source-snapshots/`. The fixed20 profiles use fills0
and204: both CNAK paths, preflight facts/registers/read failures, progress and
callback authority, original-cookie cleanup, cancellation/reuse, NAK refusal and
ten post-bind failure positions. Every profile completes one32-byte FF page and
one document in synthetic RAM. These are not native stock or physical lifecycles.
