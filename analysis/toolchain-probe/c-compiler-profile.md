# Conservative C compiler profile

xtensa-fsf-elf-gcc (GCC) 14.3.0

Compiler feature and static stock-byte compatibility gate; not a boot/CPU-state hardware test

| Macro | Required and observed |
|---|---|
| __XTENSA_EB__ | 1 |
| __XTENSA_CALL0_ABI__ | 1 |
| __XSHAL_ABI | 1 |
| __XCHAL_HAVE_BE | 1 |
| __XCHAL_HAVE_DENSITY | 1 |
| __XCHAL_HAVE_ADDX | 1 |
| __XCHAL_HAVE_L32R | 1 |
| __XCHAL_HAVE_MUL32 | 1 |
| __XCHAL_HAVE_NSA | 1 |
| __XCHAL_HAVE_DIV32 | 0 |
| __XCHAL_HAVE_THREADPTR | 0 |
| __XCHAL_HAVE_RELEASE_SYNC | 0 |
| __XCHAL_HAVE_S32C1I | 0 |
| __XCHAL_HAVE_LOOPS | 0 |
| __XCHAL_HAVE_WINDOWED | 0 |
| __XCHAL_HAVE_ABS | 0 |
| __XCHAL_HAVE_MUL16 | 0 |
| __XCHAL_HAVE_MINMAX | 0 |
| __XCHAL_HAVE_SEXT | 0 |
| __XCHAL_HAVE_FP | 0 |
| __XCHAL_HAVE_MUL32_HIGH | 0 |

| Stock counterpart | Address | Bytes |
|---|---|---|
| call0 | 0x100187b1 | 500a5d |
| ret.n | 0x1001b1fa | d00f |
| mull | 0x10013f8e | 098828 |
| nsau | 0x1001b670 | 056f04 |
| addx4 | 0x10013f75 | 07a80a |
| src | 0x10016f2b | 054418 |
| memw | 0x10008211 | 0c0200 |
