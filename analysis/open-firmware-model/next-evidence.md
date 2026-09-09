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
state. Further work includes status-notification ownership and interruption
producer/acknowledgement paths.

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
Engine/Video acknowledgement production, work retirement and status publication
remain explicit boundaries. Investigate them before promoting the preliminary
cancellation leak/null-access experiments; an injected acknowledgement alone
does not establish the actual stopping state.

The next **live** experiment remains the existing non-printing USB ladder.
Further combined firmware integration cannot establish any of the device facts
above. Once boot/USB behavior is proven, the validated C component can be joined
to that transport; any later print-driving video/engine work still requires
explicit permission and the corresponding hardware evidence.

No printer was contacted for this checkpoint. This document is an evidence
request for future authorized work, not authorization to run a hardware test.
