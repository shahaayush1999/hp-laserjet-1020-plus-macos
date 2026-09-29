# Composed USB descriptor execution

Immutable SETUP records plus exact-cookie EP0 and bulk OUT descriptors through actual TinyUSB, class/receive/JBIG output in synthetic RAM with independent wire, descriptor, pixel and document oracles.

34 host; 34 QEMU cases. Every retained snapshot, original cookie, exact packet proposal, pixel, document event and guarded allocation is compared.

No physical DCD, MMIO, IRQ, cache, boot, USB traffic or printing. CPU/DMA mapping, event sequencing, packet64/BE mode, visibility, hardware stall clearing and controller settlement remain supplied. IN actual length is separately supplied, never inferred from descriptor low16. Terminal sequence exhaustion settles controller ownership only; adapter notifications can remain pending and are not completed recovery. Copies remain metadata and output is synchronous.
