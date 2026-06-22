# HP 1020 Video Prepare Mode Model

This is a generated offline model. It does not contact the printer.

## Result

- status: `pass`
- function: `0x10014910 hp1020_video_prepare_page_candidate`

## Key Literal Values

| Name | Value |
|---|---:|
| `block_a_status` | `0xb1000004` |
| `block_b_status` | `0xb1000104` |
| `block_a_control` | `0xb1000000` |
| `block_b_control` | `0xb1000100` |
| `setup_a_timing` | `0xb1000020` |
| `setup_a_constant` | `0xb1000024` |
| `setup_b_timing` | `0xb1000120` |
| `setup_b_constant` | `0xb1000124` |
| `mode_a_register` | `0xb100001c` |
| `mode_a_clear_mask` | `0x00203f00` |
| `mode_b_register` | `0xb100011c` |
| `mode_ab_clear_mask` | `0x00180000` |
| `timing_table_0` | `0xb1000400` |
| `control_pair_clear_mask` | `0xfcffffff` |
| `mode_control_mask` | `0x03000000` |
| `timing_table_1` | `0xb1000410` |
| `timing_table_2` | `0xb1000420` |
| `timing_table_3` | `0xb1000430` |
| `vertical_a_register` | `0xb1000010` |
| `vertical_b_register` | `0xb1000110` |
| `stride_a_register` | `0xb1000014` |
| `stride_mask` | `0x0000ffff` |
| `stride_b_register` | `0xb1000114` |
| `single_plane_300_lane1_table` | `0x10005520` |
| `single_plane_300_default_table` | `0x10005530` |
| `single_plane_600_alt_table` | `0x100055a0` |
| `single_plane_600_two_output_table` | `0x10005580` |
| `single_plane_600_lane_table` | `0x10005540` |
| `single_plane_1200_sparse_mask` | `0x10030dd4` |
| `single_plane_1200_table` | `0x100055b0` |
| `two_plane_lane0_table` | `0x10005570` |
| `two_plane_lane_table` | `0x10005550` |
| `lane0_vertical_base` | `0x00000d1e` |
| `lane1_vertical_base` | `0x00000d34` |

## Timing Register Modes

| Lane selector | Resolution | Datastore 0x20 zero | Register(s) | Value | Constant register writes |
|---:|---|---|---|---:|---|
| `0` | `300` | `True` | `0xb1000020` | `0x900236ca` | `0xb1000024=0x000000e5` |
| `0` | `300` | `False` | `0xb1000020` | `0x90010598` | `0xb1000024=0x00000062` |
| `0` | `not 300` | `True` | `0xb1000020` | `0x800236ca` | `0xb1000024=0x000000e5` |
| `0` | `not 300` | `False` | `0xb1000020` | `0x80010598` | `0xb1000024=0x00000062` |
| `1` | `300` | `True` | `0xb1000020`, `0xb1000120` | `0x90028688` | `0xb1000024=0x000000e5`, `0xb1000124=0x000000e5` |
| `1` | `300` | `False` | `0xb1000020`, `0xb1000120` | `0x9001087d` | `0xb1000024=0x00000062`, `0xb1000124=0x00000062` |
| `1` | `not 300` | `True` | `0xb1000020`, `0xb1000120` | `0x80028688` | `0xb1000024=0x000000e5`, `0xb1000124=0x000000e5` |
| `1` | `not 300` | `False` | `0xb1000020`, `0xb1000120` | `0x8001087d` | `0xb1000024=0x00000062`, `0xb1000124=0x00000062` |

## Mode Register Rules

- registers `0xb100001c`, `0xb100011c`: clear mask 0x00203f00, set bit 0x100, then replace low six bits
  - `lane0_datastore_zero`: `0x0c`
  - `lane0_datastore_nonzero`: `0x05`
  - `lane1_datastore_zero`: `0x15`
  - `lane1_datastore_nonzero`: `0x08`
  - `additional_bits`: `clear 0x00180000 on both; set 0x00080000 on block B; set 0x00800000 on both`
- registers `0xb1000000`, `0xb1000100`: clear 0x100, wait busy, apply lane/mode masks, then set 0x100
  - `state_200_1`: `clear 0x03000000`
  - `state_200_2`: `write 0x01000000 under mask 0x03000000`
  - `state_200_4`: `write 0x02000000 under mask 0x03000000`
- registers `0xb1000010`, `0xb1000110`: write packed vertical offset: work +0x18 in high 16 bits, lane offset in low 16 bits
  - `lane0_low_bits`: `0x0068`
  - `lane1_low_bits`: `0x001e`

## Timing Table Blocks

| Table | Base | Words |
|---|---:|---|
| `single_plane_300_lane1_table` | `0x10005520` | `0x00000000` `0x00001fff` `0x00000000` `0x003fffff` |
| `single_plane_300_default_table` | `0x10005530` | `0x00000000` `0x0000007f` `0x00000000` `0x00000fff` |
| `single_plane_600_alt_table` | `0x100055a0` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `single_plane_600_two_output_table` | `0x10005580` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `single_plane_600_lane_table` | `0x10005540` | `0x00000000` `0xffffffff` `0x00000000` `0xffffffff` |
| `single_plane_1200_table` | `0x100055b0` | `0x00000000` `0x0003c0f0` `0x00000c00` `0x00000060` `0x00018000` `0x000fe1fc` `0x000000f0` `0x0003c000` `0x000000f8` `0x0007c000` `0x000003fe` `0x001ff000` `0x0007e3fe` `0x001ff1f8` `0x0007c0f8` `0x001ff3fe` |
| `two_plane_lane0_table` | `0x10005570` | `0x00000000` `0x00000007` `0x0000001f` `0x0000007f` |
| `two_plane_lane_table` | `0x10005550` | `0x00000000` `0x0000001f` `0x000001ff` `0x00001fff` |

## Evidence Checks

| Check | Status | Needle |
|---|---|---|
| `stride_from_work_84` | `present` | `uVar19 = (*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3` |
| `lane_count_from_work_22` | `present` | `uVar7 = (uint)*(ushort *)(param_1 + 0x22)` |
| `resolution_600_mode` | `present` | `if (sVar18 == 600)` |
| `resolution_1200_mode` | `present` | `if (sVar18 != 0x4b0) goto LAB_10014ae0` |
| `block_control_clear` | `present` | `*DAT_10006808 = *DAT_10006808 & 0xfffffeff` |
| `block_status_busy_wait_a` | `present` | `while ((uVar19 & 0x200) != 0)` |
| `block_status_busy_wait_b` | `present` | `} while ((*DAT_100067d8 & 0x200) != 0);` |
| `timing_register_a_write` | `present` | `*DAT_10006854 = uVar6` |
| `mode_register_low_bits` | `present` | `*DAT_10006884 = *DAT_10006884 & 0xffffffc0 \| local_30` |
| `table_zero_16_entries` | `present` | `while (DAT_1000680c = puVar1, DAT_10006898 = uVar7, uVar19 < 0x10)` |
| `single_plane_table_branch` | `present` | `if (*(short *)(param_1 + 0x22) == 1)` |
| `two_plane_table_branch` | `present` | `else if (*(short *)(param_1 + 0x22) == 2)` |
| `resolution_horizontal_mode` | `present` | `if (*(short *)(param_1 + 0x16) == 300)` |
| `vertical_packed_write_a` | `present` | `*DAT_100068d8 = (uint)*(ushort *)(param_1 + 0x18) << 0x10 \| uStack_2c` |
| `final_enable_bit` | `present` | `*puVar1 = *puVar1 \| 0x100` |

## Open Firmware Meaning

- Video prepare is not just a fixed register preamble; it branches on datastore entry 0x20, lane selector, plane count, and resolution.
- The 0xb1000400..0xb1000430 timing table writes are table-driven and must be understood before any printing firmware writes them.
- The safe current path remains USB-only; these tables are offline evidence for future hardware sequencing, not upload candidates.

