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
a two-page synthetic ZjStream decode exact pixels through the same path. INFO
STATUS now replies from a supplied current CODE/ONLINE observation, with empty
DISPLAY; unavailable/stale observations give no reply. Original INFO bytes,
including CODE0, agree with the open staged output. These components are not
wired into an entry loop; physical status acquisition/output remain absent.

The original numeric PJL CODE converter is now recovered beyond the truncated
decompilation. Its normal mappings and reads into following data were verified
in583 interpreter and20 QEMU cases. Original INFO/DEVICE builders also execute
in14 interpreter and8 QEMU cases; DEVICE suppresses CODE0, INFO does not. These
are supplied status observations, not sensors or proof of StatusMgr delivery.

Focused host/QEMU checks passed for bulk IN, descriptor staging, the existing
adapter, continuous documents and affected controller code. All three affected
entry profiles passed interpreter/QEMU execution and independent capture gates
with their new actual layouts. The full offline execution run passed, then its
cross-check stopped on seven old size/source-count expectations. Those were
corrected against measured builds; all136 consistency checks and the remaining
JSON/probe checks passed sequentially. The top-level command itself exited at
that cross-check; execution was not repeated after this checker-only correction.
The additional publisher passed44 host and44 target cases; the extended command
path passed64 of each. Reports retain exact tested source identities; never
rewrite hashes after edits. The command profile is uppercase ECHO with at most50
printable text bytes and exact INFO STATUS, CODE0..99999/ONLINE0..1/empty DISPLAY.

Bounded call0 cache writeback/clean-invalidate routines now reject invalid spans
before operating. Original range operands and startup attribute operands were
recovered;44 original interpreter cases,12 original QEMU cases and36 open paired
cases passed. CPU/cache/line/mapping facts remain conditional, and these routines
are not yet bound to the controller hooks. No physical visibility is claimed.

## Next useful work

Recover the actual boot memory/allocator handoff and how cached/uncached aliases
are established. Cache instruction operands are settled; they do not supply
memory capacity, physical mapping, cache-line leases or a DMA acquire operation.
Numeric conversion and reply formatting are settled. DISPLAY is initially empty
and no local writer was recovered; ONLINE remains a separate observation.
Notification candidates can differ from cached status; details are in the existing
next-evidence note. Physical status acquisition is still missing. Entry
integration must include existing controller programming/ingress/failure gates;
the IN publisher's ready hook cannot mean merely mounted. Exact contracts and useful stock
addresses are in `analysis/open-firmware-model/next-evidence.md`. Do not repeat
settled stock scheduling or cancellation investigations. Physical boot/RAM,
cache, interrupts, page output and power-cycle recovery remain unproved.

Keep work tied to the next missing capability with proportionate checks, as
`AGENTS.md` requires. Root `README.md` owns the separate working Mac driver.
