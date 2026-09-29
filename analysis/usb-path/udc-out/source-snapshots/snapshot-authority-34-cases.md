# Immutable snapshot authority: strengthened 34 cases per engine

`snapshot-authority-34-cases.tar.gz` preserves the completed run from
`/tmp/hp1020-udc-out-lrkw40ly`, plus the untouched log from
`/tmp/hp1020-udc-out-snapshot-authority-20260929.log` as `run.log`. The frozen
report records 34 sanitized host and 34 Xtensa/QEMU profiles passing. The earlier
`first-34-cases` snapshot remains unchanged.

This strengthens the existing `completion-facts` profile under both fill values;
it does not add profiles. Both descriptor snapshots keep the same current
original cookie:

1. Capture owner1, replace retained descriptor bytes with owner2/count31, then
   replay the older snapshot. It must WAIT despite the newer live bytes; actual
   service and pump still admit no READY input, pixels or document.
2. Capture owner2/count31, replace retained bytes with owner1, then replay the
   saved completed snapshot. It must accept that snapshot, retain the pending
   adapter dispatch, then use actual TinyUSB service and normal document pumping
   to produce the independently expected complete small page and notification.

The actual descriptor component/header, C fixture and target ELF match the first
run. The Python validator changed to add these controls. This distinction is
recorded by the frozen source manifests, not by editing either report's hashes.

The archive includes the full original `validation.json`, all 97 recorded source
files and `source-sha256.json`, patched effective TinyUSB source and manifest,
all six copied fixture files with `fixture-sha256.json`, every raw case event and
host/target capture (including descriptors), independent pixel oracle bytes,
target ELF and log. Only disposable host/reference executables and their host
debug-symbol bundles are omitted. No missing bytes were reconstructed from a
later working-tree revision.

Every archived member was read back and compared with the original file. All
recorded source, effective-source, copied fixture, host/target capture and ELF
SHA-256 values were checked against those exact saved bytes. The adjacent JSON
contains the archive SHA-256 and the complete per-member map.

- Validator SHA-256: `c02032dcd68d6131dd3ac9fbb6588923b6cfb1d679c69690829f80bbcb3a68ba`.
- Frozen report SHA-256: `7fe87925699bfc60145c3d3ab30099e6db8b89ac3f2b5eb2c0595655f5a6af14`.
- Target ELF SHA-256: `f6ac421b19f0845619a0da74a28969483a78115f21cfe29bd017773aa2863478`.
- Measured target adapter state/memory: 128536 bytes; descriptor component and
  descriptor storage: 80 additional bytes.

This is synthetic RAM composition with exact independently expected pixels and
document notifications. It adds zero original-code execution, native page
lifecycles, physical USB transfers or peripheral accesses. Packet64/BE mode,
CPU/DMA mapping, cache visibility/order, immutable observations and settlement
remain supplied. Descriptor ownership is not global quiescence or a recovery
promise. Copies remain metadata; output is synchronous software. It proves no
physical controller, engine, status, printing or power-cycle recovery and is not
itself a completed aggregate validation run.
