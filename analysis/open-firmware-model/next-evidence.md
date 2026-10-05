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
Current host/target checks are in `udc-in-publish-validation.json`. Entry-loop
integration must make its ready hook include existing program/ingress/OUT-failure
gates, and block new programming/publication on its own failure. This integration
and a physical backend remain absent.

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
Physical-status providers and other PJL replies remain unimplemented. The
command pump retains an original receive-ticket cursor under backpressure and
owns one immutable short reply through original-result collection. It routes
binary spans using the existing parser's framing state; PJL inside binary data
and JZJZ inside ECHO text cannot switch modes. The first profile accepts uppercase
ECHO and at most50 printable text bytes; unknown PJL lines are ignored, oversized
ECHO is rejected, and a short OUT/ZLP is not EOF. It replaces the ordinary document
pump and exclusively owns bulk-IN result collection. Do not run both pumps.
Controller/entry integration remains absent. Numeric status conversion is now
recovered from bytes and executed in `status-code-execution.json`; the existing
`status-code-correlation.md` gives conditional CODE results for cataloged events.
The old decompilation omitted the ordinary lookup entirely. Stock scans222 pairs
at0x1001bc84, past111 code pairs into the separate media table and strings; media
lookup scans40 pairs at0x1001be40 although following data begins after20. Do not
copy these adjacent-data aliases into a replacement. E.g. the numeric engine
event0xe6100800 converts to40021 and timeout0xfe001401 to50021, but those facts
alone do not prove sensor meaning, event publication or physical calibration.
Recover DISPLAY/ONLINE provenance and the builder's actual notification gates
before implementing paper/error/job replies. Existing StatusMgr publication and
priority tests need not be repeated just to reconnect their documented boundary.

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
