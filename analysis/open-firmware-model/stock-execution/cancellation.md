# Conditional original cancellation findings

48 fixture cases and two original producer paths agree across both execution engines.

- Original producers can send cancel reasons 2 and 4 to JobMgr under the recorded media/status fixtures; these selectors were not invented solely to trigger cleanup branches.
- Reason 2 leaves a 120-byte document allocation at quiescence after either tested cancellation ordering. Reason 4 before END_DOC leaves an 80-byte child allocation plus its 16-byte completion notice. The retained document/child has no aligned pointer reference in tested non-stack writable RAM; this is bounded reachability evidence, not proof against arbitrary encoded references.
- Reason 4 after END_DOC attempts a read through null at 0x1000eb6a. The same fixture avoids that invalid read when the acknowledgement is processed before END_DOC. Both CPU engines agree across fills, raster splits and overrides of the two work-release flags.

These are conditional stock-software findings, not observed printer faults. The single scheduled work is assumed to own the seeded video raster chain, reset is assumed to reach the original RAM tail, and the tested coordinator handshake is summarized as a queue relay. JobMgr executes independently in QEMU; its host stop boundary runs the tail through the separately QEMU-checked interpreter component. Engine stop, DMA ownership, interrupts, physical fault meaning and actual cancellation timing remain unverified. Status publication callbacks are omitted in the producer fixtures.
