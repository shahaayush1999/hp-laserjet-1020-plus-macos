# Compiled semantic target validation

Status: pass. 78 cases, 23,443,503 executed instructions, 899 distinct reached instructions.

The real compiled C parser, memory helpers, software unsigned division and page planner execute without a peripheral model. No upload image is produced.

All generated fixtures match independent Python field/payload/planning expectations at three fragmentation sizes. All cases also match an ASan/UBSan native oracle. MMIO, misaligned word loads, code writes and execution from data sections are rejected.

This tests compiler/ABI/CPU arithmetic and RAM behavior. It does not prove boot-ROM state, USB behavior, cache coherency, custom raster instructions or mechanical safety.
