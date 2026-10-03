# One entry through a RAM document

This is an offline ELF experiment. Six continuous interpreter/QEMU cases and
the unchanged independent raw-capture gate have passed. The original-byte/layout review, initial independent acceptance
plan, earlier drafts, three first build/audit stops and the fourth audit pass are preserved in the
archives referenced by `analysis/open-firmware-model/next-evidence.md`.

The experiment removes the existing component harness's repeated CPU/stack
setup. One supplied loaded RAM image and privileged CPU state enter at100167a8.
New assembly normalizes only the reviewed standard CPU state, establishes its
own8KiB stack and clears all129224 bytes of state/memory/mailbox BSS. The C
workload scans every cleared byte and the initialized sentinel before calling
the unchanged production receive/document/image code. It submits six supplied
RAM fragments of the existing352-byte stream, copies the actual32-byte decoded
output and original document event, calls explicit finish only after that event,
then returns to its own self-branch.

The full production state13496 and memory114704 capacities are retained. The new
layout reuses private HP runtime locations within original ELF-declared spans;
those declarations are not proof of available physical RAM or loader behavior.
Separate inert islands preserve selected address conventions. Guards and unused
gaps remain protected, and the harness must never zero ELF NOBITS on load.

`hp1020_entry_layout.c` exports a read-only compiler layout table. Every word
must match the separately hand-derived `expected-target32.json` before a test
reads production fields. `literal-oracle.py` was frozen before candidate review;
expected pixels/events do not come from the implementation or its mailbox.
Three independently chosen CPU profiles and two nonzero paints have executed.

Build/audit entry point: `scripts/validate-hp1020-entry-ram.py --audit-only`.
The strict whole-linked audit, actual call/frame review and frozen independent
capture gate passed. All37 copied-evidence controls and30 isolated interpreter
guards passed. The latter are28 rejected operations and two permitted reads,
not extra candidate lifecycles. Full sequential validation passed132 consistency
checks and both offline suites, including durable archive recovery and the
unchanged independent gate. The complete first/current paired state and traces
agree; only the reviewed publication runner changed after the first execution.
The conservative nested stack bound is784 bytes for this fixed workload; it is
not an observed maximum or an interrupt/exception stack budget.
The concrete interpreter bounds every
instruction and access. Independent QEMU uses one exact initial seed, followed
only by observations and ordered continuation. Save all initial/pre-C/pre-finish/
park RAM and CPU captures, access/step traces and complete debugger traffic.
Two actual park steps must leave all observed state unchanged.

`analysis/boot-handoff/entry-ram/capture.tar.gz` and its exact member manifest
preserve the accepted raw evidence independently of disposable tool paths.
`source-snapshots/` retains build/audit stops, pre-execution reviews, the first
positive capture, controls and full-suite evidence. The guard wrapper's first
pre-execution type-comparison stop is retained separately; its retry compares
the entire audit through the same JSON representation without dropping fields.

`references/qemu-primary/` contains unmodified, pinned official QEMU11.1.1
register/configuration sources and their provenance. Their original license
headers are retained. They establish this emulator's register map, not HP's
optional processor hardware. Shared QEMU and interpreter modules are unchanged.

No .dl, USB controller, DMA/cache/TLB operation, interrupt producer, engine or
physical printing is supplied. Current transport completions and software output
completion are explicit test inputs. Neither an ELF, PASS mailbox nor paired
software result establishes physical boot, printing or power-cycle recovery.
