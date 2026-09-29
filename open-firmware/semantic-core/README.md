# Portable semantic core

This C component constructs page metadata and compressed raster records from
incrementally supplied, big-endian JZJZ streams. It has no USB or
hardware addresses, allocator, video path, or engine path. It is not linked into
any printer probe.

In the default retained mode, the caller owns a bounded byte arena and a parser object. Feed arbitrary byte
fragments, then call `hp1020_semantic_finish`; errors are sticky, and an unfinished
chunk or document fails as truncated. Raster records use arena offsets, not
firmware pointers. Up to 16 pages, 128 raster nodes, 4096 metadata bytes per chunk,
and 16 MiB per chunk are accepted. The caller must retain the arena for the
lifetime of the records and consume records only after success.

Each page also retains its exact 20-byte BIH. The retained-mode image bridge in
`../image-core/` checks that original coding profile before decoding compressed
records into bounded packed-row bands.

`hp1020_semantic_init_streaming` selects an optional synchronous chunk consumer
while preserving the same grammar. After a complete chunk has updated metadata,
the callback receives its bytes; after successful BID consumption the arena is
reused. This mode reuses `pages[0]` for the current page and retains no raster
records or compressed history. Use `hp1020_semantic_current_page` during the
callback and copy any metadata needed beyond the next START_PAGE. The remaining
page slots stay zero. Page/raster counts and first-raster values are cumulative
counts, not indices into the arrays; the 16-page/128-record retention limits
therefore do not apply. Page/document/raster counters and per-page compressed
bytes remain bounded by uint32, and each BID must fit the supplied arena. The
retained image bridge explicitly rejects streaming parser state; its original
16-page limit remains intact and is separately checked with the same input.

Callbacks must consume/copy data before returning, may not re-enter or mutate
the parser, and must not retain the pointer. Any callback error aborts parsing
and stays sticky. The parser offers no retry or asynchronous output protocol.
Output can precede a late error, so it remains provisional until finish succeeds.
`hp1020_image_stream` supplies the bounded software decoder consumer; it adds no
device operation. Its separate stream validator checks large detailed pages,
packet/chunk reuse, retained-mode controls and consumer failures.

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

`hp1020_page_plan.c` consumes a successfully completed page and its metadata-bound
flag. Its narrow policy accepts 600dpi, NBIE1, BPP1/2, RET0, ECONOMODE0/1 and
positive heights divisible by four. It rejects the BPP4 zero-refill case and the
logical-clip declared-length mismatch. The semantic parser still retains these
inputs for analysis. The planner emits row offsets, counts and byte lengths;
it contains no device addresses or output callbacks and makes no hardware-ready
claim. Each band's bytes are at most 8192, all rows are covered exactly once per
copy, and only the final band is marked final. A4 gives 1706 four-row bands.

`python3 scripts/validate-hp1020-page-plan.py` checks 1398 cases and more than
five million band partitions under ASan/UBSan. Callback transformations, live
buffer ownership and mechanical sequencing remain outside this component.

The `freestanding/` test fixture links these same C components at synthetic
address `0x20000000`, with call0 functions, small memory helpers and software
unsigned division. It is an emulator test ELF, not a bootable printer image.
Build with `scripts/build-hp1020-semantic-target.sh` after rebuilding the compiler
with `scripts/build-xtensa-gcc-manual.sh`. The target validator executes 78 cases
and compares over 23 million instructions' results with both native sanitizer
execution and independent generated-stream expectations. It does not model USB,
cache coherency, core-specific raster instructions or engine mechanics.
