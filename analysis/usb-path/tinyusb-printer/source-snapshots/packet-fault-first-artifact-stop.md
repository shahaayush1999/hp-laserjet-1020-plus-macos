# Retained packet fault: first run stopped at the artifact gate

`packet-fault-first-artifact-stop.tar.gz` preserves
`/tmp/hp1020-tinyusb-packet-fault-5v523_sg` and the untouched
`/tmp/hp1020-packet-fault-first-20260929.log` as `run.log`.
The log records 20 host and 20 QEMU scenarios completed before the final
captured-artifact hash assertion failed. This is an incomplete run, not a
successful validator checkpoint. No success report was emitted or reconstructed.

The frozen runner copied a preexisting `annotated-disassembly.txt` into its
captured target directory before the instruction audit. That audit regenerated
its derived listing for the captured ELF/path, changing a file already included
in the pre-audit target hash map. The final gate reported
`captured target changed during replay`. The preserved
`artifact-gate-diagnosis.json` identifies that listing as the differing file.
`pre-audit-shared-annotated-disassembly.txt` retains the prior shared listing;
`target/annotated-disassembly.txt` retains the generated post-audit listing.
Both copies match the diagnosis's recorded hashes. Correcting the generator's
snapshot order and rerunning belongs to separate evidence.

All 77 recorded source files and six recorded input fixtures are preserved and
match their captured manifests. Materialized TinyUSB has all 19 recorded files;
its manifest also matches the captured build's effective-source record.
The archive includes all 20 cases' events, raw standard output/error, host/target
step captures and exact pixels/wire/receive/output bytes, the target ELF and
build artifacts, pixel oracle, failure diagnosis and log. Each of the 80 raw
host/target output pairs is byte-identical. The failed runner emitted no separate
target-artifact manifest; the adjacent archive manifest hashes the saved bytes
as archival evidence and does not pretend to be that missing run artifact.

Only disposable `host`, `reference` and their `.dSYM` bundles are omitted,
explicitly listed in the adjacent JSON. Every archived member was reread and
hashed after compression. No tested source or report hash was edited.

- Frozen validator SHA256: `38d0541705dab099e8c5ec4cd9dde8da984dc12e1dcf70d6aa1116eef0e1aeaa`.
- Target ELF SHA256: `1a8969a1d13782a18be9416131a13b237fcf6d4166d4ece175a2c8a1bdc690a6`.
- Prior listing SHA256: `0ad4d900931b02d4d6454b5301f6dd713fdab6c947a92714039f4d24a06ae304`.
- Generated listing SHA256: `3dc26375e655fe7ac682212d1fe387295ce060aafad3db5099dbdba6bcd95a70`.
- Archive SHA256: `932d3f10900ce1f157d917c4b1364ea05fdda10001be86b92636b073f840bb04`.

These are synthetic packet ownership/fault and software-output observations.
They establish no physical USB transfer, controller/cache/reset behavior,
mechanical operation, printing or power-cycle recovery. The artifact-gate stop
must remain distinct from both case completion and a later successful rerun.
