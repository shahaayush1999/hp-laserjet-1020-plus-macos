# HP 1020 Video Prepare Projection

This is a generated offline projection. It does not contact the printer.

## Result

- status: `pass`
- variants projected: `10`
- scenario rows: `80`

## Normal Path Summary

- All current generated host variants use ZJI_NBIE=1 and 600x600 declared resolution.
- For datastore 0x20 == 0 and work +0x36 == 0, the prepare code promotes the video state to a two-output 600dpi setup: state +0xc8/200 = 2, +0xf4 = 2, and +0xbc = stride*2.
- The exact vertical offset and remaining-unit fields still depend on work offsets not yet included in the print-path model.

## Variant Summary

| Case | Resolution | Raster X/Y | Video BPP | Work +0x84 | Stride +0xb8 | Callback 600dpi state |
|---|---|---|---:|---:|---:|---|
| `a4_2400x600` | `600x600` | `19072`/`6824` | `4` | `19072` | `2384` | `+0xc8/200=2, +0xf4=2, +0xbc=4768` |
| `a4_600x600` | `600x600` | `4768`/`6824` | `1` | `4864` | `608` | `+0xc8/200=2, +0xf4=2, +0xbc=1216` |
| `a4_cardstock_media` | `600x600` | `9536`/`6824` | `2` | `9600` | `1200` | `+0xc8/200=2, +0xf4=2, +0xbc=2400` |
| `a4_default` | `600x600` | `9536`/`6824` | `2` | `9600` | `1200` | `+0xc8/200=2, +0xf4=2, +0xbc=2400` |
| `a4_draft` | `600x600` | `9536`/`6824` | `2` | `9600` | `1200` | `+0xc8/200=2, +0xf4=2, +0xbc=2400` |
| `a4_logical_clip` | `600x600` | `9536`/`6824` | `2` | `9600` | `1200` | `+0xc8/200=2, +0xf4=2, +0xbc=2400` |
| `a4_manual_feed` | `600x600` | `9536`/`6824` | `2` | `9600` | `1200` | `+0xc8/200=2, +0xf4=2, +0xbc=2400` |
| `a4_two_copies` | `600x600` | `9536`/`6824` | `2` | `9600` | `1200` | `+0xc8/200=2, +0xf4=2, +0xbc=2400` |
| `legal_default` | `600x600` | `9816`/`8208` | `2` | `9856` | `1232` | `+0xc8/200=2, +0xf4=2, +0xbc=2464` |
| `letter_default` | `600x600` | `9816`/`6408` | `2` | `9856` | `1232` | `+0xc8/200=2, +0xf4=2, +0xbc=2464` |

## Setup Scenario Matrix

| Case | Datastore 0x20 zero | Lane | Secondary +0xec | Timing register value | Table | Table words |
|---|---|---:|---|---:|---|---|
| `a4_2400x600` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_2400x600` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_2400x600` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_2400x600` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_2400x600` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_2400x600` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_2400x600` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_2400x600` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_600x600` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_600x600` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_600x600` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_600x600` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_600x600` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_600x600` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_600x600` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_600x600` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_cardstock_media` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_cardstock_media` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_cardstock_media` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_cardstock_media` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_cardstock_media` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_cardstock_media` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_cardstock_media` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_cardstock_media` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_default` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_default` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_default` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_default` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_default` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_default` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_default` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_default` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_draft` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_draft` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_draft` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_draft` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_draft` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_draft` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_draft` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_draft` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_logical_clip` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_logical_clip` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_logical_clip` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_logical_clip` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_logical_clip` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_logical_clip` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_logical_clip` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_logical_clip` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_manual_feed` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_manual_feed` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_manual_feed` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_manual_feed` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_manual_feed` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_manual_feed` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_manual_feed` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_manual_feed` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_two_copies` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `a4_two_copies` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_two_copies` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_two_copies` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `a4_two_copies` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_two_copies` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `a4_two_copies` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `a4_two_copies` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `legal_default` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `legal_default` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `legal_default` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `legal_default` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `legal_default` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `legal_default` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `legal_default` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `legal_default` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `letter_default` | `True` | `0` | `False` | `0x800236ca` | `single_plane_600_two_output_table` | `0x00000000` `0x0000007f` `0x00000007` `0x00001fff` |
| `letter_default` | `True` | `0` | `True` | `0x800236ca` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `letter_default` | `True` | `1` | `False` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `letter_default` | `True` | `1` | `True` | `0x80028688` | `single_plane_600_two_output_table` | `0x00000000` `0x00000fff` `0x0000000f` `0x003fffff` |
| `letter_default` | `False` | `0` | `False` | `0x80010598` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `letter_default` | `False` | `0` | `True` | `0x80010598` | `single_plane_600_alt_table` | `0x00000000` `0x0000001f` `0x00000003` `0x000000ff` |
| `letter_default` | `False` | `1` | `False` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |
| `letter_default` | `False` | `1` | `True` | `0x8001087d` | `single_plane_600_lane_table` | `0x00000000` `0xffffffff` |

## Evidence Checks

| Check | Status | Needle |
|---|---|---|
| `stride_from_work_84` | `present` | `uVar19 = (*(int *)(param_1 + 0x84) + 0x1fU & 0xffffffe0) >> 3` |
| `callback_gate_datastore_and_work_36` | `present` | `if ((iVar5 == 0) && (*(short *)(param_1 + 0x36) == 0))` |
| `resolution_600_sets_two_output` | `present` | `if (sVar18 == 600)` |
| `resolution_1200_sets_four_output` | `present` | `if (sVar18 != 0x4b0) goto LAB_10014ae0` |
| `state_200_from_work_22` | `present` | `*(uint *)(puVar15 + 200) = uVar7` |
| `remaining_units_from_work_26` | `present` | `*(uint *)(puVar15 + 0xd0) = (uint)*(ushort *)(param_1 + 0x26)` |
| `mode_flag_from_work_74` | `present` | `if (*(char *)(param_1 + 0x74) == '\0')` |
| `single_plane_600_secondary_branch` | `present` | `if ((*(int *)PTR_DAT_100067c8 == 0) && (*(int *)(hp1020_video_state_ptr_word + 0xec) != 0))` |
| `single_plane_600_two_output_table` | `present` | `puVar11 = (undefined4 *)(PTR_DAT_100068b8 + *(int *)PTR_DAT_100067c8 * 0x10)` |
| `vertical_pack_write` | `present` | `*DAT_100068d8 = (uint)*(ushort *)(param_1 + 0x18) << 0x10 \| uStack_2c` |
| `stride_register_write` | `present` | `*puVar1 = *puVar1 & uVar7 \| uVar19` |

## Open Firmware Meaning

- This narrows the normal host-generated print cases to a small set of 600dpi setup scenarios instead of the whole firmware branch space.
- It still does not make 0xb100 safe to drive: vertical offsets, remaining-unit counts, and live status timing remain partly unmapped.
- The practical use is planning and comparison, not upload.
