# Current handoff

Updated: 2026-10-05. **The open firmware replacement cannot physically print.**
Research execution is stopped. Work is offline only; preserve the installed
HP-based Mac printing setup and do not contact the printer.

## Implemented and checked

The open path reuses JBIG-KIT and TinyUSB, consumes host ZjStream, decodes pages,
and handles software ownership, document boundaries and supplied reset recovery.
A single-entry RAM experiment consumes a complete original foo2zjs two-page job
and produces exact pixels. Controller observations, cache/mapping, transfer
settlement and output consumption are supplied by tests. PJL framing is scanned;
PJL replies and physical engine output are not implemented.

Last complete full-suite baseline: `aaa72fb` (135 consistency checks, both offline
suites). Subsequent original bulk-IN arithmetic passes focused interpreter/QEMU
checks and the 136-check consistency gate. Its full run was interrupted at the
owner's return during an unchanged native-pipeline test; this is not a full pass
or a new target failure. Production firmware C has not changed since that baseline.
Current results/captures are under `analysis/boot-handoff/entry-usb-pages/` and
`analysis/usb-path/in1-construction.*`; earlier run histories remain in Git.

## Next useful work

Implement one bounded bulk-IN reply through the existing TinyUSB adapter, with
retained source ownership, cancellation and reset handling. The endpoint is
opened but the adapter currently cannot send a payload through it. The concrete
design and original-byte findings are in
`analysis/open-firmware-model/next-evidence.md`. Validate affected code and its
callers; do not repeat settled stock scheduler/cancellation investigations.
Then address remaining output/engine contracts and truthful status. Physical
boot/RAM, cache, interrupts, page output and power-cycle recovery remain unproved.

The owner's current priority is productive implementation with proportionate
checks. Repeated audit histories and redundant archives were pruned; retain
current evidence needed to reproduce results. See `AGENTS.md` for the workflow.
Root `README.md` and `MANIFEST.md` own the separate installed Mac driver.
