# HP 1020 Memory Boundary Scan

- recovered classified memory accesses: `24`
- fail hits: `0`

## Counts

- `local_probe_state` `write`: `11`
- `setup_packet_buffer` `read`: `6`
- `stock_response_state` `write`: `2`
- `usb_staging_buffer` `write`: `1`
- `usb_transfer_descriptor_ring` `write`: `4`

## Events

| Severity | Kind | Access | PC | Offset | Instruction | Description |
|---|---|---|---:|---:|---|---|
| `watch` | `local_probe_state` | `write` | `0x10005c96` | `0x40` | `s32i	a3, a4, 64` | local probe state buffer |
| `watch` | `stock_response_state` | `write` | `0x10005d63` | `0x3c` | `s32i.n	a6, a4, 60` | stock USB response state object at 0x100212d4 |
| `watch` | `stock_response_state` | `write` | `0x10005d71` | `0x40` | `s32i	a3, a4, 64` | stock USB response state object at 0x100212d4 |
| `watch` | `usb_staging_buffer` | `write` | `0x10005d80` | `0x0` | `s8i	a6, a3, 0` | stock USB control-IN staging buffer at 0x90022bd0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005d8f` | `0x0` | `s32i.n	a7, a4, 0` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005d93` | `0x4` | `s32i.n	a3, a4, 4` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005d98` | `0x8` | `s32i.n	a3, a4, 8` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005d9c` | `0xc` | `s32i.n	a3, a4, 12` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `local_probe_state` | `write` | `0x10005dd5` | `0x44` | `s32i	a3, a4, 68` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005df0` | `0x0` | `s32i.n	a3, a4, 0` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005dfa` | `0x4` | `s32i.n	a3, a4, 4` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e01` | `0x0` | `l8ui	a3, a2, 0` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e07` | `0x8` | `s32i.n	a3, a4, 8` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e12` | `0x1` | `l8ui	a3, a2, 1` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e15` | `0xc` | `s32i.n	a3, a4, 12` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e1f` | `0x2` | `l8ui	a3, a2, 2` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e22` | `0x10` | `s32i.n	a3, a4, 16` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e26` | `0x3` | `l8ui	a3, a2, 3` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e29` | `0x14` | `s32i.n	a3, a4, 20` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e8e` | `0x6` | `l8ui	a3, a11, 6` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e91` | `0x18` | `s32i.n	a3, a4, 24` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x10005e95` | `0x7` | `l8ui	a3, a11, 7` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x10005e98` | `0x1c` | `s32i.n	a3, a4, 28` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ea8` | `0x20` | `s32i.n	a6, a4, 32` | local probe state buffer |
