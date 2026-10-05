# Recording after-device acquisition fixture

The first focused experiment passed32 sanitized host/32 audited QEMU cases,
3372 paired event rows and384 paired raw captures. The independently frozen V2
gate passed unchanged in report-only and raw-capture modes. All16 copied-evidence
controls passed. Full sequential regression retry passed131 consistency checks
and both offline suites; the earlier run's three legacy source-count failures
remain archived separately. This variant includes the publication,
programming, composed SETUP/EP0/OUT, TinyUSB and document fixtures. It uses the
actual retained OUT object and adapter DCD owner; it creates no second production
owner, descriptor decoder, receive queue or cancellation mechanism. The new
acquisition C implementation was not read while this fixture was drafted.

Only two shared fixture sources have optional `HP1020_COMPOSED_ACQUIRE` seams.
The composed fixture initializes/snapshots/checks the new fixture and routes its
four inputs, disabling old arbitrary observation/saved snapshot/direct CPU-write
operations62/65/66/67 in this variant. The publication fixture makes one guarded
private acquisition probe after a real original DCD binding, before the initiating
callback unwinds. Existing variants compile with all these seams absent.
Existing publication bypasses14/60/61 and program bypasses102/106/107 remain
blocked. Original-cookie cancellation63/64 stays available independently.

All new writes are synthetic fixture input or explicitly witnessed CPU visibility
operations. They establish no physical DMA/cache operation, original settlement,
USB success, IRQ behavior or printing. Actual CPU/DMA mapping, exclusive safe
cache-line envelopes, physical settlement and real acquire primitives remain
supplied prerequisites.

## Source and owner authority

The fixture-only device image is one144-byte guarded byte array. There is an
independent shadow initialized from the same fill. Its layout is:

| Offset | Bytes | Meaning |
|---|---|---|
|0|16|descriptor guard|
|16|16|device descriptor input|
|32|16|descriptor guard|
|48|16|payload guard|
|64|64|device payload input|
|128|16|payload guard|

Every guard remains the original fill0 or204. No C padding or pointer is captured.
The array and its saved original-cookie metadata may change only through an
admitted op140. Hooks never change the device images. The saved images are
inputs, not observations inferred from commands or production output.

Before op140 changes ANY image or CPU byte, it checks the original history
cookie against the actual adapter DCD owner, retained OUT cookie, real fake-DCD
packet, and exact buffer/descriptor allocation and DMA labels. PREPARED is
rejected; old, missing, FREE/PENDING or otherwise unretained identities are stale.
The selected slot is found independently by comparing the actual owner buffer
with all four existing receive slots; it is not read from failure diagnostics.

An admitted input poisons exactly the original descriptor16 and selected receive
prefix64. No selected slot byte64..1023, other slot, guard, output allocation or
EP0 storage is permitted to change. The allowed descriptor/payload shadows and
outer protected-memory copy are updated from the literal INPUT poison; no shadow
is inferred from component output. Mode0 writes words
`c35a0000|slot,13579bdf,fedcba90,2468ace0`; mode1 writes plausible DONE/count64
`88000040,0,slot_dma,0`. Payload byte i is
`(d3 XOR slot*29 XOR i*17) & ff`, with constants in hexadecimal. No base DCD-write
counter is incremented for this synthetic CPU activity.

## Real after-device hook calls

The only new trace kinds are6=descriptor-for-CPU,7=payload-for-CPU and8=dedicated
acquire-order. Their literal order is6 ->7 ->8. Kind6 witnesses actual descriptor
CPU address, DMA579bdf10 and length16; kind7 witnesses the ORIGINAL selected
receive prefix, one of DMA24681340/24682340/24683340/24684340 and length64. Kind8
has diagnostic DMA/length0 and receives the same original cookie.

At each hook the fixture records the actual `adapter.owners[2].cookie` as an
independent witness, checks it against the supplied cookie and saved image
identity, and verifies all actual span addresses, lengths and mapping labels.
The DCD and OUT owner must remain retained and the initiating callback must have
unwound. Existing cancellation/fenced/newer-SETUP state is allowed; current
progress7 or today's epoch cannot relabel the original packet. The fixture also
requires no earlier normal completion, cancellation request, parser/output/wire
activity or queue accounting change during that acquisition call.

OK0 copies the exact device range to CPU memory. NOT_PERFORMED1 copies nothing.
UNKNOWN2 copies exactly the first8 descriptor or first32 payload bytes, an
explicitly chosen test effect. Acquire-order has no byte effect. Allowed CPU
shadows are updated from independent saved input bytes. Every effect is checked
immediately while the original fake-DCD packet is still live, and again after
the production call BEFORE its live flag can be retired. Fully visible data
following an order failure must still remain retained and faulted.

All trace records retain the existing six-word format:
`(event, absolute all-hook ordinal, kind, DMA, bytes, result)`. Kinds1..5 retain
all previous meanings. The program read/write/order counters count only1..3;
new hook counters are separate. Read-script/trace guards and unused storage tails
are unchanged. Failure scheduling shares the existing single absolute-ordinal
slot, so an already armed failure is never silently replaced.

The descriptor, payload and order hooks each perform a private recursive packet()
probe before their scheduled effect. The real OUT busy state must produce WAIT,
without a nested hook or any metadata, diagnostic, trace, borrowed-byte or device
image mutation. After a genuine DCD bind, the analogous probe relies on actual
adapter/stack activity before callback unwind. No production busy/owner field is
set by the fixture to obtain these conditions. The probes deliberately challenge
the documented serialization guard; they do no nested work. First initialization
is real; this matrix adds no reinitialization probe or invented report-WAIT state.

## New input ABI

The existing six-BE-word event header and1024-byte payload limit are retained.
Result values are existing OUT results OK0,WAIT1,STALE2,INVALID3,FAULT4,
ADAPTER_ERROR5. Every input is serial. No hook is permitted to retain/defer work.

| Op | Arguments | Payload | Behavior |
|---|---|---|---|
|140|original history id,poison mode0/1,0,0|Exactly80 bytes|Install device descriptor16+payload64, then poison exact retained CPU spans. Unknown/old/FREE/PENDING owner returnsSTALE; exact PREPARED returnsINVALID; malformed mode/nonzero spare args returnsINVALID. Every refusal precedes all image/CPU writes.|
|141|0,0,0,0|Exactly3 raw bytes|Set transfer_settled,mapping_lease,cache_range_safe without normalizing malformed values.|
|142|original history id,mutation0..5,endpoint_fault,0|None|Call real acquisition. Mutations XOR80000000 into one of four word fields or XOR80 into endpoint; no fresh identity is assigned. Invalid envelope returnsINVALID before packet_calls. Unknown history returnsSTALE before a production call.|
|143|kind6/7/8,future absolute ordinal,outcome1/2,0|None|Arm one hook failure. An already armed schedule returnsWAIT. Ordinal is bounded by the existing1024-record trace.|

Ops140/142 stale input must not be interpreted as a new fault for today's owner.
For op142, new packet/accepted/FAULT/STALE counters count external inputs only,
not recursive probes. An unknown-history op142 increments packet_calls/STALE,
but no existing base/OUT stale counter or production diagnostic is changed
because no original cookie could be recovered. Known historical mutations invoke
the real API and use its ordinary stale result. Acquisition refuses normal
PREPARED and busy states according to its header. Genuine stale/invalid/missing-
fact/busy refusals preserve production last/first-failure diagnostics.

On accepted acquisition the production OUT object is FREE and the original
adapter owner is PENDING; the fixture checks the still-live borrowed bytes before
it retires its own DCD flag. It does not service TinyUSB, pump data, mark EOF,
rearm, clear a publication/programming failure or provide reset promises.
Explicit original cancellation uses the unchanged existing path.

## Appended80 diagnostic words

Rows have576 words; all prior496 positions are unchanged. The new symbol is
`hp1020_acquire_fixture_stats[80]`. All named fields are words; pointers and C
padding are omitted. Only relative word59 is a host/target sizeof exclusion.

| Index | Meaning |
|---|---|
|0|Last external acquisition-fixture result|
|1..2|Production initialized,failure_valid|
|3..5|Descriptor,payload,order hook attempts|
|6..8|Successful exact owner/range checks,violations,image guards okay|
|9..10|Admitted device-image writes,CPU-poison writes|
|11|Raw facts packed high-to-low as settled,mapping,cache bytes|
|12..13|Image's independently selected slot,poison mode|
|14..18|Latest actual adapter owner cookie witnessed at a hook|
|19|Saved image valid|
|20..24|Original cookie copied by value when the image was admitted|
|25..41|Production last diagnostic,17 words below|
|42..58|Production first_failure diagnostic,17 words below|
|59|sizeof production acquisition object|
|60..63|After-bind callback probes,hook probes,last probe result,unchanged flag|
|64|Rejected op140 inputs|
|65..68|External packet calls,accepted,FAULT results,STALE results|
|69..72|Current device descriptor input as four literal BE words|
|73..76|Reserved0|
|77..78|FNV32 of device descriptor16,payload64|
|79|Reserved0|

Each17-word diagnostic is cookie5,prefix,DMA,bytes,raw I/O result,reason,result,
operation,snapshot_valid,snapshot as four BE words. The snapshot is evidence only
when snapshot_valid1; no old descriptor is silently called a new capture. The
first hook failure survives retry/cancellation/reset and successful later calls.
Its result is the actual fault-report result, not a forced constant.

Initially slot/mode and last probe result areFFFFFFFF; unchanged and image guards
are1; raw facts010101; initialized1 on successful init; image-valid/counters and
both diagnostics are0. Device bytes remain fill, so their words/FNV reflect fill.
Callback probes increment once per genuine retained bind, including post-bind
PREPARED/EXPOSED publication failures. Hook probes increment once per attempted
valid hook, including its scheduled NOT_PERFORMED/UNKNOWN result. A failed owner
or range witness is a harness violation and cannot count as a successful case.

## Capture and target integration

The host codec retains all eleven existing paired raw captures and adds
`output.acquire-device` as144 bytes. Use capture key `acquire_device` and target
accessors `hp1020_acquire_fixture_device_storage()` and
`hp1020_acquire_fixture_device_storage_bytes()`; the public byte-array symbol is
also available. `hp1020_acquire_fixture_component_bytes()` returns the same size
as diagnostic59. Host/target row-size exclusions are global59/425/490/555.

The builder inherits the pinned compiler-profile gate, effective TinyUSB source
materializer, freestanding flags, undefined-symbol check and synthetic-RAM linker
layout. The production acquisition implementation lives in the existing OUT
translation unit; no new implementation .c is copied or compiled by this package.
The runner must separately audit every target instruction before any QEMU call,
preserve source/fixture/effective-source closure and raw captures, then compare
all576 rows and all twelve paired capture files. It must independently reconstruct
CPU descriptor/4096 receive bytes/device images from op140 inputs and literal
hook outcomes; neither diagnostic output nor a digest alone is that oracle.

Current source-bound results are in
`analysis/usb-path/udc-acquire/validation.{json,md}`. These recording-hook cases
establish no physical acquisition or printing.
