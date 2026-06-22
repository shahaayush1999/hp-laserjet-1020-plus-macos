# HP 1020 Memory Boundary Scan

- recovered classified memory accesses: `25`
- fail hits: `0`

## Counts

- `local_probe_state` `write`: `11`
- `marker_descriptor_source` `read`: `1`
- `setup_packet_buffer` `read`: `6`
- `stock_response_state` `write`: `2`
- `usb_staging_buffer` `write`: `1`
- `usb_transfer_descriptor_ring` `write`: `4`

## Events

| Severity | Kind | Access | PC | Offset | Instruction | Description |
|---|---|---|---:|---:|---|---|
| `watch` | `local_probe_state` | `write` | `0x10005c96` | `0x40` | `s32i	a3, a4, 64` | local probe state buffer |
| `watch` | `stock_response_state` | `write` | `0x10005d6f` | `0x3c` | `s32i	a6, a4, 60` | stock USB response state object at 0x100212d4 |
| `watch` | `stock_response_state` | `write` | `0x10005d75` | `0x40` | `s32i	a3, a4, 64` | stock USB response state object at 0x100212d4 |
| `watch` | `marker_descriptor_source` | `read` | `0x10005d84` | `0x0` | `l8ui	a6, a2, 0` | open marker descriptor hardware alias at 0x90003200 |
| `watch` | `usb_staging_buffer` | `write` | `0x10005d87` | `0x0` | `s8i	a6, a3, 0` | stock USB control-IN staging buffer at 0x90022bd0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005d99` | `0x0` | `s32i.n	a3, a4, 0` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005d9d` | `0x4` | `s32i.n	a3, a4, 4` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005da2` | `0x8` | `s32i.n	a3, a4, 8` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005da6` | `0xc` | `s32i.n	a3, a4, 12` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `local_probe_state` | `write` | `0x10005ddf` | `0x44` | `s32i	a3, a4, 68` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005df8` | `0x0` | `s32i.n	a3, a4, 0` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e02` | `0x4` | `s32i.n	a3, a4, 4` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e07` | `0x0` | `l8ui	a3, a2, 0` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e0d` | `0x8` | `s32i.n	a3, a4, 8` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e18` | `0x1` | `l8ui	a3, a2, 1` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e1b` | `0xc` | `s32i.n	a3, a4, 12` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e25` | `0x2` | `l8ui	a3, a2, 2` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e28` | `0x10` | `s32i.n	a3, a4, 16` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e32` | `0x3` | `l8ui	a3, a2, 3` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e35` | `0x14` | `s32i.n	a3, a4, 20` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e3f` | `0x6` | `l8ui	a3, a2, 6` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e42` | `0x18` | `s32i.n	a3, a4, 24` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e46` | `0x7` | `l8ui	a3, a2, 7` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e49` | `0x1c` | `s32i.n	a3, a4, 28` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e59` | `0x20` | `s32i.n	a6, a4, 32` | local probe state buffer |
