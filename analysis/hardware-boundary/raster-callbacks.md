# Stock raster callbacks

offline stock-byte audit; unresolved instructions are not executed or treated as safe

## Verified findings

- Default BPP2/600 selects 0x10015648, BPP1/600 selects 0x100159b4, BPP1/1200 selects 0x10015814.
- The indirect call has four arguments. Saved Ghidra C showed only three and lost the stride argument.
- BPP2 writes user registers 0 and 1 with EEEEEEEE and BBBBBBBB, and uses 55555555 in ordinary Boolean preparation.
- BPP2 has 16 custom encodings (groups 0x69, 0x60, 0x6d, 0x6e). BPP1 callbacks also contain unresolved groups 0x8e, 0x8f, 0x7f.
- Ghidra generic WUR output names LBEG/LEND/LCOUNT here are misleading: these are user-register numbers 0/1/2, not proof of loop-register writes.
- The callback gate is video +0xc0 and nonzero callback pointer. Stock can bypass this stage, but acceptable image quality and timing of that configuration are uncalibrated.

## Callback arguments

| Register window mapping | Value |
|---|---|
| a10_to_a2 | source = slot pointer - video +0xf4 * stride |
| a11_to_a3 | destination = transformed slot pointer at video +0x10 + slot*4 |
| a12_to_a4 | rows = descriptor units & ~3 |
| a13_to_a5 | stride = video +0xb8 (omitted by saved decompilation) |

## Exact unresolved encodings

| Function | Instructions | Unresolved groups | User registers |
|---|---:|---|---|
| bpp2_600 (0x10015648) | 175 | {'0x69': 8, '0x60': 4, '0x6e': 2, '0x6d': 2} | [0, 1] |
| bpp1_1200 (0x10015814) | 156 | {'0x8e': 22, '0x7f': 16, '0x8f': 2} | [] |
| bpp1_600 (0x100159b4) | 194 | {'0x8e': 18, '0x7f': 64, '0x8f': 2} | [2] |

Full byte-matched instruction listings and every unresolved address are in the JSON report.

## Remaining questions

- Exact value transformation and side effects of each extension encoding, including hidden state and possible memory accesses.
- Whether the stock-supported bypass can meet the narrow replacement print-quality requirement.
- Safe physical interpretation of the transformed output buffers and engine/video timing.

Obtain this core-specific ISA definition, or compare controlled inputs and outputs while stock firmware executes these callbacks. No custom opcode probe is authorized or claimed safe.
