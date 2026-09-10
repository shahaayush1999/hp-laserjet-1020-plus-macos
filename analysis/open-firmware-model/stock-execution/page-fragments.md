# Native pages with split raster data

18 completed software lifecycles, additional to the aggregate page matrix.

- Eighteen additional focused software lifecycles pass with six, thirteen and 64 raster chunks in one page, both RAM fills, and zero-tick, two-tick and consumed-event controls. The concatenated raster payload is unchanged by chunking.
- Every chunk creates a distinct original linked node. The native retirement wrapper supplies consumption once per node; original reference stores reach zero and original event-set runs once per node. No five-slot hardware batching or real DMA is inferred.
- With two explicit ticks, original JobMgr cleans every retired node before supplied completion. Consuming the event first prevents early cleanup despite those ticks. All controls retain complete final reclamation apart from the ONLINE subscriber, restored credits, page/document counters and empty waiting queues.
- Six- and thirteen-chunk cases keep the 200,000-instruction budget. The first 64-chunk case stopped at that cap during StatusMgr notification bookkeeping after all references were retired and completion was supplied; its raw capture is preserved separately, not counted as a lifecycle. The 64-chunk matrix uses an explicit 250,000-instruction budget. The byte-audited page runtime is unchanged from the aggregate baseline; the larger fixtures retain all memory, instruction and excluded-next-transfer gates.

Software execution only. FIFO consumption, completion success, task priorities, parser wrapper, initial readiness and descriptor backing values are fixtures. No PrintMgr, engine, DMA, IRQ prefix, custom raster instructions, automatic interrupts, physical printing or recovery executes. The retirement next-transfer path remains excluded. There is no claim that event bit 8 wakes JobMgr directly: explicit ticks expire its queue receive, after which it polls the event and cleans RAM. Wall-clock timing remains unproven.
