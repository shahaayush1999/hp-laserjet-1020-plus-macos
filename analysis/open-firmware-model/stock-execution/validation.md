# Original firmware execution checkpoint

Original stock routines execute in isolated host RAM; no printer contact or hardware model.

Status: pass. 9,841 cases, 713,131 executed instructions; 698 distinct instructions.

## Results

- memset: 2328 cases.
- memcpy: 6208 cases.
- memmove: 468 cases.
- strlen: 776 cases.
- parser_agreement: 59 cases.
- parser_policy_difference: 2 cases.

The original parser, item builder, page constructor, list initialization and libc routines run unchanged. Generated print streams, reordered metadata, multiple pages and split raster records are compared with the sanitizer-built C replacement. The stock queue emits document/page/BIH/BID records matching the checked fields and byte payloads.

The test exposed a reversed BE bit-branch interpretation in the earlier target interpreter. Bit branch 31 tests the least significant bit. The stock memset/memcpy/strlen routines now validate that interpretation across alignments and lengths. A taken branch to LOOP end exits rather than repeating; the original strlen routine exercises this distinction.

The logical-clip stream now demonstrably reads outside its declared allocation during actual stock item-builder execution. Zero/duplicate copies show deliberate stricter replacement policy. A one-byte callback read shows that the stock parser requires its lower input layer to assemble a full requested read.

## Explicit host substitutes

- `0x10013140`: allocate.
- `0x10013408`: free.
- `0x10013658`: queue_send.
- `0x100181a4`: datastore_lock.
- `0x10018214`: datastore_unlock.
- `0x1001262c`: document_begin.
- `0x100126b0`: document_end.
- `0x30000000`: read.
- `0x30000004`: pushback.

## Limits

- Abstract unlimited register windows; no spill/interrupt/cache/RTOS/USB/engine execution.
- Tray lookup uses an explicitly seeded empty record; its physical mapping is not established.
- Queue delivery is captured, not consumed. Comparisons cover page fields, BIH and compressed records, not printing.
- Passing results are conditional on standard ISA semantics and the listed environment substitutes.

Standard bit-branch and loop-edge semantics are cross-checked against [QEMU Xtensa translation](https://github.com/qemu/qemu/blob/master/target/xtensa/translate.c) and the local Ghidra ISA source. These references define ordinary CPU behavior, not printer-specific custom instructions.
