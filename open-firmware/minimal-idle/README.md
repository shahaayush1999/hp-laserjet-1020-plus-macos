# HP 1020 Minimal Idle Probe

This is a non-printing custom firmware candidate for offline inspection only.

It is meant to answer one narrow question later: can our own code be packaged in the HP 1020 firmware upload shape at all?

It intentionally does not:

- initialize the print engine
- touch video/raster MMIO
- touch fuser, motor, scanner, or paper-feed paths
- parse print data
- claim to be useful printer firmware

The first version only builds an Xtensa ELF with HP-like placement anchors:

- ELF machine patched to old Xtensa `0xabc7`
- entry at `0x100167a8`
- window vectors around `0x10000000`
- system interface table at `0x10000370` with every slot pointed at a local safe trap loop
- early runtime-vector words around `0x10006a14`/`0x10006a58` pointed at local trap/state placeholders
- reset vector at `0x10100020`
- HP-style date-prefixed `.img`
- HP-style PJL/ACL `.dl`

The interface table and early runtime-vector placeholders intentionally do not copy HP function pointers. Callable slots point to a local loop, so an unexpected call should hang the probe instead of jumping through null or touching printer hardware.

Do not upload this to the printer unless it passes the static layout and safety scans and the remaining boot-ROM/interface-table assumptions have been reviewed.
