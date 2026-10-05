# Current handoff

Updated: 2026-10-06. **The open firmware replacement cannot physically print.**
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

`open-firmware/image-pump/` decodes cooperatively: output waits return with owned
compressed/band/ring data intact. The USB document and PJL command owners now
support this mode with a retained original-generation input cursor. Six scenarios
with two initial fills passed host sanitizers and target QEMU: independent full
pixels, control requests during output stalls, replies and cancellation/restart,
late invalid padding, missing END_DOC and document-consumer failure. Standalone
decoding previously passed20 host and20 target cases. Entry experiments still
use synchronous mode. Copies remain metadata; software completion is not printing.

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

The owner requested a stop during integration validation. Resume by completing
the reset/pages linked callback and stack review described in `next-evidence.md`.
Their candidate-image gates deliberately still reject the new build. Then run
`scripts/validate.sh` sequentially for this broad change and resolve affected
regressions before claiming an integrated checkpoint. All four entry static
builds/audits passed; the changed entry images have not executed. Historical
accepted entry binaries/captures and reports retain their tested bytes and hashes.
After validation, connect the cooperative document/command path and shared USB
service to an entry-owned loop. Preserve existing recovery gates; no physical
backend or engine operation is authorized.

For further original-code work, follow the selected media value from PrintMgr
0x1000f84c to the recovered engine configuration. The scalar0x3300 command's
physical meaning remains unknown; its comparison/encoding is already settled.
Do not repeat lookup arithmetic, stock scheduling/cancellation, numeric CODE,
reply formatting or broad controller-reference searches without a new lead.

## Validation limits and recovery

The new cooperative integration report records exact current tested sources.
Broader reports belong to earlier sources and must be regenerated, not rehashed.
An interim legacy PJL run passed before the final shared fixture edits; its saved
report remains the previous committed baseline. The earlier complete offline run
passed execution stages, then stopped on seven old consistency expectations.
Those were corrected against measured builds; all136 checks and remaining
JSON/probe checks passed sequentially. Neither that top-level command nor the
complete suite for the current integration was subsequently run to completion.

Use `analysis/README.md` for the small evidence map and pinned tool recovery;
`analysis/open-firmware-model/next-evidence.md` holds unresolved contracts.
Run affected checks sequentially. Never rewrite report hashes after editing
sources. Root `README.md` owns the separate working Mac driver.
