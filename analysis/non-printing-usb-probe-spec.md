# HP 1020 Non-Printing USB Probe Spec

This is the narrowest custom-firmware target that currently makes sense.

It is not a print prototype. It is a boot/USB proof only.

## Goal

Prove one fact:

```text
Can a non-HP payload boot far enough to expose a basic USB identity without touching printer engine/video hardware?
```

If the answer is yes, replacement firmware becomes more realistic. If the answer is no, the blocker is
boot ROM / Xtensa ABI / ELF layout, not printing logic.

## Hard Safety Rule

A first custom probe must not touch:

- `0xb100....` video/raster block
- `0xb200....` video transfer descriptor/control
- `0xb204....` video transfer channel A
- `0xb208....` video transfer channel B
- `0xb050....` engine command/status handshake
- `0xb020....` engine/control family

It must not call or clone the behavior of:

- `0x10014910` `hp1020_video_prepare_page_candidate`
- `0x10015214` `hp1020_video_render_or_dma_candidate`
- `0x100140f8` `hp1020_video_refresh_raw_bands_candidate`
- `0x10015458` `hp1020_video_reset_or_flush_candidate`
- `0x10015c68` `hp1020_engine_status_io_candidate`
- `0x10015df8` `hp1020_engine_status_poll_candidate`
- `0x100160a8` `hp1020_engine_preflight_candidate`
- `0x10016164` `hp1020_engine_message_dispatch_candidate`

## Allowed First Target

The only plausible hardware family for a first probe is:

- `0xb300....` USB controller

Even that should be treated as a watch item, not automatically safe. The reason it is acceptable as a
first target is practical: USB identity does not require paper motion, fuser control, or raster/video
transfer.

## Candidate Behavior

Minimum behavior:

1. Boot into a controlled loop.
2. Initialize only the minimum CPU/runtime state needed for USB.
3. Expose USB descriptors compatible enough to be visible to the host.
4. Optionally respond to basic control endpoint descriptor requests.
5. Do nothing on print/raster data.
6. Never submit engine queue messages or video work.

Expected good result:

```text
macOS sees a USB device/printer-ish identity, but no printing happens.
```

Expected bad but acceptable result:

```text
device disappears or fails to enumerate until power-cycle
```

Unacceptable result:

```text
paper feed, fuser warmup, motor/scanner/laser activity, repeated mechanical noise
```

## Current Blockers

- No local old/big-endian Xtensa compiler/linker is installed.
- The exact Xtensa core/ABI is not confirmed beyond the existing `elf32-xtensa-be` container.
- The boot ROM may require the HP `.sys_interface_table`, vector layout, or hidden ABI details.
- The ACL download handoff appears to pass through a resident bootcode/interface table, so replacing the payload may not be as simple as wrapping any ELF.

## Required Gate Before Upload

Before any custom artifact is uploaded, run the candidate source/disassembly through:

```sh
scripts/check-hp1020-safety-boundary.py path/to/candidate
```

The scan must have:

- zero `fail` hits
- only expected `watch` hits for USB `0xb300....` or unavoidable boot/timer MMIO

Do not use `--allow-unsafe` for upload candidates. That option is only for validating the scanner
against known unsafe firmware code.

## Practical Next Offline Work

1. Build or locate a compatible big-endian Xtensa toolchain.
2. Produce a structurally valid ELF-shaped dummy payload without uploading it.
3. Validate the wrapper/image/ELF shape locally with `scripts/inspect-firmware-layout.py`.
4. Run the safety scanner against the candidate source/disassembly.
5. Only then decide whether a printer-connected boot/USB probe is worth the physical risk.

