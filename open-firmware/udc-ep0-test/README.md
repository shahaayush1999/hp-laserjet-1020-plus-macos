# Synthetic EP0 descriptor fixture

The fixture passes50 sanitized host/50 QEMU profiles through
`scripts/validate-hp1020-udc-ep0.py --target`. The target build is
`scripts/build-hp1020-udc-ep0-target.sh`. Controller mode, cache visibility,
actual count and settlement are supplied test facts. There is no physical DCD, IRQ, MMIO or USB operation.

## Composition and independent retention

The fixture explicitly includes the existing
`open-firmware/tinyusb-printer-test/fixture.c`. Compile this wrapper once, not the
base fixture separately, and include the repository `open-firmware` directory.
The wrapper renames the base reset/step, `dcd_edpt_xfer` and `dcd_set_address`.
Real EP0 submissions enter the new component; ordinary bulk keeps the existing
normalized synthetic lane. This experiment does not combine or replace the
separate bulk-descriptor suite and does not nest its C wrappers.

SET_ADDRESS needs its own interception because the included base setter would
otherwise call its renamed internal transfer function. The new setter keeps the
pending-address/control-epoch bookkeeping and routes NULL/0 through the real EP0
wrapper. The unchanged `dcd_edpt0_status_complete` remains a genuine TinyUSB
callback. Packet-fault suppression must prevent its invocation and address
commit. As in the base fixture, direct SET_ADDRESS submission returning false is
recorded as a fixture violation; its separate void-callback failure-recovery
policy is not invented here. Ordinary reply submission failures are injectable.

The wrapper copies actual original IN bytes before calling component preparation.
After successful preparation, its independent expected packet image changes only
those requested bytes. All previous64-byte tail/sink bytes remain expected,
including every byte for ZLPs. It does not copy actual post-prepare staging into
an allowed shadow. Original packet identity/length/pointer is also checked against
the adapter's retained owner, and the original borrowed shadow uses pre-call data.

Publication validates original/staging/descriptor CPU pointers, endpoint,
requested/allocation lengths, both DMA labels and every cookie field before any
returned pointer is dereferenced. Wrong proposals are retained as observed and
record a violation. The proposed wire capture reads actual returned IN STAGING,
never a second source copy; delayed publication contributes no wire bytes until
an actual proposal. A ZLP still has a proposal/cookie despite contributing0 bytes.

Ordinary observations and cancellation settlement pass through the component to
the real adapter, then separate service invokes actual TinyUSB/class dispatch.
No normalized EP0 completion bypass is exposed. The unchanged bulk operations
remain available for independent page/fault assertions. Adapter callbacks only
mark the base ledger's cancellation requests; a post-operation drain marks the
component outside callbacks, without supplying settlement.

Every completion/cancellation checks original borrowed bytes immediately after
the component call and before the fixture retires its own independent live flag.
Each step also checks original borrowed packets and accepted output slots via the
base independent ledger, both descriptors, both complete64-byte packet regions
and all guards. The descriptor shadow changes only on preparation or an explicit
simulated descriptor write. New operations also compare complete document-owned
memory before/after. No descriptor/packet region is erased upon retirement.

The dependency `hp1020_tusb_adapter_packet_fault` must exist in the integrated
adapter header and implementation. This component supplies no forward declaration
or fault stub. EP0 control cookies are never passed to transport-epoch fault APIs.

## Fixed synthetic mapping and captures

| Region | DMA label | Offset in full guarded capture |
| --- | --- | --- |
| OUT0 descriptor16 | `0x13579bd0` | 16 |
| IN0 descriptor16 | `0xa468ace0` | 48 |
| OUT0 sink64 | `0x3579bdf0` | 80 |
| IN0 staging64 | `0xb68ace00` | 160 |

These are explicit numeric labels unrelated to native CPU pointer values, not
proved bus mappings. Guards occupy offsets0,32,64,144,224, each16 bytes. The total
capture is240 bytes, statically checked. Both low/high DMA labels are preserved
without an alias OR or ADD.

Exported target accessors:

- `hp1020_ep0_fixture_storage()` returns the entire guarded region.
- `hp1020_ep0_fixture_storage_bytes()` returns its measured240-byte size.
- `hp1020_ep0_fixture_component_bytes()` returns compiled
  `sizeof(hp1020_udc_ep0) + sizeof(hp1020_udc_ep0_memory)`, excluding all fixture
  guards, histories, captures and shadows. Report the target result, never guess.

Host arguments retain the base codec: fill, bulk capacity, interface,
output-failure threshold, pixel/wire/receive/output paths, and an optional
document-event path (argc9/10). The extra full region is automatically saved at
`output_path + ".ep0-descriptors"`. Existing document-event capture is unchanged.
The normal descriptor packet size is64 regardless of the separately supplied bulk
capacity; use the existing supported base capacity for bulk scenarios.

The target reset/step/input/base96 names and signatures stay unchanged.
`hp1020_ep0_fixture_stats[104]` is appended by the host, yielding one flushed
JSON array of200 words per initial state and command. Native CPU pointers never
appear in added observations. The base measured-state-size word59 retains its
usual host/target normalization; added observations need none.

## Command encoding

Each host command is six BE32 words `op,a,b,c,d,data_length`, then exactly those
bytes. Target supplies the same five command words plus the input array. Both
require a fresh process/ELF for reset. The host enforces20 payload bytes for op44,
4 for op48 and `d` for op46; target orchestration must provide those same bytes.

Base operations remain, including adapter packet-fault op19 and busy
control op20. Historical EP0 op2 is rejected instead of manufacturing a status
word. Historical EP0 op3 is rejected because its original logical NULL/0 receive
buffer is not the64-byte DMA sink. EP0 op4 invokes component settled cancellation
and requires a prior request/fault. Bulk op2/op3/op4 remains ordinary normalized
input. New component result values are OK0, WAIT1, STALE2, INVALID3, FAULT4,
ADAPTER_ERROR5; base operation results retain their existing domains.

| Op | Fields |
| --- | --- |
| 40 | `a` endpoint0/0x80, `b` automatic publication0/1, `c` three packed publication fact bytes. Future policy only. Defaults all true and automatic. |
| 41 | `a` historical ID, `b` packed publication facts, `d` cookie mutation. Explicit publication. |
| 42 | `a` historical ID, `d` mutation. Request cancellation without settlement. |
| 43 | `a` historical ID, `b` settlement byte0..255, `d` mutation. Component validates the boolean; wrapper rejects only values above255. |
| 44 | `a` historical ID, `b` four packed completion fact bytes, `c` endpoint fault, `d` mutation. Data is raw descriptor16 followed by BE32 independently supplied actual count. |
| 45 | `a` endpoint0/0x80, `b` next-prepare injection kind0..12. One shot on that endpoint's next actual DCD call. |
| 46 | `a` current historical ID, `b` region0 descriptor or1 OUT sink, `c` offset, `d` count, followed by count bytes. Current exposed binding only. IN staging writes are rejected. |
| 47 | `a` current historical ID, `b` snapshot slot0..7. Capture descriptor and ORIGINAL cookie while exposed, before reuse. |
| 48 | `a` saved snapshot slot, `b` completion facts, `c` endpoint fault, `d` mutation. Data is BE32 independently supplied actual count; descriptor/cookie come from the saved snapshot. |
| 49 | `a` DeviceID logical length64 or400. Only the FIRST command after reset, before any adapter/USB event or issued identity. Default is400 if omitted. |
| 50 | `a` span0 OUTdesc/1 INdesc/2 OUTsink/3 INstage, `b` first-use init-probe kind, `c,d` DMA/span bytes for custom kind11. Initializes a separate scratch record, never an active instance. |

Unused words are zero. Publication facts are
`mode_packet64_be<<16 | descriptor_visible<<8 | packet_dma_ready`; values above
`0xffffff` are wrapper-invalid, individual byte values2/255 reach production C.
Completion facts use all32 bits:
`descriptor_cpu_visible<<24 | transfer_settled<<16 | packet_cpu_visible<<8 | in_actual_known`.
No wrapper masking of nonbooleans occurs. All-true is `0x01010101`. IN actual
count is supplied separately, never read from descriptor low16. OUT ignores the
IN-specific count fields except boolean-shape validation, as the component states.

Cookie mutations:0 unchanged;1 ID,2 epoch,3 generation,4 sequence XOR0x80000000;
5 endpoint XOR0x80. These mutate a saved cookie value, never an array index.
An old event cannot be assigned a new identity from the current descriptor.
Per-slot stale counters are attributed to the historical endpoint before any
test mutation, consistently across publication, observation and cancellation.

The DeviceID override is a fixture-only initial test input, not a production
configuration API. It adjusts the class configuration and BE length prefix
before any observable control/transport event; no class or adapter is
reinitialized. It then remains immutable. Expected bytes are BE16(length) plus
alphabet bytes `(A + i mod26)` for length-2 positions. Length64 with wLength65/128
causes real TinyUSB64-byte DATA, DATA ZLP and OUT STATUS; length64 with wLength64
requires no DATA ZLP. Later or repeated op49 is rejected.

Prepare injection kinds:

| Kind | Change |
| --- | --- |
| 0 | Normal actual TinyUSB packet |
| 1 | NULL original; use nonzero IN to test rejection |
| 2 | Requested65 |
| 3 | OUT endpoint with requested1 |
| 4 | Non-NULL pointer with requested0 |
| 5 / 6 / 7 | Nonzero original aliases staging / descriptor / component; use IN to isolate source-overlap rejection |
| 8 | Numerically wrapping original at UINTPTR_MAX-15, requested64; no invalid dereference |
| 9 | Unsupported endpoint1 |
| 10 | Backend rejection before prepare/bind |
| 11 | Backend rejection after successful binding/preparation, before proposal |
| 12 | Backend rejection after automatic publication attempt; all-true automatic facts isolate failure after exposure |

Init-probe kinds:0 valid;1 NULL CPU;2 CPU+1;3 size one short;4 DMA+1;5 DMA0;
6 DMA0xfffffff0 with a wrapping extent;7 CPU aliases aligned scratch component;
8 DMA aliases next region;9 CPU aliases next region;10 CPU aliases adapter;
11 explicit DMA `c`/span bytes `d`;12 numeric CPU wrap. The next region is
`(selected+1)&3`. Geometry is rejected without dereferencing invalid metadata.

## Additional104 observations

Indices are relative to the appended array. Global G0..7 precede two48-word
groups: OUT begins8; IN begins56.

| G | Meaning |
| --- | --- |
| 0 | Last primary component/new-op result, preserved across cancellation bookkeeping |
| 1..4 | initialized, wrapper violations, guards intact, owned-byte shadows intact |
| 5..7 | step count, last EP0 endpoint (UINT32_MAX initially), DeviceID logical length |

| P within each48 group | Meaning |
| --- | --- |
| 0..5 | phase, cancel_requested, fault_reported, fault reason, last adapter result, requested length |
| 6..10 | Current cookie ID, epoch, generation, sequence, endpoint |
| 11..13 | Descriptor DMA, packet DMA, packet span bytes |
| 14..17 | Current raw descriptor as four BE32 words |
| 18..21 | Descriptor captured at most recent publication, four BE32 words |
| 22..26 | Most recent publication cookie, all five fields |
| 27..30 | Publication descriptor DMA, packet DMA, requested length, allocation64 |
| 31..36 | preparations, proposals, accepted completions, accepted cancellations, stale, newly marked cancellation requests |
| 37..41 | Observed cookie ID, raw status, endpoint fault, packed completion facts, independently supplied actual count |
| 42 | FNV of the complete64-byte actual packet region |
| 43 | FNV of original bytes retained by the independent live DCD ledger; empty FNV if none/ZLP |
| 44..45 | Packed publication policy (`automatic<<24 | facts24`), pending injection |
| 46..47 | Current original-is-NULL while active; last publication original-is-NULL after any proposal. Otherwise zero. |

Raw descriptor observations (op44) need not equal current live descriptor bytes.
Use explicit writes/capture/replay (op46/47/48), mutate live bytes afterward,
and replay after exact address reuse to test true immutable event handling.
Counters identify publications; historical publication bytes remain recorded
after retirement. Neither captured proposed wire bytes nor a valid count proves
physical delivery or a successful hardware status handshake.

## Build and evidence closure

The repository build script locates its component/test sources relative to itself
and writes only synthetic target artifacts under `analysis/usb-path/udc-ep0/target/`.
It retains
pinned TinyUSB source/patch preparation, compiler-profile and undefined-symbol
gates. The independent Python validator must call existing annotated-instruction
`audit_target()` before any QEMU run. Host uses existing sanitized C11 source
closure, replacing base fixture/host and adding this component; additionally
include this component directory and repository `open-firmware`.

Snapshot the included base fixture as a dependency, coordinated adapter API,
component/header, fixture/host/linker/build, class/receive/document/image/semantic
sources, pinned TinyUSB/provenance/patch/effective manifest, target memory helpers,
compiler profile and instruction-audit source. Preserve exact first sources and
captures before fixing any failure. Keep existing bulk descriptor, continuous
document and physical-hardware claims separate. Passing RAM tests would not
establish USB/DMA quiescence, real cache semantics or physical printing.
