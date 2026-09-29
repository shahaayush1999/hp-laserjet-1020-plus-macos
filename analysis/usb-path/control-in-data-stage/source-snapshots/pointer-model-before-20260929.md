# Control-IN pointer model before static correction

`pointer-model-before-20260929.tar.gz` preserves exactly the three files saved in
`/tmp/hp1020-control-pointer-before-20260929/`: the earlier
`scripts/model-hp1020-control-in-data-stage.py` generator and its JSON/Markdown
reports. These are selected historical model artifacts, not a complete source
closure or an original-code execution capture. There is no failed execution or
new hardware observation associated with this archive.

The old generator computes `descriptor_base | 0x80000000` and labels the literal
as a hardware alias flag. Because the report's supplied base is `0x900226f0`, that
OR leaves the example unchanged and does not distinguish the operations. The
subsequent byte-anchored static correction separates active pointer submission
(unchanged supplied pointer) from initialization (addition of `0x80000000` modulo
32 bits, paired with HOST_BUSY status). Neither operation proves a physical
address alias or translation rule. The corrected generator/report remain at the
existing repository paths; these saved old files are untouched.

The archive adds no reconstructed stock ELF, logs or missing provenance. Its
adjacent JSON records every member SHA-256 and the archive SHA-256. Each archive
member was read back and compared byte-for-byte by SHA-256 with the frozen source.

- Old generator SHA-256:
  `352f928cbb33f56a7d430f0e0183776ad41a02ec46a3340f216bd63788c6a22f`.
- Old JSON report SHA-256:
  `81a319c902ce653e324cb5f75f4698e3ba3634cf9d9523fb9937423698113a14`.
- Old Markdown report SHA-256:
  `da74da1d47f46a68c86ad4a98cb62d77d5402d752d3918a469ce56be8db449ae`.
