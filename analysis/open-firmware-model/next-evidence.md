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

Resumed 2026-09-10. The saved failure is now traced and classified; the drafts
are no longer an unexamined success claim. `validate-hp1020-native-pipeline.py`
checks 26 completed lifecycles and six **separate conditional null reads** across
32 QEMU cases. The owner then requested another full handoff; research is paused,
not exhausted. `stock-execution/pipeline.json` retains fault traces and original
instruction bytes; `pipeline.md` summarizes scope. Raw logs, including the
aggregate/compiler-recovery failure, are in `pipeline-investigation.txt`.
The read-only boundary experiment is in `pipeline-boundary-capture.json`.
No QEMU, research-validator or compiler-recovery process was running at handoff.

**Validation status:** the last fully validated baseline remains `e7bef56` (89
consistency checks), inherited through handoff commit `fe67c4f`. The focused
native matrix passed 26 lifecycles plus six conditional stops; standalone
retirement passed 28 cases. However, three source files changed after their
corresponding successful reports, and the full aggregate has not passed:

- `hp1020_qemu_pipeline.py`: extracted existing initialization into
  `prepare_pipeline` and added input/fixture hashes to guarded-stop details.
  The matrix was not rerun after this refactor.
- `validate-hp1020-native-retirement.py`: added an assertion that original event
  creation with null current/ordinary system returns 19, and documented the
  constructor-caller fixture. This new assertion was not executed.
- `hp1020_qemu_retire.py`: changed only the old unexecuted-draft docstring after
  standalone execution passed; the assembly is unchanged.

The existing report source hashes intentionally retain the versions actually
run. `pipeline-boundary-capture.json` includes exact embedded source snapshots
for these three old versions, each checked against its successful report hash.
Do not edit report hashes by hand to hide the mismatch; rerun the generators.
Aggregate wiring in `validate-hp1020-offline-analysis.sh` and two added checks in
`check-hp1020-analysis-consistency.py` are provisional until full validation passes.
The new native page module is an additional unexecuted draft, described below.

### Immediate recovery and resume order

The attempted `scripts/validate.sh` stopped at the synthetic C target build:
`fatal error: stddef.h: No such file or directory`. The compiler executable and
profile check survive at `/tmp/hp1020-xtensa-gcc14`, but its installed GCC include
files and `libgcc.a` are missing. The expected archive
`/tmp/hp1020-gcc-14.3.0.tar.xz` and build Makefile are also missing. Follow
`scripts/build-xtensa-gcc-manual.sh` from the tool-recovery map. Its first attempted
archive download failed in the sandbox with curl exit 6 / unresolved
`ftp.gnu.org`; no source checksum or build stage was reached. Retry the pinned
recovery with network permission, preserving its SHA-256/configuration gates.
Do not improvise target headers or trust executable presence as a complete tool.

After recovery, rerun the two native validators to refresh their current-source
reports, then `scripts/validate.sh` sequentially before a validated checkpoint.
QEMU also requires its private Unix debugger socket: its sandboxed launch failed,
while explicitly permitted offline launches succeeded. This does not require
network/USB access for QEMU. All aggregate steps before the C target build passed;
no later aggregate step ran. Syntax and diff/reference/source-snapshot checks
are the final handoff checks, not a replacement for full execution validation.

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
has syntax checks only so far. The datastore
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
28 cases passed. A subsequent negative assertion expects result 19 for the
original null-caller setup, but that added assertion has not run yet. Do not
claim its result as an executed observation. No real task, engine, DMA or IRQ
prefix is inferred from this standalone setup.
The wrapper itself supplies consumed nodes, completion flag 1 and zero pending
cursor. `stock-execution/retirement.json`/`.md` own the execution evidence.

### Next experiment — saved, unexecuted page draft

`scripts/hp1020_qemu_page_pipeline.py` now contains `page_source(...)` and
`run_pages(q, program, data, documents, pages, fill)`. It has passed Python syntax
checks only. **No generated page-fixture assembly has been assembled or executed,
no page-pipeline validator/report exists, and none of its oracles is evidence yet.**
It is not called by the aggregate. Inspect and trace its first execution before
expanding the matrix or claiming native page completion.

The draft reuses `prepare_pipeline` and the native bootstrap with three asserted
source-insertion anchors. It adds a synthetic completion task with JobMgr 2,
parser 5, completion 15, StatusMgr 31. The parser signals original readiness flag
bit 8 after its last document, and completion waits for that bit through the
original event-get primitive. It consumes original queue-1 work message 11,
executes the bounded original `retire_work`, and sends fully initialized message
17 through the original indexed queue. It also drains/validates ONLINE packet
`[45,24,0,2]`; other consumer packet types hit the fixture's guarded break.
No active-work cancellation or physical-stop behavior is modeled.

Proposed first run: decode `matrix-a4_default.zjs` with the helper in
`validate-hp1020-stock-execution.py`, rebuild using `helper.stream(base)`, then
call `run_pages(..., documents=1, pages=1, fill=0)`. Rebuild the stream rather than
using its raw transport trailer. If successful, try both fills, three pages in
one document (`helper.stream(base[:1]+base[1:6]*3+base[-1:])`) and three complete
documents (`helper.stream(base)*3`). These are proposed fixtures, not run results.
The draft's current native runner has a 200,000-instruction cap; investigate any
failure before changing it, and keep any larger budget explicit and bounded.

Draft oracles observe original work scheduling, FIFO consumer ownership, initial
node reference 1, original retirement stores to zero, original event-set calls,
full original pool reclamation apart from the ONLINE subscriber, page counters
5/6, document counters, credit restoration, released locks and all four tasks
waiting on empty queues. The draft assumes the normal sample fits those fields;
verify that assumption against reached bytes if it fails. It does not simulate
DMA. A later controlled two-tick experiment can test JobMgr's event-driven RAM
cleanup before message 17, without claiming elapsed time or automatic IRQs.

Fixture map: parser TCB `0x22800000`, JobMgr +0x100, StatusMgr +0x200,
parking queue +0x400, buffer +0x600, output +0x800; pool `0x22400000`, 64 KiB;
parser/job/status/timer stacks `0x22900000` through `0x22c00000`, 64 KiB each.
A completion TCB can occupy +0x300 and a separate stack `0x22d00000`.
The original queues have capacities JobMgr 20 and StatusMgr 25. Queue 1 uses
its audited object `0x10028a74` and a synthetic buffer. Automatic CPU interrupts
remain masked; physical DMA, custom raster instructions, engine control, printing
and recovery remain unproven. No printer contact or installed-printing change
is authorized during this offline work.
