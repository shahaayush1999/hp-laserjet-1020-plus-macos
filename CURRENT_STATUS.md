# Current handoff

Updated: 2026-10-05. **The open firmware replacement cannot physically print.**
Offline work is active. Preserve the installed HP-based Mac printing setup;
do not enumerate/contact the printer or introduce print-driving MMIO.

## Implemented and checked

The open path reuses JBIG-KIT and TinyUSB, consumes host ZjStream, decodes pages,
and handles software ownership, document boundaries and supplied reset recovery.
A single-entry RAM experiment consumes an original foo2zjs two-page job and
produces exact pixels. Hardware observations and output consumption are supplied.

Bulk IN now has a separate original-cookie owner and polled result, independent
of incoming pages. It handles late completion, failed submission, cancellation,
reset, final replies and exhaustion. A second component copies one reply to owned
staging and constructs a bounded normal descriptor. A recording-hook publisher
now orders visibility, descriptor publication, interrupt unmasking, safe NAK
release and Poll Demand. It retains failed attempts through cancellation and
cleanup. Controller binding, mapping/cache, FIFO readiness and settlement remain
supplied. A bounded command pump now handles split PJL ECHO, binary/text
separation, backpressure and original reply ownership across resets. ECHOs around
a two-page synthetic ZjStream decode exact pixels through the same path. Neither
new component is wired into an entry loop; physical status/output remain absent.

Focused host/QEMU checks passed for bulk IN, descriptor staging, the existing
adapter, continuous documents and affected controller code. All three affected
entry profiles passed interpreter/QEMU execution and independent capture gates
with their new actual layouts. The full offline execution run passed, then its
cross-check stopped on seven old size/source-count expectations. Those were
corrected against measured builds; all136 consistency checks and the remaining
JSON/probe checks passed sequentially. The top-level command itself exited at
that cross-check; execution was not repeated after this checker-only correction.
The additional publisher passed44 host and44 target cases; the command path
passed36 of each. Reports retain exact tested source identities; never rewrite
hashes after edits. The command path's narrow profile is uppercase ECHO with
at most50 printable text bytes, no generated physical/job status.

## Next useful work

Use the existing engine/status evidence to recover the concrete observations a
physical-status provider will need; ECHO is not a substitute for status. Entry
integration must include existing controller programming/ingress/failure gates;
the IN publisher's ready hook cannot mean merely mounted. Exact contracts and useful stock
addresses are in `analysis/open-firmware-model/next-evidence.md`. Do not repeat
settled stock scheduling or cancellation investigations. Physical boot/RAM,
cache, interrupts, page output and power-cycle recovery remain unproved.

Keep work tied to the next missing capability with proportionate checks, as
`AGENTS.md` requires. Root `README.md` owns the separate working Mac driver.
