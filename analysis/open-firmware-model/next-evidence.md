# Evidence required beyond the offline checkpoint

The offline work now has a byte-verified BE toolchain, corrected direct work
construction, instruction-tested framing and endpoint-0 staging, a bounded C
semantic parser, a page/band planner, and execution of the actual compiled C
components in synthetic RAM. The remaining live questions concern device behavior or
core-specific operations absent from the available instruction definitions.

| Priority | Exact question | Existing evidence | Evidence that would resolve it |
|---|---|---|---|
| 1 | Does the corrected BE probe execute after the ROM loader, and can its own endpoint-0 path return its counter descriptor? | Stock-byte instruction fixtures and offline staging tests pass. The older quiet idle upload used incorrect instruction encoding. | A newly authorized cold-boot inert-probe test that returns the probe-specific descriptor. Stock USB identity alone is insufficient. |
| 2 | Does bulk OUT completion report the actual byte count and permit repeated acknowledgement/re-arm? | Static stock lane/descriptor/callback chain and offline framing tests. | The guarded 36-byte START_DOC/END_DOC transaction returns B=0x24, D=1, C=2, E=0, U=0; a later separately authorized repeat establishes re-arm. No page/raster input is needed. |
| 3 | What do the raster extension instructions do, including hidden state or memory effects? Can the stock-supported callback bypass produce acceptable output? | Exact four-argument callback contract, masks and complete instruction inventories. BPP2/600 has 16 unresolved extension instructions. Compiler annotations locate all 144 generic-decoder-unrecognized sites in four adjacent routines; the fourth has no found static reference. | A core-specific ISA definition or controlled stock callback input/output trace; alternatively, measured stock behavior with its supported bypass setting. Custom opcodes are not assumed safe for a probe. |
| 4 | Do the two video channels implement the inferred compressed-input and row-output handshake, including length/progress units, cache visibility and descriptor ownership? | Original parser/JobMgr execution verifies BIH/BID lists and scheduling; direct VIDEO_Y seed, corrected floor division, bounded host partitions and static channel writes. | A stock first-page trace showing channel lengths/status, buffer contents, ownership transitions and completion order. No custom video writes are authorized. |
| 5 | Which physical engine conditions correspond to the polled status bits/events, and what are safe timing, timeout and recovery boundaries for startup, page start and completion? | Executable status/IRQ decision models and ordered stock command sequences. | Calibrated stock behavior for idle, page acceptance, completion and relevant fault states. Numeric event values are not physical labels. |

The logical-clip metadata mismatch and BPP4 zero-refill case are already isolated
and rejected by the narrow page planner; they are not reasons to expand the
first hardware test. Other modes, malformed-input compatibility and optimization
are outside this first printing scope.

The owner has reframed the task as an offline capability evaluation. Original
stock parser/libc and status routines now execute in isolated host harnesses and
challenge the inferred models directly. These harnesses intercept all device
I/O and record explicit environment substitutes; passing them does not answer
the live questions above. Continue looking for independent binary-derived
checks before requesting physical assistance.

Original JobMgr replay now preserves full page/raster lists, BIH fields and
credit-limited page scheduling against C/input oracles. Split-BID execution exposes
a marker-initialization question: nonfinal payload `+0x4c` inherits allocation
contents through `+0x2c`; END_JBIG overwrites only the final marker with 1.
Separate original type-1 allocator execution confirms it preserves payload bytes.
All 256 tested MMIO-free compressed-render paths ignore this marker; the known
nonzero-to-hardware-flag consumer is alternate raw refresh `0x100140f8`.
Do not infer a physical failure, a zero-fill guarantee, or a new first-printing
blocker. Original render also changes list pointers before busy rejection; the
ring model ordering is corrected. See `stock-execution/jobmgr.md` for boundaries.

Original completion/release and datastore bookkeeping now execute under
serialized and cooperative queue-boundary schedules. The host explicitly
injects successful FIFO completion; it does not model DMA/engine success.
Nonempty jobs drain and recover credits. A conditional counterexample exists:
queuing an empty document behind an unfinished page can make the empty-document
finalizer free the global head; later completion reads a missing child. Eager
completion avoids it. The parser itself locks a producer mutex without waiting
for the job list to drain. Original single-language recognition, pushback, buffered
reads and dispatcher now reproduce that admission and failure across input splits,
including cooperative execution. The broad software-admission question is reduced
to actual transport delivery, multi-language state and RTOS/engine ordering.
Exact scopes and assumptions: `stock-execution/lifecycle.md` and `stock-execution/admission.md`.
This is an offline correctness question, not evidence of a physical printer fault.

Independent QEMU now checks the same compiled C target, all original libc cases
and stock signed/unsigned division/remainder helpers. Original parser messages
and JobMgr lifetime/global RAM also agree, and QEMU reproduces the delayed-empty
cleanup fault. All six original window spill/fill handlers run under nested
CALL4/8/12; corrupting a saved return store is detected. These tests use a synthetic
ABI stack and a different core configuration, not stock boot/interrupt/cache
state. Original status ownership and selected interruption producers now execute
as described below; actual scheduling and hardware stopping remain unverified.

Original constructor analysis corrects a major inherited error: queue 0 is engine,
queue 1 is PrintMgr, and JobMgr queue 3 uses object `0x10023e40`. The former
missing-consumer conclusions for engine event `0x17` and datastore `0x2d` were
routing errors, not hardware blockers. PrintMgr now executes under both CPU
engines: cancellation advances states 0 -> 1 -> 2 -> 0 on two injected stop
acknowledgements and frees only its own list nodes. Its original subscriptions
and datastore writer emit ONLINE changes to queue 1; the original consumer
updates its online byte. StatusMgr releases the remaining JobMgr completion
notices, leaving no tracked live allocations in selected completed lifecycles.
See `stock-execution/printmgr.md` and `stock-execution/notifications.md`.
Original engine cancellation queues acknowledgement 37 before calling the
hardware-stop routine. The original video post-reset RAM tail decrements raster
references and clears its slots before sending 37. Both agree with QEMU under
explicit cut-point preconditions; the omitted hardware reset/wait prefix remains
blocked. See `stock-execution/stop.md`.

Cancellation selectors 2 and 4 now have executed original producer paths. Under
the single-work ownership/reset-tail fixture, selector 2 retains a 120-byte
document allocation; selector 4 after END_DOC reads through null at `0x1000eb6a`.
Acknowledgement before END_DOC avoids that read but leaves an 80-byte child plus
its completion notice. Two fills, raster splits and release-flag overrides agree
across both engines. No aligned reference to the retained document/child remains
in tested non-stack writable RAM. This does not rule out arbitrary encoded
references or prove real-world reachability. See `stock-execution/cancellation.md`.
The precise remaining questions are whether real cancellation reaches the tested
one-work video ownership state, whether reset reaches that RAM tail, and how RTOS
ordering places END_DOC versus acknowledgement. Original status construction and
publication now execute in both CPU engines, including datastore writes, ONLINE
subscriptions, duplicate suppression and a 100-word event-history ring across
wraparound. The numeric cancel-only events produce selectors 1/3/4 without
changing ONLINE; cancellation and offline bits are distinct. Completed lifecycle
notices plus a matching-source clear exercise actual offline/online transitions.
These runs use the constructor's empty language-context table; optional outward
status callbacks and RTOS thread/semaphore creation remain host boundaries.
See `stock-execution/status-publication.md`.

Original RTOS queue creation, indexed send and receive now execute in both CPU
engines against independent FIFO oracles: supported widths, capacity rounding,
full/empty returns, repeated wraparound and created-queue rings. Selected
interleavings also execute wait-list insertion, direct receiver delivery or
waiting-sender refill, and original pending-suspension cancellation. The deferred
suspend helper runs as a fresh call after the wait is satisfied; paused CPU context
restoration and real interrupt timing are not claimed. See `stock-execution/queue.md`.
The combined StatusMgr test pre-enqueues original completed JobMgr notices,
receives/releases them through original queues, publishes its actual queued
outputs, and stops after original empty-queue wait insertion before suspension.
It retains only the persistent ONLINE subscriber. FIFO completion and pre-enqueue
ordering remain fixture choices; outgoing PrintMgr/JobMgr packets are retrieved
but not consumed by those tasks in this test. This removes whole queue substitutes
from the selected status lifecycle while leaving scheduler timing, actual page
completion and optional language callbacks unresolved. See `stock-execution/status-queue.md`.

Original explicit window flushing, initial-stack construction and voluntary
context save/restore now execute in QEMU. The stack builder also agrees with the
interpreter. Saved return/stack and special-register fields match CPU snapshots;
untouched physical data-register slots may alias older windows until access
triggers spilling, so they are not assumed to be preserved incoming values.
Two synthetic tasks repeatedly switch stacks through the original scheduler and
RFE restore, preserving separate arithmetic accumulators and nested return chains.
Those fixture tasks explicitly select each other; timer expiry is covered by
the later timer experiment below, while interrupt-driven preemption remains untested. A saved-continuation mutation is detected. See
`stock-execution/context.md`.

The next kernel experiment now executes original RAM initialization, the
thread-create core, ready lists and priority-driven blocking/wakeup/context
switches for two synthetic producer/consumer tasks. Complete message bytes,
ordering, sum acknowledgement, lowest-set-bit lookup, initial priority choice,
run counts, queue occupancy and final thread states match independent oracles.
Priority equality/extremes, capacity, width and RAM fill vary. All queue/scheduling
services execute original code. Infinite waits and zero time slices avoid timers.
The original task shell also terminates a returned consumer when appropriate.
This kernel experiment uses synthetic tasks; original StatusMgr integration is
described below, while parser/JobMgr/PrintMgr scheduling remains separate. See `stock-execution/scheduler.md`.

Original StatusMgr now runs under actual queue blocking/wakeup and priority
scheduling alongside a native producer of previously generated JobMgr notices.
Thirty cases cover repeated/empty/multi-page streams, both priority orders and
equality. Thirteen documents exceed its 25-message queue and force the producer
to block. Final idle is accepted only after all counters/ownership/output checks
pass; both tasks are suspended on empty queues. The original datastore constructor
prefix initializes 38 binary semaphores, and two original mutexes protect status
and datastore publication. These locks all execute and finish released with no
waiters. Runtime now has no whole-function host services. Original allocation/free use
a seeded pool with an additional original semaphore; only the live 16-byte
END_DOC notice storage is explicitly migrated from prior replay. An original
event group starts unset, and the native producer sets readiness through original
code, waking the status task when it ran first. Constructor thread creation
still uses a setup substitute. The datastore
constructor is stopped before its event-group/backing-value initialization, so
existing descriptor fixtures remain. This removes task scheduling and lock
substitutes for the selected status lifecycle, not for page completion, producer
JobMgr replay, optional language callbacks or outgoing PrintMgr/JobMgr consumers.
See `stock-execution/scheduled-status.md`. Original allocation/free also pass 93 independent-engine cases covering alignment,
payload preservation, deferred coalescing, reserve admission, live ownership and
accounting. Repeated free of the first block reaches a read before the bounded
arena; this negative case is caught by both RAM gates, not a device fault claim.
See `stock-execution/pool.md`. Original pool boot discovery, end-to-end producer
allocation and more printing tasks under the native scheduler remain productive
next avenues. Timed waits now have a separate original-code proof below.

Original timer initialization, timer task, tick routine and timeout callbacks now
run under native priority scheduling. Forty-four QEMU cases cover sleep, empty
receive, full send and early queue satisfaction, including 31/32/33/65-tick wheel
boundaries. Exact wake ticks, results, canceled timers, callback counts, message
contents, task states and empty final buckets agree with independent oracles.
A native clock task explicitly invokes the tick routine with system context set,
then yields. INTENABLE stays zero; original CCOUNT/CCOMPARE operations execute in
QEMU, but actual elapsed time, automatic IRQ delivery/return and time slicing are
not claimed. See `stock-execution/timers.md`. This removes a software timed-wait
boundary for later native JobMgr integration, not a physical timing uncertainty.


## In-progress handoff: native pipeline (2026-09-09)

Resumed 2026-09-10. Pinned GCC recovery completed after an interrupted download
was resumed. The unchanged build script verified the archive checksum, original
instruction encoding fixtures, and BE/call0 compiler profile, then installed
headers and libgcc. The latest sources passed the native matrix (26 completed
empty-document lifecycles, six separately classified conditional null reads),
all 28 retirement cases, then the full offline suite sequentially. That initial aggregate
passed **91 consistency checks**; subsequent timed-page integration passes 92. The historical 89-check baseline and old
source snapshots remain provenance, not the current validation limit.

The first page draft was then assembled/executed. Its invalid `beqi ...,11` was
replaced by a register comparison. Execution exposed a bad oracle: an embedded
descriptor address was expected in the free-call list. Original cleanup loads
node+12 into a6, then passes a5 (the containing node) to free at
`0x1000f0ff..0x1000f108`. The corrected assertion checks node ownership and the
observed descriptor offset, retaining the full pool-partition oracle.
`validate-hp1020-native-pages.py` passed six focused cases: one page, three pages
in one document, three one-page documents, each with both fills. These are
completed software lifecycles with supplied FIFO consumption, not device proof.
`stock-execution/pages.json` retains traces, input/fixture/source hashes and
byte-audited cleanup/retirement instructions. The original six-case focused checkpoint is committed as `8f5f656`; the subsequent timed integration is described below.

### Controlled timed cleanup (focused execution complete)

The expanded page matrix now passes **18 completed lifecycles**: each original
six-case stream/fill configuration runs without ticks, with two explicit ticks
after each retirement, and with those same ticks after consuming event bit 8
through original event-get. Original JobMgr calls `0x1000f068` with flag 8 only
in the non-consumed two-tick cases. It frees retired nodes and empties work+80
before supplied message 17. Zero-tick and consumed-event controls retain the
nodes until message 17; all final ownership/counter/queue checks still pass.

The first timed run stopped at the existing selected-code gate before
`0x1000f068`. Its complete 62-byte body was audited against stock bytes:
RAM list traversal, flag test, call to admitted cleanup `0x1000f0a8`, RAM status
store and return; padding is excluded. Its SHA-256 and bytes are in pages.json.
No MMIO or unknown instructions were added. The control's first wrapper used a
wrong BE bit-index check; original event-get had returned 0 and output flag 8.
An explicit numeric mask fixed the wrapper assertion. This is not a stock fault.

The completion task delivers ticks using the existing audited tick/context
fixture with INTENABLE zero. This expires JobMgr's two-tick queue receive;
JobMgr then polls the event and invokes cleanup. It is not direct event wakeup,
automatic IRQ delivery, wall-clock time or physical consumption evidence.
Pages are now wired into the aggregate with a separate matrix/provenance gate;
the full suite passed after that integration with **92 consistency checks**.
The 18 page cases are now part of the fully validated current-source baseline.

### Next offline experiment

Exercise native pages split into six, thirteen and 64 raster chunks, keeping
zero-tick, two-tick and consumed-event controls. The existing stock lifecycle
stream-splitting helper provides the fixture format. Check all references,
node ownership and cleanup; keep the 200,000-instruction cap until a measured
failure justifies changing it. A scratch launcher is prepared at
`/tmp/hp1020-fragment-pages.py` and is now running sequentially after full validation.

Recovery logs for this session are `/tmp/hp1020-gcc-recovery-resume.log`,
`/tmp/hp1020-gcc-download-resume.log`, `/tmp/hp1020-gcc-rebuild-resume.log`;
focused logs are `/tmp/hp1020-native-pipeline-resume.log`,
`/tmp/hp1020-native-retirement-resume.log`, `/tmp/hp1020-native-pages.log`.
Full suite log: `/tmp/hp1020-full-resume.log` (contains child log directory).
The earlier raw failure captures and exact old tested source snapshots remain
in `pipeline-investigation.txt` and `pipeline-boundary-capture.json`.
QEMU uses a permitted private Unix debugger socket and no printer connection.

### Resolved failure and fixture audit

At `0x1000e44f` the JobMgr receive trace resolves logical ARs through WINDOWBASE.
Original StatusMgr startup publishes literal `0xe6101100` from `0x100063dc`, then
original publication sends `[15,1]` from `0x10010a00`. This is not manual queue
injection or an invented cancellation selector. The original parser sends END_DOC
while JobMgr is runnable behind it. JobMgr consumes cancellation with a document
still present and END_DOC already queued, sets cancellation state 1, and sends
its own message 37 at `0x1000e9e1`. For eleven documents the remaining receive
sequence is `[15,2,37]`; for thirteen it is `[15,2,1,2,1,2,37]`.

Original END_DOC processing reaches list-pop store `0x1001306b`, removing the
last document while message 37 remains queued. The acknowledgement arm checks
cancellation state, loads the now-empty list head and attempts head+12 at
`0x1000e9f4`. The RAM gate stops before that instruction executes, with original
error `unmapped RAM 0xc+4`, cancellation 1 and status counters 11/10. This is a
conditional original-software hazard under this fixture, **not an observed
printer fault or a QEMU hardware exception**. Other execution errors still fail
the validator. This is distinct from the older `0x1000eb6a` cancellation and
`0x1000e7dd` delayed-empty-document findings.

Ten equal-priority documents pass with both fills: cancellation is consumed only
after the list is already empty, so it never becomes armed and no self-ack is
sent. Eleven is the observed boundary for this specific 72-byte repeated stream,
not a globally minimal reproducer. Both memory fills agree despite different
undefined packet suffixes. Original JobMgr/StatusMgr constructor bytes specify
priority/threshold 15 and time slice 10. Repeating ten/eleven with all three fixture
tasks set to 15 and slice 10 preserves the boundary. No ticks are delivered;
actual time slicing, input-task priority and device reachability remain unproven.

The native fixture uses original constructors, original allocation throughout,
original locks, queues and priority scheduling. Runtime host services supply only
input bytes; no producer replay or heap migration occurs. The parser wrapper calls
`0x10009d34` once per reconstructed document, not once per raw sample/trailer.
`prepare_pipeline` extracts this setup for the next experiment; that extraction
now passes the current-source native matrix. The datastore
constructor stops at `0x10010db3`; its backing-value/event initialization remains
omitted. PrintMgr is absent, with its ONLINE packet `[45,24,0,2]` retained. No
PrintMgr cancellation request occurs in these empty-document fault traces.
Successful cases still require the original ownership/queue/counter/lock oracles;
the only live allocation is the 20-byte ONLINE subscriber. Final JobMgr receive
has an original two-tick timeout armed, not expired or permanently idle.

### Native retirement tail

`hp1020_qemu_retire.py` is now exercised by
`validate-hp1020-native-retirement.py`: 28 standalone QEMU cases cover empty,
one/five/six/thirteen-node lists, three initial reference counts, both RAM fills,
and two deliberately nonzero pending-cursor mutations. Original instructions
inside `0x10014319..0x1001434b` decrement payload+78, clear the consumed video slot,
and set JobMgr event bit 8. The no-next path reaches `0x100143a5..0x100143b8`,
executes the standard CPU INTCLEAR helper and returns through the native fixture's
ENTRY frame. Work/node memory outside the two-byte reference fields is unchanged.
Both mutations stop at excluded PC `0x1001434b` before any next-transfer path.

An initial standalone setup failed the expected-zero event-creation assertion.
Static control flow identifies the null-current/ordinary-system caller check;
the corrected fixture supplies a nonwaiting constructor caller, after which all
28 cases passed. The added negative assertion now executes and confirms result 19 for the
original null-caller setup. No real task, engine, DMA or IRQ
prefix is inferred from this standalone setup.
The wrapper itself supplies consumed nodes, completion flag 1 and zero pending
cursor. `stock-execution/retirement.json`/`.md` own the execution evidence.

### Executed native page fixture

`hp1020_qemu_page_pipeline.py` reuses `prepare_pipeline` and the native bootstrap
with three asserted insertion anchors. A synthetic completion task runs with
JobMgr 2, parser 5, completion 15, StatusMgr 31. It waits for readiness bit 8
published by the parser after its final document, drains original queue-1 message
11, executes bounded `retire_work`, and sends initialized message 17 through the
original indexed queue. It also validates ONLINE `[45,24,0,2]`. Other consumer
packet types hit a guarded break. No active-work cancellation is modeled.

The executed streams rebuild `matrix-a4_default.zjs` via `helper.stream(base)`;
three pages use `base[:1]+base[1:6]*3+base[-1:]`, and three documents repeat the
rebuilt whole stream. All six cases fit the unchanged 200,000-instruction cap.
FIFO ownership, reference 1-to-0 stores, original events, page/document counters,
credit restoration, locks and pool reclamation pass. Four tasks wait on empty
queues, and only the 20-byte ONLINE subscriber remains allocated. Consumption
and message 17 are supplied; DMA, engine tasks and automatic IRQs do not execute.
The controlled-tick matrix now observes cleanup before message 17 explicitly,
with event-consumption controls, as described above.

Fixture map: parser TCB `0x22800000`, JobMgr +0x100, StatusMgr +0x200,
parking queue +0x400, buffer +0x600, output +0x800; pool `0x22400000`, 64 KiB;
parser/job/status/timer stacks `0x22900000` through `0x22c00000`, 64 KiB each.
A completion TCB can occupy +0x300 and a separate stack `0x22d00000`.
The original queues have capacities JobMgr 20 and StatusMgr 25. Queue 1 uses
its audited object `0x10028a74` and a synthetic buffer. Automatic CPU interrupts
remain masked; physical DMA, custom raster instructions, engine control, printing
and recovery remain unproven. No printer contact or installed-printing change
is authorized during this offline work.
