# Current handoff

Updated: 2026-10-02. **The open firmware replacement cannot print yet.** Continue
autonomously until the owner asks to yield. Do not enumerate/contact USB, upload
firmware, execute print-driving hardware paths or change installed printing.
AGENTS.md owns scope; `analysis/README.md` is the evidence/tool-recovery map.

## Current checkpoint

The full sequential `scripts/validate.sh` run passed **128 consistency checks
and both suites**. It includes **58 host/58 QEMU offload**, **34/34 composed**,
**132/132 raw adapter**, and **52 unchanged/160 patched protocol** cases. Log:
`/tmp/hp1020-full-offload-20261002.log`, child `hp1020-validation.LBojdq`.
All test processes are stopped. This supersedes the127-check baseline.

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

Commit and push the validated checkpoint, verify sync, then continue. The next bounded task
is ordinary raw SET_INTERFACE: source review shows status can succeed while
input stays stopped with no recovery. First execute four conditional pre-fix
observations against the validated composed ELF, preserving exact sources/raw
captures. Then integrate the independently reviewed sole-default STALL policy
and28 cases that require healthy document input and old fault/reset identities
to survive rejection. Typed SI retains its separate conditional support.

Unexecuted drafts/reviews are preserved in the composed `source-snapshots/`
`raw-si-unexecuted-proposals` archive (working copies under `/tmp`); the V2
adapter patch is the full patch against the current source, not a delta on V1.
The observer reuses the validated target in private storage and must not run
until this checkpoint is saved. It records later class reset as a separate action.
Root owns all execution and integration;
parallel agents are doing only static review/independent gate preparation.
After raw SI, assess a real endpoint-register programming backend over a recording
RAM bus. Preserve the explicit HP slot map; Linux bank arithmetic is not interchangeable.

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
