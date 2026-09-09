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

The owner explicitly paused this thread to transfer full context. The last
validated/pushed research baseline is `e7bef56` (89 aggregate consistency checks).
The following scripts are a preserved **unfinished research snapshot**, not a
new validated milestone or a claim that the replacement prints. They are not
called by `scripts/validate.sh`. No background research process remains active.

### Files and evidence

- `scripts/hp1020_qemu_pipeline.py`: new original parser + JobMgr + StatusMgr
  native scheduling experiment. Initial successes and a reproducible failure.
- `scripts/validate-hp1020-native-pipeline.py`: intended 24-case matrix; currently
  raises on the equal-priority 13-document case. No pipeline success report was
  written. Revise it to distinguish passing lifecycles from verified conditional
  failures only after obtaining the missing trace evidence.
- `scripts/hp1020_qemu_retire.py`: unexecuted draft assembly fixture for a later
  page-completion experiment. Do not treat its docstring as execution evidence.
- `stock-execution/pipeline-investigation.txt`: retained raw success/failure logs,
  including the full validation baseline summary and failure-scope experiment.
  These retain observations before disposable `/tmp` files disappear.

### Native pipeline fixture and observations

The new state begins with `Pipeline(program, data, fill)`, calls
`initialize_job()` and `initialize_receiver()`, and **does not call replay**.
`state.allocations` must stay empty: original pool code owns all allocations.
Runtime host entries are input/pushback callbacks; observed successful empty
streams used only `0x30000000` (input). Their arguments still use the existing
explicit parser context/datastore fixtures; this is not actual USB delivery.

Original constructors `0x1000e3ac` and `0x10010504` create JobMgr/StatusMgr queues,
event/publication state and locks. Their thread-create service `0x10018274` is
hosted during setup; native bootstrap subsequently creates the actual tasks
through original `0x1001a610`. Original timer initialization `0x100175f4` creates
its original timer task but no ticks are delivered in this experiment. Parser
slot-0 semaphore at the pointer in literal `0x10006624` is also created normally.
The datastore initialization still executes only `0x10010d7c..0x10010db3`, then
creates its separate mutex with the observed arguments; backing-value/event-group
initialization is deliberately omitted as in the committed StatusMgr experiment.

Fixture map:

- parser TCB `0x22800000`, JobMgr `+0x100`, StatusMgr `+0x200`;
  parser parking queue `+0x400`, its buffer `+0x600`, output `+0x800`;
- parser/job/status/timer stacks at `0x22900000`, `0x22a00000`, `0x22b00000`,
  `0x22c00000`, each 64 KiB; pool `0x22400000`, 64 KiB;
- original JobMgr queue has capacity 20, StatusMgr 25; queue 1 uses audited object
  `0x10028a74` and a synthetic buffer. PrintMgr itself is not running.
- Priority tuples are `(parser, job, status)`, lower numbers run first. All time
  slices are zero; native bootstrap masks automatic CPU interrupts and supplies
  readiness flag 4. Its parser wrapper calls the original parser once per document,
  then parks. Original stream-admission task integration remains separate work.

The input is the existing sample decoded with the helper in
`validate-hp1020-stock-execution.py`, then reconstructed with
`helper.stream(base[:1] + base[-1:])` (72-byte empty document). Repeat the rebuilt
stream, **not the raw sample file with its transport trailer**.

Confirmed examples:

- One empty document `(5,2,15)`, fill `0xcc`: 14,200 total fixture/native steps;
  full input consumed, start/end counters 1/1, empty document list; only the
  persistent 20-byte ONLINE subscriber remains allocated.
- Thirteen `(5,2,15)`, fill `0xcc`: 89,077 steps, counters 13/13, all transient
  pool allocations freed (fragmented free blocks remain, as expected).
- Thirteen `(2,5,15)`, fill `0xcc`: the durable `run_pipeline` oracles pass;
  72,998 steps, 52 original frees, six parser waits on a full JobMgr queue and
  one JobMgr wait on a full StatusMgr queue. Runtime host service only input.
- Three `(5,2,1)`, fill `0xcc`: StatusMgr-first ordering also completed.
- Ten `(5,5,5)`, fill 0: durable oracles pass.

On successful runs original StatusMgr cancellation is actually consumed by the
running JobMgr, unlike the older scheduled-status experiment where it stayed
queued. All three tasks finish suspended on empty queues. JobMgr's final receive
has an actual two-tick timer linked at `wheel + 4`; no ticks were delivered, so
this is an **armed timeout**, not permanent idle. Pool partition/accounting,
locks, counters and TCB run counts pass. The remaining queue-1 packet is
`[45,24,0,2]`; its PrintMgr consumer is absent.

### Exact pending failure — trace before classifying

The attempted 24-case matrix iterates documents `(1,3,13)`, priorities
`(5,2,15)`, `(2,5,15)`, `(5,5,5)`, `(5,2,1)`, and fills `(0,0xcc)`.
It reaches `documents=13, priorities=(5,5,5), fill=0` and is stopped by the RAM
access gate at **PC `0x1000e9f4`, read `0x0000000c`, current thread `0x22800100`**.
Separate reductions show the same fault for:

- 13 documents, equal priorities, fill `0xcc`;
- 12 documents, equal priorities, fill 0;
- 11 documents, equal priorities, fill 0.

Ten documents pass with equal priorities/fill 0. Eleven is only the minimum found
for that fixed fixture; no global minimality or hardware reachability is claimed.
The remaining matrix entries after the first failure were not all executed.

Instruction-derived control flow at the fault:

- `0x1000e9e7` loads the cancellation-state pointer from literal `0x10006308`;
  `0x1000e9ec` skips this arm if that state is zero.
- `0x1000e9ef` loads the document-list object from literal `0x100062e4`;
  `0x1000e9f2` reads its head; `0x1000e9f4` dereferences head `+12` without
  first checking whether the head is null.
- Earlier `0x1000e9d5..0x1000e9e1` can enqueue message 37 back to JobMgr itself
  when no downstream acknowledgement is outstanding.

**Working hypothesis, not yet traced:** original StatusMgr queues cancellation,
JobMgr queues its own acknowledgement, and an END_DOC removes the last document
before the acknowledgement arm runs. Do not upgrade this to a proven sequence or
a printer bug merely because the nearby instructions and null read fit it.
No manual cancellation/ack injection exists in this new native fixture, which is
why resolving the exact original queue ordering is productive.

Next instrumentation should observe without changing state:

1. At original indexed send `0x10013658`, capture queue ID and defined packet words
   from logical `a10/a11`, resolving physical AR indices through WINDOWBASE.
2. At `0x1000e44f` (JobMgr after a successful receive), capture message words at
   logical SP and document head/cancellation state. Capture both enqueue and
   receive order; queued acknowledgements can be delayed.
3. At the fault, capture head, cancellation state, current message and counters;
   preserve the actual code/RAM-gate exception. Check both RAM fills and the
   neighboring 10/11-document boundary before adding a conditional regression.
4. Audit fixture omissions (zero time slices, chosen priorities, descriptor values,
   absent PrintMgr consumer) before discussing relevance to the device.

`run_pipeline` currently adds documents/priorities/fill/PC/thread to ValueError.
It has no expected-failure mode yet. The draft validator must not simply skip the
case or weaken its ownership checks. The earlier cancellation failures at
`0x1000eb6a` and delayed-empty-document issue at `0x1000e7dd` are distinct recorded
findings; do not conflate them with this new `0x1000e9f4` observation.

### Planned page-completion extension — not implemented

`hp1020_qemu_retire.py` defines `retirement_source(video)` and narrow `RETIRE_CODE`.
It proposes a native `retire_work` loop over `work+0x50` list nodes. A fixture
`ENTRY` frame prepares the original tail's registers, supplies one consumed node
in video slot `+0xa4`, clears the other four slots and pending cursor `+0x9c`, sets
completion flag `+0xf8=1`, then jumps into original `0x10014319`.

Stock bytes show that tail decrements payload `+78` (16-bit), clears the consumed
slot, and calls the original event-set primitive with JobMgr event 8. If the
pending cursor is zero it reaches `0x100143a5..0x100143b8`, calls original
`0x100171e0` and RETW returns through the fixture frame. The latter helper is
standard `WSR.INTCLEAR` for bit 20, not MMIO. **This composition is unexecuted.**
Its allowed ranges intentionally exclude `0x1001434b..0x100143a5`, which contains
the next-transfer path. First add a standalone QEMU reference-count/event/return
oracle and a mutation that sets a nonzero pending cursor and must stop at
`0x1001434b` before any next-DMA path runs. Preserve the omitted hardware IRQ prefix
as an explicit boundary; never claim physical consumption from this fixture.

If that passes, a synthetic native completion task can consume queue-1 work
messages (11), invoke the bounded original retirement tail, then send message 17
through the original queue to JobMgr. Start with one/three ordinary pages and
explicitly deferred FIFO completion after the native parser finishes. One proposed
priority scope is JobMgr 2, parser 5, completion 15, StatusMgr 31; this avoids
pretending cancellation/physical-stop handling exists in the synthetic consumer.
An original event flag can signal parser completion. The completion task must also
observe/drain ONLINE message 45, reject unexpected packet types, and verify original
pool reclamation/counters. No completion task or page-pipeline test exists yet.
Physical DMA, engine stop, raster custom instructions and printing stay unproven.

### Recovery and verified checkpoints

The nine session checkpoints, oldest first, are:
`88fafc1` queue identity/ownership correction;
`7b01067` stop acknowledgements and conditional cancellation;
`3bcd9c5` original status publication/history;
`7b60b88` original queues/pending waits;
`4250147` original window/context restoration;
`14ddb8b` native priority scheduler;
`08f925b` scheduled StatusMgr/original locks;
`b41959f` original pool and no runtime StatusMgr substitutes;
`e7bef56` original timer task and canceled waits.
Each passed its then-current full aggregate and was pushed to private `main`.
The handoff snapshot after these is deliberately unfinished; it does not upgrade
that validation claim.

Last full log: `/tmp/hp1020-timers-full-validation.log`, detailed logs under
`/var/folders/46/5hjsxnq13752lvrwdm2q1fk80000gn/T/hp1020-validation.FT11hV`.
It passed both suites, including 89 consistency checks. Aggregate regeneration
must remain serial. The last failing pipeline log is
`/tmp/hp1020-native-pipeline-validation.log`; scoped reductions are in
`/tmp/hp1020-pipeline-fault-scope.log`. Copies of material output are retained below
the stock-execution directory. Standalone drafts were syntax-checked for handoff;
the failure was not fixed and no new full-suite claim is made.

Working tools at handoff (recover pinned tools via the README if `/tmp` is gone):
`/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf` binutils prefix;
`/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf` GCC prefix;
`/opt/homebrew/bin/qemu-system-xtensaeb` (11.1.1, `sim`, `test_kc705_be`, 32 ARs).
Stock ELF SHA-256 is
`2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d`.
`Program` in `hp1020_xtensa_call0.py` honors `.xt.insn` annotations; do not trust
linear objdump around unaligned function starts. `NativeTasks` allows 200,000
steps and rejects unsupported instructions/whole-instruction span escapes.
Original IRQ/window code uses VECBASE `0x10000000`; QEMU is still not the device.
Ghidra is Homebrew 12.1.1 with OpenJDK 21; its freshly generated datastore helper
census missed known older direct calls. Retain the saved helper captures rather
than replacing them with a poorer census. Data-store summary counts were removed
instead; entry-25 and binary-semaphore corrections are in its Java generator.

The next **live** experiment remains the existing non-printing USB ladder.
Further combined firmware integration cannot establish any of the device facts
above. Once boot/USB behavior is proven, the validated C component can be joined
to that transport; any later print-driving video/engine work still requires
explicit permission and the corresponding hardware evidence.

No printer was contacted for this checkpoint. This document is an evidence
request for future authorized work, not authorization to run a hardware test.
