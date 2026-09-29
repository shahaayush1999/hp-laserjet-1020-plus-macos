# Current handoff

Updated: 2026-09-30. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity by
reusing open components and verifying hardware contracts. AGENTS.md owns scope.

## Current offline work

The latest full `scripts/validate.sh` run passed **126 consistency checks and
both sequential suites**. Log `/tmp/hp1020-full-composed-ingress-20260929.log`;
child `hp1020-validation.MPr6yY`. Research processes are stopped at the owner's
requested checkpoint. Tools work; pinned recovery is in `analysis/README.md`.
This supersedes the124-check baseline `a230fcc` and includes:

- Composed SETUP/EP0/bulk:34 host/34 QEMU,117 sources/six fixtures. Raw requests,
  exact wire/pixels/documents and guarded allocations match. Held requests block
  old reset ACKs and delayed publication; reset-WAIT preserves its original
  identity. Terminal controller settlement is distinct from adapter PENDING.
  Target overhead296+80+88 bytes beyond adapter/document128536.
- Original post-dispatch SETUP retirement:50 conditional +32 pre-MMIO cases per
  engine,15 excluded PCs,13 sources. Explicit no-ENTRY cut, four private RAM
  redirects; complete RAM/register/access oracles agree. SETUP status return,
  separate owner-only OUT0 return and CNAK intent prove no physical settlement
  or stall clearing. Do not repeat this or completed SETUP70.

Existing132 adapter,34 continuous,34 OUT,20 retained-fault and50 EP0 host/QEMU
cases, plus66 original EP0 construction/pointer/boundary profiles also pass.
Reports and exact failed/passed archives are under `analysis/usb-path/udc-composed/`
and `analysis/usb-path/setup-retirement*`. The first composed run stopped after12
host cases at a fresh-only configuration-helper assertion. Only that validator
helper changed before34/34; production code was unchanged. Latest focused logs:
`/tmp/hp1020-udc-composed-reconnect-helper-20260929.log` and
`/tmp/hp1020-setup-retirement-first-20260929.log`. Details: `analysis/open-firmware-model/next-evidence.md`.

## Next action

On continuation, run the reviewed **unexecuted** IRQ-cut draft
`scripts/validate-hp1020-usb-irq-capture.py` sequentially; its independent gate
and static reviews are preserved under `analysis/usb-path/irq-capture/`. Planned
counts are not results, and neither draft is included in the126-check baseline.
Keep exact sources/captures if it fails; integrate its gate only after execution.

The next implementation seam is typed hardware-offload configuration/interface
notifications into TinyUSB. Official family manuals distinguish DMA-to-FIFO
completion from host ACK, and hardware status permission from a completed USB
request. Preserve these distinctions; do not fabricate raw SETUP bytes or an
extra status packet. SETUP owner bits do not prevent overwrite. PIO was assessed
and is not selected. Static evidence, mode uncertainties and the bounded next
fixture are in `analysis/open-firmware-model/next-evidence.md`. No physical DCD
exists; event order, visibility, stall clearing and settlement remain supplied.

Keep separate:26 completed empty-document lifecycles, six conditional original
null reads,28 retirement cases,36 native page lifecycles with supplied completion,
and42 fragment/bypass cases. USB/component checks add zero physical USB or native
page lifecycles. Copies remain metadata; output is synchronous. Boot, actual
USB/cache/engine behavior, physical status/printing and power-cycle recovery are
unproved. Do not repeat cancellation/END_DOC research.

## Installed Mac driver (separate, preserve)

The owner-authorized HP-based native Mac driver is installed. It uses Apple's
renderer, unchanged foo2zjs and a per-job CUPS backend. CUPS owns copies, queueing
and job lifetime. Clone/install/uninstall remains the user flow; no apps/packages/
ZIPs or Homebrew runtime are required. README owns setup; MANIFEST owns validation,
installed-byte checks and recovery. Do not restore the obsolete private worker,
daemon or per-user runtime.

Support checks passed 35 printing, 14 setup, three source-derived sandbox and
five actual macOS scheduler lifecycle cases using a simulated transport. This
is not physical printing proof. Evidence: `assets/macos-system-validation.json`
and `/private/tmp/hp1020-system-install-20260928-2/`. Root-only migration backup:
`/private/tmp/hp1020-native-migration-backup-20260928/` (`paths.json`). The native
queue was empty/idle and installed signatures/ownership/bytes matched the build.
Actual copies, status/recovery and fresh-Mac installation remain unverified.
For explicitly authorized system checks use `scripts/validate-macos-system.py`;
the older isolated scheduler ignores alternate settings on this Mac and fails
closed. No USB query, firmware upload or physical print occurred during this work.
