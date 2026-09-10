# Original raw buffer contract fragments

8 producer-selection, 22 dispatch/flag, 14 raw-pointer selection and 24 conditional retirement/cleanup cases pass, plus two raw-mode boundary controls. No completed lifecycles.

- The bounded original producer selection preserves the supplied pointer only when its input descriptor kind equals 1, setting payload source kind 1. Other tested input kinds set source kind 2 and pointer zero, even with a supplied nonzero pointer. This does not establish a generic borrowed-buffer input mode.
- Source kind 0 reaches compressed prepare; 1/2 reach alternate prepare; other kinds or work type 7 reach notification without rendering. The independent work raw flag changes the IRQ-family bit but does not change that dispatch.
- Separately entered alternate render stores the supplied node at both raw-list heads, then stops before raw refresh. Decoded image bytes and payload remain unchanged; physical image format is not established.
- After an omitted readiness/MMIO prefix, the original raw-list pointer fragment loads the decoded-band pointer for source kind 1 and the supplied null pointer for kind 2. The file-backed output selector is 2; mutation to 1 selects the other excluded output branch. Empty heads reach the return boundary. No pointer or count is written to a peripheral.
- After a skipped peripheral IRQ prefix, the original raw completion tail subtracts 16 from a nonzero payload pointer whenever its reference count is nonzero, decrements that count, sets the original JobMgr event and advances the raw head. This occurs for both source kinds 1 and 2.
- Separate generic cleanup observes buffer and node free requests for kind 1 once references reach zero, and only node free requests for kind 2. The allocator is supplied; actual freeing, pool ownership and concurrent reuse are not proven.
- An intentionally unprefixed kind-1 pointer with one reference yields a free request 16 bytes before its supplied buffer. This is a conditional fixture finding, not a stock fault: a reusable decoder-band pointer cannot be substituted without proving the prefix/ownership contract.
- Source kind 2 also controls a hardware flag in the separately audited raw-refresh bytes. Avoiding its buffer-free request is not evidence that it is a suitable physical format or mode.

Separate fragments with supplied RAM, work metadata and completion entry. Remaining prepare/render/refill paths, the peripheral IRQ prefix, engine operations, custom callbacks and all USB operations are excluded. Event creation/set executes original RTOS code with no waiters. No boot, complete page lifecycle, DMA, physical output or automatic asynchronous consumer is claimed.
