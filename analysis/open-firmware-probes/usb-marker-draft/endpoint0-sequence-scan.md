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
| `watch` | `endpoint0_sequence_write` | `0x10005cb1` | `0xb3000508` | `0x020000c1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cbc` | `0xb3000510` | `0x020080c1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cc7` | `0xb300050c` | `0x020000d1` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cd2` | `0xb300022c` | `0x00000040` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cdd` | `0xb300020c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005ce8` | `0xb300000c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cf3` | `0xb300002c` | `0x00000040` | `sequence_a` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005cfe` | `0xb3000028` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d0d` | `0xb3000504` | `0x02000000` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d18` | `0xb3000508` | `0x100000c1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d23` | `0xb3000510` | `0x100080c1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d2e` | `0xb300050c` | `0x100000d1` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d39` | `0xb300022c` | `0x00000200` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d44` | `0xb300020c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d4f` | `0xb300000c` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d5a` | `0xb300002c` | `0x00000200` | `sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_sequence_write` | `0x10005d65` | `0xb3000028` | `0x00000040` | `sequence_a,sequence_b` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_or_write` | `0x10005db9` | `0xb3000000` | `0x00000002` | `` | `s32i.n	a9, a8, 0` | begin/control-IN data stage |
| `watch` | `endpoint0_sequence_write` | `0x10005dc4` | `0xb3000014` | `0x900226f0` | `data_stage_submit` | `s32i.n	a9, a8, 0` | expected endpoint-0 sequence write |
| `watch` | `endpoint0_or_write` | `0x10005dd7` | `0xb3000000` | `0x00000108` | `` | `s32i.n	a9, a8, 0` | transfer descriptor kick pattern seen in stock data stage |
