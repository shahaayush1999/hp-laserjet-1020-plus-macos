# Continuous USB RAM experiment

One entry, stack and initialization join the actual TinyUSB, control/bulk,
receive, document and image components. The workload consumes two documents,
produces exact decoded pixels/events, drains the final original owner and
finishes once. It retains full production buffers. Final supplied zero-length
input settles its owner; it does not mean EOF.

`CONTRACT.md`, layout tables and independent literals define the workload.
Run `python3 scripts/validate-hp1020-entry-usb.py`; `--audit-only` stops before
execution. The independent gate compares full CPU/RAM, original transfer
identities, API/access traces and debugger traffic. Current results and complete
source-bound captures are in `analysis/boot-handoff/entry-usb/`.

All controller observations, mapping/cache/settlement and output consumption
are supplied RAM conditions. The fixed workload's stack bound is not a bound
for arbitrary inputs or interrupts. This ELF must not be uploaded; no physical
boot, USB transfer or printing is established. Reset recovery and real host jobs
have separate sibling fixtures.
