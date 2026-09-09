# Original memory allocation and release

93 cases pass in the interpreter and independent QEMU.

- Original public allocation on successful requests, allocation core, free and semaphore create/get/put execute in both engines without whole-function replacements.
- The pool is a partition of 12-byte headers and payloads. Header magic is 0x2e3d4c5a; size is at +4; flags at +8 include allocated bit 31, terminal bit 30 and type-0 marker bit 29 on allocated blocks (free blocks can retain stale bit 29). Lower 24 bits record a caller address and intentionally differ between synthetic caller environments.
- Type 1 rounds to four bytes. Types 0 and 2 reserve (rounded_size // 16) * 16 + 28 bytes and return a 16-byte-aligned pointer; only leading alignment padding is zeroed. Requested payload bytes retain prior contents.
- A remainder of 48 bytes is absorbed; 52 bytes produces a new 12-byte header and 40-byte free payload. Free clears the allocated flag and restores the block payload size to the counter, without clearing payload or immediately coalescing. A later scan merges adjacent free blocks, returning each removed header to free-byte accounting.
- The core can reject a request despite enough contiguous space: type 0 preserves a reserve; type 1 permits requests through 2048 bytes despite the reserve but rejects the tested larger request below it; type 2 bypasses that reserve check. Core failure returns zero.
- Repeatedly freeing the first type-1 block reaches a backward header search before the bounded arena. Both engines are stopped by the strict RAM gate at that read; there is no general double-free safety guarantee or claim that this occurs on the device.
- Seeded allocation/release traces verify exact arena partition and free-byte accounting after every operation, no overlapping live allocations, preserved live contents, semaphore balance, and matching independent-engine outcomes.

One explicitly seeded, word-aligned RAM arena and one ordinary current thread. No boot pool discovery, concurrent allocation, semaphore contention, allocator retry/sleep/low-memory notification path, IRQs, timers or hardware. Null free is tested; invalid and repeated frees have no safety guarantee. Differential comparison excludes caller-address provenance bits, but validates block structure and independently written live payloads. Type-0 wraparound policy is not covered by the initial-allocation cases.
