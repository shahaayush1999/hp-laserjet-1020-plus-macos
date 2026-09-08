# Independent QEMU cross-check

Status: pass. 13091 cases using QEMU emulator version 11.1.1.

Compiled C target results agree across QEMU, our instruction interpreter, ASan/UBSan native C and fixture expectations. Original parser messages, input consumption and allocation ownership also match, using actual stock window spill/fill handlers under QEMU. JobMgr completion and cleanup also match allocation ownership, scheduled work, defined notification fields and all stock writable global RAM. QEMU independently reproduces the delayed-empty-document failure. Host services intentionally share the existing boundary fixture. Stock libc agrees with complete bytearray oracles; four stock division/remainder helpers agree with independent Python arithmetic, including zero-divisor return-zero and signed-overflow wrapping.

Original six window spill/fill handlers execute under independent QEMU exceptions for CALL4/8/12 recursion through depth 64. Results match a triangular-number arithmetic oracle and the abstract interpreter. Corrupting one saved-return store in the QEMU RAM copy is detected.

Synthetic, aligned ABI stacks and QEMU test_kc705_be with 32 physical ARs; not stock boot state, real core register count, interrupts, cache or malformed-stack recovery.

Original compiled BE/call0 target ELF bytes loaded through a private Unix GDB socket. Original stock memset/memcpy/memmove/strlen also run through actual windowed CALL8/ENTRY/RETW and hardware loops, matching complete 1024-byte RAM oracles. No QEMU instruction decoding is delegated to our interpreter. No printer or host USB backend exists.

The QEMU CPU is not the printer CPU configuration. This does not test firmware boot, arbitrary window/interrupt state, custom raster instructions, caches, interrupts, transport or physical printing.
