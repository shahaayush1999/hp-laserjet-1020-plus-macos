# Original stream admission execution

Status: pass. 79 normal cases and 8 reproduced conditional counterexamples.

The original single-language stream recognizer admits consecutive ZjStream documents without waiting for JobMgr list drain. Non-head empty-document cleanup still frees the unfinished head under serialized and delayed-completion cooperative host schedules. Eager completion avoids the fault.

Original ZjStream registration, language matching, parser dispatch, input-buffer construction, pushback, buffered read, parser mutex wrappers, parser, JobMgr and completion bookkeeping execute unchanged in host RAM.

## Explicit limits

- One transport and one registered language (ZjStream); other language handlers are not modeled.
- Host readiness bit and low-level read callback deliver the supplied bytes. Nonblocking probe reads are fragmented; timed reads supply requested available bytes. No elapsed-time, timeout, disconnect or USB controller simulation.
- RTOS setup, allocation, locks and queues retain prior host substitutes. Successful FIFO raster consumption and completion ordering are injected.
- This reduces the unresolved software admission question. Actual host USB delivery, RTOS/IRQ scheduling, engine backpressure and physical occurrence remain unverified. It is not a demonstrated printer bug.
