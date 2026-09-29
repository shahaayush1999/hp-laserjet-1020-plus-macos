# Retained packet fault: completed 20 cases per engine

`packet-fault-passed-20-cases.tar.gz` preserves
`/tmp/hp1020-tinyusb-packet-fault-vs8yc_mm` and the untouched
`/tmp/hp1020-packet-fault-fixed-capture-20260929.log` as `run.log`.
The frozen `packet-fault-validation.json` records 20 host and 20 QEMU cases
passing, including the final source/build-artifact closure gates. The measured
target adapter state plus fixed memory remains 128536 bytes.

This rerun corrects only the validator's artifact snapshot order. It excludes
the audit-derived annotated disassembly from the initial build copy, verifies
immutable build artifacts through the audit, then hashes the new listing before
QEMU replay. The prior failed run remains in
`packet-fault-first-artifact-stop.*`; its absent success report was not backfilled.
The two recorded 77-file source maps differ only in the packet-fault validator,
and their target ELF bytes are identical. Test completion and end-of-run evidence
closure remain separate claims.

The archive retains the original success report, all 77 recorded source files,
all six fixtures, all 19 materialized TinyUSB source files, source/fixture/effective
manifests, the target artifact manifest and every target artifact including ELF,
all 20 cases' events and raw host/target steps/output captures, pixel oracle and
log. Source, fixture, effective-source, build-artifact, ELF and all 160 reported
host/target capture hashes were checked against the preserved bytes. Each raw
host/target output pair also matches byte-for-byte.

Only disposable `host`, `reference` and their `.dSYM` bundles are omitted,
explicitly listed in the adjacent JSON. All archive members were reread and
hashed after compression. No report or tested source was edited.

- Validator SHA256: `84531357a9905f7491c04a9258e96c7b8230ecb524f72bc1fd154414a898cfcf`.
- Target ELF SHA256: `1a8969a1d13782a18be9416131a13b237fcf6d4166d4ece175a2c8a1bdc690a6`.
- Frozen report SHA256: `c22522ac799a5ffdda80fc3d75b451c0e01ef283951144c282464aec53d8bc46`.
- Archive SHA256: `2197e343586ca1d5fe1f98676431c12869c908f2400453e4b866ac31f64f44eb`.

The tests use a synthetic controller interface and supplied event/settlement
facts. They establish no physical USB transfer, actual controller/cache/reset
behavior, mechanical operation, printing or power-cycle recovery. This focused
passing run is separate from the completed 121-check aggregate checkpoint and
adds zero original native page lifecycles.
