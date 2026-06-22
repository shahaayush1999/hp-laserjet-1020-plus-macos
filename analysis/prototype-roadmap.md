# HP 1020 Open Firmware Prototype Roadmap

This roadmap is for the narrow goal: replace the HP firmware blob enough to
print normal host-generated pages. It is not trying to implement unrelated
features or support other printer families.

## Current State

| Layer | Current status |
|---|---|
| Upload envelope | solved; PJL/ACL wrapping and date-prefixed Xtensa ELF shape are reproducible |
| Toolchain | solved enough for assembly-only probes using the manual Xtensa binutils prefix |
| Minimal custom firmware artifact | solved; `open-firmware/minimal-idle/` builds a non-printing idle probe |
| First custom upload | attempted once; backend sent bytes and printer stayed green/quiet |
| USB register map | mapped enough for non-printing USB-only probes |
| USB descriptor payloads | solved at byte level from stock firmware |
| Open USB marker candidate | built; not uploaded yet; still depends on unproven setup-buffer/response-state assumptions |
| Host print stream | modeled; ZjStream parser and object/message path are known up to video/engine handoff |
| Video/engine hardware | partially mapped; this is still the real printing risk |
| Safe full printing | not solved |

## What Changed Since The First Estimate

The early estimate assumed we still had to discover the firmware shape,
toolchain path, upload wrapper, and broad architecture. Those moved much faster
than a normal manual reverse-engineering pass.

The remaining hard part is different: it is not finding where printing begins.
We have that. The hard part is safely replacing the parts that talk to physical
hardware.

## Current Milestone Ladder

1. Non-printing boot proof
   - Status: partially tested with the idle probe.
   - Meaning: custom upload did not obviously damage or disturb the printer.
   - Missing proof: visible execution signal.

2. Non-printing USB proof
   - Status: USB snapshot and marker probes are built and statically gated.
   - Next test: one staged hardware run from `analysis/open-firmware-probes/hardware-test-ladder.md`.
   - Meaning if successful: open firmware can affect host-visible USB behavior.

3. Minimal open USB/control endpoint
   - Goal: answer descriptor/status requests without stock firmware.
   - Needed before print replacement: a reliable host-to-firmware data path.

4. ZjStream intake
   - Status: offline model exists in `analysis/open-firmware-model/print-path-model.md`.
   - Goal: accept the same host-side ZjStream that `foo2zjs-wrapper` already generates.
   - Practical note: this part is now much less mysterious than video/engine output.

5. Video/engine bring-up
   - Goal: turn one known-safe raster band/page into physical output.
   - Risk: this is where motors, fuser, paper timing, laser/scanner/video, and sensors matter.
   - Rule: do not attempt this until USB/control execution is proven and the unsafe MMIO paths are isolated behind explicit gates.

## Best Next Technical Step

With the printer detached, the best offline work is mostly tightening harnesses
and reports. The next decisive technical step needs hardware:

```text
run one staged non-printing USB probe with before/after USB identity capture
```

Use:

```sh
scripts/run-open-firmware-usb-test-ladder.sh --dry-run
```

Then, only with the printer connected and freshly power-cycled:

```sh
HP1020_ALLOW_OPEN_FIRMWARE_LADDER_UPLOAD=1 \
  scripts/run-open-firmware-usb-test-ladder.sh \
  --upload \
  --stage marker \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...' \
  --i-understand-this-uploads-open-firmware
```

## Safety Gate Before Any Upload

Do not upload a custom firmware candidate unless:

- the printer is physically present and easy to power-cycle
- the stock print path was working recently
- the selected candidate avoids engine/video/fuser/motor/paper-feed MMIO
- the upload goes through the guarded script, not hand-written backend commands
- the expected failure mode is temporary USB silence until power cycle

## Practical Assessment

Progress on reverse engineering is now well past the initial "can we even
understand the blob?" stage. The project is not done, but the unknowns are
sharper:

- Can open code reliably run and affect USB after upload?
- Can we build a small open USB/control loop without leaning on stock runtime state?
- After that, can we drive video/engine hardware without unsafe sequencing?

The first two are still reasonable exploratory firmware work. The third is the
point where the project becomes a real printer-engine bring-up effort.
