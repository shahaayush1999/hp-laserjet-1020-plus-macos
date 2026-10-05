# Entry-owned USB runtime: public contract

Authored2026-10-03 as an **unexecuted header/contract only**. No runtime C,
compiler invocation, script import, target run or repository edit is included.
Root must approve this contract and the independent author must freeze its
addendum before implementation. Later validation belongs to execution reports.

The single profile is `raw-configuration-two-documents-final-out-zlp`, already
specified independently in the copied plan/literals. Existing production
components, pinned/patched TinyUSB and full capacities stay unchanged. This
package adds an explicit RAM provider contract, not a physical controller or
another USB/receive/ownership model.

## Storage and initialization

The layout agent's frozen `runtime.ld` owns actual placement and cap checks.
The public header declares these separate objects:

| Object | Section / placement | Exact bytes |
|---|---|---:|
|document|`.runtime_document`, first in generic BSS at10010000|13512|
|memory|`.runtime_memory` at10016800|114704|
|mailbox|`.runtime_mailbox` at10016060|1024|
|sentinel|file-backed `.runtime_sentinel` at10016500|256|
|witness|`.runtime_witness` at10032830|9216|

Class, adapter, OUT64+descriptor16, EP0136+memory160, SETUP80+source record16,
program88, publisher140, acquisition152 and provider state are separate ordinary
BSS objects. The provider is hand-derived204 target32 bytes;384 is its hard cap.
Its two retained records are current EP0 IN and current OUT only. The14 append-only
bind rows below are evidence, never an event-identity lookup or second queue.
An unexpected EP0 OUT/IN1 submission is a bounded-profile error before binding.
Return the existing single custom class driver directly; no duplicate driver
array, giant fixture state, payload history, shadow document or allocator.

The actual generic BSS used end, including all TinyUSB/private globals, must fit
10013fe0. Zero the actual generic BSS, mailbox, memory and witness once in startup;
never zero their remaining capacity gaps, stack, loaded code/data or sentinel.
Custom NOLOAD definitions must be uninitialized/zero-initialized; inspect retained
input objects so NOLOAD cannot hide discarded nonzero initializers.

Before **any** initializer, guard initialization or mailbox write, C scans every
byte of all four zero spans through volatile byte reads. It also checks all256
sentinel bytes against `(0x31 + 0x21*(i & 15)) & 255`, the prior nonzero sentinel
pattern. Retain bad-byte count/first bad address in locals until every scan has
finished; failure records the observation and returns without initialization.
C also reads/hashes the actual linked generic initialized-data span into locals.
That hash is an observation, not an invented source-level expected checksum:
independent pre-C acceptance compares those pointer-containing bytes to the exact
ELF file image. Initialized TinyUSB data may change normally during C; sentinel
is never writable by the experiment. Full actual storage and protected gaps are
captured externally; hashes alone cannot establish unchanged bytes.

Use only ordinary `.rodata` for immutable facts, source352, raw SETUP16,
descriptors and the compiler layout witness. One352-byte input is reused twice;
its required SHA256 is `ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d`.
The previous builder/oracle owns these existing bytes; this contract has not
generated a new document. The full image/receive production memory is untouched
by initialization beyond existing APIs; no buffer capacities may be reduced.

## One schedule and real component boundaries

Use existing production APIs; the only new execution entry is
`hp1020_usb_runtime_c(void)`. Ordinary DCD callbacks and provider hooks belong in
the proposed separate RAM-provider translation unit. No generic opcode engine
or new transport-completion API is required.

The header freezes nine cross-file helpers. `ram_init` alone initializes the
production objects/USB stack after scans. `ram_scope` chooses the next read-script
scope without allocating a cookie. The three observation/image helpers construct
explicit RAM inputs without admitting/completing them. `ram_retired` verifies
component FREE/adapter PENDING before releasing only the provider's live flag.
`ram_note` writes secondary diagnostics, `step` bounds outer transitions and
`fail` retains the first error. All later production APIs remain explicit in the
orchestrator. Standard DCD/cache/output callback signatures already come from
production/TinyUSB headers; their bodies remain solely in the RAM provider.

1. Initialize document with real pixel/event callbacks, printer and adapter,
   then SETUP, EP0, OUT, program, publisher and acquisition stationary objects;
   initialize TinyUSB once after all callback dependencies exist. This initial
   adapter generation is1 and input remains fenced. Guard bytes may be installed
   only after the complete pre-initializer scan.
2. Admit supplied bus reset sequence1/full-speed through the SETUP bridge and
   service it through `hp1020_udc_publish_service`. No ownership/recovery promise
   follows merely from admission. Next install immutable raw record
   `80000000000000000009010000000000` once in the dedicated source-memory16;
   offer/copy it with sequence2 and explicit DMA label, then dispatch canonical
   SET_CONFIGURATION1 with supplied capture facts/stall-clear fact. No later raw
   request, typed SC/SI, SET_ADDRESS, automatic-status owner or CSR_DONE occurs.
3. Genuine core endpoint-open callbacks use `hp1020_udc_program_open` with the
   real seven descriptor bytes. The standard reply's actual IN0 callback uses
   `hp1020_udc_ep0_prepare`; retain its returned cookie and verify the actual
   adapter owner before returning. Record the bind even if a later operation
   fails. After the callback/service unwinds, take its RAM proposal under the
   combined progress gate. It is original NULL/length0 plus separate staging64,
   never a synthetic auto-status owner.
4. Supply an explicit EP0 completion: synthetically write only its actual owned
   IN descriptor16 to BE words `(8800ffff,0,b68ace00,0)`, copy those actual bytes
   into an observation carrying the retained original cookie, and invoke EP0
   observe with `in_actual_known=1,in_actual=0`. Staging64 stays unchanged zero.
   The lowffff is deliberately not the IN length. Service the resulting real
   TinyUSB completion/status callback; no wire/hardware ACK is inferred.
5. Retain the real pending recovery ticket, then supply RECEIVE, OUTPUT and
   TRANSPORT promises separately in that order. Each is an explicit capability
   input, not a deduction from endpoint bits/empty storage. Finish the current
   recovery once under full combined progress. It reaches generation2 without
   creating a class request or extra EP0 reply.
6. Sole arm path: `hp1020_udc_publish_arm_out`; actual OUT1 DCD callback calls
   prepare-and-publish. Snapshot the original cookie from the actual owner at
   bind, preserving it after any post-bind failure. After unwind, supply one
   device image/settled acquisition, service through the publisher, then pump
   through the adapter. Repeat twelve data packets64/64/64/64/64/32 twice, eagerly
   arming the next packet after each consumed completion. No document-level
   close, finish, reset or reinitialization is allowed.
7. After packet12 is consumed and packet13 is already armed, reach the **first
   actual `hp1020_tusb_adapter_close_input` entry**. Both END_DOC events/pixels
   already exist; original final cookie is retained and DCD-owned. Call close
   once; then, with **no intervening service poll**, install/acquire an explicit
   successful zero-length packet for that same retained cookie. This ZLP is a
   supplied transfer, not EOF or cancellation.
8. The **next actual `hp1020_udc_publish_service` entry after close** is another
   read-only checkpoint, before service: OUT is FREE, adapter PENDING, receive
   count1/consumed12. Service and pump the empty view. The **first actual
   `hp1020_tusb_adapter_finish` entry** then exposes count0/consumed13 and no
   owner; call finish once and return to the owned park. Execute two self-jumps.

No marker functions substitute for these actual symbol entries. The runner must
track their counts and argument identity independently. Combined progress guards
ordinary service/arm/pump/close/finish; SERVICE-only actual reset drainage remains
the existing exception. Original-cookie settlement and separately supplied reset
parts retain existing component admission. Normal operations are bounded by256
outer steps, a step being one explicit schedule/API transition; an unexpected
WAIT/error in this fully supplied first schedule fails rather than busy-waiting
or repairing state. Hooks/callbacks do not count as extra outer transitions.
`tusb_time_millis_api` may return fixed0, explicitly no physical clock/timeout.

## Provider capabilities and exact RAM effects

Every field of the immutable supplied-facts object is1 except
`ep0_complete.in_actual=0`. The existing programming API's `dynamic_csr=1`
capability is explicit even though this is raw software request delivery.
This does not identify HP's actual mode or establish a physical combination of
delivery/default-state semantics. All mode, FIFO, quiet-window, mapping, cache,
stall-clear, setup-stability, transfer-settlement and recovery facts remain
external inputs. Publication reacquires its idle/stable lease before **every**
reservation; a previous successful write never proves the next lease.

Retain the exact asymmetric DMA labels in the header. Actual CPU spans come from
the linked objects and the production receive buffer returned to the DCD, never
from a guessed DMA translation. Dedicated descriptor/packet/source allocations
are16-aligned, while whole-cache-line safety remains a supplied capability.

The read hook takes values from an immutable ordered script, independent of all
writes: the nine initial programming reads plus five fresh reads per publication
as frozen in the independent literals. It checks the expected offset before
writing its output. A mismatch fails without assigning an alleged value. Writes
and barriers append their exact attempted arguments/outcome only; they perform
no MMIO, automatic readback, owner transition or fake endpoint effect.

Before-device kinds4/5 compare all five supplied cookie fields to the **actual**
adapter DCD owner. They verify the actual current slot by CPU-pointer equality,
owner length64, actual passed CPU/DMA/range, and the prepared descriptor words.
They also compare the selected prefix against the single64-byte snapshot taken
on entry to the genuine DCD callback. They record preparation intent only and
do not alter payload/descriptor/ownership. The provider is a recording backend,
not a claimed coherent/no-op cache implementation.

Before each acquisition, while exact original ownership is retained and OUT is
EXPOSED, provider installation writes its separate device descriptor16/payload64
images. Then it poisons only the actual OUT descriptor16 and that original
slot's64-byte CPU prefix. PREPARED/FREE/PENDING, stale identity, wrong mapping or
unexpected callback context must fail **before** any image/CPU mutation.
The source image retains a separate full original cookie and slot by value.
Moving to a new arm scope clears only device_valid, never relabels that old
image identity; successful installation replaces it with the verified original
owner. Cache hooks must compare this identity as well as the hook/actual owner.

For sequence k1..13, slot s=(k-1)%4, count n from the frozen packet schedule:

- Device descriptor: BE words `(88000000|n,0,RX_DMA[s],0)`.
- Device bytes0..n-1: the exact source352 fragment, independently selected by
  document/fragment index. Sequence13 has n0 and no input bytes.
- Device bytes i from n through63: `0x80 | ((0x69 ^ (s*0x1d) ^ (i*7)) & 0x7f)`.
  This is an explicitly new nonzero padding formula. Use unsigned arithmetic
  with s0..3/i0..63; no overflow occurs before the stated mask.
- Poison descriptor: BE words `(c35a0000|s,13579bdf,fedcba90,2468ace0)`.
- Poison prefix byte i: `(0xd3 ^ (s*0x29) ^ (i*0x17)) & 255` for all64 bytes.

The nonzero padding intentionally differs from the old acquisition fixture's
unmasked tail, which could contain zero. It is not retrospectively assigned to
old reports. All other receive bytes, including each960-byte unused slot tail,
stay unchanged. Device image writes/poison are synthetic CPU operations, never
claimed physical DMA effects.

After-device kinds6/7/8 again check the original argument against the current
actual DCD owner and stable device-image cookie/slot, without consulting failure
diagnostics. Kind6 copies exactly actual device descriptor16 to actual owned CPU
descriptor16; kind7 copies exactly device payload64 to that original CPU prefix64;
kind8 records acquire-order and changes neither range. Order is6→7→8, all outcomes
OK0 in this first scenario. The component then copies/decodes actual CPU bytes.
It may retire OUT ownership but the adapter must remain PENDING until service.
Original retained metadata becomes nonlive only after verifying that transition;
its cookie stays intact until another actual bind, including the final record.
No historical/failure-control matrix is copied into this initial runtime.

Any cancellation request merely records/marks the matching original live owner
and causes this first schedule to fail after callback unwind. It never completes
or frees that owner. Unsupported callback/endpoint, recursion, missing capacity,
unexpected input count or a second init similarly fails with state preserved;
no recovery promises or cleanup are invented to make a failing profile pass.
Public DCD entry points that are irrelevant to this profile must be bounded
recording/refusal stubs, not physical interrupt/connect/address implementations.

## Actual output, logs and mailbox

The output callback may only peek/accept/complete the production ring. Verify its
plan/ring/context identity, bounds and actual returned pixel view before copying
bytes to the64-byte witness, then immediately accept and explicitly complete
that same slot. This is supplied software consumption, not a physical page.
The document callback copies its four real event fields by value and records
the callback return separately; do not synthesize generation/document counters.
Both callbacks reject recursion, capacity overflow and output during/after
closing. Expected output is two32-byte FF views and two events; copies remain
metadata only, no copy replay or wider feature claim is added.

Mailbox indices are the header's fixed0..127 schema;128..255 stay zero. Counters
are updated from actual calls/results. `RESULT_DOMAIN` disambiguates enums.
Close/finish counters count calls after they return; the provider sets `closing`
immediately before first close to forbid late output, without changing any
production close/finish field. The runner separately observes actual entry counts.
Snapshot words81..114 are filled from actual final production fields; getters
are read-only. `BEFORE_CLOSE_CORE_BUSY` and `BEFORE_FINAL_SERVICE_CORE_BUSY` are
secondary observations. Acceptance also reads actual `_usbd_dev` bytes using
separately source-derived private offsets and verified linked symbol size.

`DATA_BYTES` is the actual initialized-data span length; `INPUT_CONSUMED` counts
704 parser input bytes, not832 acquired payload bytes. `PAYLOAD_COPIED` counts
832 bytes, `DESCRIPTOR_COPIED`208 bytes, exclusively from bulk acquire hooks.
FNV means FNV-1a32 (basis2166136261, multiplier16777619, modulo2^32): RECEIVE
covers all4096 receive bytes, OUTPUT all32768 production output bytes, PIXELS
all64 actual witness bytes, TRACE/RANGES/BINDS only their used BE row bytes.
No digest substitutes for independent literal/full-storage comparison.

Witness byte offsets (all relative to `hp1020_usb_runtime_witness`):

| Range | Meaning |
|---|---|
|0..15|head guard, A7|
|16..5775|240 rows ×24; `[scope,ordinal,kind,argument,value,outcome]`|
|5776..5791|I/O guard, A7|
|5792..8131|65 rows ×36; `[ordinal,id,epoch,G,sequence,endpoint,span_cpu,owner_cpu,owner_length]`|
|8132..8143|zero padding|
|8144..8159|range guard, A7|
|8160..8663|14 rows ×36; `[id,epoch,G,sequence,endpoint,original_cpu,requested,descriptor_cpu,packet_cpu]`|
|8664..8671|zero padding|
|8672..8687|bind guard, A7|
|8688..8831|guarded device144: guards at relative0,32,48,128; descriptor at16, payload at64|
|8832..8895|64 actual copied pixels|
|8896..8935|two20-byte event rows `[G,document_id,first_page,pages,callback_result]`|
|8936..9215|reserved zero|

All guards are sixteen A7 bytes and every unused append row stays zero. There is
no serialization of C padding. Numeric CPU addresses in evidence are never used
to choose a target or translated into a DMA label. Range rows take their cookie,
owner CPU and length from the actual adapter at hook entry; compare the supplied
hook cookie independently before recording/effects. Matching trace row holds the
actual hook DMA/length, including zero/zero and span_cpu0 for acquire-order.
The compiler/manual member offsets and bind rows independently identify the
actual selected receive slot; no failure object is an oracle.

## Read-only layout evidence and acceptance points

`layout-objects.tsv` and `layout-fields.tsv` freeze a manual target32 schema from
the pinned public headers. A future separate const-only translation unit emits
the header's table with real `sizeof`, `_Alignof`, `offsetof` and field widths.
Do not compile the literal expected offsets into the implementation witness.
Compare every emitted word against this independent table before using it;
resolve object addresses/unique extents separately from the ELF symbol table.
No mutable diagnostic snapshot may stand in for actual production fields.

The manual object ABI assumes pointers/enums/uint32/size_t size/alignment4,
uint16 alignment2 and byte alignment1; receive memory explicitly aligns16.
The prior independently derived document/memory table is retained as provenance.
New type offsets derive from the exact copied public headers. These are static
expectations, not compiler measurements. TinyUSB's private `_usbd_dev` needs its
own independent effective-source derivation, not an invented public offsetof.

Capture unchanged initial/normalization/pre-C/first-close/park evidence and add
the next-service/first-finish entry snapshots specified above. Before close:
G2 issued13/consumed12/count1, final `(14,3,2,13,1)` DCD-owned, OUT EXPOSED,
237 trace rows,62 range rows,14 binds,12 images/acquisitions,64 pixels/events2;
the final arm adds its kind4/5 rows before close:12×5 plus those final two hooks.
After final acquisition/before service:240 trace/65 range rows, OUT FREE,
adapter PENDING, count1/consumed12. Before finish:count0/consumed13 and no owner,
still unfinished. At park:finished/stopped/fenced1, same G2 and original IDs,
all owners free, exactly one close and finish, zero cancellations, unchanged
64 pixels/two events. The independent plan owns the remaining literal fields.

Important limits remain explicit: no real IRQ/event source, register/MMIO,
mapping/cache implementation, physical settlement/IN wire ACK/defaults,
print engine, copies replay, cold boot or working replacement claim. A future
first run may fail; preserve exact pre-execution sources and first captures
before any correction. Root owns all implementation/integration/execution.
