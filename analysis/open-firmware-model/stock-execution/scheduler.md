# Original priority scheduling and blocking queues

80 QEMU cases pass complete-message, arithmetic, priority, queue and thread-state oracles.

- Original RTOS RAM initialization builds the full 256-byte lowest-set-bit lookup table against an independent integer oracle. Omitting initialization left this BSS table zero and caused an invalid fixture to idle despite a ready thread.
- Original thread-create core, initial-stack builder, resume, ready lists, priority selection, suspend, voluntary context switch, thread shell and queue create/send/receive execute without any whole-function host service.
- A synthetic producer sends complete one-word or four-word records, blocks on full queues and waits for an acknowledgement. A synthetic consumer receives every record in order, validates via an external complete-byte oracle, and acknowledges the arithmetic sum. Queue capacity, priority order/equality/extremes and initial RAM fills vary.
- The scheduler chooses the initially highest-priority ready task, with FIFO creation order for the tested equal-priority pair. Run counters match observed scheduler selections and preemption bookkeeping balances. Both queues finish empty without suspended waiters.
- When the producer has higher priority, acknowledgement delivery preempts the consumer. Otherwise the consumer returns and the original thread shell terminates it before the producer finishes; the corresponding final thread states agree.

Only two synthetic tasks and explicit initial system state are tested. The original thread-create core receives known-valid arguments; its outer validation wrapper is not exercised here. Waits are infinite and time slices zero, so no timer expiry or interrupt-driven preemption occurs. The workload has no parser, JobMgr, PrintMgr, DMA, custom raster instruction or hardware. This removes scheduling substitutes from this kernel experiment, not from the existing printing-lifecycle harnesses. The producer is observed at its final sentinel, and the consumer may remain paused at acknowledgement delivery.
