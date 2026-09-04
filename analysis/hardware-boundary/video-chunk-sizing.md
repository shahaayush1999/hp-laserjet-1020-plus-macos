# HP 1020 Video Chunk Sizing

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- scope: video state `+0xcc/+0xd0` sizing and raw-band flag helper behavior

## Verified Helper

- function: `0x1001b668`
- working name: `unsigned_divide`
- exact denominator 0 case: `0`
- exact denominator 1 case: `numerator`
- verified behavior: for denominator >= 2, returns floor(numerator / denominator)
- evidence: Complete ELF-matched decode and independent instruction execution are recorded in video-helper-disassembly.md.

## Constants

| Name | Value |
|---|---:|
| `chunk_budget_bytes_DAT_10005dc8` | `8192` / `0x00002000` |
| `secondary_budget_DAT_10005ddc` | `2048` / `0x00000800` |
| `high_bit_DAT_10005e34` | `2147483648` / `0x80000000` |
| `clear_high_bit_DAT_1000628c` | `2147483647` / `0x7fffffff` |

## Chunk Projection

| Case | Work +0x84 | Stride +0xb8 | floor(8192/stride) | +0xcc max chunk units | Channel-B length formula | Payload +0x48 |
|---|---:|---:|---:|---:|---|---:|
| `base` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `a4_2400x600` | `19072` | `2384` | `3` | `0` | `min(+0xcc,+0xd0) * 2384` | `9080` |
| `a4_600x600` | `4864` | `608` | `13` | `12` | `min(+0xcc,+0xd0) * 608` | `4448` |
| `a4_cardstock_media` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `a4_default` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `a4_draft` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `a4_logical_clip` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `a4_manual_feed` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `a4_two_copies` | `9600` | `1200` | `6` | `4` | `min(+0xcc,+0xd0) * 1200` | `6364` |
| `legal_default` | `9856` | `1232` | `6` | `4` | `min(+0xcc,+0xd0) * 1232` | `6388` |
| `letter_default` | `9856` | `1232` | `6` | `4` | `min(+0xcc,+0xd0) * 1232` | `6376` |

## Flag Encoding Scenarios

| Units | +0xc4 | Final | Secondary | Encoded units | Flag word |
|---:|---:|---:|---:|---:|---:|
| `4` | `1` | `0` | `0` | `4` | `0x00000004` |
| `4` | `1` | `1` | `0` | `4` | `0x01000004` |
| `4` | `1` | `1` | `1` | `4` | `0x03000004` |
| `5` | `2` | `0` | `1` | `2` | `0x02000002` |
| `7` | `2` | `1` | `1` | `3` | `0x03000003` |

## Field Conclusions

- +0xb8 is stride bytes: ((work +0x84 + 31) & ~31) >> 3.
- +0xcc is a maximum chunk-unit cap: floor_div(8192, stride) rounded down to a multiple of 4.
- +0xd0/+0xd4 are copied from work +0x26 and then decremented by the refill helper.
- Raw-band flag words use unsigned floor-divided units ORed with final/secondary bits; physical interpretation remains uncalibrated.

## Checks

| Check | Status | Detail |
|---|---|---|
| `division_helper_zero_one_cases_visible` | `present` | 0x1001b668 exposes exact divisor 0/1 behavior despite bad decompiler flow after that |
| `prepare_computes_stride_from_work_0x84` | `present` | prepare derives stride +0xb8 from work +0x84 rounded to 32 then divided by 8 |
| `prepare_computes_cc_from_budget_and_stride` | `present` | prepare computes +0xcc from helper(chunk budget, stride) rounded down to a multiple of 4 |
| `prepare_copies_remaining_units_from_work_0x26` | `present` | prepare copies work +0x26 into remaining counters +0xd0/+0xd4 |
| `raw_band_uses_helper_for_flag_encoding` | `present` | normal queue and alternate raw refresh both use the helper before raw-band flag writes |
| `known_constants_read` | `present` | ELF constants for chunk budget and high-bit masks match current reports |
| `a4_default_chunk_projection` | `present` | a4_default projects to stride 1200 and +0xcc max chunk units 4 under verified unsigned floor division |
