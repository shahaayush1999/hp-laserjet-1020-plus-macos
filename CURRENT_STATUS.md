# Current handoff

Updated: 2026-09-29. **The open firmware replacement cannot print yet.** Do not
contact/enumerate USB, upload firmware, execute print-driving hardware paths or
change the installed printing setup. Work toward normal-use feature parity in
verified stages, reusing open components. AGENTS.md owns the scope and authority.

## Latest firmware evidence

The new `open-firmware/usb-receive-core/` composes a bounded receive queue with
ZjStream parsing, JBIG decoding and software output. **75 sanitized host and
75 independent QEMU cases pass**: delayed/out-of-order completions, full queues,
all owner/status combinations, stale notifications, count/identity overflow,
changing page sizes, 65 pages, framing failure and cancellation/restart.
Input and output storage remain protected until separate external quiescence
acknowledgements; both acknowledgement orders recover from accepted output and
produce a fresh exact-pixel document. These acknowledgements are supplied by
fixtures, not proof of real DMA/engine shutdown. No actual USB port exists yet.

The component uses 128168 bytes of target state/fixed buffers, excluding code,
stack and test captures. Focused log:
`/tmp/hp1020-usb-receive-target-20260929.log`. Report:
`analysis/usb-path/receive-core/validation.json/.md`. The previous image-output
component remains validated at 45 host/45 QEMU cases, stream at 66/44; copies
remain metadata. Retained-file parsing keeps its independent 16-page bound.

The pinned classic Synopsys reference does not interpret RX status values, and
its cancellation return is not an HP quiescence condition. A generation-scoped
endpoint-fault API now fences even empty/already-ready queues. Six original
software-list drains agree in both engines with explicit free/mask substitutes:
the list empties while a supplied busy descriptor remains unchanged. They add
no hardware cancellation proof. Controller-family evidence retains 24 literal
matches, 18 original anchors, 12 re-arms, 51 status fragments, two pre-MMIO
rejections, plus 11 new ownership/reset anchors. Wrapper/PHY, byte order,
cache/aliases and real reset/abort remain unresolved.

Full sequential validation passed **108 consistency checks and both suites**,
in `/tmp/hp1020-full-usb-receive-20260929.log` (child `hp1020-validation.SAqbeg`).
No validation process remains running. Tested source hashes match; reports were
regenerated, never patched. `scripts/validate-hp1020-output-submission.py` is a
saved, **unexecuted** next-experiment draft, excluded from that validation.
The detailed handoff preserves the preamble-fixture correction and earlier
74-case host result with exact sources. The preceding full baseline is `89863e9`.

Next close controller receive/reset ownership and the physical output contract
using original bytes and narrow offline execution. Keep software quiescence
promises distinct from actual hardware state. Detailed questions and run paths:
`analysis/open-firmware-model/next-evidence.md`; source map/tool recovery:
`analysis/README.md`. Do not repeat resolved selector/cancellation investigations.

Preserve separate evidence categories: 26 completed empty-document lifecycles,
six conditional original null reads, 28 retirement cases, 36 native page
lifecycles with supplied completion, and 42 fragment/bypass cases. New receive
software and USB fragments add **zero native page lifecycles and zero USB
transfers**. Boot, actual USB, physical packing, engine control, timing/cache,
printing and power-cycle recovery remain unproved.

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
