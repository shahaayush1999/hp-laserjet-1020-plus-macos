# Research map

Start with `../CURRENT_STATUS.md`. The goal is working replacement firmware.
Read the relevant source/report below; this is not a checklist to repeat.
Paths in code notation are relative to the repository root.

| Work | Source and useful evidence |
|---|---|
| Next missing capability and hardware questions | [Next evidence](open-firmware-model/next-evidence.md) |
| Stream parsing and decoded pages | `open-firmware/semantic-core/`, `open-firmware/image-core/`; [image path](open-firmware-model/image-core/output-validation.md), [metadata](open-firmware-model/raster-field-semantics.md) |
| USB protocol and document integration | `open-firmware/tinyusb-device/`, `open-firmware/tinyusb-printer-adapter/`, `open-firmware/usb-receive-core/`, `open-firmware/usb-printer-class/`; [adapter results](usb-path/tinyusb-printer/validation.md) |
| Controller adapter | `open-firmware/udc-{out,ep0,setup,program,publish}/`; [family reference](usb-path/controller-family.md), [manuals](usb-path/controller-reference/manuals/README.md), [OUT acquisition](usb-path/udc-acquire/validation.md) |
| Commands and outgoing replies | `open-firmware/pjl-command/`, `open-firmware/tinyusb-printer-adapter/`, `open-firmware/udc-in/`, `open-firmware/udc-in-publish/`; `scripts/validate-hp1020-{pjl-command,bulk-in,udc-in,udc-in-publish}.py`; [original IN1 arithmetic](usb-path/in1-construction.md), [corrected callback roles](usb-path/usb-bulk-callbacks-model.md) |
| Continuous execution | `open-firmware/entry-{ram,usb,usb-reset,usb-pages}-test/`; current source-bound reports and raw `capture.tar.gz` in `analysis/boot-handoff/entry-*/` |
| Raw pixels to engine boundary | [Raw parser route](hardware-boundary/raw-parser.md), [software ring](hardware-boundary/software-ring.md), [output pointers/counts](hardware-boundary/output-submission.md), [format selection](hardware-boundary/output-format.md), [first-page sequence](hardware-boundary/first-page-hardware-sequence.md) |
| Status and recovery | [Stock status decisions](hardware-boundary/stock-status-execution.md), [executed CODE mapping](status-path/status-code-correlation.md), `scripts/validate-hp1020-pjl-status-reply.py` (original reply bytes), [port status limits](usb-path/port-status.md), [PJL contract](non-printing-status-probe/pjl-status-contract.md), [engine topology](hardware-boundary/engine-print-topology.md) |
| Original software reference | `analysis/open-firmware-model/stock-execution/`; use only when a new hardware/protocol question needs those paths |
| Future authorized device tests | [Hardware ladder](open-firmware-probes/hardware-test-ladder.md), [bounded bulk plan](open-firmware-probes/usb-bulk-parser-draft/hardware-test-plan.md) |
| Working Mac driver | Root `README.md`, `MANIFEST.md`; independent of open firmware research |

## Checks and tools

Run the focused validator for changed behavior and affected callers. Reports
identify their generator/source hashes. `scripts/check-hp1020-analysis-consistency.py`
checks current saved evidence; `scripts/validate.sh` rebuilds/runs the complete
offline suites when broad integration changes justify it. All validators must
run sequentially. Prose/archive cleanup needs reference/hash checks, not firmware
re-execution. No offline command authorizes contacting USB.

Toolchains under `/tmp` are disposable. Recover only through the pinned builds:

| Tool | Recovery |
|---|---|
| BE Xtensa binutils | `scripts/build-xtensa-binutils-manual.sh`; default `/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf`, override `XTENSA_PREFIX`. Use a fresh `XTENSA_BINUTILS_SRC` if an old source checkout is incomplete. |
| BE/call0 GCC 14.3.0 | `scripts/build-xtensa-gcc-manual.sh`; default `/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf`, component override `HP1020_GCC_PREFIX`. Recover binutils first; target headers, libgcc, ar and ranlib are required. Keep checksum/encoding/profile gates. |
| Independent CPU execution | Homebrew `qemu-system-xtensaeb`, override `HP1020_QEMU`; tested 11.1.1. Harness uses `sim`, `test_kc705_be`, supplied RAM and a private Unix debugger socket. `fsf` lacks required debugger registers. |
| Host build/checks | Homebrew Bash for `mapfile`, Python 3, clang; GCC recovery also uses GNU make/GMP/MPFR/MPC. Existing sample generators use Ghostscript/GNU sed/foo2zjs. |
| Optional binary analysis | Saved Ghidra exports; refresh scripts need Ghidra and OpenJDK 21. Verify discoveries against original bytes. |

## Evidence that stays useful

Original inputs, reference licenses/provenance, current generated reports,
necessary byte fixtures and accepted execution captures remain. Historical
session archives and superseded proposals live in Git history; old generated
reports may retain their original historical paths. Do not recreate those files
just to preserve a narrative. Never rewrite a report's hashes after source edits.

The extracted stock ELF comes from `assets/firmware-source/`; generators under
`scripts/` locate exact reference bytes and fixtures. Emulator agreement proves
only the tested software path. Real boot, controller/cache behavior and printing
require separately authorized physical evidence.
