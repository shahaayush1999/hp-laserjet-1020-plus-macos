# Original software lifecycle

Original software lifecycle in serialized/cooperative schedules under injected ordered successful completion; no device or printing evidence.

110 passing lifecycle cases, 2 reproduced conditional counterexamples and 72 retirement-block cases; 2892395 original instructions, 1281 distinct addresses.

- Original completion handling restores scheduling credits and drains jobs larger than the initial queue capacity.
- Cooperative queue-boundary schedules interleave parser and JobMgr contexts with eager, end-document and end-parser FIFO completions. Nonempty documents preserve final ownership/counts; standalone empty documents finalize. A delayed mixed empty/nonempty sequence is recorded separately as a counterexample.
- Multiple documents, copies and split rasters finish in FIFO order, leaving only queue-10-owned completion notices allocated.
- Original publication/finalization, parser lock/unlock wrappers and datastore counter instructions now run; these were previously host substitutes or untested.
- The parser lock wrapper only acquires its producer mutex; it does not wait for the JobMgr document list to drain. The separate 0x10012644 helper contains that drain wait and is not the parser call target.
- The channel-A RAM block retires five saved pointers only when video +0xf8 is nonzero, clearing each pointer and decrementing payload +0x4e.
- The retirement decrement has no zero guard: synthetic zero references wrap to 65535. Valid pipeline cases never require that state.
- An empty document queued behind an unfinished nonempty document triggers incorrect head-document release in two schedules, followed by a missing-child access at 0x1000e7dd. Eager completion of the earlier page avoids it; physical reachability is unproven.

## Explicit environment

- The host injects one successful JobMgr message 17 for each queued work request, in FIFO order, after simulated consumption of its rasters.
- The host batches consumed nodes into five saved-pointer slots and sets the progress flag, then executes only the original RAM retirement block. Its preceding/following MMIO is never executed.
- Allocation/free, task-ready, mutex/semaphore/event operations and queue delivery remain host services; queue 10 notices are captured but not consumed.
- Datastore records 5/6 have explicit zeroed word storage, and subscriber lists for 5/6/27/28 are empty. All selected datastore read/write logic executes.
- Three exact critical-section instructions in the release loop use a serialized fixture substitute; no general interrupt model is claimed.

## Limits

- The counterexample assumes a second parser invocation is admitted while an earlier document still has unfinished pages; live transport/producer admission and external completion timing remain unverified.
- Only queue-boundary cooperative interleavings are exercised; instruction-level preemption, allocation failure, cancellation, out-of-order completions, reset/power cycle and physical consumption remain unverified.
- Duplex cases exercise stock bookkeeping only; the replacement remains narrow simplex.
- Completion injection is an assumption to verify software lifetime, not a claim that the open replacement can produce that event.
