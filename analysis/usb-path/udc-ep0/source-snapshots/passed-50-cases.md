# EP0 composition: completed 50 cases per engine

`passed-50-cases.tar.gz` preserves `/tmp/hp1020-udc-ep0-cdvp51wr` and the untouched
`/tmp/hp1020-udc-ep0-integrated-build-20260929.log` as `run.log`.
The frozen `validation.json` records 50 host and 50 Xtensa/QEMU cases passing.
Target measurements retain the existing adapter's 128536 bytes and add 296 bytes
for the two-slot EP0 component plus its descriptor/packet storage.

The preceding host-only build stop remains in `first-host50-build-stop.*`.
The two recorded 92-file source maps differ only in
`scripts/build-hp1020-udc-ep0-target.sh`: the integrated builder now uses the
repository's established paths/settings. The component, fixture and validator
sources are identical between those attempts. Neither archive's recorded source
hashes were edited to substitute the later builder.

All 92 recorded source files, six input fixtures, 19 materialized TinyUSB source
files, their manifests, full target build/audit artifacts and target manifest,
ELF, success report, pixel oracle, log, and every raw case event/host/target
capture are preserved. Captures include exact wire/pixels/document notifications,
receive/output memory and both guarded EP0 descriptor/staging/sink regions.
All 600 reported host/target capture hashes and every source, fixture, effective
source and target-artifact hash were checked against those bytes. Each raw
host/target output pair also matches byte-for-byte.

The recorded original-construction reference and its full ten-file source
closure are included and match the earlier 66-profile report. Its raw original
execution captures remain separately archived in
`../../ep0-construction/source-snapshots/first-66-cases.*`. This component run
reuses that evidence and executes zero additional stock instructions; its
50 synthetic composition profiles are distinct from those original-code cases.

Only disposable `host`, `reference` and their `.dSYM` bundles are omitted,
explicitly listed in the adjacent JSON. Every archive member was reread and
hashed after compression. No tested source or report was modified.

- Validator SHA256: `b6fa90e24c14c1a38d443c5bec0e48fe0e453b97c9c13fc67ec24ae8afa850bf`.
- Integrated builder SHA256: `aad3d8b85d526482e2da895af7db2db601fd9c42fa61ddf46eb09661a5a044b8`.
- Target ELF SHA256: `e3884895d38dd6b5f966d32d18cca1515445e755d4ad85fe065566e5ee88847d`.
- Frozen report SHA256: `c3133a9040a576f0b939c71a4efe0130bc680b9b32b6a0c449d4107744016afa`.
- Archive SHA256: `2b65c397a6e733dcd8dc3b78d5802efd3a00d2864d5e354911fbc57f37a40ab5`.

This remains RAM-only composition with supplied controller mode, CPU/DMA mapping,
cache visibility, immutable event identity, actual count and settlement facts.
Proposed staging bytes do not prove physical wire delivery. The run adds zero
physical USB transfers, peripheral accesses or original native page lifecycles
and establishes no controller quiescence, physical printing or power-cycle
recovery. It is separate from the completed 121-check aggregate checkpoint.
