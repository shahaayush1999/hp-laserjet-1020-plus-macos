# One-descriptor USB OUT execution

One original-cookie RAM descriptor per 64-byte OUT submission, actual patched TinyUSB dispatch and existing bounded receive/JBIG/output with independent byte, packet, notification and pixel oracles.

34 host cases; 34 target cases. Exact bytes, notifications, ownership and storage checked.

No physical DCD, controller/MMIO/boot/cache/IRQ implementation or printing. Packet64/BE mode, exact CPU/DMA mapping, cache visibility/publication order, immutable original-cookie observations and transfer settlement remain supplied. Descriptor owner bits do not settle DMA or acknowledge global reset promises. Synchronous software output; copies remain metadata.
