# HP 1020 Engine Status Decision Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- function: `0x10015df8 hp1020_engine_status_poll_candidate`
- scenarios: `21`
- scenario failures: `0`

## Scenario Table

| Scenario | Status | Primary | Status 0x20 | Status 2 | Substatus 0x16 | Substatus 0x13 | Stored event | Side-effect commands | Extra events | Trace |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| `primary_all_ones_no_update` | `pass` | `0xffff` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `None` | - | - | `primary_0xffff_short_circuit` |
| `primary_0x4040_default` | `pass` | `0x4040` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x04800100` | - | - | `primary_valid_default_0x04800100` |
| `status_0x20_0x800` | `pass` | `0x0000` | `0x0800` | `0x0000` | `0x0000` | `0x0000` | `0xf6000300` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20` |
| `status_0x20_0x400` | `pass` | `0x0000` | `0x0400` | `0x0000` | `0x0000` | `0x0000` | `0xf6000400` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800` |
| `status_2_0x4000` | `pass` | `0x0000` | `0x0000` | `0x4000` | `0x0000` | `0x0000` | `0xe6100800` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800` |
| `status_2_0x424` | `pass` | `0x0000` | `0x0000` | `0x0004` | `0x0000` | `0x0000` | `0x20001607` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000` |
| `status_2_0x1000` | `pass` | `0x0000` | `0x0000` | `0x1000` | `0x0000` | `0x0000` | `0xe6101100` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000`<br>`status_2_no_0x424` |
| `status_2_0x2000` | `pass` | `0x0000` | `0x0000` | `0x2000` | `0x0000` | `0x0000` | `0xe6100e00` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000`<br>`status_2_no_0x424`<br>`status_2_no_0x1000` |
| `ready_rewrite` | `pass` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x14000a04` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000`<br>`status_2_no_0x424`<br>`status_2_no_0x1000`<br>`ready_ok_from_status_2`<br>`rewrite_low16_0x0a01_to_0x14000a04` |
| `primary_0x40_fallback_error` | `pass` | `0x0040` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x80000000` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000`<br>`status_2_no_0x424`<br>`status_2_no_0x1000`<br>`fallback_error_primary_0x40_without_status_2_0x200` |
| `primary_0x40_status_2_0x200_ready` | `pass` | `0x0040` | `0x0000` | `0x0200` | `0x0000` | `0x0000` | `0x14000a04` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000`<br>`status_2_no_0x424`<br>`status_2_no_0x1000`<br>`ready_ok_from_status_2`<br>`rewrite_low16_0x0a01_to_0x14000a04` |
| `substatus_0x16_ready_0x40_with_status_2_0x40` | `pass` | `0x0000` | `0x0000` | `0x0040` | `0x0040` | `0x0000` | `0x14000a04` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_has_0xc0_read_0x16`<br>`substatus_0x16_exact_0x40_ready`<br>`rewrite_low16_0x0a01_to_0x14000a04` |
| `substatus_0x16_ready_0x40_with_status_2_0x4040` | `pass` | `0x0000` | `0x0000` | `0x4040` | `0x0040` | `0x0000` | `0xe6100800` | `0x0000501a` | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_has_0xc0_read_0x16`<br>`substatus_0x16_exact_0x40_ready`<br>`send_0x501a_and_force_e6100800` |
| `substatus_0x16_low_clear_sends_0x501a` | `pass` | `0x0000` | `0x0000` | `0x0040` | `0x0000` | `0x0000` | `0x80000000` | `0x0000501a` | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_has_0xc0_read_0x16`<br>`substatus_0x16_bits_0x0000`<br>`send_0x501a_substatus_low_bits_clear` |
| `substatus_0x16_bit_0x10` | `pass` | `0x0000` | `0x0000` | `0x0040` | `0x0010` | `0x0000` | `0xe6000d03` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_has_0xc0_read_0x16`<br>`substatus_0x16_bits_0x0010` |
| `substatus_0x16_bit_0x08` | `pass` | `0x0000` | `0x0000` | `0x0040` | `0x0008` | `0x0000` | `0xe6000d06` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_has_0xc0_read_0x16`<br>`substatus_0x16_bits_0x0008` |
| `substatus_0x16_bit_0x04` | `pass` | `0x0000` | `0x0000` | `0x0040` | `0x0004` | `0x0000` | `0xe6000d04` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_has_0xc0_read_0x16`<br>`substatus_0x16_bits_0x0004` |
| `status_0x13_default` | `pass` | `0x0000` | `0x0000` | `0x0100` | `0x0000` | `0x0000` | `0xe6100b0a` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_0x13_default_subcase_0x0` |
| `status_0x13_case_0x10` | `pass` | `0x0000` | `0x0000` | `0x0100` | `0x0000` | `0x0020` | `0xe6100b0b` | - | - | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_0x13_special_subcase_0x10` |
| `previous_0x0100_to_ready_extra_emit` | `pass` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x14000a04` | - | `0xe6100a01` | `primary_valid_default_0x04800100`<br>`primary_missing_0x4040_read_0x20`<br>`status_0x20_no_0x800`<br>`status_0x20_no_0x400_read_0x2`<br>`status_2_no_0x100_no_0xc0_default_e6100800`<br>`status_2_no_0x4000`<br>`status_2_no_0x424`<br>`status_2_no_0x1000`<br>`ready_ok_from_status_2`<br>`rewrite_low16_0x0a01_to_0x14000a04`<br>`previous_0x0100_to_0x0a04_extra_ready_emit` |
| `leave_e6100800_sends_0x5043` | `pass` | `0x4040` | `0x0000` | `0x0000` | `0x0000` | `0x0000` | `0x04800100` | `0x00005043` | - | `primary_valid_default_0x04800100`<br>`leave_e6100800_family_send_0x5043` |

## Evidence Checks

| Check | Status | Needle |
|---|---|---|
| `primary_read` | `present` | `uVar4 = hp1020_engine_status_io_candidate(1)` |
| `status_0x20_read` | `present` | `uVar5 = hp1020_engine_status_io_candidate(0x20)` |
| `status_2_read` | `present` | `uVar5 = hp1020_engine_status_io_candidate(2)` |
| `substatus_0x16_read` | `present` | `uVar7 = hp1020_engine_status_io_candidate(0x16)` |
| `substatus_0x13_read` | `present` | `uVar9 = hp1020_engine_status_io_candidate(0x13)` |
| `ready_rewrite` | `present` | `if ((uVar6 & 0xffff) == DAT_10006974)` |
| `previous_low16_transition` | `present` | `((*(uint *)(PTR_DAT_10006920 + 0x60) & 0xffff) == 0x100)` |
| `leave_e6100800_side_effect` | `present` | `hp1020_engine_status_io_candidate(DAT_1000697c)` |
| `substatus_side_effect` | `present` | `hp1020_engine_status_io_candidate(DAT_10006968)` |
| `video_reset_latch` | `present` | `hp1020_video_reset_dispatch_candidate()` |

## Open Firmware Meaning

- Later raw status captures can be fed into this model to classify the exact stock branch without rereading Ghidra output.
- This model predicts stock event words and side-effect commands only; physical labels still require printer-side calibration.
- The safe offline conclusion is that a printing replacement needs this branch behavior before it can reliably decide when to start, wait, recover, or surface errors.

