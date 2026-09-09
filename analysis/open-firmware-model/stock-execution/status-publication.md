# Original status publication and history

15 cases agree between QEMU, the instruction interpreter and explicit state/datastore/history/lifetime oracles.

- Original StatusMgr constructor registers queue 10 and initializes status state 2, online byte 1, cached event 0x04800100 and source 10; RTOS object creation is an explicit host service.
- Original startup/publication, datastore lock/read/write, ONLINE subscriber dispatch and 100-word event history all execute. Selected lifecycle notices balance counters and free every transient allocation, leaving only the persistent 20-byte ONLINE subscription.
- The numeric preflight event sets ONLINE to zero; the tested matching-source clear event restores ONLINE and state 2. Duplicate clear events leave all original writable globals unchanged. The history ring agrees with a circular-array oracle across wraparound.
- Cancel selectors 1, 3 and 4 are produced with original publication effects included under the recorded cached-status/active-document fixture. These events contain cancel bit 0x02000000 but lack offline bit 0x80000000: cached status/history/datastore 25 change while the online byte and ONLINE subscription stay unchanged.

Completed parser/JobMgr inputs still rely on injected FIFO completion. Engine events and source IDs are numeric fixtures, not physical calibration. RTOS object creation, scheduling, synchronization, allocation and queue delivery remain host services. The constructor initializes an empty language-context table, so optional outward status callbacks do not execute. No hardware, USB response or physical recovery is demonstrated.
