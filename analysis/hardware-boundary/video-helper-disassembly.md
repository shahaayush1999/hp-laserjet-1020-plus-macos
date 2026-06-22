# HP 1020 Video Helper Disassembly Limit

This generated report is offline only. It does not contact the printer.

## Result

- status: `pass`
- helper: `0x1001b668` `ceil_div_or_units_encode_candidate`
- confirmed denominator 0 behavior: returns 0
- confirmed denominator 1 behavior: returns numerator
- denominator >= 2: caller-fit hypothesis remains ceil(numerator / denominator)
- why not final: Ghidra and local objdump do not currently provide a clean decode of the old Xtensa/custom divide path.

## Plain-English Meaning

We know this helper matters and know its no-divide edge cases. We do not yet have a clean instruction-level decode for the real divide path, so the ceil-div name is a strong model fit, not final proof.

## Raw Bytes

- range: `0x1001b668..0x1001b6c8`
- first 32 bytes: `6c10026e3239d620056f04043f04745b2405440c00410400331a220a006d490d`
- similar helper `0x1001b6b0` first 32 bytes: `6c10026e322f052f04043f04745b1e05440c00410400331ad30f6d4908732302`

## Caller Impact

| Caller | Role | Evidence |
|---|---|---|
| `0x10014910 hp1020_video_prepare_page_candidate` | computes stride-derived chunk cap +0xcc and a secondary chunk value | `present` |
| `0x10013f34 hp1020_video_band_queue_or_list_candidate` | encodes normal descriptor-queue raw-band counts before flag writes | `present` |
| `0x100140f8 hp1020_video_refresh_raw_bands_candidate` | encodes alternate raw linked-list counts before flag writes | `present` |

## Decoder Evidence

- Ghidra pcode error hits: `4`
  - `analysis/zjs-parser-boundary-run.txt`: `WARN  Decompiling 1001b668, pcode error at 1001b685: Unable to resolve constructor at 1001b685 (DecompileCallback)`
  - `analysis/queue-send-census-run.txt`: `WARN  Decompiling 1001b668, pcode error at 1001b685: Unable to resolve constructor at 1001b685 (DecompileCallback)`
  - `analysis/message-producers/message-producers-run.txt`: `WARN  Decompiling 1001b668, pcode error at 1001b685: Unable to resolve constructor at 1001b685 (DecompileCallback)`
  - `analysis/jobmgr-producer-boundary-run.txt`: `WARN  Decompiling 1001b668, pcode error at 1001b685: Unable to resolve constructor at 1001b685 (DecompileCallback)`

- objdump tool: `/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf-objdump`
- objdump return code: `0`
- decoder limit markers: `9`

Relevant objdump lines:

- `1001b668:	6c10                	movi.n	a0, -31`
- `1001b66f:	20056f               	excw`
- `1001b672:	04043f               	muls.ad.hh	a4, m2`
- `1001b678:	240544               	excw`
- `1001b680:	331a22               	excw`
- `1001b685:	6d49                	excw`
- `1001b687:	0d73                	excw`
- `1001b695:	147363               	excw`
- `1001b6ad:	20d10f               	excw`
- `1001b6b0:	6c10                	movi.n	a0, -31`
- `1001b6b5:	2f052f04043f0474 	{ excw; excw }`

## Checks

| Check | Status | Detail |
|---|---|---|
| `helper_bytes_extracted` | `present` | ELF bytes at 0x1001b668 match the current stock firmware extraction. |
| `zero_one_cases_visible` | `present` | Ghidra decompile still exposes denominator 0 -> 0 and denominator 1 -> numerator. |
| `bad_instruction_path_visible` | `present` | Ghidra still marks the helper's wider divide path as bad instruction data. |
| `ghidra_logs_show_pcode_error` | `present` | Batch decompile logs include the pcode constructor failure at 0x1001b685. |
| `known_callers_accounted_for` | `present` | Prepare, descriptor-queue, and alternate raw-band callers still reference the helper. |
| `local_objdump_does_not_confirm_divide_path` | `present` | Current local objdump path is absent or emits old-Xtensa/custom-instruction-looking markers instead of a clean helper decode. |
