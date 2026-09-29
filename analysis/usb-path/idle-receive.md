# Original USB idle receive intent

58 conditional RAM cases agree in both engines; 6 unredirected-register cases reject before peripheral access.

Original idle receive helper skips when supplied DEVSTS RXFIFO_EMPTY is set or its byte latch is nonzero. Otherwise it requests OUT1 SNAK, sets the latch, supplies delay 5/50, rereads DEVCTL and sets RDE bit 2. Independent expected access traces and every nonstack mutable byte agree in both engines.

The original USB2IdleThread directly loops around this helper; its creation literal and caller bytes are checked but never executed. Each phase is a fresh original helper ENTRY with retained supplied RAM. IRQ mask and unmask services are substitutions, not actual interrupt operations.

A supplied RDE-clear word at the delay boundary is followed by the original RDE-set operation. The original does not inspect a cancellation generation or descriptor ownership here. A future transport must settle or fence pending receive-enable work before acknowledging quiescence; this experiment does not supply that acknowledgement.

Three register-address literals point to RAM, with no self-clearing bits or controller behavior. Delay-return DEVCTL changes are explicit synthetic inputs, not evidence of an actual stock scheduling race or completed stop. Delay/clock/interrupt bodies, the surrounding infinite loop, startup, IRQ, rearm, pause and reset paths are excluded. No owner transition, descriptor retirement, FIFO flush, DMA reset, pending-event drain or physical quiescence is established. Descriptor and payload preservation refers only to supplied RAM canaries. Family bit names do not identify HP silicon or authorize peripheral writes. Zero USB traffic or printing.
