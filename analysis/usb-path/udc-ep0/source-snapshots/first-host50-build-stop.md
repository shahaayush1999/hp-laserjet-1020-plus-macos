# EP0 composition: 50 host cases before a build-integration stop

`first-host50-build-stop.tar.gz` preserves
`/tmp/hp1020-udc-ep0-srkbp5vo` and the untouched
`/tmp/hp1020-udc-ep0-first-20260929.log` as `run.log`.
All 50 host scenarios completed. The run then stopped at the target build
script's initial `HP1020_REPO_ROOT` requirement, which still reflected its
external draft environment. Target compilation and QEMU cases did not run;
no component target ELF, target captures or success report was emitted.
This is an incomplete validator run, not a completed target checkpoint.

The archive preserves all 92 recorded source files, including the exact old
builder that rejected the invocation, all six recorded fixture bytes, all
materialized TinyUSB files/manifests, and every host case's original events,
standard output/error, base/EP0 step captures, pixels, wire bytes, document
notifications, receive/output storage and complete guarded descriptor/staging
capture. The source closure includes the reused original-construction report
and its full ten-file source closure. That earlier original execution's raw
captures remain separately preserved under
`../../ep0-construction/source-snapshots/first-66-cases.*`; the component run
adds no new original-instruction execution.

All recorded source, fixture and effective-source hashes were matched to their
saved bytes, all 50 case file sets were checked, and every archived member was
reread and hashed after compression. Only disposable `host`, `reference` and
their `.dSYM` bundles are omitted, explicitly listed in the adjacent manifest.
No working-tree source replaced the captured old builder. No missing report,
target artifact or target result was invented.

- Validator SHA256: `b6fa90e24c14c1a38d443c5bec0e48fe0e453b97c9c13fc67ec24ae8afa850bf`.
- Captured old builder SHA256: `8d7d04170d255756b08b37a86ee0c6e5ef6efc890217bcabf0bbaeee5b49994d`.
- Reused original-construction report SHA256: `8e41f358f5d956d5cdab71b45c136d6216bfa302af30a658f06f56e99696b53d`.
- Archive SHA256: `e814c4031d54b7cfefcdcff4a00371369a2532b2b9319a215c286689844508db`.

The host scenarios use synthetic events and supplied mode, mapping, cache,
actual-count and settlement facts. They establish no physical DCD, USB transfer,
controller quiescence, printing or power-cycle recovery. The build correction
and successful target replay belong to separately captured evidence.
