# Continuous document evidence snapshots

These archives preserve two completed 2026-09-29 runs. Each adjacent JSON
manifest records the archive SHA256 and every regular member's SHA256.
Paths inside each archive are relative to its original capture directory.

- `first-34-cases.tar.gz` preserves
  `/tmp/hp1020-continuous-printer-fv4qr0kn`: 34 host and 34 QEMU cases before
  the independent oracle tightening. Its `run.log` is the unchanged
  `/tmp/hp1020-continuous-printer-20260929-run1.log`. The continuous validator
  SHA256 is `5d319fd056534ad296f9b55c563c832b4b16f87b19ffbd20a26499ee71affcb7`.
- `strengthened-34-cases.tar.gz` preserves
  `/tmp/hp1020-continuous-printer-fmiz_gav`: the 34 host and 34 QEMU cases
  repeated with explicit ZLP events between partial END_DOC bytes, strict
  retained receive/output slot assertions and independently expected restart
  generations. Its `run.log` is the unchanged
  `/tmp/hp1020-continuous-regression-continuous-printer-20260929.log`. The
  continuous validator SHA256 is
  `3e9a27fac60c29b423ae458a7e2116b668e03355af3ffd07021689c2e457e1ed`.

The archives retain each run's unmodified `validation.json`, source manifest
and complete `source/` closure, materialized `effective-source/`, all case
events and raw host/target captures, and `target-check.elf`. Both target ELFs
have SHA256 `e55da315ba856079a62cae0bcdb4f5ab7deadcbc60d691fd0161e78cd850365c`.
The imported adapter validator's report limitation text also changed between
these runs; neither report's recorded source hashes were rewritten.

`tested-fixtures/` additionally preserves the six repository fixture files
after checking their bytes against each report's `fixture_sha256` map.
The disposable `host`, `reference` and their two `.dSYM` bundles are omitted
explicitly in the manifests. Every archived member was reread and hashed
after compression; source closure and target ELF hashes match their reports.

These are synthetic transport and software-output observations, including
full decoded pixels and document notification traces. The second run adds
stronger checks to the same scenarios; it is not another set of original
firmware page lifecycles. Neither run observes physical USB, status or printing.
Later source changes require separate execution and must not inherit these
archives' passing claims.
