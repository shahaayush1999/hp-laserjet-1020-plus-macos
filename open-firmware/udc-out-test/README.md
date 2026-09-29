# Synthetic one-descriptor fixture

The first focused execution passes 34 sanitized host/34 QEMU scenarios.
Strengthened current-snapshot controls also pass all 34 host/34 QEMU cases;
the first source/report/capture archive remains unchanged. The component's adjacent README describes the original-byte evidence
and unresolved hardware requirements. This fixture supplies those requirements
as test inputs; it contains no MMIO, controller implementation or device access.

## Composition and source closure

`fixture.c` explicitly includes the current repository's
`open-firmware/tinyusb-printer-test/fixture.c`, renaming its `dcd_edpt_xfer`,
`hp1020_bulk_fixture_reset` and `hp1020_bulk_fixture_step` definitions. Include
the repository `open-firmware` directory when compiling. Compile the new fixture
once; do not also compile the base fixture as a separate translation unit.

The actual externally linked `dcd_edpt_xfer` wrapper preserves the shared EP0
path. For OUT1 it calls the component's `prepare()` before copying the original
cookie into the existing history/packet ledger. The default then calls
`take_submission()` with all three publication facts true. Shared SET_ADDRESS
uses the renamed shared EP0 implementation directly; its existing ledger,
pending-address identity and cancellation behavior are preserved.

Normal bulk completion enters only through the descriptor component. That calls
the actual existing adapter; later ordinary service invokes genuine TinyUSB and
class callbacks. Pumping remains separate. No direct bulk adapter-completion or
cancellation bypass is exposed. The included file still contains its original
op2/op4 code, but this wrapper intercepts every historical OUT1 cookie before
calling that code. Direct raw DCD event ingress is not added.

Each run requires a fresh process/ELF and capacity **64**. The existing 1024-byte
synthetic experiment remains separate and unchanged. The numeric descriptor DMA
label is `0x13579bd0`; receive slot `i` gets `0x24681340 + i*0x1000`. Slot identity
comes from comparing the actual reserved buffer with the four existing receive
slot addresses, never from casting a CPU pointer to a DMA address. These are
synthetic numeric labels, not mapped bus addresses. Custom DMA controls likewise
assert a mapping rather than proving one.

`scripts/build-hp1020-udc-out-target.sh` retains pinned TinyUSB preparation,
compiler-profile and undefined-symbol gates, generating a synthetic RAM target
under `analysis/usb-path/udc-out/target/`.
The independent validator must also call the existing image-core `audit_target`
gate before any QEMU execution. Its source snapshots must include this explicit
base fixture dependency plus the component/header, new fixture/host/linker/build
files, adapter, class/receive/document/image/semantic closure, effective TinyUSB
manifest and pinned source/patch files, target memory helpers, compiler profile
and target-audit source. The first run passed both build/profile and target ISA audit gates.

Host compilation follows the existing sanitized C11 build, replacing the base
fixture/host files with these and adding `hp1020_udc_out.c`. Additional include
directories are the component directory and repository `open-firmware`; retain
all existing TinyUSB/class/receive/image/semantic/JBIG includes and sources.

## Input, captures and symbols

The reset/step/input/96-word symbols retain their original names and signatures.
`hp1020_bulk_fixture_documents[512][5]` remains exported by the included fixture.
The target adds `hp1020_udc_fixture_stats[48]` and these accessors:

- `hp1020_udc_fixture_descriptor_storage()` returns the entire guarded region.
- `hp1020_udc_fixture_descriptor_storage_bytes()` returns its measured size,
  statically required to be 48 bytes: 16-byte prefix, 16 descriptor bytes, 16 suffix.
- `hp1020_udc_fixture_component_bytes()` returns the measured
  `sizeof(hp1020_udc_out) + sizeof(hp1020_udc_out_memory)`. It excludes every
  synthetic guard, capture, shadow and history allocation. Do not guess this size
  or equate host and target pointer sizes.

Host arguments match the base codec: fill, capacity, interface, output-failure
threshold, then pixel/wire/receive/output paths and an optional document-event
path (`argc` 9 or 10). The final descriptor region is automatically saved at
`output_path + ".udc-descriptor"`. The optional document file preserves the five
BE words per callback attempt, enabling uninterrupted END_DOC checks.

Each command remains six BE u32 words `op,a,b,c,d,data_length`, followed by data.
Initial state and every command produce one flushed JSON line with the existing
96 observations followed by the additional 48 below. Target calls use the same
five command arguments and `hp1020_bulk_fixture_input` separately. The host
requires exactly 16 bytes for op22/op30 and exactly `c` for op26; the target caller
must supply the same bytes. No controller status is silently manufactured.

Each step captures both current descriptor bytes and the last proposed
descriptor image/cookie. Their words are decoded as BE integers solely to make
host/target observations portable; Python must independently re-encode and check
the expected wire bytes. Neither array contains native CPU pointers. Counters
identify a new proposal; old proposal bytes remain available after retirement.
Before dereferencing a returned publication pointer, the fixture separately
checks both CPU pointers against the actual descriptor and retained packet,
endpoint1, capacity64 and every original cookie field. A mismatch records a
violation while retaining the returned proposal as observed; it does not replace
the wrong metadata or dereference an unverified address.

## Operations

Base operations 0..18 remain as documented in the shared fixture, with these
explicit bulk restrictions: op2 with a historical OUT1 cookie returns INVALID;
use op22/op28/op30. Op3 writes bulk payload only after an exposed proposal. Op4
with an OUT1 cookie supplies cancellation settlement through the component and
requires a prior cancellation request/fault. Ordinary EP0 op2/op3/op4 remains
unchanged. Base op13 remains the existing generation/epoch-scoped endpoint fault
input, which is meaningful even with no live descriptor; use a raw descriptor
observation when testing exact old-submission identity. Base op14 still rejects
the next DCD submission before binding (1) or after binding (2).

All new operations use component result values OK=0, WAIT=1, STALE=2,
INVALID=3, FAULT=4, ADAPTER_ERROR=5. Base operation results retain their existing
domains. Unused words must be zero. Publication fact fields may carry 0..255 so
the component's >1 rejection is reachable; values above 255 are fixture INVALID.

| Op | Words and behavior |
| --- | --- |
| 20 | `a` automatic publication 0/1; `b` mode flag, `c` descriptor-visible flag, `d` buffer-ready flag. Changes future policy only. Defaults are all 1. |
| 21 | `a` original history ID; `b,c,d` the three publication facts. Attempt explicit publication without changing automatic policy. |
| 22 | `a` original history ID; `b` completion-facts mask; `c` independently supplied endpoint fault; `d` cookie mutation selector; exactly 16 immutable descriptor bytes follow. Does not write the retained descriptor. |
| 23 | `a` original history ID, `d` cookie mutation selector. Request cancellation; no settlement or adapter reset promise. |
| 24 | `a` original history ID, `b` explicitly supplied settlement byte 0..255, `d` mutation selector. Deliver cancellation settlement; the component itself rejects values above1. |
| 25 | Set next bulk preparation injection: `a` kind, `b` custom DMA and `c` span bytes for kind16. One-shot when the next actual bulk DCD callback occurs. |
| 26 | `a` current history ID, `b` descriptor byte offset, `c` count; `c` bytes follow. Explicit synthetic descriptor write to the currently exposed binding only. Updates the independent allowed-write shadow. |
| 27 | `a` current history ID, `b` snapshot slot 0..7. Copy the original cookie and current 16 descriptor bytes while that binding is exposed. Never retag after reuse. |
| 28 | `a` saved snapshot slot, `b` completion-facts mask, `c` supplied endpoint fault, `d` mutation selector. Replay copied bytes and their original cookie. |
| 29 | `a` first-use descriptor-span probe kind, `b` DMA and `c` span bytes for kind9. Uses a separate aligned scratch record; never reinitializes the active component. |
| 30 | Same raw16 descriptor/cookie/fault/mutation input as op22, but `b` packs three raw fact bytes: descriptor-visible at bits16..23, settled at bits8..15, payload-visible at bits0..7. Component validation receives all byte values, including2/255. |

Completion-facts bits for op22/op28: bit0 descriptor CPU-visible; bit1 transfer
settled; bit2 payload CPU-visible. Other bits are fixture INVALID. Op30 instead
accepts raw packed bytes up to `0xffffff`; each nonboolean reaches the component's
own rejection path. Op24 likewise forwards settlement bytes0..255; only values
above255 are rejected by the wrapper to avoid truncation. These are explicitly
supplied facts, not derived from owner, count, NAK, reset or a timeout.

Cookie mutation selectors: 0 unchanged; 1 ID, 2 epoch, 3 generation, 4 sequence
XOR `0x80000000`; 5 endpoint XOR `0x80`. They mutate a copied historical cookie,
never an array index or current owner. A mutated endpoint cannot cause array OOB.

Preparation injection kinds:

| Kind | Change |
| --- | --- |
| 0 | Normal mapped slot, requested 64, endpoint1 |
| 1 / 2 / 3 | Buffer CPU NULL / CPU+1 / span bytes63 |
| 4 / 5 / 6 | DMA+1 / DMA0 / DMA `0xfffffff0` with 64 bytes (wrap) |
| 7 / 8 / 9 | Buffer CPU aliases descriptor / DMA aliases descriptor / CPU aliases adapter |
| 10 / 11 | Requested63 / wrong endpoint0x81 |
| 12 | Backend rejects before `prepare` |
| 13 | Backend rejects after binding/preparation and before publication |
| 14 | Backend rejects after automatic publication attempt; use all true facts to specifically test failure after exposure |
| 15 | Buffer CPU aliases aligned component record |
| 16 | Explicit DMA `b`, span bytes `c`, otherwise real reserved CPU buffer |
| 17 | Numerically wrapping CPU span at `UINTPTR_MAX-15`; no dereference |

Descriptor-init probe kinds: 0 valid; 1 NULL CPU; 2 CPU+1; 3 bytes15;
4 DMA+1; 5 DMA0; 6 DMA `0xfffffff0`/bytes32; 7 CPU aliases aligned scratch
record; 8 CPU aliases adapter; 9 explicit DMA `b`/bytes `c`; 10 wrapping CPU
span at `UINTPTR_MAX-7`. Invalid numeric metadata is rejected before any buffer
dereference or binding. A valid probe initializes only its local scratch record,
never the active descriptor or transport identity.

All adapter cancellation callbacks keep the shared packet record live and only
set its request flag. A post-operation step then calls the component's request
function outside the callback. This never supplies settlement. The primary
component result remains in U0; bookkeeping must itself return OK or the fixture
records a violation. Explicit op23 also does not impersonate an adapter reset.

## Additional 48-word observations

`U` indices below are relative to the appended array, so U0 is JSON index96.

| U | Meaning |
| --- | --- |
| 0 | Last primary component/new-operation result; queued cancellation bookkeeping does not overwrite it |
| 1..6 | initialized, phase, cancel_requested, fault_reported, fault_reason, last adapter result |
| 7..9 | wrapper violations, all descriptor canaries intact, descriptor equals allowed-write shadow |
| 10..15 | preparations, publication proposals, accepted normal completions, accepted cancellations, stale observations/cancels/publications, newly marked cancellation requests |
| 16..20 | Current cookie ID, epoch, generation, sequence, endpoint (zero after retirement) |
| 21..23 | Descriptor DMA, current buffer DMA, current declared span bytes |
| 24..27 | Current descriptor bytes as four BE u32 values |
| 28..32 | Last proposed cookie ID, epoch, generation, sequence, endpoint |
| 33..36 | Exact descriptor image captured at that proposal, four BE u32 values |
| 37..39 | Last proposal descriptor DMA, buffer DMA, capacity |
| 40..43 | Last observed cookie ID, status word, endpoint fault, completion facts (mask for op22/op28; raw packed bytes for op30) |
| 44 | Pending next-preparation injection kind |
| 45 | Policy packed `automatic<<24 | mode<<16 | descriptor_visible<<8 | buffer_ready` |
| 46 | Step count |
| 47 | Last actual receive-slot index, UINT32_MAX before first bulk DCD attempt |

Base96 and U48 can be compared between host and target without pointer-size
normalization, except the base fixture's existing measured-storage-size word59.
Report measured component size from its separate target accessor; no guessed
or normalized size is inserted into U48.

## Retention checks and limitations

The shared ledger preserves full original cookies and borrowed payload shadows.
Every operation rechecks them and all accepted output-slot acceptance hashes.
New descriptor operations also compare the complete document-owned storage
before/after. Descriptor bytes have independent guards and an allowed-write
shadow, updated only after successful preparation or an explicit op26 write.
Ordinary observations, faults, cancellation requests/settlement and rejected
publication must not change them. Final full guarded descriptor bytes are
captured independently of the summary hashes/words.

Raw op22 events are externally supplied immutable snapshots; to demonstrate
actual snapshot retention across address reuse, first write/capture with
op26/op27, then replay with op28. None of these events is a real controller IRQ.
One descriptor retires only after accepted settled completion/cancellation;
the existing queue and pending TinyUSB callback may still own the received data.
These are separately observed and must be serviced before normal queue reuse.

The independent validator covers descriptor bytes,
owner/RX/L/count cross product, fault precedence, three completion-fact gates,
publication facts, span controls, backend rejection at all three stages, old
cookies after descriptor and receive-slot reuse, delayed actual TinyUSB dispatch,
queue pressure, uninterrupted document notifications, exact independently decoded
pixels and recovery with separately supplied reset promises. The current
snapshot extension contrasts copied event bytes with different live descriptor
bytes in both directions. Tests must not
convert synthetic settlement or packet64/BE/cache assumptions into hardware proof.
