# Original JobMgr execution

Serialized original parser, JobMgr, list append, memcpy, page scheduling and selected MMIO-free render paths in isolated RAM; queue 1 requests are captured, never delivered to hardware.

118 pipeline, 36 allocator and 256 MMIO-free render cases; 197516 downstream instructions (616668 including parser/allocator/render); 1057 distinct original instruction addresses.

- Page and raster fields agree with sanitizer-built C, and every compressed chunk agrees byte-for-byte with its input.
- Original list links preserve page/raster ordering and correct head/tail; END_JBIG overwrites the last raster marker with 1.
- Earlier raster markers retain allocator contents copied from payload +0x2c: zero in the zero-fill fixture, CCCC in the poison-fill fixture. The parser/JobMgr path does not establish zero initialization.
- Separate original type-1 allocator execution preserves all requested payload bytes across 36 poisoned/zero-memory cases; a zero-fill guarantee cannot be attributed to that path.
- BIH buffers are copied then freed; BID wrappers and payload bytes remain on page-owned lists.
- Original scheduling emits at most available credits, preserving page order; no consumer replenishes credits in this fixture.
- Complete MMIO-free render paths ignore the raw marker and change video +0x9c/+0xa0 even when returning busy. Earlier ring-model ordering incorrectly put these stores after rejection.
- Duplex fixture doubles the raster copy halfword, wrapping at 16 bits. This is observed stock behavior; no duplex support is added to the narrow replacement.

## Explicit limits

- Parser is run before serialized queue replay; concurrent production/consumption, interrupts, queue backpressure and allocation failure are not exercised.
- Pipeline task startup, document publication, RTOS critical sections, allocation and queue delivery are host substitutes; the separate allocator experiment executes original allocation with only mutex substitutes.
- Document publication substitute writes its bookkeeping flag; datastore/queue-10 effects are omitted.
- Only MMIO-free rejection/queued render paths execute; initial hardware arming, decompression, custom raster instructions, USB and mechanical timing remain outside.
- No empty documents, cancellation, malformed message ordering or multi-document lifecycle are claimed.
