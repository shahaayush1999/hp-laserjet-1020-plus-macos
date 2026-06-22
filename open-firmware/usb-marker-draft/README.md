# HP 1020 USB Marker Draft

This is an offline-only, write-capable USB endpoint-0 marker draft.

It is meant to answer a narrow implementation question:

```text
Can we assemble an HP-shaped open firmware image that polls for a standard
GET_DESCRIPTOR product-string request and programs only the stock-mapped USB
endpoint-0 registers with the extracted stock sequences?
```

It intentionally does not:

- touch engine, fuser, motor, paper-feed, or video/raster MMIO
- parse or print ZjStream data
- claim to be hardware-ready
- upload itself to the printer

Compared with `usb-register-snapshot`, this candidate writes USB controller
registers. That makes it a later-stage hardware experiment, not a casual probe.
It now keeps polling across non-matching setup packets instead of parking after
a one-shot miss, and it uses the clipped host `wLength` in both the response
state and the transfer descriptor word.
Do not upload it without a fresh power cycle, explicit test plan, and passing
layout, safety, USB-contract, access, and endpoint-0 sequence scans.
