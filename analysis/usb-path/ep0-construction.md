# Original EP0 construction cuts

Explicit original IN0 zero/single-packet and ordinary OUT0 construction cuts, plus distinct active pointer passthrough and initialization ADD-only cuts; literal BE descriptor, ordered writes, every mutable RAM byte and independent pointer arithmetic compared in both engines.

36 descriptor-construction and 12 pointer-only profiles; 16 pre-MMIO and 2 out-of-profile controls; 18 excluded PCs. Counts are per engine and establish no USB lifecycle.

All logical registers, pointer cells, nonzero-path MPS RAM word and preexisting RAM are supplied. Original ENTRY/control setup, copy/cache helper, SETUP initialization/publication, multi-descriptor path, controller accesses, kick, event wait and completion are excluded. Numeric encoded buffer pointers are never dereferenced; no CPU/DMA mapping or alias is inferred. OUT zero count proves no allocation capacity or completed status packet. The initialization ADD-only cut asserts no HOST_BUSY construction. Mode, cache/publication order, immutable hardware events, success/count/settlement, boot and printing remain unproved.
