# Original notification routing and ownership

12 cases agree between interpreter, QEMU and explicit packet/counter/lifetime expectations.

- Original PrintMgr subscriber creation followed by original datastore lock/read/write emits [45,24,value,2] to queue 1. Relaying that packet and committed ONLINE byte to original PrintMgr updates its online state for both zero and one.
- Original StatusMgr consumes JobMgr begin/end notices, balances document counters and releases the final 16-byte completion allocations. All parser/job/page/raster/notice allocations are freed in the selected completed lifecycles.

Original parser/JobMgr fixture supplies completion notices after injected FIFO completion. QEMU independently executes the producer and receiver instruction ranges. Queue relay and initialized task state are explicit composition boundaries. Status publication at 0x10010838 remains a host callback; optional host-language callbacks are disabled by original context flags. No USB, mechanical stop, DMA, RTOS schedule or physical printing is proved.
