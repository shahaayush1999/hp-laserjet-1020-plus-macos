# HP 1020 Memory Boundary Scan

- recovered classified memory accesses: `19`
- fail hits: `0`

## Counts

- `local_probe_state` `write`: `11`
- `setup_packet_buffer` `read`: `6`
- `stock_response_state` `write`: `2`

## Events

| Severity | Kind | Access | PC | Offset | Instruction | Description |
|---|---|---|---:|---:|---|---|
| `watch` | `local_probe_state` | `write` | `0x10005c96` | `0x40` | `s32i	a3, a4, 64` | local probe state buffer |
| `watch` | `stock_response_state` | `write` | `0x10005d6f` | `0x3c` | `s32i.n	a6, a4, 60` | stock USB response state object at 0x100212d4 |
| `watch` | `stock_response_state` | `write` | `0x10005d74` | `0x40` | `s32i	a3, a4, 64` | stock USB response state object at 0x100212d4 |
| `watch` | `local_probe_state` | `write` | `0x10005d90` | `0x44` | `s32i	a3, a4, 68` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005da8` | `0x0` | `s32i.n	a3, a4, 0` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005db2` | `0x4` | `s32i.n	a3, a4, 4` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005db7` | `0x0` | `l8ui	a3, a2, 0` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005dbd` | `0x8` | `s32i.n	a3, a4, 8` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005dc8` | `0x1` | `l8ui	a3, a2, 1` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005dcb` | `0xc` | `s32i.n	a3, a4, 12` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005dd5` | `0x2` | `l8ui	a3, a2, 2` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005dd8` | `0x10` | `s32i.n	a3, a4, 16` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005de2` | `0x3` | `l8ui	a3, a2, 3` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005de5` | `0x14` | `s32i.n	a3, a4, 20` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005def` | `0x6` | `l8ui	a3, a2, 6` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005df2` | `0x18` | `s32i.n	a3, a4, 24` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005df6` | `0x7` | `l8ui	a3, a2, 7` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005df9` | `0x1c` | `s32i.n	a3, a4, 28` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e09` | `0x20` | `s32i.n	a6, a4, 32` | local probe state buffer |
