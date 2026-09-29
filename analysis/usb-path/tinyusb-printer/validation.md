# Reusable USB printer execution

Patched pinned TinyUSB, reusable class/receive adapter and bounded document/JBIG/output composition under synthetic DCD events, with independent USB packet and decoded pixel oracles.

98 host cases; 98 target cases. Exact decoded pixels, retained buffers and packet proposals checked.

No controller/MMIO/boot/cache implementation, physical status, USB traffic or printing. Initial class reset, cancellation, three recovery promises and end-of-input are supplied. Output progress is synchronous; copies remain metadata. Continuous normal jobs need a later validated document-boundary/completed-page path.
