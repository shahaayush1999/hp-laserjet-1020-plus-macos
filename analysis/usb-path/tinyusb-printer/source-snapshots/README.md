# Reusable printer evidence snapshots

`automatic-recovery-116-cases.tar.gz` preserves the completed 2026-09-29 run
from `/tmp/hp1020-tinyusb-printer-txwh1ric`: 116 host and 116 QEMU scenarios.
The adjacent JSON manifest records the archive SHA256 and every regular
member's SHA256. `run.log` is the unchanged
`/tmp/hp1020-automatic-printer-20260929-run1.log`.

The archive retains the original `validation.json`, source manifest and
76-file `source/` closure, materialized `effective-source/`, all case events
and raw host/target captures, and `target-check.elf`. The tested adapter
validator SHA256 is
`8fe5ad7e80ffb5528d590216d1f6f60115d02471cb098c3f3ea1bb6f16a55f0d`;
the target ELF SHA256 is
`e55da315ba856079a62cae0bcdb4f5ab7deadcbc60d691fd0161e78cd850365c`.
`tested-fixtures/` additionally preserves the six repository fixture files,
verified against the report's `fixture_sha256` map.

Only the disposable `host`, `reference` and their two `.dSYM` bundles are
omitted, as recorded in the manifest. All archived members were reread and
hashed after compression. The preserved source closure and target ELF hashes
match the report; no report hash was edited.

This run adds new-configuration recovery with three explicitly supplied
quiescence promises while retaining the earlier explicit-reset cases. The
controller and output consumer remain synthetic. It proves no physical USB
transfer, printing or hardware recovery and predates subsequent work on the
initial standard-reply submission failure gap. Its source hashes identify
its tested scope; later source edits do not inherit its passing claims.

The older archives in this directory preserve earlier host checkpoints,
oracle failures and target-audit stops under their existing names. They are
not replaced by this completed 116-scenario capture.
