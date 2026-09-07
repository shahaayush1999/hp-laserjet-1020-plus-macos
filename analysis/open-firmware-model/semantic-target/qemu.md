# Independent QEMU cross-check

Status: pass. 12930 cases using QEMU emulator version 11.1.1.

Compiled C target results agree across QEMU, our instruction interpreter, ASan/UBSan native C and fixture expectations. Stock libc agrees with complete bytearray oracles; four stock division/remainder helpers agree with independent Python arithmetic, including zero-divisor return-zero and signed-overflow wrapping.

Original compiled BE/call0 target ELF bytes loaded through a private Unix GDB socket. Original stock memset/memcpy/memmove/strlen also run through actual windowed CALL8/ENTRY/RETW and hardware loops, matching complete 1024-byte RAM oracles. No QEMU instruction decoding is delegated to our interpreter. No printer or host USB backend exists.

The QEMU CPU is not the printer CPU configuration. This does not test firmware boot, register-window spills, custom raster instructions, caches, interrupts, transport or physical printing.
