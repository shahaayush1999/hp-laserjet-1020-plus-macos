# Current handoff

Updated: 2026-10-05. **The open firmware replacement cannot physically print.**
Work remains offline. Preserve the installed HP-based Mac driver; do not contact
or enumerate the printer or introduce print-driving MMIO. Follow `AGENTS.md`.

## Current capability

The open path reuses JBIG-KIT and TinyUSB, parses host ZjStream and produces exact
page pixels in RAM. Controller programming, incoming data, replies and reset
ownership have checked software components with supplied hardware observations.
`open-firmware/usb-service/` joins the existing IN/OUT/program/command gates;
failure in either direction blocks new work while original results can drain.
The bounded PJL path supports uppercase ECHO (50 printable bytes) and INFO STATUS
from a supplied current CODE/ONLINE observation. It does not fabricate physical
status or JOB/PAGE completion. These components still need entry integration
and real platform providers.

`open-firmware/image-pump/` now decodes cooperatively: output waits return with
owned compressed/band/ring data intact. Its20 host and20 target cases match an
independent full JBIG decoder, including held events, late errors and stop.
It is not yet connected to USB; the existing command/document path is synchronous.
Copies remain metadata. Software completion never means paper printed.

The original engine reply/command handshake and page-setting sequence are now
recovered.29 isolated reply/event RAM cuts and45 configuration/lookup/dispatch
cases agree with QEMU, with every engine/peripheral operation excluded. Supplied
stale events can satisfy a later command; supplied setting failures can still
be followed by a start request. These are conditional code findings, not observed
printer faults. Require fresh, serialized replies and successful configuration
in the replacement; do not reproduce those assumptions.

The256-word engine-interface startup table remains undecoded. An Agilent
programmable-I/O patent is an architectural lead, not an opcode map or confirmed
chip identity. The concrete loader/reference findings are in `next-evidence.md`.
Boot memory arithmetic and cache operands are recovered, but installed capacity,
physical mapping, cache visibility, interrupts and output timing remain unproved.

## Next useful work

Connect cooperative decoding to the USB document/command owner so a busy output
cannot block control and cancellation. Preserve the original receive-generation
cursor, immutable replies and the existing receive/output/transport recovery
gates. Avoid a second unrelated pipeline or speculative engine emulator.

For further original-code work, follow the selected media value from PrintMgr
0x1000f84c to the recovered engine configuration. The scalar0x3300 command's
physical meaning remains unknown; its comparison/encoding is already settled.
Do not repeat lookup arithmetic, stock scheduling/cancellation, numeric CODE,
reply formatting or broad controller-reference searches without a new lead.

## Validation limits and recovery

New cooperative decoding and original engine configuration passed their focused
host/interpreter and QEMU checks. Reports retain exact tested sources. The latest
shared USB service, PJL, publisher and affected controller checks also passed.
The earlier complete offline run passed execution stages, then stopped on seven
old consistency expectations. Those were corrected against measured builds;
all136 checks and remaining JSON/probe checks passed sequentially. The top-level
command itself was not rerun after that checker-only correction.

Use `analysis/README.md` for the small evidence map and pinned tool recovery;
`analysis/open-firmware-model/next-evidence.md` holds unresolved contracts.
Run affected checks sequentially. Never rewrite report hashes after editing
sources. Root `README.md` owns the separate working Mac driver.
