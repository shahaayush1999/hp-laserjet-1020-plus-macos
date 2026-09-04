# Portable semantic core

This C component constructs page metadata and compressed raster records from
incrementally supplied, big-endian JZJZ streams. It has no I/O callbacks, USB or
hardware addresses, allocator, video path, or engine path. It is not linked into
any printer probe.

The caller owns a bounded byte arena and a parser object. Feed arbitrary byte
fragments, then call `hp1020_semantic_finish`; errors are sticky, and an unfinished
chunk or document fails as truncated. Raster records use arena offsets, not
firmware pointers. Up to 16 pages, 128 raster nodes, 4096 metadata bytes per chunk,
and 16 MiB per chunk are accepted. The caller must retain the arena for the
lifetime of the records and consume records only after success.

The implemented grammar is START_DOC, followed by zero or more
START_PAGE / JBIG_BIH / one-or-more JBIG_BID / END_JBIG / END_PAGE sequences,
then END_DOC. Multiple framed documents are supported. Only the controlled
uint32 metadata and single-layer/single-plane BIH subset is supported; duplicate
metadata, unsupported encodings, invalid transitions and exhausted storage fail
closed. This is deliberately narrower than the proprietary parser.

Supported page items are retained verbatim. The active-work sidebands are the
low 16 bits of VIDEO_Y, RET and ECONOMODE, verified against the stock direct
START_PAGE item builder in `analysis/hardware-boundary/zjs-direct-work.md`.
This establishes the source of the values, not their physical hardware meaning.
The `reserved` header field is checked against payload size but does not delimit
metadata: existing foo2zjs logical-clip output understates it. Item count and
actual chunk size bound parsing instead. This behavior is a safe host component
choice and does not assert that stock handles that malformed length safely.

Run `python3 scripts/validate-hp1020-semantic-core.py` from the repository.
Validation compiles with AddressSanitizer and UndefinedBehaviorSanitizer, compares
all generated streams with the print-path model, and exercises fragmentation,
malformed inputs, capacity limits, truncation, multipage/multi-raster inputs and
opaque binary payloads. Compressed bytes are retained; they are not decoded.
