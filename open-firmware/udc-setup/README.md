# SETUP capture bridge

The bridge joins a copied controller-format SETUP record to the existing
TinyUSB/class/document adapter. It is exercised by the 34 host/34 QEMU composed
cases in `analysis/usb-path/udc-composed/validation.json/.md`, with its own 88-byte
target state/source-allocation budget. It reuses the completed 70-case stock
admission/conversion evidence. It implements no live DCD, interrupt path,
physical record acquisition, DMA/cache work, rearm or ACK.

## Narrow API and identity choice

`hp1020_udc_setup_init(bridge, adapter, setup_dma)` runs once after a fresh adapter
initialization, before control events/submissions. The application already owns
the dedicated SETUP allocation; `setup_dma` is its explicit numeric label. The
bridge owns one copied16-byte observation and a few identity/diagnostic words.
It has no queue, allocator, packet cookie or additional control state machine.

`offer(observation)` freezes one valid-source immutable record before validation.
`dispatch(original_sequence, capture_facts, ep0_stalls_cleared)` validates that
retained record and calls the existing `hp1020_tusb_adapter_setup()` with its exact
eight wire bytes. Offer `OK` means a retained capture; dispatch `OK` means request
admission, not a USB transfer or acknowledgement. Adapter service and retained
packet settlement remain separate. Printer status is frozen with the original
observation and keeps the class's existing validation/fallback policy.

An unsolicited SETUP precedes every adapter submission and cannot possess a
normal EP0 cookie. The caller therefore supplies one nonzero, strictly increasing,
nonwrapping ingress sequence, shared by SETUP captures AND actual bus-reset
notifications. It assigns the sequence once at ingress and retains it across
copies/deferred callbacks and descriptor reuse. The component compares supplied
identities but never allocates one. Identical bytes with sequence21 and22 are
two requests; a second sequence21 is stale even if the source address changed.

This single lifetime order removes the need for a separate external reset-domain
counter. `bus_reset(original_sequence, FULL)` retains that reset in the single
pending-event tag before delegating to the existing adapter. This supersedes an
older held-capture tag while preserving its bytes. If the adapter returns `WAIT`,
later offers and every dispatch remain blocked; only the same original reset
sequence can retry. A newer reset remains caller-owned and waits too. The reset
barrier commits and the retry tag clears only on `OK`. Nothing releases a
controller record or settles a transfer. The protocol identity remains the
adapter's own control epoch; the bridge records it and detects accidental direct
SETUP/reset admission around the bridge. Only full-speed reset is supported, so
the retry's speed is fixed rather than adding another saved variant.

Example, all events in original chronological order:

1. Offer sequence10 and retain it while stall-clear is unknown.
2. Admit actual reset11 through the bridge. Capture10 is now stale.
3. Offer SETUP12, which physically arrived after reset11. Its dispatch returns
   `WAIT` while the adapter's pending reset retains an old EP0/bulk owner.
4. Supply genuine settlement for that owner's ORIGINAL cookie and service the
   pending reset. Dispatch12 now copies the retained bytes exactly once.
5. A late capture10 or duplicate reset11 stays stale. A new identical request13
   is admitted normally. Another reset14 invalidates any older pending capture.

If reset admission returns `WAIT`, it has not committed the adapter/reset barrier,
but the bridge retains its exact retry tag and blocks overtaking. A pre-reset
capture cannot revive while the reset waits. The caller must not reorder or
silently drop an earlier destructive SETUP to invent a usable sequence gap.
A repeated physical bus reset is a NEW sequence, not a duplicate.

`UINT32_MAX` is reserved as a terminal ingress-limit observation, not a request or
reset admission. A valid-source SETUP observation with that sequence is copied
and retained; a reset retains its original pending-reset tag and older capture
bytes. Both return `LIMIT` without calling the adapter. Ordinary progress must
stop through the permission gate below; neither wrapping nor reinitialization
is a recovery operation. Adapter identity exhaustion independently returns
`LIMIT` and may already have changed control identity/fenced owners, so the bridge
records the resulting epoch, retains its pending event and fails closed. Read-only
`terminal` distinguishes local sequence1 from adapter2 exhaustion.

## Ownership, facts and scheduling

The configured source is SETUP SUBPTR storage, separate from ordinary OUT0
DESPTR and both EP0 component staging/status buffers. Each observation contains
BE status at0, opaque reserved word at4 and eight raw USB wire bytes at8. The
bridge's dispatch checks owner2 and RX0 only. Low status bits, L, and the reserved word are
not normal-descriptor pointer/count tests. It does not mutate any source record
or swap any wire field.

The caller supplies `format_be_wire`, `cpu_visible`, and `stable` to dispatch as
exact booleans. They describe the original copy, not a later reread of recycled
storage. Unknown facts return `WAIT` with the immutable capture retained; invalid
boolean values return `INVALID` and also retain it. A wrong DMA label is rejected
before offer takes a capture. Numeric equality cannot establish
physical mapping, hidden aliases, correct SETUP-vs-status event classification,
complete cache maintenance or coherence with the sampled descriptor status.
Those remain caller obligations. The observation object itself must be readable
and immutable during offer. Numeric pointer checks do not validate actual
allocation validity. No live peripheral is read.

Owner-not-DONE returns `WAIT`; a supplied endpoint fault or nonzero RX status
returns `FAULT` without adapter admission, retaining the capture. A later
assertion must still describe this saved snapshot; it cannot refresh a busy
snapshot from newer live bytes. In particular, no transport-epoch fault API is
called using an EP0 epoch
or a made-up packet cookie. An ingress fault must stop ordinary protocol/input
progress until the real controller owner resolves it; the permission gate blocks
ordinary work while the capture stays held. This bridge cannot invent the right
physical fault-recovery operation. An actual later supplied bus-reset observation
can supersede the capture. There is no generic SETUP-fault discard/recovery API.

After offer succeeds the original observation may be overwritten; the component
has its private copy. This grants no permission to return live DMA storage to
the controller. After dispatch succeeds the adapter has its own eight-byte copy;
the bridge leaves its previous record bytes unchanged. A second pending capture
is not stored: newer offer returns `WAIT` and remains externally retained. In the
usual path, immediate dispatch frees the single slot and the adapter's existing
pending-SETUP replacement policy handles subsequent requests.

New SETUP admission must precede ordinary protocol service/pumping after that
capture becomes known. Otherwise an old DATA completion could continue a reply
after its superseding request was already captured. The integration owner must
enforce `hp1020_udc_setup_progress()` before every forward operation:

- SERVICE1 permits `adapter_service()`.
- ARM2 permits `adapter_arm_out()`.
- PUMP4 permits `adapter_pump()`. `adapter_close_input()`, `adapter_finish()`,
  `adapter_finish_reset()`, manual EP0/OUT descriptor publication and other
  output-driving operations require all three bits. `finish_reset()` can restart
  input and submit a deferred control ACK, so it is forward progress rather than
  merely a supplied reset promise. Exact-cookie settlement and `ack_reset(part)`
  remain allowed independently; SERVICE-only permission cannot authorize an ACK.
- Normal permission is7. A held capture, reset retry, local/adapter terminal
  condition, busy context or changed adapter control epoch blocks ordinary work.
- SERVICE-only1 is the narrow exception for an already admitted pending reset.
  Its saved actual control epoch is current but differs from the adapter's
  active control epoch. Service can drain that reset's settled owners and deliver
  the reset; afterward the permission is recomputed. No private adapter
  `pending_kind` value is inspected. This remains permitted with a later held
  capture or local terminal condition; an unadmitted reset retry still blocks.

Exact-cookie settlement/fault ingress and queued cancellation marking remain
allowed independently of these forward-progress permissions. The predicate
cannot itself stop DMA, fence the adapter, or stop a caller that bypasses it.
The composed fixture must exercise the actual gates rather than merely log their
values. Calls rejected before any offer captures an event remain caller-owned;
do not treat an argument failure as permission to lose a known incoming event.

All functions run in one serialized context after any initiating TinyUSB callback
returns. No IRQ scheduling API is provided. `request_cancel` callbacks only queue
component cancellation work, drained after dispatch/reset returns.

`ep0_stalls_cleared` is an independent supplied fact before dispatch; false waits,
2/255 reject. The bridge never clears controller stalls or treats SETUP receipt
as settled IN/OUT DMA. TinyUSB resets its SOFTWARE EP0 status upon SETUP; hardware
stall clearing is a separate port responsibility. In particular old IN staging,
OUT status sink, bulk input and accepted output retain their original owners.
Cancellation still goes through the existing descriptor components and original
adapter cookies, and all three class recovery promises remain external.

## Byte and source evidence

Paths below are relative to the repository root.

- `analysis/sihp1020.elf` SHA256
  `2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d`.
  Original literals at `0x10005ee8..0x10005efb` are
  `1001bbc0 1001bc60 1001bc68 b3000210 b3000214`: separate SETUP global,
  OUT0 descriptor/sink globals and SUBPTR/DESPTR. Global `0x1001bbc0` initially
  contains `90021340`; raw packet bytes begin at `90021348`.
- Original `0x10009361` bytes `8b80` load status pointer through SUBPTR;
  `0x10009387..9396` compare owner mask `c0000000` against `80000000` then
  require RX mask `30000000` clear. `0x10009399..939f` bytes
  `18f2d3 2c8200 24cc08` separately reload the request global and add8.
  The bridge deliberately uses one snapshot, not the stock two-pointer assumption.
- `scripts/validate-hp1020-usb-setup-ingress.py` and
  `analysis/usb-path/setup-ingress.json/.md` own the completed70-case execution.
  Only wIndex and wLength are swapped by original `0x10009399..0x1000940b`;
  passing that converted buffer to TinyUSB would swap those fields twice on BE.
  This bridge instead passes the unchanged raw wire bytes. Report JSON SHA256
  in the reused evidence: `06f11e47627fa1a4f1282478d8426e5c11456d02108596a363801f556bb0bc30`.
- Pinned Linux v6.12 commit `adc218676eef25575469234709c2d87185ca223a`, under
  `analysis/usb-path/controller-reference/linux-v6.12/`:
  `amd5536udc.h:295–312` SETUP status fields;
  `:437–441` SUBPTR/DESPTR distinction; `:451–473` SETUP/normal record shapes.
  `snps_udc_core.c:2437–2480` acknowledges IRQ/status, handles BNA and SETUP,
  requests IN NAK, copies the two wire words, then restores HOST_READY.
  This ordering is family reference evidence, not an HP rearm/cache/abort proof.
  Header SHA256 `8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648`;
  core SHA256 `c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf`.
- Pinned TinyUSB0.21.0 commit `dae3f9a366bfcddbf9dcf1b48d7500286a849539`:
  `vendor/tinyusb-0.21.0/src/device/dcd.h:217–227` copies8 wire bytes and converts
  all three16-bit fields; `:173–175` expects automatic hardware EP0 stall clear.
  SHA256 `baf785f2d5d8e3f74bd6d6a04559fc606d341983aad35aa08e168b452c2750db`.
  `usbd.c:729–755` handles queued SETUP and clears only software EP0 status.
- Existing `open-firmware/tinyusb-printer-adapter/hp1020_tusb_adapter.c`:
  `setup` copies raw bytes and invalidates control permission; `bus_reset`
  admits the reset boundary; `deliver` suppresses superseded EP0 callbacks;
  `service` waits for actual owners before SETUP dispatch. New code calls only
  those existing admission APIs, never TinyUSB event helpers directly.

## Remaining physical integration obligations

The shared ingress sequence is a real future DCD obligation. Without
it, exact-once capture cannot be inferred from status bits, payload equality,
address, or the currently active control epoch. A backend that cannot preserve
one global nonwrapping order would need an explicit reset-domain + sequence
ticket instead; do not silently retrofit such a counter into this helper.

The one-slot backpressure and enforced integration permissions are deliberate.
The composed tests exercise retention through pending reset, original-sequence
retry, old completion priorities and deferred publication without a general
event queue. Actual IRQ overflow/SETUP overwrite, coherency, endpoint faults,
hardware stalls and cancellation remain open physical port requirements. A real
integration must establish these facts before using this RAM-only bridge.
