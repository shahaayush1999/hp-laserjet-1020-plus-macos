# Original USB printer-class reset boundary

20 original-byte cases agree between the interpreter and QEMU. Zero completed control transfers or page lifecycles.

Original class request 0x21/0x02 dispatch clears the supplied handle registration, drains pending software nodes and selects a zero-length control response, stopped before its sender. Nearby unsupported requests select stall intent before any stall register access.

The ready/owner prefix, actual control response, physical reset, interrupt scheduling, DMA and cache behavior are omitted. Two one-hot handles and bounded queues are supplied. Free and outer mask services are substituted; original list and registration routines execute, and QEMU also executes the original short list critical helper. Neither those frees nor their device safety are proven. A standalone supplied busy status word stays unchanged; no live descriptor/buffer relationship to the drained list is modeled. Noncanonical reset fields demonstrate original dispatch behavior, not recommended acceptance policy.
