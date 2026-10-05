# One entry through a RAM document

This offline ELF initializes its own stack/BSS, runs the compiled stream/image
path from one entry, produces exact decoded pixels and a document event, drains
ownership and parks. Original ELF memory ranges are layout references, not proof
of physical RAM or ROM handoff. The fixed workload retains full production
buffers and an independent compiler/manual layout comparison.

Run `python3 scripts/validate-hp1020-entry-ram.py`; `--audit-only` builds and
checks the linked bytes without execution. The independent checker verifies
saved CPU/RAM, accesses, executed instructions and debugger traffic against
separate literal expectations. The current result and complete source-bound
capture are in `analysis/boot-handoff/entry-ram/`.

Pinned QEMU reference sources and licenses remain in `references/qemu-primary/`.
Controller, cache and output observations are supplied by the test. This ELF is
not a printer upload image. No USB contact or physical printing is established.
