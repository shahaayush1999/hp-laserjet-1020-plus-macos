# HP 1020 USB Register Snapshot Probe

This is a non-printing custom firmware candidate for offline inspection only.

It is meant to answer a narrower question than printing:

```text
Can open code safely touch only the mapped USB-controller read side after upload?
```

The probe reads the mapped `0xb300....` USB endpoint-0 registers into a local
RAM snapshot buffer, then parks in an idle loop.

It intentionally does not:

- write any USB controller register
- touch video/raster MMIO
- touch engine/fuser/motor/paper-feed MMIO
- parse print data
- expose a USB descriptor marker yet
- print anything

The snapshot is not host-readable yet. This probe is a stepping stone between
the pure idle payload and a future USB marker: it exercises read-only USB MMIO
under the stricter contract scanner while keeping the mechanical hardware out
of scope.

Do not upload this without a fresh power cycle, explicit hardware-test plan, and
passing safety scans.
