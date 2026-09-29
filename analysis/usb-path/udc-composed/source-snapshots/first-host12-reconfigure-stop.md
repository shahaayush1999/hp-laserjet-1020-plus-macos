# Composed UDC: 12 host cases before a reconnect-helper stop

`first-host12-reconfigure-stop.tar.gz` preserves
`/tmp/hp1020-udc-composed-dqriz2gg` and the untouched
`/tmp/hp1020-udc-composed-first-20260929.log` as `run.log`.
The first 12 of 34 planned host profiles completed. The thirteenth profile,
`case-012` (`bus-reset-retained-capture/fill=0/capacity=64/interface=3`), stopped
at an inherited Python configuration-helper assertion. Its 53 submitted events
and 54 raw output rows, including initialization, are retained as an incomplete
case. The remaining 21 profiles never started. Target build and QEMU replay did
not run; no composed target artifacts or success report were emitted. This
archive is a stopped run, not a completed validation checkpoint.

The captured helper in `source/scripts/validate-hp1020-continuous-printer.py:48`
assumed a fresh class request counter of zero. The final row instead retains the
previous class request id 1, with deferred reply 0; genuine reconfiguration did not
create a class request. The receive queue also retains its earlier issued/count
of 1/1 until the separate recovery promises, so the helper's later zero-reservation
assumption was also inappropriate for reconnect. A new internal recovery id 2 is
active. All captured ownership/guard checks remained healthy. This diagnosis is
read-only interpretation of the saved rows and exact source, not a claim that
the interrupted profile completed.

All 117 recorded source files, six exact fixtures, 19 materialized TinyUSB files
and their manifest, and all 15 files from each of the 13 started host cases are
preserved. Sources include the stock bytes and the reused original SETUP/EP0/
controller reports and dependencies; no new original-firmware execution was
performed. All recorded source, fixture and effective-source hashes were matched
to saved bytes. Every archived member was reread and hashed after compression.
Only disposable `host`, `reference` and their `.dSYM` bundles are omitted, as
listed in the adjacent manifest. The final raw pixel `oracle` file is retained.
No working-tree source was substituted for this run's captured source closure.

- Validator SHA256: `ffdc8eacf6a0bd0282b08b22b790b9c72dc44a47953ab0172399fddf54c08a41`.
- Composed fixture SHA256: `4831b55affd876bb21099b5149d02e259131b74c623e21835e80805e1adbf563`.
- Archive SHA256: `63e625a75e314b97a9c13597e56b87531de12dcfe39c692e26c4ca8e3deff1db`.

The only recorded source change in the later `passed-34-cases` archive is the
composed Python validator's reconnect helper. The stopped evidence remains
unchanged. All USB/descriptor/cache/settlement events here are supplied synthetic
facts; these cases establish no physical USB transfer, controller quiescence,
printing or power-cycle recovery.
