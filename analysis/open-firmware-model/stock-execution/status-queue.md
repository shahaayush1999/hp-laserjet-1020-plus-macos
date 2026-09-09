# Original status task with original queues

8 combined cases agree between QEMU and the interpreter.

- Original completed JobMgr notices are pre-enqueued through original indexed send. Original StatusMgr creates queue 10, receives the queued notices, updates counters/status and frees every transient notice allocation; only the persistent ONLINE subscription remains.
- Original status publication queues ONLINE [45,24,0,2] to PrintMgr queue 1 and cancel [15,1] to JobMgr queue 3. Original receive retrieves both from actual queue buffers; no whole queue function is substituted.
- After draining all notices, original infinite-wait receive inserts the current thread into the queue suspension ring, records its destination and wait state, and reaches the explicit scheduler boundary. The test stops before thread suspension/context switching.

Parser/JobMgr notice production still uses injected FIFO page completion. Notices are pre-enqueued; this is not a concurrent task schedule. RTOS semaphore/thread creation, locks, allocation and final task suspension remain host services. Empty language-context table omits outward callbacks. PrintMgr/JobMgr do not consume the emitted packets in this combined test. No printer, DMA, hardware stop, IRQ or recovery evidence is claimed.
