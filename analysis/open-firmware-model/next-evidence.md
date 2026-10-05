# Work needed for a practical replacement

Keep research tied to implementation decisions. The replacement may use a simple
event loop and different buffers from HP. JBIG-KIT already supplies software
image decoding; TinyUSB supplies generic USB handling. Neither Linux nor an RTOS
is a prerequisite. The installed foo2zjs Mac driver remains separate.

## Next: one outgoing reply packet

`open-firmware/tinyusb-printer-adapter/` opens IN1 but owns only EP0 OUT, EP0 IN
and bulk OUT. `owner_for` cannot bind IN1 and `driver_xfer` rejects it. Implement
one bounded packet through actual TinyUSB endpoint claim/transfer/callbacks before
adding PJL formatting. This is the immediate missing software capability.

Original-byte evidence is in `analysis/usb-path/in1-construction.json` and
`usb-bulk-callbacks-model.json`; the generator pins the original ELF and cut.
The stock function at `0x10008bac` queues outgoing bytes, and `0x100081f4` is its
send wrapper. Queue acceptance retains the source and returns before transmission;
`0x10008b78` later frees done heads' original sources. It is not an RX completion.

The original construction cut `0x1000899f..0x10008b41` executes before publication.
It writes one 16-byte BE descriptor, preserves its reserved word and the record's
original-source/done fields, and adds `0x80000000` numerically to the source.
For length <= cap it sets last|length, next=0 and remaining=0. For length > cap it
still builds only one last-marked descriptor, sets next=descriptor+16 and advances
current source/remaining by cap. No mapping, queue, cache or peripheral operation
is established. Zero-length arithmetic does not prove stock ZLP behavior: the
stock queue selector skips zero remaining. Focused interpreter/QEMU checks pass;
the later full regression was intentionally interrupted, as CURRENT_STATUS records.

Implement these bounded semantics:

- Borrow one immutable 0..64-byte source with an original by-value cookie. Use
  explicit NULL/0 for a requested ZLP; do not add automatic ZLPs or HP heap queues.
  Bind only inside the synchronous DCD submission window. Admission failure takes
  no ownership; failure after binding retains the exact source and cookie until
  real settlement and callback drainage.
- Add a separate IN owner/result. Split OUT admission/finish predicates from
  combined bulk reset/cleanup predicates. Review `owner_for`, bind, complete,
  fault, deliver and class callbacks, plus `no_owners` in `udc-program` and
  `udc-publish`, which currently enumerate only three owners. IN must never call
  `receive_complete_data` or release an OUT reservation.
- Use the transport epoch, unique submission ID and sequence0 for IN. A benign
  SETUP only supersedes EP0. Destructive reset/reselection must drain both bulk
  directions. A late success releases its old owner without authorizing a reply
  in a newer transport binding.
- Return a polled completion with original result/count/cookie and a separate
  current-binding permission. Recheck that permission when consumed. Settled
  results may survive reset for the caller to collect; they block another IN send
  but need not block endpoint reset after actual DCD/TinyUSB callback drainage.
- Normal input close/finish may still allow a final reply when the active and
  current transport epochs agree. A destructive fence invalidates that binding.
  Require exact-length success for this bounded packet. Preserve result drainage
  on identifier exhaustion; stale malformed cookies cannot erase fresh recovery.
- Reuse EP0's owned staging, explicit DMA spans and cache/settlement seams for the
  eventual IN publisher. TinyUSB BUSY must clear through its real callback.
  Source release, FIFO settlement and host receipt remain distinct.

Validate the changed adapter and affected controller/entry callers with exact
payloads, retained failures, late callbacks and reset reuse. Production layout
changes need fresh affected entry/layout/stack checks; never force old addresses
or patch report hashes to keep old reports green. No production IN owner, PJL
formatter or physical-status provider has been implemented yet.

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
