# HP 1020 Endpoint-0 USB Write Sequence Scan

- recovered USB writes: `30`
- fail hits: `0`

## Sequence Counts

- `bulk_contract`: `8`
- `data_stage_submit`: `1`
- `sequence_a`: `6`
- `sequence_a,sequence_b`: `6`
- `sequence_b`: `6`

## Events

| Severity | Kind | PC | Register | Value | Sequence | Instruction | Description |
|---|---|---:|---:|---:|---|---|---|
| `watch` | `endpoint0_sequence_write` | `0x10005cdd` | `0xb300022c` | `0x00000040` | `sequence_a` | `s32i.n	a11, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `additional_contract_write` | `0x10005ce8` | `0xb3000418` | `0xfffcfffe` | `bulk_contract` | `s32i.n	a9, a8, 0` | USB event-lane mask word |
| `watch` | `additional_contract_or_write` | `0x10005cfb` | `0xb3010000` | `0x00000005` | `bulk_contract` | `s32i.n	a9, a8, 0` | HP USB wrapper control; bit meanings incompletely established |
| `watch` | `additional_contract_or_write` | `0x10005d0e` | `0xb3000404` | `0x00000008` | `bulk_contract` | `s32i.n	a9, a8, 0` | USB device control (DEVCTL), transmit-DMA enable request |
| `watch` | `additional_contract_or_write` | `0x10005d21` | `0xb3000220` | `0x00000100` | `bulk_contract` | `s32i.n	a9, a8, 0` | EP1 OUT control (SNAK/CNAK requests) |
| `watch` | `endpoint0_or_write` | `0x10005d34` | `0xb3000200` | `0x00000100` | `` | `s32i.n	a9, a8, 0` | EP0 OUT control CNAK request; not interrupt acknowledgement or DMA quiescence |
| `watch` | `additional_contract_write` | `0x10005d5f` | `0xb3000234` | `0x90021370` | `bulk_contract` | `s32i.n	a2, a8, 0` | bulk OUT receive descriptor submit register |
| `watch` | `additional_contract_or_write` | `0x10005d72` | `0xb3000220` | `0x00000100` | `bulk_contract` | `s32i.n	a9, a8, 0` | EP1 OUT control (SNAK/CNAK requests) |
| `watch` | `additional_contract_write` | `0x10005d8d` | `0xb3000224` | `0x00000400` | `bulk_contract` | `s32i.n	a9, a8, 0` | bank-1 lane-1 bulk OUT status |
| `watch` | `additional_contract_or_write` | `0x10005da0` | `0xb3000220` | `0x00000080` | `bulk_contract` | `s32i.n	a9, a8, 0` | EP1 OUT control (SNAK/CNAK requests) |
| `watch` | `endpoint0_sequence_write` | `0x10005f11` | `0xb3000508` | `0x020000c1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f1c` | `0xb3000510` | `0x020080c1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f27` | `0xb300050c` | `0x020000d1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f32` | `0xb300022c` | `0x00000040` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f3d` | `0xb300020c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f48` | `0xb300000c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f53` | `0xb300002c` | `0x00000040` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f5e` | `0xb3000028` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f6d` | `0xb3000504` | `0x02000000` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f78` | `0xb3000508` | `0x100000c1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f83` | `0xb3000510` | `0x100080c1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f8e` | `0xb300050c` | `0x100000d1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005f99` | `0xb300022c` | `0x00000200` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005fa4` | `0xb300020c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005faf` | `0xb300000c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005fba` | `0xb300002c` | `0x00000200` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005fc5` | `0xb3000028` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_or_write` | `0x1000601b` | `0xb3000000` | `0x00000002` | `` | `s32i.n	a9, a8, 0` | EP0 IN control F/flush request under the pinned family layout; no flush-completion proof |
| `watch` | `endpoint0_sequence_write` | `0x10006026` | `0xb3000014` | `0x900226f0` | `data_stage_submit` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_or_write` | `0x10006039` | `0xb3000000` | `0x00000108` | `` | `s32i.n	a9, a8, 0` | EP0 IN control CNAK plus P/poll-demand request; not a completion acknowledgement |
