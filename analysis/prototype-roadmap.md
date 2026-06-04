# HP 1020 Open Firmware Prototype Roadmap

This is the practical roadmap after the current reverse-engineering pass.

## Current State

We now know enough to split the problem into layers:

| Layer | Status |
|---|---|
| Upload envelope | known; reproducible byte-for-byte |
| ELF shape | known; Xtensa big-endian ELF with date prefix |
| Boot/vector shape | mapped enough to understand constraints |
| RTOS primitives | queue/thread/timer object model partially mapped |
| USB descriptors/path | mapped enough for a minimal clone target |
| Queue/message routing | mapped enough for architecture reasoning |
| Engine/video hardware | entry points and first MMIO semantics mapped |
| Safe printing behavior | not solved |

## Prototype Options

### Option A: No-Hardware Static Prototype

Goal:

- generate a firmware-like `.dl` file from a controlled ELF-shaped payload
- verify wrapper, date prefix, and structural fields locally

What it proves:

- packaging pipeline works
- repo can generate candidate upload artifacts

What it does not prove:

- printer boot ROM accepts it
- USB enumerates
- hardware is safe

Risk:

- none to the printer if not uploaded

### Option B: Minimal Boot/USB Probe

Goal:

- upload a tiny ELF that tries to boot and expose USB, or at least reach a visible state

What it could prove:

- boot ROM accepts non-HP code in the same wrapper/ELF shape
- minimal firmware can run after upload

Problems:

- we do not yet have the exact Xtensa variant/toolchain ABI
- boot/runtime interface expectations may be stricter than ELF headers
- if the firmware fails silently, the printer may just disappear until power-cycle

Risk:

- probably recoverable by power-cycle if it only touches USB/boot state
- should not touch engine/video/fuser registers

Hardware needed:

- printer on and connected
- user available to power-cycle
- a known-good HP firmware upload ready afterward

### Option C: USB Identity Clone

Goal:

- boot custom code that enumerates as the printer and responds to basic USB/PJL identity/status

What it could prove:

- open firmware can replace the non-printing host-visible layer

Hard parts:

- USB controller setup
- descriptor/control endpoint handling
- matching enough HP/PJL behavior for host tools

Risk:

- still mostly USB-side if engine registers are avoided

### Option D: Controlled Single-Page Print

Goal:

- print one deliberately simple page

Hard parts:

- raster band format
- `0xb100`/`0xb200`/`0xb204`/`0xb208` video transfer
- `0xb050` engine handshakes
- paper/fuser/motor/scanner timing
- error handling and recovery

Risk:

- real mechanical/thermal risk if engine sequencing is wrong

This should wait.

## Best Next Technical Step

Before uploading anything custom, the best offline step is a minimal candidate-ELF builder only if a compatible Xtensa toolchain can be identified.

Needed facts:

- Xtensa core variant / ABI compatibility
- expected reset vector and entry behavior
- whether `.sys_interface_table` must be preserved
- whether boot ROM validates sections beyond program headers

If toolchain support is weak, the better next step is not "write firmware." It is a smaller emulator/static-loader experiment:

- parse the HP ELF program headers
- emit an identical section/program-header layout report
- define the minimum set of sections a custom ELF would need
- compare candidate ELF layout byte-for-byte against structural expectations

## Safety Gate Before Any Upload

Do not upload a custom firmware candidate unless:

- the printer is physically present and easy to power-cycle
- the stock `sihp1020.dl` upload still works
- the custom candidate intentionally avoids engine/video MMIO
- the user explicitly agrees to a hardware test
- the candidate artifact is saved and checksummed
- the expected failure mode is "printer disappears until power-cycle"

## Practical Assessment

The analysis front-end moved fast. The remaining gap is not just "more labels"; it is proof that custom code can boot on this specific Xtensa/HP boot ROM path, and proof that hardware registers can be used safely.

Right now the most defensible next milestone is:

```text
produce a structurally valid custom firmware candidate, but do not upload it yet
```

That keeps progress concrete while avoiding unnecessary risk to the working printer.

