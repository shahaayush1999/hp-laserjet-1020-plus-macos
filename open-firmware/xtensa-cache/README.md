# Bounded CPU cache maintenance

Three BE/call0 routines implement writeback, writeback-plus-invalidation and
invalidation without writeback for an
already owned cached CPU range. They check alignment, size, wrap and the chosen
numeric CPU window before any operation, then issue MEMW, one operation every16
bytes and DSYNC. Empty requests do nothing. They neither round into adjacent
storage nor translate a CPU pointer to a DMA address. They are not linked into
the current controller/entry profiles.

The caller still needs a valid memory/cache/privilege profile and exclusive
ownership of every actual cache line, including aliases. See the header for the
preconditions. In particular, clean-invalidate belongs **before** device writes;
using it to acquire DMA output could write stale dirty bytes over that output.
These functions supply CPU instructions, not proof of DMA settlement or hardware
visibility. The16-byte original stepping is insufficient by itself to establish
the physical cache-line size.

`invalidate_owned` supplies the discard-only operation needed before reading
completed device output through a cached address. Completion/visibility must
already be independently established; no CPU modifications anywhere in the
touched lines may need preservation. It is not a DMA completion check. The
cache profile must also ensure unlocked lines: DHI and DHWBI can leave locked
lines present without raising an exception. See the primary
[Cadence ISA summary, DHI/DHWBI](https://www.cadence.com/content/dam/cadence-www/global/en_US/documents/tools/silicon-solutions/compute-ip/isa-summary.pdf).

Original helpers0x100173c8,0x10017414 and0x1001733c use DHWB/DHWBI/DHI respectively, increment
addresses by16 and finish with DSYNC. Bulk-IN queuing calls the former at
0x10008bcc; the incoming callback calls DHWBI. The DHI helper's existence is not
proof that the original USB path calls it. The original count is
`((bytes + (address & 15) + 15) mod 2^32) >> 4`. Thus an unaligned zero-length
request still touches a line, while large lengths can wrap to no work. The open
API rejects nonempty unaligned/wrapping requests and does no work for zero.

Original startup operand computation at0x10006d4a first writes attribute2 to all
eight instruction/data regions. The later0x10006def loops write low-to-high
attributes`4,4,2,2,2,2,15,15`, at512-MiB intervals. Under Xtensa region protection,
these correspond to cached lower regions, bypassed middle regions and denied
upper regions; see the primary [QEMU region-attribute implementation](https://raw.githubusercontent.com/qemu/qemu/v10.1.0/target/xtensa/mmu_helper.c).
The selected attribute loops omit CPU reset, cache initialization and boot.
Their operands do not establish the actual processor configuration, physical
memory map, available RAM or equivalence of0x100.../0x900... addresses. Do not
turn this into an unconditional bit31 DMA mapping rule.

`python3 scripts/validate-hp1020-xtensa-cache.py` checks original operands and
the open routines in the interpreter and independent QEMU, rejecting other
operations before execution. QEMU cache instructions are not a dirty-cache or
bus model. Original TLB writes are recorded only, since the emulator CPU uses a
different MMU profile. The compact current result is
`analysis/boot-handoff/cache-contract.json`; no printer is contacted.
