# Open bounded ZjStream image consumption

Status: pass. The existing open parser consumes complete ZjStream input through a fixed compressed chunk, a bounded decoder and a synchronous band consumer. No complete compressed or decoded page is kept in component memory.

66 host cases and 44 QEMU cases. Reused packets and compressed chunks, fragmented input, 129/257 BID partitions, consumer failures and final padding boundaries are checked.

The deterministic detailed page contains 10112256 packed source bytes and 10548956 serialized bytes. Host output equals every original-decoder/source byte; larger target output uses a prefix plus full FNV-1a and counts.

The 32-bit component state and fixed memory total 91028 bytes.

Streaming reuses one current-page metadata slot with checked 32-bit totals; retained-file mode still has 16 slots. Narrow planner/profile, default padding and a 65552-byte BID limit. Output remains provisional until finish. Consumer errors abort rather than retry. State/memory totals exclude code, stack, caller packets and test captures. No asynchronous scheduler, raw queue, cache, engine, USB, boot or printing.
