# Initial standard EP0 submission failure: reproduced before the fix

`initial-standard-reproduced.tar.gz` preserves
`/tmp/hp1020-tinyusb-printer-4bdfwxef` and the unchanged
`/tmp/hp1020-standard-submit-reproduction-20260929.log` as `run.log`.
The adjacent JSON manifest hashes the archive and every regular member.

The first 116 host scenarios passed. Case 116 (the 117th scenario),
`initial-standard/descriptor/active-input/fill=0/capacity=1024/interface=3`,
then failed at step 26: service returned OK (0), where the new regression
required ERROR (5) after a retained initial standard reply was rejected.
The raw snapshot retains the EP0 IN and bulk OUT owners while receive remains
unfenced. This is the deliberate reproduction, before the adapter guard fix.
No target validation ran. There is no target ELF, target capture or completed
`validation.json`; no passing report has been invented for this attempt.

All 76 recorded source files are present and match `source-sha256.json`.
The materialized TinyUSB sources match `effective-source/effective-source.json`.
Every event and raw capture from all 117 started host scenarios is preserved.
The validator SHA256 is
`22a4a267ffe6f0a7e752cdfd71005a8bf823a5e6f94c988c156f71b74fc3ffb1`;
the unfixed adapter SHA256 is
`fbe163b3b02cad77dc3f1d61b904e58e3ff9c712e7f56ae3927c3682ef914e8b`.

External fixture files were not copied or separately hashed by this stopped
run. `recovered-fixtures/` therefore comes from the earlier immutable
`automatic-recovery-116-cases.tar.gz`, verified against its archive, member
and completed-report hashes. `archival-input-provenance.json` records the
provenance and byte comparisons: all five JBIG headers/compressed bodies and
the used template metadata match this failed run's saved case 000/002 events.
Unused base-file portions, its preamble and overwritten original metadata
cannot be established from those events. The recovered hashes are not claimed
as hashes recorded by the failed run. No working-tree source was substituted.

Only disposable `host`/`reference` executables and their `.dSYM` bundles are
omitted. Every archived member was reread and hashed after compression.
This preserves a synthetic software failure; no hardware or USB was contacted.
