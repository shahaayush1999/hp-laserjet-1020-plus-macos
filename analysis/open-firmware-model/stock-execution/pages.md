# Native page pipeline with supplied consumption

6 completed software lifecycles. No physical printing evidence.

- Six native cases complete one page, three pages in one document, and three one-page documents, under both RAM fills. Original parser, JobMgr and StatusMgr use original allocation, queues, locks and scheduling. Runtime host services supply input bytes only.
- A synthetic fourth task waits until parsing finishes, consumes queue-1 work in FIFO order, supplies successful consumption to the bounded original retirement tail, and sends message 17 through the original JobMgr queue. Reference fields change from one to zero through original stores; original event-set calls execute.
- Original completion processing restores credits, updates page/document counters and releases all pool allocations apart from the persistent 20-byte ONLINE subscriber. All four tasks finish waiting on empty queues; JobMgr has a two-tick receive timeout armed. No ticks are delivered.
- The first draft did not assemble because beqi cannot encode immediate 11. Replacing it with a register comparison allowed execution. The first executed draft then failed an incorrect descriptor-free oracle: stock cleanup frees the containing node (node+12 points to its embedded descriptor at node+16), not that descriptor address. Original bytes and pool partition evidence establish the correction.

Software execution only. FIFO consumption, completion success, task priorities, parser wrapper, initial readiness and descriptor backing values are fixtures. No PrintMgr, engine, DMA, IRQ prefix, custom raster instructions, automatic interrupts, physical printing or recovery executes. The retirement next-transfer path remains excluded. There is no claim that event bit 8 wakes JobMgr before message 17; controlled timed cleanup is a separate experiment.
