# Original timer task and timed waits

44 QEMU cases pass explicit tick, queue and task-state oracles.

- Original timer initialization builds its 32-slot wheel and creates the original timer task, initially suspended. Its original entry, input magic and thread control block are checked; only stack address, stack size and priority are fixture inputs.
- A native low-priority clock task invokes the original tick function. Original timer-task wakeup, bucket processing, callback invocation, requeue beyond 32 ticks and priority scheduling execute without whole-function host services.
- Sleep wakes on the requested software tick with result 0. Empty receive and full send expire on that tick with results 10 and 11, respectively. Cases cross the 31/32/33 and 64/65 wheel boundaries.
- When another native task satisfies a queued send or receive on tick 1, original queue/resume code removes its pending timer. Continuing beyond the old deadline produces no timeout callback and preserves the delivered message.
- Independent oracles check wake tick, result, callback count, queue contents and wait lists, task states/run counts, preemption balance, clock count, empty timer buckets and the exact final wheel cursor.

These are original software timeouts under explicitly supplied ticks, not physical elapsed-time or interrupt-delivery proof. The original tick routine executes QEMU CCOUNT/CCOMPARE operations, while INTENABLE stays zero; the clock task explicitly marks its call as system context and yields afterward. Worker, clock and timer priorities are fixed at 5, 31 and 0 with zero time slices. No hardware/MMIO, USB, boot clock calibration, automatic IRQ entry/return, time slicing, periodic application callbacks, or original printing-task integration is demonstrated.
