# Continuous RAM document reset experiment

The workload interrupts an old partial document, drains its genuine late
completion, requires separate receive/output/transport recovery promises,
rejects stale metadata at actual buffer reuse and completes a fresh document.
It runs the existing production USB/document/image code from one owned entry.

`CONTRACT.md` and `AMENDMENT.md` define this profile. `ACCEPTANCE.md`,
`ADDENDUM.md`, the literal oracles and `LIBRARY_SELECTION.md` are inputs pinned
by the independent linked/capture checks; retain them with the test.

Run `python3 scripts/validate-hp1020-entry-usb-reset.py`; `--audit-only` stops
before execution. Current results and complete source-bound CPU/RAM captures
are in `analysis/boot-handoff/entry-usb-reset/`. Validators run sequentially.

The RAM provider supplies controller images, cache visibility, physical
settlement and output consumption. Clearing software ownership does not prove
real cancellation. This is not an upload image or physical reset/printing proof.
