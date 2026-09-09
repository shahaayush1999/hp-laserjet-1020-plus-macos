# Original context construction, save and switching

180 QEMU cases match independent arithmetic/frame/bookkeeping oracles. The initial stack builder also agrees with the instruction interpreter.

- Original explicit window flush preserves the nested return chain for CALL4/8/12 through depth 32, matching a triangular-number arithmetic oracle.
- Original voluntary context save, window flush, scheduler selection and RFE restoration execute on QEMU. Before explicit window flushing, saved return/stack and loop/SAR/PS/continuation fields match an independently captured CPU-register oracle; untouched data registers can alias older live windows before access-triggered spilling and are not treated as preserved input; flushing may reuse ABI spill slots, and the restored caller arithmetic also agrees; current-thread pointer, run count and time-slice bookkeeping agree.
- Corrupting the saved continuation in synthetic RAM is detected before execution can leave the permitted code ranges.
- Original initial-stack builder agrees between the interpreter, QEMU and a complete defined-frame oracle, including alignment and untouched padding.
- Two synthetic tasks alternate on separate stacks using original voluntary save, window flush, scheduler selection and RFE restoration. Both independent arithmetic accumulators and every selection/run count agree across nested CALL4/8/12 and repeated switches.
- After a cross-thread switch WINDOWBASE can differ from startup: results must be read through the current logical register mapping. The remaining live window matches that current base.

Only the same synthetic thread is selected after each voluntary save. A different QEMU core, synthetic stacks and an explicitly seeded ordinary-thread/time-slice environment are used. No cross-thread switch, actual interrupt, timer delivery, boot, custom raster opcode, MMIO or printer execution is established.

The fixture tasks explicitly choose each other by writing the selected-thread pointer. This verifies context switching, not RTOS priority policy, interrupts, timer expiry, blocking task integration, boot, custom instructions, hardware or physical printing. Task B remains suspended after task A completes.
