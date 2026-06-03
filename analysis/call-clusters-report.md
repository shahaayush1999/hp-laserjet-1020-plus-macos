# HP 1020 Firmware Call-Cluster Pass

This pass creates a coarse map of the firmware's functions using Ghidra-discovered calls, known labels from earlier passes, strings, and hardware-address references.

Generated artifacts:

- `analysis/ghidra-scripts/ClusterHp1020Functions.java`
- `analysis/call-clusters/call-clusters.md`
- `analysis/call-clusters/seed-decompiled/`

## Summary

Ghidra currently finds `326` functions in the extracted firmware ELF. The automated split is:

- USB control and enumeration: `12`
- PJL, ACL, and printer identity/status: `4`
- Memory/string/runtime helpers: `33`
- RTOS/threading/scheduler candidates: `96`
- Hardware register or SRAM touch points: `0` as a separate bucket, because the obvious ones are already classified into USB
- Other or unresolved: `181`

The `Other or unresolved` count is still high, but that is expected at this stage. The useful result is that the firmware is no longer a black box: USB enumeration/control and PJL/status handling now have clear neighborhoods and seed labels.

## What Is Now Fairly Clear

### USB Side

The USB control/enumeration area is concentrated around `0x10007c00` to `0x10009b00`.

Important functions:

- `0x10008ff0` `hp1020_usb2_thread`
- `0x10009934` `hp1020_usb2_idle_thread`
- `0x10008c24` `hp1020_usb_control_tx_data_stage_candidate`
- `0x10007c00` `hp1020_usb_register_transfer_candidate`
- `0x10008fb0` `hp1020_usb_drain_pending_queue_candidate`

The USB control-transfer function touches the `0xb300....` register range and `0x9002....` SRAM/DMA-looking buffers. That strongly supports the earlier interpretation that this is real device-side USB controller code, not driver glue.

### Descriptor And Identity Side

The static USB descriptors are mapped separately in `analysis/usb-path/internal-blocks.md`.

Known descriptor data:

- device descriptor: `0x1001bc00`
- configuration/interface/endpoint descriptor tree: `0x1001bc20`
- device qualifier descriptor: `0x1001bbd0`

Identity/status text is mostly ASCII runtime data, not static USB UTF-16 descriptor data. See `analysis/identity-report.md`.

### PJL/Status Side

Important functions:

- `0x1000ad44` `hp1020_acl_download`
- `0x1000b3f8` `hp1020_pjl_ustatus_result_builder`
- `0x1000bd04` `hp1020_pjl_info_capabilities_builder`
- `0x1000cdb0` `hp1020_pjl_echo_matcher`
- `0x1000d6b0` `hp1020_pjl_read_or_poll_candidate`

This part builds printer-language/status responses like `USTATUS`, `INQUIRE`, paper sizes, trays, page counts, and capability text. It is string-heavy and much more tractable than the print-engine side.

### RTOS/Runtime Side

The firmware includes ThreadX text:

- `Copyright (c) 1996-2001 Express Logic Inc. * ThreadX ARM9/ARM Version G4.0.4.0 *`

The CPU is not ARM; the string appears to be a generic ThreadX build/version banner. Function behavior still looks like an RTOS/runtime tail.

Seed candidates:

- `0x10017d28` `threadx_queue_receive_candidate`
- `0x10018274` `threadx_thread_create_candidate`

The current cluster pass marks many functions from `0x10017600` onward as RTOS/threading candidates. That is deliberately broad and should be narrowed later.

## What This Means For The Original Estimate

AI speed helps with tooling, scripting, labeling, and report generation. It does not remove the hard embedded parts.

In this session, the fast part moved faster than a normal manual reverse-engineering pass:

- toolchain setup
- ELF extraction/import
- descriptor mapping
- identity/status mapping
- first call-cluster map

But the remaining work is not just "more typing." The hard part is proving behavior against hardware:

- which `0xb300....` registers do what
- how the print engine accepts raster/page data
- motor/fuser/scanner timing and safety states
- whether unknown resident vectors at `0x10000350`/`0x1001be90` hide boot ROM or interface-table behavior

So the practical estimate changes like this:

- "Can we map USB and PJL/status enough to understand the firmware shape?" Yes, and it is already happening quickly.
- "Can we make a small open USB identity/status firmware?" Maybe, if hardware upload/boot details cooperate.
- "Can we make firmware that safely prints?" Still not a day-or-two task. That remains months-class unless a public hardware manual, matching SDK, or prior firmware project appears.

## Next Useful Passes

1. Thread/task map: find where names like `USB2Thread`, `PrintMgr`, `tEngine`, and queues are created and which function pointers they use.
2. MMIO map: resolve literal tables that point at `0xb300....` registers and group every function touching them.
3. ACL/PJL command parser map: label command dispatch tables and input-token functions.
4. Print-engine map: trace `PrintMgr`, `tEngine`, `?Video Queue`, and page/raster buffers.
