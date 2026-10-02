# Original USB IRQ cuts: first completed run

The archive preserves all 839 files from `/tmp/hp1020-usb-irq-capture-jsuu8up_`, the first-run log
as `run.log`, and the unchanged independent gate used after that run. Nothing is
omitted. All 13 original source snapshots, original byte audit, supplied inputs,
engine observations, and before/expected/after RAM captures are retained.

The first run passed 82 paired cases: 44 conditional cuts and 38 pre-peripheral
guards, plus 75 phase-specific excluded-PC controls. All 3636 memory-region
digests were checked against 492 complete raw RAM captures, including stack and
record canaries. Expected/after bytes and the two engines agree. All 841
archive members were reread and hashed after compression; the adjacent JSON
records exact member hashes. These preservation checks do not execute firmware.

- Tested generator SHA256: `c3402dce5f5b7cc4e02f941fc6d1814814963bf0cbec715d2b3bb1d3e845acdf`.
- Report SHA256: `53e981d00f4765d1e743e0d859d03df12a1218848bba91525f2a5bff3f77abde`.
- Independent gate SHA256: `0334e8ef6f7f6689dac6ace424db292584a942af03fbfbcf02c0d70f0f6d30a7`.
- Archive SHA256: `0199be21699d670b047861502b3e45e92699d7e1377dbbd5145434c89af39d67`.

Only the sampling prefix executes original ENTRY. Endpoint selection and OUT0
wake intent are separate cuts with supplied frame/register state. There are no
omitted-helper calls or actual peripheral accesses. RAM acknowledgement stores
are not W1C hardware. Conditional mask selection does not establish a reachable
hardware bug, event chronology, coherent SETUP acquisition, cancellation,
controller settlement or physical USB completion. No native page lifecycle,
boot, printing or power-cycle evidence is added.
