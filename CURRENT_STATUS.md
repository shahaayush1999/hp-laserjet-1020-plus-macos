# Current handoff

Updated: 2026-10-02. **The open firmware replacement cannot print yet.** Continue
autonomously until the owner asks to yield. Do not enumerate/contact USB, upload
firmware, execute print-driving hardware paths or change installed printing.
AGENTS.md owns scope; `analysis/README.md` is the evidence/tool-recovery map.

## Current checkpoint

The latest full sequential `scripts/validate.sh` run passed **128 consistency
checks and both suites**, including **62 host/62 QEMU composed**, **58/58 typed
offload**, **132/132 raw adapter**, and **52 unchanged/160 patched protocol**
cases. Log: `/tmp/hp1020-full-raw-si-20261002.log`, child
`hp1020-validation.Kd7EIu`. All execution is stopped at this checkpoint.
Focused raw-SI validation and eight independent gate-negative controls also
passed. Do not run validators concurrently or change captured sources during a
run; regenerate reports through their validators, never relabel old hashes.

The new typed configuration/interface path preserves original status ownership
and separately supplied hardware permission, endpoint defaults and cleanup. It
creates no raw SETUP capture, DMA descriptor, extra status packet or host ACK.
USB2 requires defaults/halt reset on repeated nonzero configuration; the patched
core now closes/reopens that binding while preserving connection/address state.
Raw/typed partial-open failures retain their original cleanup ticket across reset.
Measured target sizes: adapter/document128588, EP0296, bulk80, SETUP96 bytes.

Exact first/full tested sources, all raw captures and untouched proposals are
archived under `analysis/usb-path/udc-offload/source-snapshots/`; separate protocol/adapter archives
are in their existing evidence directories. The strengthened independent gate
passed the first captured report and eight deliberately corrupted controls were
rejected. Its first oracle corrections are preserved. Official USB2 PDF page
locators were corrected before the full rerun; first-run metadata stays intact.
Details and current supplied-fact limits: `analysis/open-firmware-model/next-evidence.md`.

## Next action

Ordinary raw SET_INTERFACE was reproduced in **four host/four QEMU conditional
observations,404 paired rows**, reusing the validated composed ELF. SI status
completed but input stayed stopped and no SI recovery was created; a separately
requested class reset then recovered a fresh exact document. Full sources/raw
captures are archived in composed `source-snapshots/raw-si-before-policy.*`.

The reviewed sole-default STALL policy is integrated and focused-validated.
First execution stopped after46 host cases because a scenario wrongly expected
class SOFT_RESET admission to wait for bulk settlement. Its exact failed sources
and captures are preserved; only that expectation changed, adding a pre-settlement
finish-WAIT check. Production V2 code was unchanged before62/62 passed. Failed,
passed and gate-control archives are beside `raw-si-before-policy.*`.

Rejected raw SI preserves healthy bulk input and old fault/reset tickets. Typed
SI retains its separately conditional acceptance. Root's independent gate passed
unchanged, including fixed pixels/generations, exact status packets and original
ownership. Full-run source/raw-capture archives are
`udc-composed/source-snapshots/raw-si-full-suite-62-cases.*` and
`udc-offload/source-snapshots/raw-si-full-suite-58-cases.*` under `analysis/usb-path/`.

Save this checkpoint, then continue. Root owns execution and integration; agents
prepared an unexecuted endpoint-register backend over recording RAM I/O.
The latter must use the explicit HP slot map, not Linux bank arithmetic; mode,
geometry, endpoint defaults and settlement remain separate supplied facts. Its
review/draft is under `/tmp/hp1020-next-controller-backend-20261002.md` and the
frozen `/tmp/hp1020-udc-program-draft-20261002/` directory. Independently review
and archive untouched proposals before integration. Register reads are explicit
inputs, not simulated effects of writes; defaults, settlement and physical gate
currentness remain external. Partial failures must retain their original ticket.

Tools currently work; recover disposable tools only through pinned scripts in
the analysis map if needed. No physical DCD exists. Actual event chronology,
visibility, mode, stall clearing and settlement remain supplied. Boot, USB/cache,
engine behavior, physical status/printing and power-cycle recovery are unproved.
Keep separate:26 completed empty-document lifecycles, six conditional original
null reads,28 retirement cases,36 native page lifecycles with supplied completion,
and42 fragment/bypass cases. USB/component tests add zero physical USB or native
page lifecycles. Do not repeat cancellation/END_DOC or completed IRQ/SETUP research.

## Installed Mac driver (separate, preserve)

The authorized HP-based native driver uses Apple's renderer, unchanged foo2zjs
and a per-job CUPS backend. CUPS owns copies, queueing and job lifetime. README
owns clone/install/uninstall; MANIFEST owns validation/recovery. No app/package,
ZIP or Homebrew runtime is required. Do not restore the obsolete daemon/runtime.

Support checks passed35 printing,14 setup, three sandbox and five actual macOS
scheduler cases with simulated transport. Installed signatures/ownership/bytes
matched the build and the queue was empty/idle; actual copies, status/recovery
and fresh-Mac installation remain unverified. Evidence:
`assets/macos-system-validation.json`, `/private/tmp/hp1020-system-install-20260928-2/`.
Root-only migration backup: `/private/tmp/hp1020-native-migration-backup-20260928/`.
System checks require separate authorization; no physical print occurred here.
