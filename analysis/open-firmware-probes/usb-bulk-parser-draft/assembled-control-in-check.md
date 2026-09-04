# Assembled control-IN RAM execution check

Status: pass; 64 cases; zero MMIO accesses.

Executes compiled selection/clipping and response-copy instructions. Tests device/config/language/manufacturer/product descriptors at zero, odd, short, exact and oversized host lengths; bulk status tests include zero, live-test and mixed hexadecimal counters.

All controller reads and writes are skipped at explicit boundaries. The test injects the register clobbers from gate/sequence code, then checks exact staged bytes, response length/pointer and all four transfer-record words. It rejects out-of-range RAM writes and every MMIO access. USB completion, status-stage behavior and physical timing remain untested.

Regressions caught: `a4` must be restored after counter formatting, and the selected descriptor pointer must survive the `a2` gate-register loads. Both failures reproduced against checkpoint `16cec37` before the fixes.
