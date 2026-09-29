# Bounded document-to-output composition

Status: pass. Compiled bounded ZjStream parser, JBIG decoder and four-slot output ring with synchronous consumer progress. Exact pixels and entire output storage compared, with differing pages/documents and explicit completion ownership.

45 sanitized host cases and 45 QEMU cases.

Target state and fixed memory: 123988 bytes, excluding code, stack, caller packets and fixture captures.

Explicit software consumer supplies all output acceptance/completion. No device operations, scheduler, interrupt/cache integration, physical packing, printing or native lifecycle proof. Copies are forwarded metadata, not replayed output. Streaming page metadata is reused, with checked 32-bit counts; the retained-file parser keeps its independent 16-page limit. Late errors may follow already consumed rows and leave outstanding storage owned; caller must quiesce output before reuse.
