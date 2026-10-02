# Composed USB descriptor fixture

The current focused run passes62 sanitized host and62 QEMU cases.
It joins original-format SETUP captures, separate EP0 packet allocations and one
bulk OUT descriptor to actual TinyUSB, printer-class recovery and exact decoded
document output. This is a synthetic RAM experiment, not a physical DCD or
printing evidence. Reports: `analysis/usb-path/udc-composed/validation.json/.md`.

## Integration and verification

Run `python3 scripts/validate-hp1020-udc-composed.py --target` sequentially with
other validators. The runner freezes 117 source files and six input byte fixtures
before execution, builds a sanitized host fixture, audits target instructions,
and replays every event on the captured ELF. It compares all 288 row values
except the architecture-dependent base size field, plus complete guarded storage,
wire proposals, independently decoded pixels and document notifications.
Measured shared component sizes are EP0296, bulk OUT80 and SETUP96 bytes
beyond adapter/document128588. The original
composed run used SETUP88 and adapter/document128536. Fixture guards/shadows are
separate test overhead. No new original firmware instructions are executed;
completed SETUP70, EP0 construction66 and OUT reference evidence is reused and
checked against its source hashes and original bytes.

The original34 profiles comprise four protocol cases at both fills and interfaces
0/3, plus fifteen additional
scenarios run at both fills: immutable capture/replay, deferred newer-capture
retry, unknown/malformed acquisition facts, raw owner/RX/fault admission, held
capture blocking an old reset ACK or delayed descriptor publication, superseded
control beside retained bulk, soft reset, bus reset with retained post-reset
capture, exact reset-admission retry, terminal reset draining, both local
sequence-limit paths, and IN/bulk descriptor faults. Controller-free records and
adapter notifications still PENDING are asserted separately at terminal limits.
The28 raw-SI profiles described below extend this baseline without new fixture
entry points or normalized-operation shortcuts.

The first run passed 12 host profiles and stopped in the reconnect case before
target build. The inherited configuration helper assumed a fresh class identity
and empty receive reservations. Captures showed the previous class identity
unchanged and an aborted reservation retained correctly until recovery. The new
helper checks preservation, refused new reservations and all three existing
recovery promises. Only the validator changed before the 34/34 run. Both source
closures and raw captures are preserved under the report's `source-snapshots/`.

The five optional EP0 fixture names preserve its default ABI and behavior.
The composed fixture includes that fixture exactly once; that in turn includes
the base packet ledger exactly once. Its real exported DCD calls the renamed
EP0 implementation; the sole non-EP0 fallback is the composed production OUT
implementation. No second normalized DCD wrapper is nested around another.
The old normalized base entry points remain compiled as the shared fixture's
implementation details, but public composed event admission cannot invoke their
SETUP/reset/completion/cancellation/data-write operations.

## External facts and storage

There is no hardware/DMA/IRQ operation. Every control request begins as a raw
immutable 16-byte SETUP observation. Event order comes from the externally
supplied, nonzero, strictly increasing sequence shared with actual bus resets.
No transfer cookie is generated for unsolicited SETUP. The bridge alone admits
SETUP/reset to the existing adapter; packet identities are still the original
cookies returned by real DCD submission.

The bridge copies before validation. Unknown format/visibility/stability, owner
not 2, RX errors, endpoint faults or missing stall-clear fact retain the same
snapshot. They cannot authorize continued old reply/page progress. The fixture
obeys the bridge's SERVICE/ARM/PUMP permission bits for base operations 1/6/7.
Operations 8/9/12 (close/finish/finish-reset) and manual descriptor publication
41/61 require FULL permission 7. In particular, finishing an old deferred class
reset cannot emit its ACK while a newer raw SETUP is held. Blocked operations
return WAIT 1, without invoking the underlying operation.

Pending-reset lookup, individual recovery promises, explicit transport-clear
promise and exact-cookie observation/cancellation remain separately allowed.
Thus a pending bus reset can drain old owners; none of these facts by themselves
settles a controller packet. Cancellation callbacks only set the original base
ledger's queued marker. After the initiating call returns, the fixture forwards
those exact cookies to component `request_cancel`; `cancelled(...,1)` remains a
separate explicit event. Faults retain all original storage.

Numeric labels are independently checked for alignment, nonwrap and pairwise
nonoverlap before component initialization:

| Region | Synthetic DMA | Bytes |
| --- | --- | --- |
| EP0 OUT descriptor | `0x13579bd0` | 16 |
| EP0 IN descriptor | `0xa468ace0` | 16 |
| EP0 OUT status sink | `0x3579bdf0` | 64 |
| EP0 IN staging | `0xb68ace00` | 64 |
| Bulk OUT descriptor | `0x579bdf10` | 16 |
| Bulk receive slot i (0..3) | `0x24681340 + 0x1000*i` | 64 |
| Dedicated live SETUP record | `0x79bdf130` | 16 |

Actual stationary CPU buffers are separate. EP0 retains its five canaries and
independent packet/descriptor shadows; the base ledger retains borrowed original
control/bulk buffers and accepted output. OUT and live SETUP each have separate
16-byte before/after canaries and complete live-byte shadows. The bridge's whole
capture is checked against the independently saved offered input: sequence,
DMA, endpoint fault, all sixteen bytes and both printer-status bytes. It is
never refreshed by reading the bridge's result. The live source may subsequently
be overwritten without changing that retained capture.

OUT prepare's allowed descriptor shadow is constructed from the literal
`08000000,0,buffer_dma,0`, and its payload shadow is captured before prepare.
Publication verifies exact pointer/cookie/DMA/capacity before dereferencing and
captures the actual descriptor. EP0 captures actual staging bytes proposed for
transmission, including packet boundaries and a true NULL/0 original for ZLP.
Successful observe/cancel calls check all original borrowed bytes before erasing
the independent packet ledger. All transport-only operations also preserve the
whole document-memory region; an explicit OUT payload write permits only that
one exact range to change.

These checks do not prove numeric labels correspond to physical addresses,
coherent acquisition, hardware stall clearing, original event ordering, cache
maintenance or bus/engine settlement. Those remain independently supplied facts.

## Event ABI

Same host wire header as the base fixture: six BE32 words `op,a,b,c,d,data_len`,
followed by `data_len` bytes, at most 1024. Input scratch is clobbered after every
step. Host commands require exact 16 bytes for 62/80, exact `d` bytes for 46/65,
20 for EP0 observe44, and four for EP0 saved-observe48.

Base0/2/3/4/5 always return INVALID3: they cannot bypass raw SETUP/reset or
component packet events, even with invalid/stale ids. Other base commands and
EP0 commands40..50 retain their old meanings subject to the permission gate.
Base20 remains available for its existing test-only exhaustion/reentry controls.

| Op | Arguments and input | Action |
| --- | --- | --- |
| 60 | a=automatic0/1,b=`mode<<16\|descriptor_visible<<8\|DMA_ready` | Set bulk publication policy; initially auto1/facts010101 |
| 61 | a=original cookie id,b=publication facts,d=mutation | Publish retained bulk descriptor once; requires progress7 |
| 62 | a=id,b=`descriptor_CPU<<16\|settled<<8\|payload_CPU`,c=endpoint fault,d=mutation,input16 | Observe the entire immutable raw OUT descriptor, not live RAM |
| 63 | a=id,d=mutation | Request bulk cancellation, never settle it |
| 64 | a=id,b=settled byte,d=mutation | Explicit bulk cancellation settlement |
| 65 | a=id,b=0 descriptor/1 payload,c=offset,d=length,input exactly d | Simulate DMA writes only to the current EXPOSED original owner; update only independent allowed bytes |
| 66 | a=id,b=snapshot slot0..7 | Save original cookie and live descriptor while current/EXPOSED |
| 67 | a=snapshot slot,b=three completion facts,c=endpoint fault,d=mutation | Observe the saved immutable cookie/descriptor after live reuse |
| 80 | input exactly16 | Explicitly overwrite the complete dedicated live SETUP record; neither offer nor dispatch |
| 81 | a=external sequence,b=record DMA,c=endpoint fault,d=`value<<8\|known` | Offer a copy of the live SETUP record plus original printer status |
| 82 | a=original sequence,b=`BE_wire<<16\|CPU_visible<<8\|stable`,c=stall-clear byte | Dispatch only the bridge's retained snapshot |
| 83 | a=external reset sequence,b=FULL speed enum0,c=test busy0/1 | Admit/retry the actual reset; c1 temporarily makes adapter.busy true, so the bridge retains its exact reset retry |

Cookie mutation0 preserves all fields; 1..5 XOR `0x80000000` into id, epoch,
generation or sequence, or XOR `0x80` into endpoint. Every original cookie is
looked up from saved submission history; no mutation retags it from current
adapter state. Packed fact bytes preserve malformed values2/255.

Op82 c1 explicitly models the separately supplied hardware-clear fact by clearing
only the synthetic EP0 hardware stall mask before calling the bridge, regardless
of its result. c0/2 makes no clear. It does not call TinyUSB clear-stall, clear
BUSY, acknowledge a request or settle ownership. Successful bridge return alone
performs no synthetic hardware clear.

## Row ABI

Exactly288 uint32 values: base96, EP0104 unchanged, OUT48, SETUP40. The current
operation result remains base[0]. Extra result fields retain their lane's last
operation/submission result, as in the standalone component fixtures.

OUT starts at200 and retains the standalone OUT48 layout except local offset44,
which exposes the original adapter owner states rather than an injection code:

| Local offsets | Meaning |
| --- | --- |
| 0..9 | result,initialized,phase,cancel,fault_reported,reason,last_adapter,violations,guards,shadow |
| 10..15 | prepare,publish,complete,cancel,stale,cancel-mark counts |
| 16..20 | current cookie id,epoch,generation,sequence,endpoint |
| 21..23 | current descriptor DMA,buffer DMA,buffer bytes |
| 24..27 | live descriptor four BE32 words |
| 28..32 | last publication cookie |
| 33..36 | actual last publication descriptor four BE32 words |
| 37..39 | publication descriptor DMA,buffer DMA,capacity |
| 40..43 | last observation id,status,endpoint fault,packed fact bytes |
| 44 | adapter owner states: OUT0 low byte, IN0 middle byte, bulk OUT high byte |
| 45..47 | auto/facts packed as auto<<24 plus three bytes,OUT special steps,last receive slot |

Word44 reads `adapter.owners[0..2].state` directly. The actual adapter enum is
NONE0, DCD1, PENDING2. IN0 and bulk OUT both DCD-owned therefore give `0x010100`;
both settled with adapter notifications still pending give `0x020200`; all three
adapter records empty give zero. These diagnostics are independent of descriptor
component FREE phases and fixture live flags. Supplied cancellation settlement
can release component records while leaving adapter notifications pending; a
local terminal gate may intentionally prohibit the service that would deliver
them. That boundary is not completed recovery or a physical settlement proof.

SETUP starts at248:

| Local offsets | Meaning |
| --- | --- |
| 0..3 | result,initialized,pending_kind,pending_sequence |
| 4..8 | last_sequence,last_reset_sequence,last_admitted_sequence,adapter_control_epoch,reset_control_epoch |
| 9..14 | last_adapter_result,terminal,progress,violations,guards,live-shadow bit0/capture-shadow bit1 (healthy3) |
| 15..21 | live writes,offer calls,new retained copies,dispatch calls,admissions,reset calls,reset OK |
| 22..27 | capture sequence,DMA,endpoint fault,printer value<<8\|known,configured DMA,blocked ordinary calls |
| 28..31 | live source record four BE32 words |
| 32..35 | retained bridge record four BE32 words |
| 36..39 | SETUP special steps,blocked SERVICE calls,blocked ARM calls,current queued cancel mask |

The reset `WAIT` sequence is the pending tag; `last_sequence` remains the last
accepted observation/barrier. Pending kinds0/1/2 are none/capture/reset; terminal
0/1/2 is none/local sequence exhaustion/adapter exhaustion. No state is invented
to make those independent values coincide.

## Captures and target entry points

Host arguments remain `fill capacity interface fail_at pixels wire receive output
[documents]`. Documents remain BE32 records of five words, one per callback.
Extra files use the output path as a prefix:

- `.ep0-descriptors`: existing240-byte guarded EP0 layout.
- `.udc-descriptor`: before16, actual descriptor16, after16 (48 total).
- `.setup-record`: before16, actual live record16, after16 (48 total).

The retained SETUP bytes/status/identity and each original packet cookie are
captured in every row, in addition to the raw input event stream. Reusing the live
source can therefore be checked independently against the prior offered event.

Target exports retain `hp1020_bulk_fixture_reset/step`, base storage accessors,
EP0 storage/component-size functions and add:

- `hp1020_composed_out_stats[48]`, `hp1020_composed_setup_stats[40]`.
- `hp1020_composed_fixture_out_storage()` / `_out_storage_bytes()`.
- `hp1020_composed_fixture_setup_storage()` / `_setup_storage_bytes()`.
- `hp1020_composed_fixture_out_component_bytes()`: measured state plus16 descriptor bytes.
- `hp1020_composed_fixture_setup_component_bytes()`: measured state (including its private copy) plus16 source-record bytes.

The guard/shadow ledger is synthetic fixture overhead, not a physical DCD budget.
The matrix compares raw wire packet order, exact pixels and document events
across host/QEMU, independent literal descriptors, unchanged old identities,
full retention at each refused promise and recovery only after exact settlement. Existing SETUP70, EP0 construction66 and OUT stock
references are reused; this composition adds no stock instruction lifecycles.

## Ordinary SET_INTERFACE rejection

This sole-default-interface profile explicitly rejects ordinary raw SET_INTERFACE
with EP0 STALL, as permitted by USB2 §9.4.10. It first supersedes old EP0 reply
permission and waits for original ownership settlement, then rejects without
stopping healthy bulk input, resetting endpoint defaults or replacing an existing
fault/recovery ticket. Wrong interface indices cannot fall into another driver's
TinyUSB success fallback. Typed controller-handled SI remains a separate path.

Four preserved pre-fix host/QEMU observations show ordinary SI status followed by
stopped input without SI recovery; their later successful class reset is separate.
The corrected matrix passes62 host/62 QEMU cases, adding28 profiles at fills0/204
and interfaces0/3. They cover a live partial document, retained old EP0 data, seven
field controls, existing bulk fault, pending reset, retained bulk HALTs and an
unconfigured device. Literal wire bytes, original cookies, all guarded captures,
exact black pixels and fixed document generations agree. Physical USB behavior
and host interoperability remain unproved.

The first run's class-reset timing assertion failed after46 host cases. Class
reset legitimately starts deferred recovery before old bulk settles; final restart
still waits. The scenario was corrected and given an explicit pre-settlement
finish-WAIT check; production code did not change. Failed/passed captures, exact
sources, untouched proposals and the independent gate's eight negative controls
are preserved in `analysis/usb-path/udc-composed/source-snapshots/raw-si-*`.
The full sequential regression passed128 consistency checks and both suites
(`/tmp/hp1020-full-raw-si-20261002.log`, child `hp1020-validation.Kd7EIu`);
full62-case sources/captures are in `raw-si-full-suite-62-cases.*` beside the
focused archive. Raw-SI retained STATUS/late SUCCESS
and supersession of an already pending destructive request are not separately
exercised by these28 additions.
