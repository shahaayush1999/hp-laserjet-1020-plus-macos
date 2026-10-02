# Typed standard-request offload fixture

Focused execution passes **58 sanitized host and 58 big-endian QEMU cases**.
The runner freezes126 sources and six document fixtures. All5422 event rows,
eight complete raw captures per case and independent pixels/wire/document
oracles agree. This is RAM-only software, not a physical DCD; it adds zero
physical USB or native page lifecycles. Reports are in
`analysis/usb-path/udc-offload/validation.{json,md}`. Exact first-run sources,
captures and independent gate are in `source-snapshots/first-58-cases.tar.gz`.
The neighboring `unexecuted-proposals` archive retains both pre-integration
drafts and their static reviews; those drafts are not relabeled as executed.

## Implemented boundary

The shared ingress bridge accepts a typed `hp1020_tusb_offload` in its existing
single event slot. The original nonzero, nonwrapping external sequence spans
raw SETUP, offload and actual reset observations. Typed samples have no fabricated
raw descriptor or SETUP DMA address; the existing raw capture bytes stay intact.
The bridge copies the typed sample before accepting separate controller facts.

Supported reconstructed events are CONFIGURATION (kind1, configuration0/1) and
INTERFACE (kind2, configuration1/interface0/alternate0). The printer interface
must itself be0. A mode fact explicitly supplies dynamic CSR support; neither
the stock decoder nor an IRQ bit proves that capability. Coherence/current
event association, validation of original request bits absent from the four-bit
sample, and cleared EP0 stalls are separate promises. Unknown facts hold the
event and block ordinary progress. Unsupported values stay held/FAULT until an
actual reset: conventional STALL-and-continue rejection remains unfinished.

The adapter retains typed provenance and constructs only a canonical eight-byte
notification for the existing TinyUSB event boundary. Those bytes are internal
protocol input, never reported as original captured SETUP bytes. The local
TinyUSB patch extends configuration reinitialization as described below. SET_ADDRESS is outside
this fixture; no synthetic address event or second address status is introduced.

The DCD intercepts the standard IN0 NULL/0 submission for the active offload
event and calls `hp1020_tusb_adapter_bind_auto_status`. This acquires the normal
exact-cookie ownership ledger but creates no EP0 component descriptor, staging
buffer, publication or wire ZLP. Generic descriptor binding rejects offload EP0.
Granting is a later, one-shot `hp1020_udc_setup_take_auto_status` call. It requires
full bridge permission, the latest original admitted sequence, the original
cookie/current control epoch and retained transport identity, completed CSR
programming, and a physical status gate still associated with that event.
An offered but undispatched newer request already prevents the old grant.

The returned grant is permission for the serialized caller's immediate controller
action; this RAM component does not perform a register write. It must not be
queued/reused across an intervening ingress. It is neither completion nor host
ACK. The held no-buffer owner can survive document-generation recovery without
retagging. Generic SUCCESS is rejected and retains that owner. Explicit settled
cancellation transitions it to adapter PENDING, and later permitted service
retires it without any TinyUSB completion or status callback. A new control
admission/reset clears the old TinyUSB BUSY state through its normal path.

A successful nonzero configuration uses the existing class-owned recovery and
all three external promises, including repeated selection of the same value.
USB2 sections9.1.1.5 and9.4.5 require affected endpoint defaults, DATA0 toggles and
halt reset. The local TinyUSB patch closes/reopens the old binding; admission
fences and drains its original owners first. Repeated configuration0 remains
idempotent. INTERFACE0/alternate0 is an explicit reselection: admission
fences/cancels the prior transport, service waits for old owners, and accepted
status binding establishes one new transport binding/recovery even though
TinyUSB's fallback does not call `driver_open`. No fake reset or printer class
SOFT_RESET request is generated. config0 can grant status while unmounted and
stopped, and creates no recovery. The grant and recovery are independent:
accepted no-buffer status ownership can remain held while all three promises
finish, just as the existing configuration path permits held EP0 status. The
supplied CSR-programmed fact includes completed endpoint defaults/toggle/halt
reset. A retained core bulk STALL keeps configuration1 grants waiting, while
BUSY from a legitimate newly armed packet after recovery does not block them.

Failed raw or typed endpoint programming saves a dirty ticket with the original event
sequence/control epoch/transport epoch **before fencing advances identities**.
Sequence0 explicitly denotes raw provenance; its nonzero, nonwrapping control
epoch and original transport epoch still identify that exact failed attempt.
An OUT success followed by IN failure stays visibly partially programmed.
No later request/reset clears the ticket or authorizes another endpoint open.
The independent completed-programming-cleanup promise requires the exact dirty
ticket, no retained DCD/PENDING/prepared/delivering/response ownership, a stopped
document, and no mounted/open binding. It can legitimately match the original
failure after newer request/reset observations; it must not be retagged from
current state. It never starts recovery or supplies any document reset promise.
After a new later failure, replaying the older ticket is stale.

## Reuse and build integration

`fixture.c` enables `HP1020_COMPOSED_OFFLOAD` and includes the established
composed fixture once. The optional block lives in `udc-composed-test/fixture.c`;
its default build and288-word ABI remain unchanged. Existing EP0/OUT descriptors,
raw capture bridge, guarded allocations, cancellation queue and borrowed-byte
ledgers are reused. This adds no production translation unit; it extends the
existing verified local TinyUSB protocol patch without changing upstream pins.
Compile the same source/dependency list as the composed target builder,
using this fixture/host codec/linker script as SOURCE. The lead owns the separate
builder, source closure, paired host/target validator and aggregate gate.

The new host codec emits368 BE-compatible numeric stats per row: existing
base96 + EP0104 + OUT48 + SETUP40 + OFFLOAD80. It retains the exact pixel, wire,
receive storage, output storage and document outputs, and `.ep0-descriptors`,
`.udc-descriptor`, `.setup-record` suffixes. No new DMA storage is present.
All pre-existing normalized bypass operations remain forbidden by composition.
New commands carry no payload bytes; input scratch is clobbered after each step.

## New command ABI

The six-word BE header remains `op,a,b,c,d,data_len`. The new operations require
`data_len=0`. Unlisted fields are zero/ignored. Cookie mutation0 preserves the
original; 1..5 toggle id/epoch/generation/sequence high bit or endpoint direction.
Every cookie comes from immutable submission history, not current state.

| Op | Fields | Result domain / action |
|---|---|---|
|100|a=original sequence; b=kind1 SC/2 SI; c=`configuration<<16\|interface<<8\|alternate`|Bridge result; freeze typed observation |
|101|a=sequence; b=`dynamic<<24\|coherent_current<<16\|request_validated<<8\|stalls_cleared`; c=test-only adapter busy0/1|Bridge result; dispatch exact retained observation. Stall-clear1 separately clears only synthetic hardware EP0 stall flags, regardless of result |
|102|a=sequence; b=original cookie id; c=`csr_programmed<<8\|status_gate_current`; d=mutation|Bridge result; take current one-shot grant, leave output unchanged on failure |
|103|a=original auto cookie id; b=settled0/1; d=mutation|Adapter result; explicit auto-status cancellation settlement.0 waits; malformed values reject |
|104|a=original auto id; b=reason; d=mutation|Adapter result; exact retained fault ingress, including old-generation/stale controls |
|105|a=original auto id; b=SUCCESS0; c=0; d=mutation|Adapter result; deliberately attempt prohibited generic success; no completion/ACK may occur |
|106|a=0/off,1/fail next OUT open,2/fail next IN open|Adapter result; one-shot raw or typed configuration failure |
|107|a=original failed sequence; b=failed control epoch; c=failed transport epoch; d=completed-cleanup byte|Bridge result; supplied physical programming cleanup, exact ticket only |

Existing op14 still rejects a status submission before bind (1) or after bind
(2). Existing base20 identity/reentry probes and normal descriptor fault controls
remain available. New operations do not bypass EP0/OUT component settlement for
normal packet owners. An auto owner has no component descriptor to settle.

## OFFLOAD80 stats (offset288 in the complete row)

| Word(s) | Meaning |
|---|---|
|0|Last new-operation result (not overwritten by unrelated operations) |
|1..4|Typed offers, accepted copies, dispatch attempts, admissions |
|5..10|Auto-bind attempts, acquired owners, grants, cancellation settlements, retained-fault calls, generic-success probes |
|11..15|Fixture violations, immutable typed shadow equality, independent owner live, queued cancel, independent grant-taken flag |
|16..20|Last independently retained original owner cookie: id/epoch/generation/sequence/endpoint |
|21..25|Bridge's retained typed sequence/kind/config/interface/alternate |
|26..31|Adapter active typed sequence/kind/config/interface/alternate, captured transport epoch |
|32..36|Adapter IN0 auto flag, grant flag, owner state, TinyUSB BUSY, TinyUSB STALLED |
|37..41|Last actual returned grant original sequence/kind/config/interface/alternate |
|42..46|Last actual returned grant cookie, same five fields |
|47..48|Last packed dispatch facts and grant facts |
|49..52|Actual OUT/IN open attempts, OUT/IN successful opens |
|53..56|Actual OUT/IN close calls, close-all calls, pending open-failure injection |
|57..59|Actual TinyUSB status-complete callbacks, cleanup acknowledgements, adapter programming-dirty flag |
|60..63|Original saved failed sequence/control epoch/transport epoch, last successful cleanup's original sequence |
|64..66|Two BE32 words containing actual adapter canonical active_setup bytes, then configuration_value |
|67..71|Independent programmed endpoint map, retained failed-attempt flag, original failed sequence/control epoch/transport epoch |
|72..75|Last OUT-open, IN-open and close-all callback event order, total programming callback events |
|76..79|Reserved zero |

All80 words should match on host/target, along with existing288 except the
established host/target structure-size word59. Measure target sizes; do not guess.
SC/SI sequences must leave actual EP0 descriptor/staging and live raw SETUP
storage unchanged, with no wire bytes or EP0 publication added. Normal later raw
GET_DESCRIPTOR/class requests must still produce their original wire/pixel/
document oracles through the existing component paths.

Word67 is a separate programming witness, initially the literal EP0 map3. It
changes only on actual successful endpoint-open/close callbacks or an explicitly
supplied exact-attempt programming cleanup. A bus-reset notification alone cannot
clear it. Word68 tracks the fixture's independently retained failed attempt until
cleanup acknowledgement; words69..71 are captured at the injected failure before
the adapter faults, not copied from the adapter's later ticket. Failed IN open
therefore leaves a visible successful OUT mapping and ordered callback history.

## Executed controls and remaining limits

The29 profiles run with fills0/204, interface0 and64-byte reservations. They cover
config1/repeated-config1/config0/SI0; absent/malformed facts; stale/mutated grants;
newer raw/typed/reset barriers; reset retry; explicit cancellation; rejected
generic auto success; retained original cookies across recovery; old-generation
faults; typed OUT/IN-open and raw IN-open failure; exact cleanup through reset
and replay after another failure; before/after-bind status failure; repeated
configuration drainage/close/reopen and a fresh document; SI halt/default gates;
deferred SOFT_RESET supersession; external-sequence and transport-epoch exhaustion.
Base word68 observes TinyUSB connection state, distinct from mounted state.

The unchanged/patched protocol comparison independently queries both halted
bulk endpoints after ordinary repeated configuration. Only the patch clears
their halt and performs reset/reopen. USB specification provenance is in the
controller-reference manuals directory. Target measured adapter/document state
is128588 bytes; EP0 adds296, bulk80 and SETUP96, excluding test shadows/guards,
stack/code and other upstream state. Structure sizes are measured, not proof
of device fit or physical operation.

Only the restricted notifications described above are supported. Unsupported
settings remain held until an actual ordered reset; general rejection/STALL
recovery is unfinished. No automatic-owner success/ACK contract is proposed.
No artificial control/submission/class-recovery MAX seed or impossible internal
prepared/delivering state is advertised as covered here. Physical mode, event
currentness, endpoint defaults and settlement still require evidence.

The sequential full suite on2026-10-02 also passed58 host/58 QEMU profiles and
128 aggregate consistency checks. Its complete raw captures and exact126-source
closure are preserved in `analysis/usb-path/udc-offload/source-snapshots/full-suite-58-cases.*`.
This rerun includes corrected one-based USB2 PDF locators; first-run metadata is
retained unchanged. `independent-gate-review.*` preserves the initial gate-oracle
corrections and eight rejected negative controls. No physical controller or USB
behavior is established by these software checks.
