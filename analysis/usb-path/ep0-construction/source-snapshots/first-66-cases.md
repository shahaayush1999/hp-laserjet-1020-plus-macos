# Original EP0 construction: first 66 cases per engine

`first-66-cases.tar.gz` preserves the completed run from
`/tmp/hp1020-ep0-construction-rzkl2u5c` and the untouched
`/tmp/hp1020-ep0-construction-first-20260929.log` as `run.log`.
The original saved report records 66 conditional profiles passing in the
interpreter and in Xtensa/QEMU, plus 18 excluded-code controls in both engines.

The profiles comprise 36 IN0/ordinary OUT0 descriptor-construction cases,
12 distinct pointer-only cases, 16 pre-MMIO rejection controls and two excluded
multi-descriptor controls. The latter controls stop at the harness boundary;
they are not stock protocol rejection observations. Active submission preserves
the supplied descriptor pointer. The separate initialization cut executes a
wrapped ADD of `0x80000000`, including high-pointer inputs; it does not execute
the hardware store or establish a general DMA alias rule.

The archive contains all 10 recorded source files, including the original stock
ELF, source hashes/origins, exact `report.json` and `report.md`, byte-audit and
excluded-code records, and every engine's supplied inputs, observation/event
record and before/expected/after raw RAM. It preserves all 676 capture files plus
the log; nothing is omitted. There is no newly built target ELF: this experiment
executes the archived original stock ELF through explicit construction cuts.

Before archiving, all source hashes and report records were matched to their
saved files, and all 1,980 reported memory-region hashes were checked against the
396 raw RAM captures with exact file lengths. Every one of the 677 archive
members was then reread and hashed. The adjacent JSON records the archive hash
and every member hash. No report or tested source was edited.

- Validator SHA256: `f2b239fffbac1ec5af498174975129b56ab32e7100ff863f5d486c1f9dfadde5`.
- Original ELF SHA256: `2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d`.
- Frozen report SHA256: `8e41f358f5d956d5cdab71b45c136d6216bfa302af30a658f06f56e99696b53d`.
- Archive SHA256: `2f7d757d9b4de79b63ffe163d6fb057cd5bd09e8dcc0575b56bc53effb502644`.

These are explicit entry/stop cuts with supplied logical registers, pointer
cells, MPS RAM and initial memory. Original ENTRY, controller setup, buffer-copy/
cache helpers, multi-descriptor transmission and every peripheral access remain
excluded. Initialization pointer arithmetic and active pointer passthrough are
separate observations. There are no private literal redirects or supplied
services. The run adds zero completed USB control transfers, native page
lifecycles or physical USB operations and establishes no controller quiescence,
actual mapping, cache visibility, physical printing or power-cycle recovery.
