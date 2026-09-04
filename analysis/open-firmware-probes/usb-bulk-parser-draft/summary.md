# HP 1020 USB Bulk Receive And Parser Probe

This is a buildable, mechanically inert open-firmware probe. It was generated and validated offline and was not uploaded to a printer.

## Proven Offline

- The Old-Xtensa source assembles and links into ELF, date-prefixed IMG, and wrapped DL artifacts.
- Endpoint 0 exposes a writable product string with bytes, descriptor, recognized-chunk, parser-error, and unknown-chunk counters.
- Bulk OUT uses only the statically mapped bank-1/lane-1 descriptor, buffer, status, acknowledgement, and submit contract; it polls lane status directly instead of recreating the stock ThreadX event bit.
- Completed receive data is bounded to 0x400 bytes, parsed incrementally across transfers, and never reaches engine, video, laser, fuser, motor, or paper-feed code.
- Host model: 11/11 generated samples and 33/33 boundary cases passed.
- Every generated safety, USB, memory, source, descriptor, and parser report passes.

## Unproven Until Hardware

- Whether custom code actually executes after upload on this printer.
- Whether the mapped USB controller retains enough boot-ROM initialization for endpoint 0 and bulk OUT to operate under this standalone probe.
- Whether a real bulk completion reports the expected descriptor status/length encoding and continues after repeated re-arms.

The next meaningful step is the guarded test in `hardware-test-plan.md`: upload after a fresh power cycle, read the product descriptor marker, send one START_DOC/END_DOC-only stream, then read the counters again. No print or mechanical command is involved.

## Artifacts

- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.dl`: `fff2a9718d5e646434f3760a6df7f1662fa7c6fbc000c4a11a44696ea9bb0ee7`
- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.elf`: `ec0b664e52bedee5169a1ffb45d9f0fd954a8d977f69801874b6e8f834b1042c`
- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.img`: `0453f7290e1565a8d92690f86b4040671b2d9d16d3c798735f207551359eb852`
- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.map`: `6d67a0b4f003f4b1553a09e2d7953efc1f7ac06f9b47a8d11c9b92ed27261be8`
