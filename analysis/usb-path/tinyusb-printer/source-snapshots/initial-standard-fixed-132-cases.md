# Initial standard EP0 guard: completed 132-case run

`initial-standard-fixed-132-cases.tar.gz` preserves the completed run from
`/tmp/hp1020-tinyusb-printer-3m6u4fne`: 132 host and 132 QEMU scenarios.
`run.log` is the unchanged `/tmp/hp1020-standard-submit-fixed-20260929.log`.
The adjacent JSON manifest hashes the archive and every regular member.

The archive retains the original `validation.json`, complete 76-file source
closure and source manifest, exact materialized TinyUSB sources, every raw
event and host/target capture, and `target-check.elf`. All source hashes and
the target ELF match the completed report. No working-tree source was used.

The same validator as the unfixed reproduction has SHA256
`22a4a267ffe6f0a7e752cdfd71005a8bf823a5e6f94c988c156f71b74fc3ffb1`.
The tested adapter SHA256 is
`1b689e373e3da263ad239f31ec7f8ad8bacf43e935c66f2fcb4642d6a2862d49`;
the target ELF SHA256 is
`d59507aa2508fd40de18bda4ed60b9e60e65de621528b29f18d8030ac8638bae`.
The recorded target component state/fixed-memory size is 128536 bytes,
excluding code, stack, TinyUSB and fixture captures.

The six `tested-fixtures/` members were recovered from the earlier immutable
`automatic-recovery-116-cases.tar.gz`; its archive/member hashes were checked,
and each recovered file independently matches this completed run's recorded
`fixture_sha256`. Only disposable `host`/`reference` executables and their
`.dSYM` bundles are omitted. Every archived member was reread and hashed
after compression.

This run covers the initial standard-reply guard alongside the prior adapter
scenarios. Transport and output remain synthetic; no hardware quiescence,
physical USB transfer or printing is established. Later source edits require
separate execution and do not inherit this snapshot's passing claims.
