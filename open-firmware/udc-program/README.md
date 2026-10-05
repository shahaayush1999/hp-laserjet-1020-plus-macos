# Endpoint programming and status-command construction

This is experimental freestanding C behind injected logical register-I/O hooks.
The first integrated run passed28 sanitized host/28 QEMU cases. No live MMIO
implementation is included. The repository's controller descriptor components, ingress
bridge, original cookies, recovery promises and no-buffer status owner remain
the sole owners of their existing state.

The missing operation addressed here is concrete: actual TinyUSB endpoint-open
and configuration-close callbacks issue the reviewed endpoint register commands,
and an existing one-shot typed SC/SI permission can immediately issue CSR_DONE.
The recording fixture checks actual callback commands and immediate grant writes.
This unit does not implement IRQ sampling, descriptor publication/completion,
SETUP acquisition, startup, physical cancellation, PHY/wrapper access or output.

## I/O and supported profile

`read32(context, offset, output)`, `write32(context, offset, value)` and
`order(context)` return OK, NOT_PERFORMED or UNKNOWN. Offsets are relative to the
reviewed register block; no base address or physical pointer is accepted. A hook
must perform its CPU operation synchronously without reentry or new ingress.
The hook contract concerns CPU I/O ordering; success is not proof of device-side
completion, DATA0, memory settlement or USB ACK.

The fixture consumes a queued sequence of explicit read observations
and record write/order attempts independently. A write must not automatically
become the next read value. There is no modeled self-clear, NAK acknowledgement,
FIFO transition, DMA completion or default-state restoration. Fills0/204 apply
to ordinary allocations/guards, not to arbitrary invented command-register
values. Positive read scripts must use a separately reviewed valid register
profile. A failed/unknown write keeps the exact successful/uncertain prefix.

Only full-speed bulk OUT1/IN1, MPS64, interface0/alt0 are supported. The explicit
HP candidate NE slots are OUT1 +0x508 and IN1 +0x50c. The backend never writes
EP0 +0x504, inherited OUT1-alt1 +0x510 or any other NE entry. A coherent complete
table, including the unused alternate, is an external startup prerequisite.
No NE enable bit is invented and a zero NE word is not called disable.

The IN FIFO allocation is a supplied fixed number of words, at least16. Every
IN programming attempt reads +0x028 and checks its low16 against that allocation;
it never changes FIFO size. Stock writes64 words for IN1 and16 for IN0, whereas
Linux chooses a different full-speed default. None proves total HP FIFO geometry.
The integration should initially supply the stock64-word candidate for IN1,
with allocation/overlap/capacity remaining explicit external facts.

Program facts are seven exact booleans: logical I/O profile, packet64/BE DMA,
dynamic CSR support, affected non-control DMA/FIFO/event quiescence, coherent
complete table, valid FIFO geometry, and safe IN SNAK point. The last condition
includes the documented IN-token/empty-TxFIFO prerequisite; source-DMA completion
alone does not satisfy it. Low-level register and descriptor byte order remain
separate assertions. TinyUSB FULL enum0 is never written as a device speed field.

## Emitted commands

The program operations use read/modify/write only for reviewed fields. Logical
EPCTL writes suppress old F/P/SNAK/CNAK/RRDY intent and RO NAK (`0x3ca`), then
request only SNAK. Open also replaces ET with bulk and clears the S bit. That
clear is programming intent, not proof that host-observed HALT or DATA0 changed.
Unrelated read fields are preserved under the supplied register profile; no
unknown read pattern is promoted into a supported hardware state.

| Operation | Ordered register operations |
|---|---|
| OUT1 open | R/W +0x220 ET/S/SNAK; R/W +0x22c low16=64; R/W +0x508 low30=0x020000c1; R/W +0x418 clear bit17; order |
| IN1 open | R +0x028 check fixed allocation; R/W +0x020 ET/S/SNAK; R/W +0x02c low16=64; R/W +0x50c low30=0x020000d1; R/W +0x418 clear bit1; order |
| Bulk close | R/W +0x418 set bits1/17; R/W +0x220 request SNAK; W +0x234=0; R/W +0x020 request SNAK; W +0x034=0; order |
| Granted status | R +0x404; order; existing bridge consumes permission; W +0x404=`read\|0x2000`; order |

The close sequence has an independent quiescence prerequisite before its first
write. It does not obtain that prerequisite by masking IRQs, SNAK, clearing old
descriptor pointers, or resetting software. It establishes bounded NAK,
IRQ-mask and old-DESPTR-clear intent, not logical/NE disable. It leaves NE entries
intact and does not issue FIFO flush, global RDE/TDE, DEVCFG, DMA-reset or USB-reset
commands.

CSR_DONE additionally requires five supplied booleans: I/O profile, dynamic CSR,
completed endpoint defaults/DATA0/halt, current physical status gate, and stable
DEVCTL throughout read/order/permission/write. Hardware can auto-clear RDE, so
software serialization alone is insufficient. This first backend also requires
**read-back RDE=0**; RDE1 returns WAIT before permission is consumed and is never
replayed. Resume/flush/CSR_DONE command bits must read zero. A legitimate software
bulk owner may exist while actual receive DMA is disabled. This is deliberately
narrower than the existing adapter's software permission.

Every stale/current-cookie/core-halt test occurs before bus access. The existing
bridge still performs the authoritative one-shot mutation immediately before
the write. No grant escapes for deferred use, and no descriptor/ZLP/completion/
ACK callback is generated. The original no-buffer owner remains retained.

## Scheduling, selection and errors

Call `service()` instead of direct adapter service. It retains the bridge's
scheduling rules and establishes the only legal DCD open/configuration-close
callback window. DCD submission callbacks must first check
`submission_allowed()`, which is also valid during that window. It is explicitly
mutating: a current raw SC0 status which retains old open-command history or has
an unsupported request shape latches its original REQUEST failure before any owner
is bound. Outside a trusted current stack callback, stale active request bytes
cannot create that failure. This is a failure barrier, not a replacement for
the descriptor components' owner checks.

Use `progress()` before ordinary service/arm/pump and require all three bits for
finish/close-input/finish-reset and manual descriptor publication. This preserves
the prior bridge rule and additionally blocks a failed backend or an unprogrammed
typed SI after it has entered service. A typed SI superseded before its first
service creates no committed programming/recovery operation. Normal protocol
service may prepare control traffic; do not call the
idle-only `progress()` recursively from a DCD callback. Already-authorized DCD
callbacks instead use `submission_allowed()` and the existing component gates.

Typed SI has no TinyUSB open callback. After service, call `complete_selection()`
to run the same OUT/IN programming sequence before recovery/grant. It retains its
original current ticket and the existing auto-status owner. A duplicate SI is
stale. A newer raw request cannot erase the outstanding programming requirement;
another valid configuration can establish a fresh binding.

The same helper handles typed SC0 when TinyUSB was already unconfigured and did
not call close_all. This matters after a real reset: reset does not erase prior
programming history. If that history still contains completed open commands,
the helper issues the ordinary close sequence under new supplied facts. If the
recorded state has no completed-open command history, repeated SC0 is a no-op;
it does not restamp the old selection ticket or claim new physical programming.
Ordinary raw SC0 uses only the core's actual configuration-close callback. When
the core is already cfg0 and emits none, this backend does not manufacture one;
its old command history remains retained. The actual status submission is
rejected and latches REQUEST failure if completed-open command history remains.
Malformed raw low-value0 aliases are rejected there too, even if history was
initially empty. Exact explicit cleanup and a new request are required; the
reset notification alone cannot supply cleanup. Fresh canonical raw SC0 and
raw SC0 after a successful ordinary close retain their normal status path.

A failure retains the existing original sequence/control/transport ticket,
exact failing operation/offset/value, hook result and whether status permission
had been consumed. Sequence0 remains raw provenance. No new allocator, transfer
owner or event queue is introduced. This local record covers failures from void
close, post-service SI and CSR_DONE even when adapter.driver_open never creates
an adapter programming ticket. The first failure remains unchanged.

In an actual open/void-close callback, absent/malformed supplied prerequisites
also latch failure; the core cannot continue to a status submission and silently
count that operation as done. After TinyUSB unwinds, `service()` reports the new
backend failure even if the core otherwise returned OK. Ordinary progress then
stops. An already admitted actual reset can still drain with SERVICE-only; exact
original-cookie settlement remains permitted. This is a software barrier, not
an implemented physical abort. No response bytes are released by failure.
Trusted callback identity and supported request fields are separate checks.
The pinned core narrows configuration to its low byte and can dispatch malformed
raw aliases; those genuine callbacks latch REQUEST failure before I/O. Calls
outside the current service/callback window remain INVALID without inventing a
failure identity. The callback's existing raw sequence0/control/transport ticket
is saved before adapter open-failure fencing can advance transport identity.

After grant consumption, every failed/uncertain write or final ordering hook is
terminal for that grant. Even a definite NOT_PERFORMED result is not retried.
Cleanup requires the exact still-retained failure ticket, a separate physical
programming-clean promise, stopped/unmounted software and no retained adapter
owners/reservations/response. A matching adapter dirty ticket, when present, is
cleared through its public cleanup API. Reset/new ingress alone never clears
either record. Cleanup performs no I/O or reopening and supplies no document
recovery promise; an old cleanup cannot clear a later failure.

## Evidence and limits

The pinned Linux header supplies the layout and masks; the original HP literal/
store anchors establish the explicit NE arrangement. The independent field
formula yields the full-speed words above rather than the stock startup's
512-byte bulk values. Sony rev1.1.0 pp1153/1155/1160–1161 support the SNAK,
HALT and fixed-FIFO constraints; pp1134/1138/1211–1212 and AMD33238G pp321/323
support the conditional status gate. Sources and provenance remain under
`analysis/usb-path/controller-reference/`.

HP mode capability, initial state, unused table entries, valid logical register
access, cache/interconnect behavior, FIFO geometry, physical quiescence, event
chronology, status acceptance, actual enumeration and printing remain unproved.
Current command-construction and integration results are in
`analysis/usb-path/udc-program/validation.{json,md}`. Recording-I/O tests do not
discharge the external conditions above or authorize a physical backend.
