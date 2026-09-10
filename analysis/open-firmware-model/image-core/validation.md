# Open streaming image decoder validation

Status: pass. Open streaming software JBIG decoding and packed-row bands. Full host byte comparisons against the existing full decoder and generated source pixels. No stock custom code, DMA, MMIO, USB, engine or printing.

176 focused cases, 21 original/normalized full-decoder comparisons and 32 separately classified mutations. Host runs use ASan and UBSan, row/band guards, input poisoning between feeds, paused-consumer checks and sticky error checks.

QEMU: 66 cases; two identical target builds; 286,367 instructions in the separate small-page interpreter check. A4 state/history/four-row band storage: 11,512 bytes, excluding code, stack, caller input and test fixtures.

This report tests the decoder independently; the semantic-page bridge has separate validation. No stock raw queue integration. Physical pixel format, CPU throughput, printer RAM placement, cache visibility and output remain unproven. Existing parser still stores compressed input. Output before DONE is provisional; JBIG has no checksum.
