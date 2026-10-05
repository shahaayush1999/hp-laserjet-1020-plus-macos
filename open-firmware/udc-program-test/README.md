# Recording register-command fixture

The first integrated run passed28 sanitized host/28 QEMU cases. This extends the existing composed/offload RAM
fixture with one reusable register-programming backend and recording hooks.
It is not a controller simulator, boot image, upload image or physical DCD.
Untouched pre-execution drafts remain archived separately from tested sources.

The fixture still has exactly one adapter, printer class, document decoder,
SETUP bridge, EP0 bridge, bulk bridge and original-cookie ledger. Descriptors,
packets, pixel output, document notifications and storage assertions retain
their existing ABI. The new backend is compiled separately. The two optional
shared-fixture seams preserve ordinary builds: op1 invokes a default-preserving
service macro inside the existing storage protection, and the program build
adds real callback/submission/scheduling hooks to the composed fixture.

`program_fixture_open` and `program_fixture_close_all` run only from actual
TinyUSB DCD callbacks. Successful backend calls permit the existing callback
bookkeeping. Failure returns false or suppresses the void close's success
bookkeeping; the backend service wrapper retains the failure. Both the final
`dcd_edpt_xfer` and separate `dcd_set_address` path check submission permission.
That check is never called by diagnostic snapshots: backend V2 may latch a
failure when a genuine raw configuration status attempts to bypass necessary
programming. Ordinary forward scheduling uses the backend progress predicate;
original-cookie settlement and actual reset ingress remain reachable.

The isolated draft package preserves frozen backend V1 and V2 separately.
Backend V2 is required for the malformed raw-configuration and skipped
raw-SC0-close controls. The fixture adds no workaround for either production
failure and does not edit those backend sources.

## Inputs and explicit limitations

The first initialization supplies interface0, OUT1/IN1, capacity64, HP candidate
CSR slots508/50c, fixed64-word IN FIFO, and three initialization facts equal1.
The seven programming facts initially equal1; later input events replace them
with exact bytes, including malformed values. The five last grant facts start0.
These are supplied test conditions, never discovered hardware facts. Other
interfaces, speeds, mappings, mode startup and FIFO geometries are outside this
fixture's first matrix.

The new read FIFO contains immutable `(offset, logical_value, outcome)` words.
Every successful read returns only the next supplied observation; writes do not
feed it or change any simulated register. An offset mismatch, absent read,
wrong context, guard corruption, injection-kind mismatch or storage overflow
increments both a program violation and the existing fixture violation count.
A failed read leaves the backend's output word untouched and records value0,
not a claimed observation. Failed writes retain their attempted value. The
outcomes are OK0, NOT_PERFORMED1 and UNKNOWN2; no failure permits automatic replay.

Every I/O hook attempt records six words in order:
`(input_event, all_hook_ordinal, kind, offset, value, outcome)`.
Event and ordinal are one-based; fixture reset has event0 and no I/O. Kind is
read1, write2 or order3. Order has offset `ffffffff`, value0. One independent
write/order failure schedule names an absolute all-hook ordinal. Read failures
come solely from queued read outcomes; a schedule that instead reaches a read
is a harness violation. No write or order sets defaults, clears RDE, changes a
read observation, acknowledges an interrupt, settles DMA or completes status.

The old independent programmed-map word remains a DCD callback/cleanup ledger.
Explicit `complete_selection` records its real command trace without inventing
open/close callbacks or updating that map. It is not physical endpoint state.
The program variant's existing offload dirty witness also retains first failure
from selection/grant/submission, using an independently copied pre-call ticket.
Nested actual callback/submission entry wins over its enclosing service entry.
Reset and successful cleanup retain the historical witness; only a later first
failure replaces it. Ordinary builds retain their existing offload behavior.

Backend grant observes the actual owner's `auto_granted` transition. It records
one permission consumption even if a later write/order fails. Original typed
request and cookie are copied before the call. No descriptor, wire ZLP, TinyUSB
completion or ACK is fabricated. Cleanup uses the exact supplied original
ticket and clean byte through the backend; only actual success permits the old
synthetic endpoint bookkeeping to clear. Cleanup performs no register operation
and supplies none of the document's three separate recovery promises.

## New event ABI

The existing24-byte event header is six BE words: opcode,a,b,c,d,payload length.
Old operations and the first368 diagnostic words remain unchanged. Only the
program build refuses old direct grant102, open-failure injection106 and
adapter-only cleanup107 with backend INVALID3; they would bypass this backend.
Backend operation results are OK0/WAIT1/STALE2/INVALID3/FAULT4/ADAPTER_ERROR5.
Do not confuse these with results of existing operations in other domains.

| Op | Arguments | Payload | Action |
|---|---|---|---|
|120|a=count; b/c/d=0|12×count BE bytes|Append read triples; at most85 per event,256 total. Invalid outcome rejects the entire append.|
|121|a=kind2 or3; b=absolute future all-hook ordinal; c=outcome1 or2; d=0|None|Arm one failure. A second outstanding schedule returns WAIT; ordinal must be at most1024.|
|122|a/b/c/d=0|Exactly7 bytes|Replace io_profile, mode_packet64_be, dynamic_csr, affected_quiescent, table_coherent, fifo_geometry, in_snak_safe.|
|123|a/b/c/d=0|None|Call complete_selection with the stored seven facts, including when only SERVICE is permitted.|
|124|a=original sequence; b=original saved token; c=existing cookie mutation0..5; d=0|Exactly5 bytes|Grant with io_profile, dynamic_csr, affected_defaults, status_gate_current, devctl_stable.|
|125|a/b/c/d=0|None|Query pending cleanup into retained poison-initialized output; rejected calls must leave it unchanged.|
|126|a=original sequence; b=original control epoch; c=original transport epoch; d=clean byte|None|Acknowledge backend cleanup with that original ticket.|

Unused read observations are retained even after early refusal/failure. The
codec validates payload lengths before calling the fixture; the target replay
must enforce exactly the same envelope. Direct C calls have no payload-length
parameter and therefore rely on that caller contract.

## Program diagnostic64 words

The program block follows the old368 words, giving432 words per row. Word0 is
the latest program operation/helper result, including successful fixture-only
read/fact/injection bookkeeping; the ordinary event result remains base word0.
Pure progress is current; last submission permission reports only a genuine
submission check and is `ffffffff` before the first such call.

| Relative words | Meaning |
|---|---|
|0|Latest program result|
|1..9|initialized,busy,servicing,failed,completed_mask,selection_mask,binding_ready,pure progress,last submission permission|
|10..15|selection sequence/control epoch/transport epoch,service control epoch,last adapter result,last bridge result|
|16..23|failure sequence/control epoch/transport epoch,operation,offset,attempted value,I/O result,grant consumed|
|24..31|read queued,read cursor,trace count,read/write/order attempt counts,guards1,violations0|
|32..35|injection kind,absolute ordinal,outcome,armed|
|36..42|Seven exact programming fact bytes|
|43..47|Five last grant fact bytes|
|48..55|Query output: sequence/control epoch/transport epoch,offset,value,operation,I/O result,consumed|
|56..57|Query result (`ffffffff` before query),sizeof backend|
|58..63|Independent failure entry sequence/control epoch/transport epoch,entry kind,failure witness count,genuine submission-check count|

Entry kinds are service1, OUT-open2, IN-open3, close-all4, selection5, grant6,
submission7. Query output starts with each byte `a7`, including padding; only
explicit fields are serialized. Rejected query output is checked byte-for-byte.
Backend size is intentionally host/target dependent and is a separate measured
component size, not part of the existing adapter/document footprint.

## Captures and build boundary

Public globals are `hp1020_program_fixture_stats[64]`,
`hp1020_program_fixture_reads` and `hp1020_program_fixture_trace`. The latter
two have four guard words, respectively256×3 and1024×6 data words, then four
guard words. Their exact sizes are3104 and24608 bytes. Data starts at symbol+16.
Only appended records may replace the initial fill; consumption does not mutate
read records. All unused tails and guards remain the exact initialization fill.
Fixture shadows also check preservation; independent validation must compare
the complete captured words to its own input/trace oracle.

The host codec saves, relative to its existing output-storage path:

- `.program-read-script`: all queued triples, including any unconsumed suffix.
- `.program-trace`: every actual hook attempt.
- `.program-storage`: complete guarded read object followed by complete guarded
  trace object,27712 bytes total, including unused tails.

All are explicitly serialized BE words. The target reader uses the same public
symbols and exact lengths; C structure pointers never appear in the captures.
The original wire/pixel/document/EP0/bulk/SETUP/storage captures remain present.

The builder retains the existing pinned compiler-profile, patched
TinyUSB materializer, undefined-symbol and target disassembly gates. The
validator audits the target before QEMU. The linker file
places this synthetic fixture in test RAM; it is not a boot or upload image.
Execution and integration belong to the lead. This fixture supplies
no proof of bus semantics, register revision, defaults, ordering completion,
cache visibility, physical status handshake, enumeration or printing.

The fixture covers malformed raw first-open, void-close and skipped-close
status barriers as well as successful page/document output. `trace-oracles.py`
supplies independent literal command sequences. Current results are in
`analysis/usb-path/udc-program/validation.{json,md}` and are checked by
`scripts/check-hp1020-udc-program.py`. No physical bus semantics are established.
