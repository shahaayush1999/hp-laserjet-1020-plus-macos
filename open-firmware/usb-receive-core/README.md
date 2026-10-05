# Bounded receive and document composition

This is compiled software for a future controller adapter. It does not access
USB registers, build a device image, schedule DMA or run on the printer. The
existing installed Mac driver and inert probe stages are separate.

`hp1020_usb_receive` owns four stationary, 16-byte-aligned 1024-byte buffers.
Reservations carry a generation and sequence. Completion can arrive in any
order; consumption remains in reservation order. Full storage applies
backpressure. A slot cannot be reused until its consumer releases
it. Duplicate, consumed and old-generation tickets cannot mutate new work.
Both identity counters stop before wrap.

The controller adapter must provide a stable, CPU-visible data/status snapshot
and report endpoint-wide faults before allowing consumption. The queue admits
owner 2, RX field zero, last flag set and count within the reservation. Only
ownership/count extraction is established by original execution. RX-zero and
single-descriptor last are conservative acceptance policies, not documented HP
success semantics. Encoded zero is an empty transfer, never stream EOF. BNA/HE
or any other nonzero endpoint fault fences the generation, even with an empty
queue or already-ready descriptor. Stale-generation faults are rejected.

`hp1020_usb_document` connects this queue to the existing bounded ZjStream,
JBIG and output-ring implementation. Pump returns WAIT for a delayed head and
releases only successfully consumed input. Validated END_PAGE drains software
output; END_DOC optionally reports original receive generation, one-based document
ID and encoded-page range. Empty documents have zero pages. These boundaries do
not close admission, finalize input or advance generation. A callback error is
sticky and retains the current/later input even when output has already drained.
Callbacks must copy event values, remain nonreentrant and are preserved on restart.

Explicit finish is shutdown: the caller first closes external admission and
consumes every reservation. Missing END_DOC stays TRUNCATED even after complete
page output. Short/ZLP transfers do not finish documents. Calling `receive_stop`
instead prevents both pumping and finishing. The extended initializer attaches
an optional document consumer; the original initializer remains a wrapper.

`hp1020_usb_document_init_cooperative` instead performs one bounded input or
decoder step per pump call. The outer loop advances the exposed pump ring through
peek, acceptance and actual completion. Output waits retain the original receive
ticket and byte cursor, compressed data and output storage. The PJL command pump
can own that cursor instead; never mix both input owners. Document notifications
keep the original receive generation. The synchronous initializer remains valid
for existing callers; the entry experiments still use that mode.

Stop/error fences all new work and retains input/output storage and ownership.
Restart requires two distinct acknowledgements for the stopped generation:

1. The receive adapter confirms no old DMA/write/callback can touch its storage.
2. The output consumer confirms no old output operation/callback can touch its
   published or accepted storage.

These calls assert external conditions; the code cannot establish them. An empty
software list, descriptor owner, timeout or reset request is insufficient. After
both acknowledgements, restart advances generation and resets parser/output
state. When using the composition, never restart its embedded receive queue
alone. Init is first-use only. Every API and callback is serialized and
nonreentrant; interrupt marshalling, visibility, memory barriers and real
controller/engine shutdown belong to future ports.

The pinned Linux controller source is a reference, not a linked dependency.
Its global receive-enable and platform-dependent abort/reset paths do not give
us an HP cancellation sequence. See
[`controller-family.md`](../../analysis/usb-path/controller-family.md) for the
byte comparison, original software-list drain and upstream limitations.

Run `python3 scripts/validate-hp1020-usb-receive.py --target` from the repository
root. The validator uses sanitizers on the host, then independent QEMU execution
of the same freestanding C. It verifies exact pixels against separately decoded
source patterns, FIFO/late completion, input poisoning, all status states,
endpoint faults, stale identity, checked overflow and recovery. Exact pre-stop,
pre-fault and pre-acknowledgement snapshots retain all memory and ownership;
both acknowledgement orders are exercised with accepted output still present.
Original stock execution remains a distinct category.

The receive/document state uses fixed storage, shared between the synchronous
and cooperative decoder modes. The report records its compiled target size,
excluding code, stack and test captures. Copies remain metadata. Hardware boot,
actual USB, cache behavior, physical pixel packing, engine output and recovery
remain unproved. Reports: `analysis/usb-path/receive-core/validation.json/.md`.
The cooperative USB/PJL path is exercised separately by
`scripts/validate-hp1020-cooperative-usb.py --target`, including a real TinyUSB
control request during an output wait, cancellation with retained input/output
and reply ownership, and exact pixels after gated recovery. Its controller and
completion observations are supplied in RAM; it does not establish device I/O.
