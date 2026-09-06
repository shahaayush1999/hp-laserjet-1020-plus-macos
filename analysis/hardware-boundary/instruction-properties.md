# Stock instruction annotations

Static stock-byte/annotation agreement; not proof of runtime reachability or hardware ISA semantics.

The ELF has 435 nonoverlapping instruction regions (85858 bytes) and 70 literal regions. Each region decodes contiguously and matches the original bytes.
All 6462 decoded direct control transfers land on annotated instruction starts. All 3289 literal loads resolve to file-backed data outside instruction regions; 28 loads use literal pools omitted from .xt.lit (startup/scheduler code). The literal table is therefore incomplete.

Decoding each region recovers 32600 instructions, including 623 starts missed by whole-section linear decoding (0 differing decodes at shared starts). Stock execution now requires these boundaries and refuses literal, padding and instruction-interior PCs.

The generic decoder cannot name 144 encodings beyond 7 identifiable user-register writes. Every such site lies in 0x10015518..0x10015bc5; this is a static census, not proof they all execute. Groups: {'0x68': 1, '0x66': 1, '0x65': 1, '0x64': 1, '0x69': 8, '0x60': 4, '0x6e': 2, '0x6d': 2, '0x8e': 40, '0x7f': 80, '0x8f': 4}.

The previously unaudited routine at 0x10015518 has four additional groups (68/66/65/64), writes user registers, and transforms row words. A scan of all annotated direct targets and every byte offset in allocated file-backed sections finds no reference to its entry. Do not add it to the active printing path without evidence; computed references remain possible. The three selected callbacks retain their existing report.

Malformed annotation and forbidden-PC checks reject 8 mutations.

Format provenance: Pinned binutils bfd/elf32-xtensa.c: xtensa_read_table_entries and xtensa_get_property_predef_flags; old tables use address,size pairs with implicit flags.

## Limits

- Annotations exclude padding/data; they are not a function map or a reachability proof.
- Generic binutils names do not establish exact core support or side effects. Unrecognized encodings remain forbidden in execution.
- Code outside annotations is not proven impossible to execute; the stock host interpreter conservatively refuses it.
- The additional routine contains groups 0x68/0x66/0x65/0x64 absent from the three selected callbacks; their semantics remain unknown.
