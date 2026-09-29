# TinyUSB 0.21.0 selected device core

Pinned upstream commit `dae3f9a366bfcddbf9dcf1b48d7500286a849539` from the repository in
`PROVENANCE.json`. Each selected file is byte-identical to its Git blob; that
manifest also records SHA256. `LICENSE` retains the upstream MIT license.

This is the small generic device/EP0, FIFO and OS_NONE source closure for a
synthetic offline compatibility experiment. Built-in classes and hardware DCD
ports are excluded. Unchanged and locally patched builds are executed separately
on the host and simulated BE target; see `open-firmware/tinyusb-device/README.md`.
The vendor files stay unchanged: the reviewed patch is applied only to verified
disposable copies. No actual USB enumeration or printer operation is implied.

Any future local changes must preserve the original bytes and provenance,
carry a reviewable patch, and be tested independently of the upstream baseline.
