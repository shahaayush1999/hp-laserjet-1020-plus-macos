# Original chunk-12 parser and raw-list admission

10 parser/admission cases and 2 metadata-only controls agree in the interpreter and independent QEMU. Zero completed page lifecycles.

- Ten nonempty chunk-12 inputs run through the full original parser, real allocator/queue and JobMgr admission. Original document/page/work packets construct the owner hierarchy; input callbacks, readiness and document notification/publication remain host boundaries.
- The actual data allocation requests exactly 16 bytes with allocator kind 0. The parser stores the returned pointer unchanged in payload+0x54, and admission preserves it. This route does not supply the 16-byte image prefix used in the separate raw-retirement fixtures.
- Explicit bitmap metadata 0 selects source kind 1; bitmap metadata 1 selects source kind 0. Both tested variants send selector 3, append to work+0x50 and receive one or two references from the original copy metadata. Work raw-IRQ flag +0x74 is zero after construction and after admission.
- Payload source size is 16, dimensions are 32 by 4, bpp is 1 and the terminal flag is 1. Two controls omit explicit band width/height: original BIH/cache fallback produces the same dimensions. No physical packing or support for arbitrary metadata is inferred.
- Two metadata-only chunk-12 controls allocate no data and emit no message 9. All twelve comparisons agree between the bounded interpreter and independent QEMU, including pool partitions, bytes and explicit host boundaries.
- The original standalone helper at 0x10010420 is never entered by this parser route. This establishes a separate software producer, not that helper's caller, raw-mode reachability, completion, second-copy cursor restoration or physical output.

Synthetic single-thread RAM and seeded allocator/queue state; input callbacks, document begin/end, document publication and task readiness are explicit boundaries. Nonempty runs stop immediately after the first raw-list admission, with END_PAGE/END_DOC still queued. The raw IRQ flag is not forced, no raw retirement/VideoThread/PrintMgr/engine/custom instruction/MMIO/USB path executes, and zero completed page lifecycles or physical printing are claimed. Numeric chunk 12 exists in this stock ELF; its host header name is not proof of another model's support. The open parser grammar is unchanged.
