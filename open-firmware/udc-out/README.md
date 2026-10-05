# One-descriptor bulk OUT boundary

This RAM-only component connects original-format descriptors through actual
TinyUSB dispatch to exact decoded pages/document notifications. Current results
are in `analysis/usb-path/udc-out/validation.{json,md}`. It supplies no DCD, MMIO, IRQ, engine,
allocator, new receive queue or identity allocator. The existing adapter and
four-slot receive queue remain the owners of protocol/document flow.

## Integration contract

Initialize the existing adapter with OUT endpoint 1, full-speed MPS 64 and
`out_capacity=64`. Allocate a stationary `hp1020_udc_out`, a 16-byte-aligned
descriptor, and provide an explicit CPU/DMA span for it. `init()` is first-use
only and does not modify descriptor storage. CPU/DMA spans assert real writable
RAM and an externally established mapping. Numeric checks cannot discover
aliases or validate a physical bus mapping.

The application's actual `dcd_edpt_xfer` bulk-OUT branch calls `prepare()` with
the adapter's supplied buffer, a supplied DMA span, and requested length 64.
This validates address geometry before calling the existing `bind_submission`;
the returned original cookie is copied by value. After binding there is no
fallible validation or publication. The descriptor is built with explicit BE
byte stores, including zero reserved/next words. The adapter reservation remains
fenced on a failed DCD submission, even if this boundary rejected before binding.

After externally performing the necessary publication/cache work, call
`take_submission()` with supplied mode/cache facts. It returns a proposal with
the descriptor/buffer addresses and exact cookie. The function itself performs
no hardware operation. It conservatively marks the storage exposed before
return; rejection by the later backend still requires explicit settlement. A
proposal must not be retained and used after cancellation. The surrounding
transport must serialize publication/cancellation and fence delayed receive
enable work; this component cannot stop an already-returned proposal elsewhere.

All normal event ingress occurs after the initiating TinyUSB call returns.
The hardware-facing caller must copy descriptor bytes and the original cookie
into one immutable observation BEFORE descriptor address reuse. It must not
manufacture that identity from the current endpoint, generation or descriptor
pointer. `observe()` requires supplied descriptor visibility before decoding and
separate transfer-settled/payload-visible assertions before adapter completion.
An owner-2 status word alone does not settle anything. A successful completion
leaves data with the existing adapter/queue; separate `service()` and `pump()`
perform actual TinyUSB dispatch and parsing. This component never calls them.

The caller supplies endpoint-wide faults to the adapter's existing `fault()`
API even if no descriptor is active. For an active cookie, an observation's
`endpoint_fault` must contain a fault reason such as BNA/HE, not a raw EPSTS word
with ordinary data/TDC bits. Any supplied fault fences before status admission.
Raw RX zero, L one, count at most 64 and unchanged reserved/buffer/next fields
are conservative acceptance rules, not newly proven HP success semantics.

`request_cancel()` only fences this component's future publication and retains
every borrowed byte. It belongs in queued cancellation work, never synchronous
adapter callback reentry. `cancelled(..., transfer_settled=1)` relies on an
external assertion that old descriptor/payload accesses cannot recur and all
pending observations retain their original identities. Only successful adapter
acceptance retires the record. Queued old observations remain stale even after
the descriptor address is reused. A clean late success after a cancellation
request may settle the transfer through normal adapter completion; an observed
fault requires the explicit cancellation path. Neither path acknowledges class
RECEIVE, OUTPUT or TRANSPORT reset promises or resets endpoint stalls/toggles.

Every operation is serialized and nonreentrant. The adapter cancellation callback
must queue work. Retained objects and all API input/output structs are stationary
and nonoverlapping; CPU and DMA aliases that numeric comparisons cannot expose
remain caller preconditions. A WAIT/error from fault delivery must be retried
before pumping queued data; it is not permission to ignore that event.

## Evidence and intentional limits

The integrated `hp1020_udc_acquire.h` path passed its first32 sanitized host/32
audited QEMU cases and the independent raw-capture gate. Full sequential
regression validation is pending. It replaces
supplied CPU-visibility flags with mandatory descriptor16, payload64 and acquire-
order callbacks, followed by a real copy from the retained descriptor allocation.
The historical observer and this path share one locked decoder; the original OUT
layout, adapter owner, cancellation machinery and receive queue remain unchanged.
An exact retained old cookie may settle while a newer SETUP/reset or publication
failure blocks forward work. Acquisition never services/pumps or supplies reset
promises. Hook failures retain the original owner and first failure; later calls
report that fault without retrying visibility work. Separate exact-cookie
cancellation remains available. Physical settlement, mappings, exclusive safe
cache-line envelopes and actual acquire primitives are still supplied.

`open-firmware/udc-acquire-test/README.md` owns the separate device-image/
poisoned-CPU experiment. Historical observer results below describe their exact
preserved sources; the shared-source edit still requires sequential regression
validation before a new checkpoint.

- `analysis/usb-path/controller-family.{json,md}` already records original
  descriptor and status execution. Stock `0x10008708..0x1000871a` writes the
  receive address in BE order; `0x10008766..0x1000876f` clears next;
  `0x1000877f..0x100087a6` writes status `08 00 00 00`.
- Stock preserves reserved bytes 4..7. This component initializes them to zero;
  differential comparison must supply zero there to compare equal final images.
  It does not copy the original order of submission before final status stores.
  All bytes are constructed before a separate publication proposal is exposed.
- Stock `0x100084fe..0x10008525` reconstructs status and admits owner 2;
  `0x10008536..0x1000853f` reconstructs the low-16-bit count. RX/L/error checks
  are the replacement's stricter policy. TDC/wake hints are not proof of transfer
  success or memory visibility.
- Pinned Linux v6.12 `amd5536udc.h:327–340,464–474` defines the corresponding
  fields/layout; `snps_udc_core.c:774–787,887–895` builds max-packet chains.
  OUT descriptors do not encode requested capacity as an IN-style byte count.
  A 64-byte packet-mode assumption is therefore explicit here. The existing
  synthetic 1024-byte DCD results prove software integration only, not one HP
  descriptor's capacity or packetization. Those tests remain separate.
- Stock `DEVCTL |= 0x320` does not establish reset values or clear BF/DU;
  Linux configures those separately at `snps_udc_core.c:1890–1899`. This component
  cannot determine whether the actual HP controller is in the supplied mode.
- BE descriptor mode, packet limits, DMA mapping/reachability, cache maintenance,
  DMA/pointer publication ordering, descriptor atomicity and immutable snapshots,
  exact event identity, endpoint error capture/acknowledgement and transfer
  settlement remain external assertions. No amount of RAM testing proves them.

The intended benefit is to connect actual descriptor bytes and explicit DMA
addresses to the tested original-cookie adapter. It is not an implementation of
controller setup, EP0, interrupt handling, live cancellation, or physical reset.
