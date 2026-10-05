# Work needed for a practical replacement

Keep research tied to implementation decisions. The replacement may use a simple
event loop and different buffers from HP. JBIG-KIT already supplies software
image decoding; TinyUSB supplies generic USB handling. Neither Linux nor an RTOS
is a prerequisite. The installed foo2zjs Mac driver remains separate.

## Checked reply path and its remaining integration

The TinyUSB adapter now borrows one immutable 0..64-byte IN packet, returns its
original result/cookie and keeps late/cancelled replies separate from current
transport permission. Actual callbacks drain BUSY. Normal input finish permits
final replies; destructive recovery waits for both bulk directions. See the
adapter header and its focused `bulk-in-validation.json`.

`open-firmware/udc-in/` adds one descriptor and a separate 64-byte staging buffer
through that real DCD callback. Mode, CPU/DMA mappings, visibility and terminal
memory access remain supplied. It does not publish registers. Memory release,
FIFO retry/capacity and host receipt are distinct: do not require an invented
wire-ACK counter to free a DMA source, or assume that freeing it empties the FIFO.
The new component's latest tested source closure is `udc-in-validation.json`.

`open-firmware/udc-in-publish/` now supplies the narrow recording-I/O publisher.
Original bytes at `0x10008b41..0x10008b75` load the descriptor cell, write its
value to `0xb3000034`, clear bit1 of `0xb3000418`, then OR8 into `0xb3000020`,
with MEMW ordering. Literal words at `0x10005e00/7c/84/88` bind these addresses.
The pinned Linux family header names control bit3 Poll Demand. This static
sequence does not establish the preceding NAK/FIFO state. The implementation
requires a stable binding, packet64/BE with transmit DMA already enabled and
independent TX-idle/FIFO-empty evidence. It adds CNAK with supplied safe RX-empty
interval and independent readback before POLL. It accepts concurrent receive DMA
without rewriting DEVCTL. Any failure after cache work retains the original
owner and poisons the attempt through cancellation/cleanup. No IRQ observation
or host receipt is invented; newer family FIFO-empty bits remain unproved on HP.
Current host/target checks are in `udc-in-publish-validation.json`.
`open-firmware/usb-service/` now joins program/ingress/OUT/IN/command gates.
Its ready hook includes the existing gates, and IN failure blocks new programming
and OUT publication. Captured control input also blocks DCD submission; this
callback-safe predicate permits adapter-busy callbacks without bypassing the
ingress epoch/reset barriers. Real SET_INTERFACE selection can still complete
from SERVICE-only permission. Original-result collection can run behind failed
gates without pumping input/status or sending a new reply. Its focused
`usb-service-validation.json` checks both directions, programming failures and
reset drainage, plus exact two-page pixels. This is component coordination;
entry-loop integration and a physical backend remain absent.

Original IN1 construction evidence remains in `in1-construction.json` and
`usb-bulk-callbacks-model.json`. Queue acceptance retains the original source and
returns before transmission; done-head cleanup frees it later. For length>cap,
the tested arithmetic constructs only one last-marked descriptor and advances
remaining/source. The numeric source+0x80000000 is not a proved DMA mapping.
The stock queue skips zero remaining; replacement ZLP support is explicit policy.

`open-firmware/pjl-command/` now implements the bounded PJL ECHO response through
real incoming reservations, the decoder, TinyUSB and recorded IN publication.
Its current source-bound host/target result is `pjl-command-validation.json`.
Normal host jobs also request
status, but do not emit JOB START/PAGE/END from decoded input: the Mac backend's
START disables its eight-second no-status fallback and makes it wait for physical
completion. Preserve exact job tokens for eventual truthful status. Its firmware
recognition also requires the IEEE-1284 ID's `FWVER` field; a future replacement
must identify itself truthfully so the host does not try to reload stock firmware.
Physical-status providers and other PJL replies remain unimplemented. INFO STATUS
now formats a supplied current CODE/ONLINE snapshot, with an empty DISPLAY and
no response for unavailable/stale observations. Its actual staged bytes match
executed original INFO envelopes. Sampling waits for free reply storage; reset
cannot overwrite an already borrowed reply. This does not enable unsolicited
DEVICE/JOB/PAGE events. The
command pump retains an original receive-ticket cursor under backpressure and
owns one immutable short reply through original-result collection. It routes
binary spans using the existing parser's framing state; PJL inside binary data
and JZJZ inside ECHO text cannot switch modes. The first profile accepts uppercase
ECHO and at most50 printable text bytes, plus exact uppercase INFO STATUS;
unknown PJL lines are ignored, oversized
ECHO is rejected, and a short OUT/ZLP is not EOF. It replaces the ordinary document
pump and exclusively owns bulk-IN result collection. Do not run both pumps.
The shared service integrates controller permissions; entry integration remains
absent. Numeric status conversion is now
recovered from bytes and executed in `status-code-execution.json`; the existing
`status-code-correlation.md` gives conditional CODE results for cataloged events.
The old decompilation omitted the ordinary lookup entirely. Stock scans222 pairs
at0x1001bc84, past111 code pairs into the separate media table and strings; media
lookup scans40 pairs at0x1001be40 although following data begins after20. Do not
copy these adjacent-data aliases into a replacement. E.g. the numeric engine
event0xe6100800 converts to40021 and timeout0xfe001401 to50021, but those facts
alone do not prove sensor meaning, event publication or physical calibration.
The original INFO wrapper0x1000c568, query0x1000bfb0 and builder0x1000b624 now
execute through string assembly and final callback in `status-reply-execution.json`.
INFO samples datastore25 and emits even CODE0. DEVICE0x1000b6d8 suppresses CODE0
before allocation; its other replies use `@PJL USTATUS DEVICE` with the same
CODE/DISPLAY/ONLINE body. Both end CRLF then FF. Decimal formatting, allocation,
locks and final callbacks are supplied boundaries; sensors are not executed.

DISPLAY entry26 has descriptor0x1001d084, original zeroed68-byte buffer0x1001cdbc.
No local writer was recovered; OPMSG/RDYMSG/STMSG all call0x1000d2a8, whose inspected
bytes consume syntax without writing this buffer. Exported datastore service
slots62–67 leave external clients possible. ONLINE is the separate datastore24
value, not a consequence of a numeric code or an empty software queue.

The original updater0x10010838 passes the normalized candidate saved at[sp+32]
through0x10010a37 to0x10010a3c, then as a11 at0x10010a6e to0x1000b6d8. Event
bit0x20000 suppresses notification; the20-client loop requires client+0x40
bits30–31 nonzero. A higher-priority pending candidate can notify without updating
cached datastore25 (stores0x10010909–0b versus publication gate0x100109ae).
Thus asynchronous events cannot be reconstructed just by rereading cached status.
Existing StatusMgr publication/priority tests need not be repeated. Next status
work must connect genuinely current engine observations to a provider; another
formatter/model would not supply that missing capability.

## USB hardware questions that remain

The recovered layout matches the classic Synopsys device-only UDC family;
`analysis/usb-path/controller-reference/linux-v6.12/` is the pinned reference.
It is not the DWC2 layout or proof of an unchanged compatible driver. Current C
constructs/consumes descriptor and register-command records through supplied
RAM hooks. Real reset, cache visibility, mapping and interrupt observations are
still missing. Preserve that explicit boundary.

<a id="next-implementation-seam-hardware-handled-standard-requests-2026-09-30"></a>

The controller manual/stock evidence in
`analysis/usb-path/controller-reference/manuals/README.md` resolves what to ask:

| Question | Needed evidence / implementation consequence |
|---|---|
| Boot and memory | Establish ROM handoff, physical RAM attributes, startup state and safe stack/exception handling. Original ELF ranges and a RAM simulation alone do not prove these. The existing inert hardware ladder owns eventual device tests. |
| DMA/cache | Establish CPU/DMA address mapping, alignment, visibility ordering and when external accesses truly finish. Pointer alias arithmetic and resetting C state do not supply these facts. |
| Interrupts and SETUP | Establish event provenance/order and immutable raw SETUP capture. Current instruction cuts recover selection and byte conversion; task wake hints are not completed transfers. |
| Configuration offload | SET_ADDRESS is family-handled; SC/SI expose sampled fields. HP startup preserves inherited CSR_PRG; dynamic-mode capability/defaults remain unproved. CSR_DONE grants a status response, not host ACK. Keep mode/capability explicit. |
| IN completion | TDC/DMA_DONE can mean data reached TxFIFO while retries remain possible. Do not equate source release with host receipt or assume newer family FIFO-empty bits exist on HP. |
| Cancellation/reset | Establish physical drain and endpoint defaults before buffer reuse. Existing receive/output/transport promises are separate; late events must retain their original identity. |

The existing software and original-code tests already resolve ordinary
configuration/reset bookkeeping, SETUP byte order and conditional cancellation
ordering. Reopen them only for a specific new hardware-facing question.

`open-firmware/xtensa-cache/` now supplies checked call0 writeback,
clean-invalidate and discard-only invalidation for already owned cached spans. They are not linked
into a controller backend. Original16-byte stepping, DSYNC and initial/final
attribute operands are recovered in `cache-contract.json`; its README explains
why this does not establish line geometry, available RAM or a bit31 mapping.
The open routines reject nonempty unaligned/wrapping/out-of-profile spans before
any operation. DHI supplies the CPU invalidation part of an eventual acquire;
it cannot establish completed/visible device writes. All touched lines must be
unlocked, and discard-only invalidation must not lose CPU changes anywhere in
those lines. Actual full-line leases, mapping and hardware effects
remain separate. Do not repeat these operand tests to claim physical visibility.

Original boot memory arithmetic is now executed in `memory-contract.json`;
`analysis/boot-abi/boot-abi.md` records the exact chain. Supplied bits30–31 of
`0xb0800008` select2/8/16/32MiB. Stock reserves16KiB after BSS, then gives the
allocator `0x100391e0` through `0x10000000 + capacity`. That numeric extent also
contains boot-SP/reset/debug addresses; it cannot be copied as a safe replacement
layout. The replacement must reserve its own live objects. Installed capacity,
loader handoff and physical aliases remain unknown. More arithmetic tests will
not resolve those physical facts; proceed with the missing controller/reply
integration while retaining explicit supplied mapping and memory limits.

## Pixels, engine and status

The open stream/image path produces packed rows with bounded storage. Its narrow
profile normalizes an admitted JBIG header, handles default foo2zjs padding and
reuses page metadata. It does not establish printer throughput or physical pixel
format. Copies are metadata until an output implementation replays pages.
Use `open-firmware/image-core/README.md` and its current validators for details.

Prefer software decoding and the stock raw-output route to recovering the custom
compressed-image ISA. Original datastore32 has file-backed value1, suppressing the
custom callback in tested prepare paths. That does not prove every live setting.
`analysis/hardware-boundary/raster-bypass.*`, `raw-parser.*`, `software-ring.*`,
`output-submission.*` and `output-format.*` retain executable findings.

The remaining implementation questions are:

1. Map decoded row packing/polarity/stride to actual output lanes. Original
   payload+0x50 source-kind selection, work+0x74 IRQ selection and engine-derived
   single/dual-output selection are distinct. Source kind2 also changes a hardware
   count flag; it cannot be chosen merely to avoid freeing a borrowed buffer.
2. Supply physical readiness, submission and terminal consumption to the existing
   bounded ring. Supplied completions in stock/native tests do not prove DMA or
   engine acceptance. BPP metadata alone does not define physical pixel order.
3. Recover the smallest engine page-start/completion/timeout/recovery contract
   from the original byte-backed first-page sequence and engine topology. Determine
   what the existing engine controller already handles before rebuilding it.
   No print-driving operation is authorized during this offline work.
   Original engine initialization `0x10016024..0x10016088` overwrites selector
   `0x1001cdac` from command0x92's reply masked by0x7e00: 0x3400 selects1 (dual),
   0x1a00/0x3200 select0, otherwise2. Both0/2 are single-output with different
   format tables. The file-backed2 is not a live-mode guarantee. Existing byte
   verification of this branch does not establish polarity or physical bit order.
4. Connect actual status to paper/jam/cover/error replies. Original port-status
   construction only establishes a fixed byte in the tested cut; don't invent
   physical meanings from event numbers. Long output waits will need cooperative
   progress so cancellation/status remain responsive.
   Next inspect the response producer and interrupt registration behind
   `0x10015c68`'s command/wait helper. Existing polling tests supply that helper's
   result; they do not establish when the captured response is current. Keep
   any execution cut entirely outside engine MMIO and interrupt changes.

## Settled work and validation limits

Current accepted entry captures live in `analysis/boot-handoff/entry-*/` and
embed their tested sources, complete RAM and traces. Component reports live next
to their generators' output. These and focused byte fixtures support development;
old failed runs, review diaries and repeated full-suite snapshots remain in Git.
Do not rebuild historical narratives or expand tests solely to increase counts.

The stock native pipeline already has26 completed lifecycles and six separately
classified conditional null reads; bounded retirement and split-raster work are
also resolved in `stock-execution/`. No need to repeat cancellation/END_DOC or
reconstruct more stock scheduling without an implementation question.
The last whole-suite baseline and newer focused results remain distinct in
CURRENT_STATUS. Tests exercise supplied RAM/software conditions. A working
replacement still requires separately authorized repeatable physical printing
and recovery after a power cycle.
