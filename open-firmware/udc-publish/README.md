# Single bulk OUT publication

This component replaces one supplied publication boundary with code: a real TinyUSB
OUT1 request can build the existing descriptor, synchronize its exact ranges,
consume its existing submission permission and issue an immediate sequence of
logical register commands. The first focused experiment passed40 sanitized
host/40 audited QEMU cases and an independently frozen raw-capture gate. Full
sequential validation passed130 consistency checks and both suites with the same
case rows and capture identities. There is no physical bus/cache binding, USB
contact or successful receive claim.

The component reuses `udc-program`, `udc-setup`, `udc-out`, the TinyUSB adapter and
the existing four-slot receive queue. It allocates no transfer/recovery identity,
buffer queue or descriptor format. Its only retained failure identity is the
original adapter cookie, copied by value. Only full-speed64, endpoint OUT1,
big-endian descriptors, one terminal PPBNDU packet, DU0/BF0/THE0 and classic
single RX FIFO are in scope. IN, SETUP acquisition, startup and mechanics are
excluded.

## The ownership boundary

Initialize the existing objects first, then this object before any control or
packet activity. Supply four explicit DMA labels for the actual receive queue's
64-byte slot prefixes. The mapping is independent of CPU pointer values. Init
checks16-byte alignment, nonzero/nonwrapping numerical ranges and disjointness
from the descriptor/other prefixes; physical aliases remain supplied facts.

The public `arm_out` is the sole arm path. Before reserving receive memory it
requires current program/ingress readiness, ordinary adapter readiness and the
exact supplied lease facts, then performs nonmutating preflight reads. Missing
facts or unsupported sampled state return WAIT, invalid booleans INVALID, and
failed reads PREFLIGHT_ERROR. No descriptor bytes, receive sequence, cookie or
peripheral word are changed by those refusals. Diagnostic preflight fields have
no cookie and cannot authorize cleanup.

A known full receive queue waits before any read as well. The underlying
adapter remains authoritative and can still return WAIT without invoking a DCD
callback; the wrapper closes its one-shot window on that path too.

After preflight the wrapper calls the actual adapter arm operation. Its real
bulk DCD callback must call `prepare_and_publish`, once, synchronously. This
helper rejects direct, duplicate or out-of-window calls before descriptor
preparation. It verifies the actual reserved CPU buffer and looks up its fixed
DMA label; it never casts a pointer into an address.

The stopped/settled/mapping/cache lease starts **before preparation**. Existing
`udc_out_prepare` writes HOST_READY as its final store. Observing RDE0 afterward
would not make those earlier stores safe. The lease excludes old accesses until
the final RDE request and keeps the published mappings stationary throughout
their original ownership. A free software owner or an RDE/NAK bit is not that
physical promise.

After prepare the output cookie is copied immediately, even if later operations
fail. The DCD must preserve that cookie, payload shadow and ownership ledger
before returning false. The adapter then fences and queues cancellation while
unwinding. No hook or helper reenters fault, completion, cancellation, service or
recovery APIs; process queued cancellation after the arm wrapper returns.

## Exact command and cache sequence

The hook receives logical register offsets/words, with no volatile pointer or
physical base. Each read is a separate observation. Writes must not be modeled
as automatically changing later read inputs.

Preflight is fail-fast in this order:

| Offset | Accepted observation |
| --- | --- |
| `404` | Require bits `220`; forbid bits `0000fcd7`; preserve only `ffff0328` |
| `220` | Exactly `20` (bulk, NAK0) or `60` (bulk, NAK1) |
| `22c` | Low16 is64; upper16 is uninterpreted and never written |
| `408` | RXFIFO_EMPTY bit `8000` set; no status write follows |

All numbers in the table are hexadecimal except64. `cnak_window_safe` may be0
only on the initial NAK0 path. Nonboolean values always reject. The other six
facts must be1 before any preflight read. These checks do not discover HP's
mode, global SETUP readiness, mapping, cache granule or settlement.

The actual callback then performs:

1. Existing OUT prepare/bind, with no replacement descriptor encoder.
2. `rx_before_device(original_cookie, exact CPU/DMA span64)`: device-write range.
3. `descriptor_before_device(original_cookie, exact CPU/DMA span16)`:
   bidirectional descriptor range, after all its bytes are complete.
4. Memory ordering hook, then existing `take_submission` once into a local value.
5. Write `234 = descriptor_dma`, then order.
6. Only for initial NAK1: write `220 = 120`, order, read `220` and require `20`.
7. Write `404 = saved_stable_devctl | 4`, then order.

The CNAK command omits the read-only NAK bit. A rejected/uncertain write, failed
order/cache hook, or unexpected single NAK readback stops the sequence. There
is no retry queue, CNAK loop, RRDY, FIFO flush, status acknowledgement, SETUP rearm
or global-RX enable after unproved CNAK acceptance. RDE is not read back and
required to remain1; a genuine arrival can clear it. Even full command issuance
leaves the original OUT descriptor EXPOSED and adapter owner DCD-owned. It is
not a packet completion, actual byte count, host ACK or proof of physical write
arrival.

The mandatory cache hooks reuse the existing OK/NOT_PERFORMED/UNKNOWN policy.
They need real range/direction semantics and safe rounding within exclusively
owned cache-line envelopes, or an independently justified coherent/uncached
mapping.16-byte alignment alone proves neither. TinyUSB's generic weak success
no-ops are not a cache implementation. Post-device acquisition remains outside
this initial publisher and is still supplied to the existing observation API.

## Failure, reset and cleanup

Every post-bind failure preserves the first full original cookie, successful
software prefix, failing operation/outcome, register value or cache DMA/range,
and whether `take_submission` already exposed the record. Prefix bits report
CPU operations only; neither `exposed=0` nor a NOT_PERFORMED result authorizes
automatic reuse. The original diagnostic bytes survive successful cleanup.

Replace normal service/progress/final-submission checks with the combined
publisher wrappers. A publication failure blocks normal service, arm, pump,
finish, restart, manual descriptor publication and new submissions. Exact-cookie
observation/cancel settlement and actual reset ingress remain separate. Failed
service permits only the bridge's **already admitted inactive actual reset**;
the program's SERVICE-only unready-binding condition is not sufficient.

Program selection/grant retain their own admission checks, with an additional
local publisher failed/busy/arming/servicing barrier. In particular valid typed
SI may require `complete_selection` while program readiness is SERVICE-only;
requiring combined7 for that call would deadlock readiness. Program cleanup
retains its own exact programming-ticket contract and cannot clear publisher
failure. Callers may not bypass the publisher barrier by using the older direct
grant, manual bulk proposal or normal adapter arm/service path.

Publisher cleanup checks the **original complete cookie**, not current epochs,
plus an explicit completed physical-clean promise. It requires OUT FREE, no
adapter DCD/PENDING/prepared/delivering/response owners, stopped/fenced receive,
unmounted/unopened configuration and nonterminal adapter. A real reset alone
does not clear failure or supply that promise. The old receive queue count may
remain nonzero: its fenced reservation is intentionally retained until the
ordinary three-promise generation restart. Requiring count0 would deadlock that
recovery, and dropping the count would forge it. Cleanup performs no I/O,
descriptor edit, command replay, reconfiguration or recovery acknowledgement.

## Evidence and remaining physical obligations

The frozen proposal includes independent primary/cache reviews with exact source
identities. Existing stock bytes identify OUT1 DESPTR `b3000234`, CTL `b3000220`,
MPS `b300022c`, DEVCTL `b3000404` and RXFIFO_EMPTY `8000`; stock rearm tests that
empty-FIFO bit before requesting CNAK. Linux v6.12's pinned `snps_udc_core.c`
uses descriptor publication, CNAK inspection and a separately controlled RDE
writer. Sony CXD5602 manual1.1.0 distinguishes the normal descriptor pointer
from SETUP SUBPTR, CNAK/FIFO restrictions and PPBNDU timing. Those are conditional
family/reference contracts, not proof of HP mode or physical behavior.

The primary review is `/tmp/hp1020-next-dcd-boundary-review-20261002.md` and cache
review `/tmp/hp1020-dma-visibility-contract-review-20261002.md`, both preserved in
the proposal's `reviews/` directory. Root's independent original-byte check is
preserved there as well. No existing original IRQ/SETUP/idle/pause experiment
was repeated.

Still supplied: stationary CPU/DMA mapping and aliases; actual cache operations
and granule isolation; old bus-access settlement; hardware-stable register
window and all global-RDE writers; compatible BE packet capability; safe FIFO
interval; global OUT/SETUP storage readiness; posted-I/O behavior; immutable
event identity and CPU-visible settled completion; endpoint defaults; all three
document recovery promises. The useful next execution is an independently
scripted recording-bus composition, not a physical printer test.
