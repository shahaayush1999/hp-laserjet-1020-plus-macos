# HP 1020 Firmware Identity Mapping

This pass maps the printer identity strings and the functions that appear to assemble identity/status responses.

## What Was Mapped

- `analysis/ghidra-scripts/MapHp1020IdentityData.java` searches for HP/product/PJL identity strings, pointer-table references to those strings, and related functions.
- `analysis/identity/identity-map.md` is the generated address map.
- `analysis/identity/identity-decompiled/` contains Ghidra decompiler output for the related functions.

## Main Finding

The firmware does not appear to store USB string descriptors as simple static UTF-16 descriptor blobs. The visible manufacturer/product text is stored as ASCII data and used through pointer tables and response-builder functions.

That means the USB descriptor path has two layers:

- static USB binary descriptors for device/config/interface/endpoint structure
- runtime-built identity strings/device-ID/PJL responses using ASCII product data

This is normal embedded firmware behavior, but it matters for replacement work: copying static descriptors is not enough. A replacement firmware would also need to recreate the runtime device-ID and status response behavior expected by drivers and spoolers.

## Identity Data

Important strings found:

- `0x1001bf70`: `Hewlett-Packard`
- `0x1001bf8c`: `HP LaserJet 1020`
- `0x1001bfb0`: `HP LaserJet 1020`
- `0x1001bfd4`: `ACL.PRINTER`
- `0x10004728`: `@PJL ECHO `
- `0x10004cd3`: `xxMFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;`
- `0x10003b18`: `HPBOISEID`
- `0x10003734`, `0x10004d04`, `0x10004d28`: `20050309`

Important pointer-table locations:

- `0x100034a4` points to `Hewlett-Packard`
- `0x100034a8` points to `HP LaserJet 1020`
- `0x10004c74`, `0x10004c7c`, `0x10004c84` are identity/device-ID table entries
- `0x100064e0`, `0x100064e4`, `0x100064f0` are literal-pool/table references used near identity/status construction

## Related Functions

- `0x1000b3f8` `hp1020_pjl_ustatus_result_builder`
- `0x1000bd04` `hp1020_pjl_info_capabilities_builder`
- `0x1000cdb0` `hp1020_pjl_echo_matcher`

These are PJL/status side functions, not the low-level USB control-transfer function. They build strings such as USTATUS and capability responses with helper routines:

- `0x10007430` `hp1020_format_into_buffer_candidate`
- `0x100169d4` `hp1020_strlen_like`
- `0x1001b544` `hp1020_append_string_to_buffer_candidate`
- `0x1000dc00` `hp1020_alloc_buffer_candidate`

## What This Says About Viability

This is useful progress but not a shortcut to replacement firmware. We can now point to real identity/status paths and not just say "there are strings." However, even this small area already shows firmware behavior being assembled dynamically through runtime buffers and helper calls.

For an open replacement, the easy part would be cloning the USB descriptor and basic IEEE1284 identity response. The hard part remains the print engine and hardware timing path.
