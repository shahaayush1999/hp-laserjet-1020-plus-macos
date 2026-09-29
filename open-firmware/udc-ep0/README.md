# EP0 normal descriptors in synthetic RAM

The component passes50 sanitized host/50 independent QEMU profiles via
`scripts/validate-hp1020-udc-ep0.py --target`, using actual TinyUSB packetization.
It connects two normal descriptor records to the existing original-cookie
adapter; they do not implement a DCD, MMIO, cache maintenance, IRQ handling,
SETUP storage/parser, cancellation hardware or USB reset. No device was contacted.

## Bounded roles and ownership

The component has one stationary OUT0 record and one stationary IN0 record.
Each gets an independent16-byte descriptor and independent64-byte packet buffer.
The IN packet buffer is staging; the OUT packet buffer is a status sink. The
optional `hp1020_udc_ep0_memory` layout provides those four allocations; callers
still supply four explicit CPU/DMA spans. There is no new queue or cookie,
generation, sequence or control-stage allocator.

The actual `dcd_edpt_xfer` branch calls `prepare(endpoint, original, requested)`:

- IN0 (`0x80`): lengths0..64, including DATA ZLP and STATUS ZLP.
- OUT0 (`0`): length0 only, for the status direction already selected by TinyUSB.
- Every zero-length call requires the original pointer to be NULL, matching
  pinned TinyUSB. Nonzero IN must point to its real readable borrowed packet.

Other endpoints, IN packets above64, control OUT DATA and normal-descriptor use
for SETUP are unsupported. The component never parses a SETUP or guesses DATA
versus STATUS from a zero length; TinyUSB retains those decisions. It neither
assembles a whole response nor reproduces HP's five-descriptor batches.

Numeric span validation precedes binding and every byte mutation. Each CPU/DMA
span must be nonzero, aligned16, sufficiently large and nonwrapping. The four
used regions must not overlap each other numerically in either address domain,
or overlap component/adapter CPU state. Original IN bytes must not overlap any
owned region/state. Actual mappings, allocation extent and aliases cannot be
discovered by numeric comparison and remain caller promises. API argument and
output objects also have an explicit nonalias contract.

`prepare` calls the existing `bind_submission` with the EXACT original TinyUSB
pointer, endpoint and requested length. It keeps that original cookie by value.
Only after binding succeeds does it copy requested IN bytes to its own staging
buffer and encode all16 descriptor bytes. A zero-length packet still points its
descriptor at a real64-byte staging/sink allocation; original NULL/0 is preserved
in the adapter. No staging/sink trailing byte is cleared as an incidental effect.
No descriptor or packet byte changes on initialization or binding rejection.

The descriptor is explicit BE bytes:

| Offset | IN0, requested n | OUT0 status |
| --- | --- | --- |
| 0 | `BE32(0x08000000 | n)` | `BE32(0x08000000)` |
| 4 | zero | zero |
| 8 | Explicit IN staging DMA address | Explicit OUT sink DMA address |
| 12 | zero | zero |

With n<=64, stock's flag addition and this OR produce identical bits. There is
no hidden alias transform of either DMA address. Payload bytes keep wire order.

`take_submission` separately requires supplied packet64/BE mode, descriptor
visibility and packet DMA-readiness facts. It returns both original and DMA
packet pointers so callers can distinguish their ownership. All proposal bytes
are ready before exposure. Returning a proposal conservatively exposes storage;
a backend that subsequently rejects it still owes settlement. External transport
serialization must prevent an old proposal from being used after cancellation.

## Completion, faults and cancellation

`observe` receives an immutable descriptor/cookie snapshot captured before
address reuse and a separate endpoint fault. It checks the entire original
cookie before mutation. Only exact endpoint0/0x80 selects a slot; no unchecked
endpoint-derived index exists. Every supplied boolean is checked for0/1.

A nonzero endpoint fault takes precedence over owner/visibility waiting. The
strict initial status profile requires owner2, TX/RX0, L1 and unchanged reserved,
packet-pointer and next fields. Other owners mean WAIT. This is replacement
policy, not an assertion that HP's routines performed these checks.

OUT0 requires received count0. IN0 deliberately does not interpret postcompletion
descriptor low16 as an actual byte count: after supplied descriptor visibility,
transfer settlement and packet CPU-visibility, it requires `in_actual_known=1`
and independently supplied `in_actual==requested`, including zero. Unknown actual
length waits; a known mismatch faults and retains the record. Tests must vary the
IN low16 independently to demonstrate that an encoded requested count cannot
serve as its own success oracle. The IN-specific actual fields are ignored for
OUT0, apart from validating the boolean-shaped field.

Only then does the component call `adapter_complete(SUCCESS, requested)`. An
accepted completion retires local ownership metadata without clearing descriptor
or packet bytes. The original borrowed buffer may still be PENDING in the
adapter until ordinary service invokes TinyUSB. The component never invokes
service, emits an ACK, submits the next packet, commits SET_ADDRESS, clears a
stall/toggle or acknowledges a class-reset promise.

Fault delivery uses the coordinated new adapter API:

```
hp1020_tusb_adapter_packet_fault(adapter, original_cookie, reason)
```

The integrated adapter header declares this real dependency. Its separate20
host/20 QEMU profiles verify retained faults, including late successful settlement
that must not acknowledge a faulted request.
It does NOT pass a control epoch to the existing transport-epoch fault function.
The agreed contract is: OK accepts a nonzero fault for an exact, still-current
DCD-owned cookie, fences input/recovery and requests cancellation without release;
STALE is no mutation for unknown, retired/PENDING, superseded or old-generation
cookies. Both may latch this component's local fault but authorize no reuse.
WAIT retries. LIMIT/other error is exposed through the slot's adapter result and
retains all ownership; explicit settled cancellation remains a separate action.

Once locally faulted, a later clean descriptor cannot become a success through
this component. An old superseded control fault may remain locally faulted while
the adapter correctly declines to fault newer work. `request_cancel` only fences
future publication. Queued cancellation callbacks are drained after adapter calls
return. `cancelled(..., settled=1)` requires actual accesses to descriptor, owned
packet and original packet to have ended, with pending events retaining their
old identities. Only adapter acceptance retires the record. A clean late success
after a mere cancellation request may settle normally; an observed fault uses
the cancellation path. Neither path proves controller-wide quiescence.

All calls use one serialized context. The sole synchronous adapter reentry is
binding inside `dcd_edpt_xfer`; ordinary observations and cancellation settlement
arrive only after the initiating TinyUSB call returns. Retry fault-delivery
WAIT/errors before service/pumping unrelated data; they are not permission to
ignore a fault. Reinitializing an active component is never a recovery method.

## Original evidence and limits

`analysis/usb-path/ep0-construction.{json,md}` executes36 descriptor construction
profiles and12 pointer-only profiles in both engines, plus16 pre-MMIO and2
length65 scope controls and18 excluded PCs. All are explicit supplied-register
cuts; no original ENTRY, copy/cache helper, completion or peripheral operation
runs. The component validator reuses that completed evidence and verifies its
stock bytes, sources and independent descriptor/pointer oracles again.
`control-in-data-stage.{json,md}` now distinguishes active passthrough from the
initialization ADD; its former OR/physical-alias claim is corrected separately.

Original zero-byte IN construction at0x10008c83..0x10008cf9 stores a real buffer
pointer and zero reserved/next, then status08000000. The nonzero <=MPS construction
at0x10008e20..0x10008e96 stores the same layout with flag+length. Active submissions
at0x10008d02..0x10008d0c and0x10008f11..0x10008f1b preserve the supplied descriptor
pointer; initialization's separate wrapped ADD is not a general DMA alias rule.
The original sender waits for an event and does not inspect completed TX/count.

OUT0 initialization at0x10009143..0x100091a2 builds the ordinary sink descriptor;
SUBPTR's embedded SETUP record is distinct. The tail at0x10009898..0x100098f6
checks only owner2 before rebuilding status. It does not prove the strict status
acceptance policy or the actual sink allocation size. The64-byte allocation here
belongs to the explicitly supplied packet64 profile.

Pinned `amd5536udc.h:313–340,464–473` supplies the family normal-descriptor field
map. Linux's early IN giveback at `snps_udc_core.c:2700–2704` and zero-length
shortcut at1094–1120 are not copied: publication is never synthetic completion.
TDC/wake events can coexist with faults and contain no original cookie. Neither
family agreement nor the stock event wait proves settlement or CPU visibility.

Still external: actual mode/reset values, BF/DU behavior, mappings/aliases,
cache and DMA publication ordering, descriptor atomicity, SETUP capture,
IRQ error ordering and identity, successful actual count, abort/reset quiescence,
stalls/toggles and address commit timing. No RAM test can establish those facts.

Execution evidence is `analysis/usb-path/udc-ep0/validation.{json,md}`;
`open-firmware/udc-ep0-test/README.md` owns the fixture contract. Exact first
50-host build-stop and subsequent50/50 passed sources/captures are preserved in
`analysis/usb-path/udc-ep0/source-snapshots/`. The failure was an unadapted draft
build path, before target compilation/execution. The component C/H did not change.
Target descriptor component plus four allocations measures296 bytes beyond the
existing adapter's128536 bytes. These counts establish no physical transfers.
