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

- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.dl`: `a12e63807660f7e328021342d5288d1234690f278b0ad6ea0f0e16e2d22d44da`
- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.elf`: `8f25286ccc9f070b803abb68ae87a8d23a748990c269c861be19f7a31d35aa3f`
- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.img`: `f32b210cdb34bfb71438c1838b4010db6085fa3cd3fcc5780348b8b966d9582d`
- `usb-bulk-parser-draft/hp1020-usb-bulk-parser-draft.map`: `68b6b041d1b1e3ab279bb0b7c02a82bf1299438029290ab0ce69c6afd90498b6`
