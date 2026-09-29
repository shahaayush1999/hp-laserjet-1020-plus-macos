# HP 1020 USB Interrupt Event Model

This is an offline model of the interrupt-side producer for USB event flags. It does not contact the printer.

## Key Result

- USB interrupt task `0x10008208` scans two groups of 16 event lanes.
- Each lane uses a `0x20`-byte hardware/status stride.
- Per-lane TDC status `0x400` can issue one wake; the OUT path can issue another with or without TDC.
- These event flags request another software check. They do not establish successful completion, buffer reuse or quiescence.
- Exact stock byte anchors and the pinned family header distinguish status acknowledgement from endpoint control requests. No IRQ or hardware path executes here.

## Resolved Constants

| Name | Value |
|---|---:|
| `irq_status` | `0xb300040c` |
| `irq_pending_lanes` | `0xb3000414` |
| `usb_global_status` | `0xb3010004` |
| `device_config_register` | `0xb3000400` |
| `masked_lane_word` | `0xb3000418` |
| `lane_bank0_base` | `0xb3000004` |
| `lane_bank1_base` | `0xb3000204` |
| `pending_transfer_list` | `0x10022740` |
| `transfer_state` | `0x100212d4` |
| `usb_event_flags` | `0x10021318` |
| `out0_control_register` | `0xb3000200` |
| `bulk_descriptor_pointer_global` | `0x1001bc48` |
| `descriptor_owner_mask` | `0xc0000000` |
| `descriptor_owner_done` | `0x80000000` |
| `bulk_available_size_word` | `0x1001bc50` |
| `bulk_source_offset_word` | `0x1001bc4c` |
| `bulk_next_offset_word` | `0x100216c0` |
| `bulk_buffer_base_word` | `0x1001bc40` |
| `bulk_suppress_copy_byte` | `0x1001bc6f` |
| `bulk_remaining_request_word` | `0x1001bc54` |
| `bulk_threshold_word` | `0x10021590` |
| `bulk_next_pointer_word` | `0x1001bc44` |
| `bulk_destination_offset_word` | `0x10021594` |

## Event Scan

- pending word: `0xb3000414`
- mask word: `0xb3000418`
- lane stride: `0x20`
- per-lane status bits: `0x200`, `0x80`, `0x40`, `0x30`, `0x400`
- TDC status bit: `0x400`
- sampled EPINT is acknowledged at `0x1000839b` before lane status is sampled at `0x100083eb`

| Bank | Lane Base | Event Bits |
|---:|---:|---|
| `0` | `0xb3000004` | `0x00000001..0x00008000` |
| `1` | `0xb3000204` | `0x00010000..0x80000000` |

## Bulk Receive Lane

- bank/lane: `1` / `1`
- event bit: `0x00020000`
- lane status register: `0xb3000224`
- lane control register: `0xb3000220`; SNAK request mask `0x80`
- status acknowledgement masks at the status register: `0x200`, `0x80`, `0x40`, `0x30`, `0x400`
- bulk descriptor global/initial pointer: `0x1001bc48` / `0x90021370`
- guard: additional receive processing: bank 1 lane 1 and bulk_done_byte != 0; common OUT wake does not require this guard

Bulk buffer fields updated by this branch:

| Field | Address |
|---|---:|
| `available_size_word` | `0x1001bc50` |
| `source_offset_word` | `0x1001bc4c` |
| `next_offset_word` | `0x100216c0` |
| `buffer_base_word` | `0x1001bc40` |
| `suppress_copy_byte` | `0x1001bc6f` |
| `remaining_request_word` | `0x1001bc54` |
| `threshold_word` | `0x10021590` |
| `next_pointer_word` | `0x1001bc44` |
| `destination_offset_word` | `0x10021594` |

## Event Flag Outputs

| Condition | Call | Meaning |
|---|---|---|
| per-lane status bit 0x400 and event bit != 0x2 | `event_flags_set(0x10021318, event_bit, 0)` | TDC-associated task wake before OUT processing; not a successful-transfer or ownership assertion |
| bank 1 transfer-service branch | `event_flags_set(0x10021318, event_bit, 0)` | common OUT task wake, including paths with no TDC or receive processing; may repeat the earlier lane wake |

## Special Cases

- event bit 0x2 has a pending-transfer-list path instead of the direct completion event set
- bank 1 lane 1 processes the bulk descriptor global 0x1001bc48, initially 0x90021370; 0x90022bc0 instead belongs to ordinary OUT0
- bank 1 lane 1 is bulk OUT: event bit 0x00020000, EPSTS 0xb3000224, EPCTL 0xb3000220
- USB2Thread separately waits on event bit 0x00010000
- control-IN data stage waits on event bit 0x00000001

## Open-Firmware Meaning

- Separate EPSTS acknowledgements at 0xb3000224 from SNAK control requests at 0xb3000220; the masks are not interchangeable.
- The first TDC-associated wake at 0x100084b4 precedes OUT processing. On applicable bulk paths, counter updates and rearm at 0x100086ad precede the later common OUT wake at 0x100086c0.
- A TinyUSB DCD must validate descriptor identity, ownership, count and errors, then forward at most one completion per original transfer. Stock event flags are wake hints that can coalesce or repeat.
- No IRQ execution, cache/DMA behavior, hardware ownership transition, abort completion or physical quiescence is established. Existing hardware access permissions are unchanged.

## Original Byte Checks

| Address | Bytes | Meaning |
|---:|---|---|
| `0x10005de8` | `b3000414` | irq_pending_lanes |
| `0x10005e00` | `b3000418` | masked_lane_word |
| `0x10005df4` | `b3000400` | device_config_register |
| `0x10005e04` | `b3000004` | lane_bank0_base |
| `0x10005e08` | `b3000204` | lane_bank1_base |
| `0x10005e18` | `10021318` | usb_event_flags |
| `0x10005e24` | `b3000200` | out0_control_register |
| `0x10005e2c` | `1001bc48` | bulk_descriptor_pointer_global |
| `0x10005e30` | `c0000000` | descriptor_owner_mask |
| `0x10005e34` | `80000000` | descriptor_owner_done |
| `0x10008219` | `8880` | l32i.n a8,a8,0: sample EPINT pending word |
| `0x1000821d` | `9810` | s32i.n a8,a1,0: preserve sampled pending word |
| `0x1000837e` | `c030` | movi.n a3,0: start IN bank |
| `0x10008380` | `c021` | movi.n a2,1: event-bit source |
| `0x10008382` | `d430` | mov.n a4,a3: event-bit bank offset starts zero |
| `0x1000838d` | `8a80` | l32i.n a10,a8,0: read endpoint mask |
| `0x1000838f` | `8e10` | l32i.n a14,a1,0: reload sampled EPINT |
| `0x1000839b` | `9e90` | s32i.n a14,a9,0: acknowledge sampled EPINT before lane reads |
| `0x100083c9` | `19f68e` | l32r a9,0x10005e04: IN status base |
| `0x100083e0` | `19f68a` | l32r a9,0x10005e08: OUT status base |
| `0x100083e3` | `0b5811` | slli a8,a5,5: lane stride 32 bytes |
| `0x100083eb` | `8670` | l32i.n a6,a7,0: sample lane status once |
| `0x100083ed` | `282a00` | movi a8,0x200: HE acknowledgement mask |
| `0x100083f0` | `786004` | bnone a6,a8,0x100083f8: HE absent skips its store only |
| `0x100083f6` | `9870` | s32i.n a8,a7,0: HE status acknowledgement |
| `0x100083f8` | `280a80` | movi a8,128: BNA acknowledgement mask |
| `0x100083fb` | `786005` | bnone a6,a8,0x10008404: BNA absent skips its store only |
| `0x10008401` | `287600` | s32i a8,a7,0: BNA status acknowledgement |
| `0x10008404` | `c480` | movi.n a8,64: IN status mask |
| `0x1000840c` | `9870` | s32i.n a8,a7,0: IN status acknowledgement |
| `0x10008439` | `c380` | movi.n a8,48: OUT type mask |
| `0x1000843b` | `086801` | and a8,a6,a8: retain sampled OUT status bits |
| `0x10008443` | `287600` | s32i a8,a7,0: OUT type status acknowledgement |
| `0x10008446` | `284a00` | movi a8,0x400: TDC acknowledgement mask |
| `0x10008449` | `78606a` | bnone a6,a8,0x100084b7: no TDC still reaches OUT service |
| `0x1000844f` | `9870` | s32i.n a8,a7,0: TDC status acknowledgement |
| `0x10008459` | `69724c` | bnei a7,2,0x100084a9: IN1 is the special list path |
| `0x100084a9` | `1af65b` | l32r a10,0x10005e18: first wake event object |
| `0x100084ac` | `db70` | mov.n a11,a7: first wake uses lane event bit |
| `0x100084b4` | `583e3d` | call8 0x10017dac: TDC-associated wake before OUT processing |
| `0x100084b7` | `683102` | beqi a3,1,0x100084bd: OUT service path |
| `0x100084c8` | `685102` | beqi a5,1,0x100084ce: OUT1 special receive processing |
| `0x100084cb` | `6001e1` | j 0x100086b0: other OUT lanes still wake |
| `0x100084d4` | `6481d8` | beqz a8,0x100086b0: inactive bulk path still wakes |
| `0x100084d7` | `18f653` | l32r a8,0x10005e24: OUT0 control base |
| `0x100084da` | `0b3911` | slli a9,a3,5: OUT bank value 1 selects control+0x20 |
| `0x100084dd` | `2a0a80` | movi a10,128: SNAK control request mask |
| `0x100084e0` | `a899` | add.n a9,a9,a8: OUT1 control address |
| `0x100084ea` | `0a8802` | or a8,a8,a10: add SNAK request |
| `0x100084f3` | `289600` | s32i a8,a9,0: SNAK request, not EPSTS acknowledgement |
| `0x100084f9` | `18f64c` | l32r a8,0x10005e2c: bulk descriptor global |
| `0x100084fc` | `8b80` | l32i.n a11,a8,0: bulk descriptor pointer |
| `0x100086ad` | `580011` | call8 0x100086f4: rearm on applicable path before common OUT wake |
| `0x100086b0` | `1af5da` | l32r a10,0x10005e18: common OUT wake object |
| `0x100086b3` | `a54b` | add.n a11,a4,a5: bank offset plus lane |
| `0x100086b5` | `00b104` | ssl a11: select event-bit position |
| `0x100086b8` | `002b1a` | sll a11,a2: event bit |
| `0x100086c0` | `583dba` | call8 0x10017dac: common OUT wake |
| `0x100086db` | `244c10` | addi a4,a4,16: OUT event offset 16 |
| `0x100086de` | `233c01` | addi a3,a3,1: advance bank |
| `0x1001bc48` | `90021370` | file-backed initial bulk descriptor pointer |

## Evidence Checks

- status: `pass`

| Status | Needle |
|---|---|
| `present` | `uVar7 = *DAT_10005de4` |
| `present` | `uVar12 = *DAT_10005de8` |
| `present` | `uVar13 = *DAT_10005e00` |
| `present` | `puVar10 = (uint *)(uVar8 * 0x20 + iVar11)` |
| `present` | `if ((uVar9 & 0x400) != 0)` |
| `present` | `FUN_10017dac(PTR_DAT_10005e18,iVar11,0)` |
| `present` | `if ((uVar8 == 1) && (*PTR_DAT_10005e20 != '\0'))` |
| `present` | `*(uint *)(DAT_10005e24 + 0x20) = *(uint *)(DAT_10005e24 + 0x20) \| 0x80` |
| `present` | `*(uint *)PTR_DAT_10005e38 = *(int *)PTR_DAT_10005e38 + uVar9` |
| `present` | `FUN_100086f4(*(undefined4 *)PTR_DAT_10005e40)` |
| `present` | `FUN_10017dac(PTR_DAT_10005e18,1 << 0x20 - (0x20 - (uVar6 + uVar8 & 0x1f)),0)` |

