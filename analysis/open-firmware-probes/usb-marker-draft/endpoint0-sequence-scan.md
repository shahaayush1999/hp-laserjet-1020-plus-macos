# HP 1020 Endpoint-0 USB Write Sequence Scan

- recovered USB writes: `20`
- fail hits: `0`

## Sequence Counts

- `data_stage_submit`: `1`
- `sequence_a`: `5`
- `sequence_a,sequence_b`: `6`
- `sequence_b`: `6`

## Events

| Severity | Kind | PC | Register | Value | Sequence | Instruction | Description |
|---|---|---:|---:|---:|---|---|---|
| `watch` | `endpoint0_sequence_write` | `0x10005ca5` | `0xb3000508` | `0x020000c1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cb0` | `0xb3000510` | `0x020080c1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cbb` | `0xb300050c` | `0x020000d1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cc6` | `0xb300022c` | `0x00000040` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cd1` | `0xb300020c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cdc` | `0xb300000c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005ce7` | `0xb300002c` | `0x00000040` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cf2` | `0xb3000028` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d01` | `0xb3000504` | `0x02000000` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d0c` | `0xb3000508` | `0x100000c1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d17` | `0xb3000510` | `0x100080c1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d22` | `0xb300050c` | `0x100000d1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d2d` | `0xb300022c` | `0x00000200` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d38` | `0xb300020c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d43` | `0xb300000c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d4e` | `0xb300002c` | `0x00000200` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d59` | `0xb3000028` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_or_write` | `0x10005daf` | `0xb3000000` | `0x00000002` | `` | `s32i.n	a9, a8, 0` | EP0 IN control F/flush request under the pinned family layout; no flush-completion proof |
| `watch` | `endpoint0_sequence_write` | `0x10005dba` | `0xb3000014` | `0x900226f0` | `data_stage_submit` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_or_write` | `0x10005dcd` | `0xb3000000` | `0x00000108` | `` | `s32i.n	a9, a8, 0` | EP0 IN control CNAK plus P/poll-demand request; not a completion acknowledgement |
