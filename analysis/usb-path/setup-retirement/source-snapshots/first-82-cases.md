# Original SETUP retirement: first 82 cases per engine

`first-82-cases.tar.gz` preserves the completed run from
`/tmp/hp1020-setup-retirement-2a9pf7bb` and the untouched
`/tmp/hp1020-setup-retirement-first-20260929.log` as `run.log`.
The saved report records 82 paired interpreter/Xtensa-QEMU cases: 50 conditional
tail profiles and 32 pre-peripheral rejection controls, plus 15 excluded PCs
rejected before execution in both engines. These counts describe the bounded
experiment, not completed USB requests, native pages or physical transfers.

The explicit post-dispatch cut is `0x1000985c..0x1000992e`, with supplied logical
registers including a2 stall intent and a3 zero, pointer globals, record bytes,
available-count values and ordinary RAM control images. No original ENTRY,
admission/dispatch, sender, IRQ, event wait, timer, cache or peripheral access
executes. Four exact original peripheral-address literals are redirected only
in private executor RAM; removed-redirect, escaped-pointer and direct-access
controls reject before the relevant peripheral instruction executes. There are
no substituted services. The archive preserves the original ELF unchanged.

The archive contains all 13 recorded source files, source hashes/origins, exact
`report.json` and `report.md`, byte-audit and excluded-code records, every engine's
supplied input and observation/event record, and before/expected/after raw RAM.
All 839 capture files plus the log are preserved; nothing is omitted. There is
no newly built target ELF: the original stock ELF is executed through the
explicit cuts.

All source hashes and report rows were matched to their saved files. All 4,380
reported memory-region digests were checked against 492 raw RAM captures with
exact region bounds, concatenation order and file lengths, including stack and
guards. Expected/after bytes and the two engines' corresponding raw captures
match. Every one of the 840 archive members was then reread and hashed after
compression. The adjacent JSON records the archive hash and every member hash.
These are archive-integrity checks; no validator, builder or firmware execution
was repeated, and no report or tested source was edited.

- Validator SHA256: `5b4a803c301deb330b93167cd72a286b774144b9d01b2f74ef0811de081c5124`.
- Original ELF SHA256: `2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d`.
- Frozen report SHA256: `71fcb813203d9cef40fb3bcc455a268c566c4cd5b45eb46df8e618a28213321b`.
- Archive SHA256: `7872f11230dadab6b16b0d0792f51fd7e944a59467a4e3b120369dc259e48df5`.

Plain RAM stores do not model write-one-to-clear or self-clearing commands.
The tail preserves an existing stall bit; CNAK intent does not prove hardware
stall clearing or transfer settlement. Its owner-only OUT0 header reset does
not validate RX/count or authorize safe buffer reuse. Mismatched observed/target
record controls expose a supplied stock pointer assumption, not a recommended
port policy. SETUP storage and older EP0 packet ownership remain separate.
The run adds zero completed USB control transfers, native page lifecycles or
physical USB operations. Controller rearm, quiescence, actual mapping, event
ordering, cache visibility, printing and power-cycle recovery remain unproved.
