# Original RTOS queue RAM operations

80 cases pass in both execution engines against independent oracles.

- Original queue create, send, receive, registration and indexed send execute with no whole-function host replacements. All five supported message widths, capacity rounding, full/empty errors and repeated FIFO wraparound agree with a Python deque and independent QEMU.
- Queue layout: +8 words/message, +12 capacity, +16 occupied, +20 available, +24/+28 buffer bounds, +32 read cursor, +36 write cursor, +40/+44 suspended list/count, +48/+52 created-list links. Original creation builds the circular list and count.
- Four-word messages copy all 16 bytes, including producer-uninitialized words; queue code does not sanitize them. Nonblocking empty/full return 10/11; the indexed send wrapper maps any nonzero send result to 0xffffffff.
- Rejected arguments and forbidden interrupt-context waits leave all original writable globals and fixture RAM unchanged.
- An explicit interleaving satisfies an empty receive or full send before its suspend helper runs. Original queue code delivers directly to the receiver or replaces the consumed slot from the waiting sender; original resume clears pending suspension, and the subsequently invoked original suspend helper restores preemption bookkeeping without a task switch.

A synthetic ordinary thread is current. FIFO cases have no waiters. Race cases cut before suspension and invoke the deferred helper as a fresh call; they do not restore the paused caller or simulate an actual task switch, interrupt, timer expiry, hardware or USB. The interpreter abstracts PS masking; QEMU executes the original critical-section instructions on a different Xtensa core. FIFO delivery under these preconditions does not establish actual cancellation timing.
