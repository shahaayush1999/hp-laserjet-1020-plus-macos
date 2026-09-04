# Freestanding C compiler checkpoint

The compiler now builds and runs on this Mac. The target remains synthetic
host-emulated RAM; no new uploadable firmware image is generated.

- GCC **14.3.0**, [upstream source archive](https://ftp.gnu.org/gnu/gcc/gcc-14.3.0/gcc-14.3.0.tar.xz).
- Archive SHA-256: `e0dc77297625631ac8e50fa92fffefe899a4eb702592da5c32ef04e2293aca3a`.
- Compiler: `/tmp/hp1020-xtensa-gcc14/bin/xtensa-fsf-elf-gcc`.
- Assembler/linker: repaired BE prefix `/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf`.
- Rebuild: `scripts/build-xtensa-gcc-manual.sh`; requires the existing Homebrew
  make, GMP, MPFR and MPC installations plus the repaired assembler.

The pinned upstream Xtensa configuration retains big-endian instructions and
soft float. Hardware division, hardware loops, thread-pointer access, release
synchronization, S32C1I, register windows, ABS, MUL16, MINMAX and SEXT are disabled
for this component. The retained call0, return, MUL32, NSA and scaled-add support
has exact instruction counterparts in the stock ELF. This is a conservative
component profile, not a recovered definition of the complete printer CPU.
The **separate** `XSHAL_ABI` setting is changed to `XTHAL_ABI_CALL0`; disabling
`XCHAL_HAVE_WINDOWED` alone does not select call0 in GCC. The build gate checks
`__XTENSA_EB__` and `__XTENSA_CALL0_ABI__` before producing objects.

The [GCC Xtensa options documentation](https://gcc.gnu.org/onlinedocs/gcc/Xtensa-Options.html)
describes the ABI switch. Here the configured default supplies call0: explicitly
passing `-mabi=call0` would also pass a newer `--abi-call0` metadata option that
the recovered old assembler does not understand. Generated calls and returns
are still call0 instructions, and their ABI is exercised by the RAM interpreter.

Host build adjustments: use system zlib to avoid the bundled zlib/macOS SDK
conflict; disable LTO; rebuild libgcc after changing the default ABI. No installed
printer files or global compiler defaults are modified.

## Target validation

`scripts/build-hp1020-semantic-target.sh` compiles the real portable parser,
page planner, tiny memory helpers, test harness and software divide helper into
an ELF linked at synthetic address `0x20000000`. It has 2536 bytes of text and
139668 bytes of BSS, mostly test input/arena buffers. There is no boot-ROM layout,
ACL wrapper, USB transport or device output entry point.

`scripts/validate-hp1020-semantic-target.py` executes 66 cases: **19,991,177
instructions**, 859 distinct reached instructions, zero MMIO. Generated streams
match independent Python expectations at three fragment sizes; all cases also
match an ASan/UBSan native build. The interpreter rejects unmapped memory,
unaligned accesses, code writes, execution from data sections and
unsupported/custom instructions. It does not
model register windows, caches, peripherals or hardware division.

Two successive target builds produce identical ELF and map files. This is a
compiler/ABI/RAM checkpoint, not evidence of execution on the printer.
