# HP 1020 Unsigned Division and Remainder Audit

The previous ceiling-division hypothesis was wrong. The complete stock helper computes unsigned floor division; its neighbor computes remainder.

The missing instruction `6d 49 0d` at `0x1001b685` is `loopnez a4,0x1001b696`. Ghidra 12.1.1 uses the LE `at=7` field layout for its loop constructors; BE needs `at=13`. The isolated repair uses the existing endian-aware `bri8_m/bri8_n` fields. It changes no installed tool or ELF.

The branch/shift/subtract sequence matches the unsigned division and remainder algorithms in [GCC 3.4.6](https://github.com/gcc-mirror/gcc/blob/releases/gcc-3.4.6/gcc/config/xtensa/lib1funcs.asm). This is supporting source correlation, not proof of the exact compiler version.

## Verification

- Status: `pass`
- 169890 differential executions; all 48 decoded instructions exercised.
- Inputs: exhaustive 8-bit pairs, 32-bit power boundaries, seeded 32-bit random pairs, and video sizes.
- Loop count and control flow are executed explicitly, independently of Ghidra loop p-code.
- All decoded bytes and function hashes must match the stock ELF on every validation run.
- Not exhaustive over all 2^64 inputs; no hardware execution, timing, ABI, or Ghidra loop p-code claim.

## Consequences

`+0xcc = floor(8192 / stride) & ~3`. A4 stride 1200 still gives four units, but the intermediate quotient is six, not seven. At stride 1100 the old rule permits eight units (8800 bytes) against an 8192-byte budget; the stock rule permits four. Raw-band unit encodings must also use floor division. This arithmetic correction does not validate hardware timing.

| Numerator | Divisor | Stock quotient | Old ceiling hypothesis |
|---:|---:|---:|---:|
| 1 | 2 | 0 | 1 |
| 7 | 2 | 3 | 4 |
| 8192 | 1200 | 6 | 7 |
| 8192 | 608 | 13 | 14 |
| 8192 | 1100 | 7 | 8 |
| 4294967295 | 2 | 2147483647 | 2147483648 |
| 4294967295 | 4294967295 | 1 | 1 |
| 123 | 0 | 0 | 0 |

## Complete decoded bodies

### unsigned_divide

```text
1001b668  6c1002  entry a1, 0x10
1001b66b  6e3239  bltui a3, 0x2, 0x1001b6a8
1001b66e  d620    mov.n a6, a2
1001b670  056f04  nsau a5, a6
1001b673  043f04  nsau a4, a3
1001b676  745b24  bgeu a5, a4, 0x1001b69e
1001b679  05440c  sub a4, a4, a5
1001b67c  004104  ssl a4
1001b67f  00331a  sll a3, a3
1001b682  220a00  movi a2, 0x0
1001b685  6d490d  loopnez a4, 0x1001b696
1001b688  736304  bltu a6, a3, 0x1001b690
1001b68b  03660c  sub a6, a6, a3
1001b68e  b122    addi.n a2, a2, 0x1
1001b690  0f2211  slli a2, a2, 0x1
1001b693  031314  srli a3, a3, 0x1
1001b696  736302  bltu a6, a3, 0x1001b69c
1001b699  222c01  addi a2, a2, 0x1
1001b69c  d10f    retw.n
1001b69e  c020    movi.n a2, 0x0
1001b6a0  736301  bltu a6, a3, 0x1001b6a5
1001b6a3  c021    movi.n a2, 0x1
1001b6a5  060000  retw
1001b6a8  c830    beqz.n a3, 0x1001b6ac
1001b6aa  d10f    retw.n
1001b6ac  c020    movi.n a2, 0x0
1001b6ae  d10f    retw.n
```

### unsigned_remainder

```text
1001b6b0  6c1002  entry a1, 0x10
1001b6b3  6e322f  bltui a3, 0x2, 0x1001b6e6
1001b6b6  052f04  nsau a5, a2
1001b6b9  043f04  nsau a4, a3
1001b6bc  745b1e  bgeu a5, a4, 0x1001b6de
1001b6bf  05440c  sub a4, a4, a5
1001b6c2  004104  ssl a4
1001b6c5  00331a  sll a3, a3
1001b6c8  d30f    nop.n
1001b6ca  6d4908  loopnez a4, 0x1001b6d6
1001b6cd  732302  bltu a2, a3, 0x1001b6d3
1001b6d0  03220c  sub a2, a2, a3
1001b6d3  031314  srli a3, a3, 0x1
1001b6d6  732302  bltu a2, a3, 0x1001b6dc
1001b6d9  03220c  sub a2, a2, a3
1001b6dc  d10f    retw.n
1001b6de  732302  bltu a2, a3, 0x1001b6e4
1001b6e1  03220c  sub a2, a2, a3
1001b6e4  d10f    retw.n
1001b6e6  220a00  movi a2, 0x0
1001b6e9  060000  retw
```

## Reproduce

Regular validation requires only Python 3. To regenerate the independent mnemonic decode, install `pypcode==4.0.0` in a temporary virtual environment and run `scripts/recover-hp1020-division-decode.py` with Ghidra 12.1.1 available. Then run `scripts/model-hp1020-video-helper-disassembly.py`.
