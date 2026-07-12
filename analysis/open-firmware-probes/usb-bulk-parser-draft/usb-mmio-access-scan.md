# HP 1020 USB MMIO Access Scan

- allowed mapped USB registers: `21`
- read accesses: `17`
- write accesses: `30`
- fail hits: `0`

| Severity | Access | Register | PC | Instruction | Description |
|---|---|---:|---:|---|---|
| `watch` | `read` | `0xb3010000` | `0x10005cc2` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb300022c` | `0x10005cdd` | `s32i.n	a11, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000418` | `0x10005ce8` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3010000` | `0x10005cf0` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3010000` | `0x10005cfb` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000404` | `0x10005d03` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000404` | `0x10005d0e` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000220` | `0x10005d16` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000220` | `0x10005d21` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000200` | `0x10005d29` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000200` | `0x10005d34` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000234` | `0x10005d5f` | `s32i.n	a2, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000220` | `0x10005d67` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000220` | `0x10005d72` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000224` | `0x10005d8d` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000220` | `0x10005d95` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000220` | `0x10005da0` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000508` | `0x10005f11` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000510` | `0x10005f1c` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300050c` | `0x10005f27` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300022c` | `0x10005f32` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300020c` | `0x10005f3d` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300000c` | `0x10005f48` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300002c` | `0x10005f53` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000028` | `0x10005f5e` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000504` | `0x10005f6d` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000508` | `0x10005f78` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000510` | `0x10005f83` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300050c` | `0x10005f8e` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300022c` | `0x10005f99` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300020c` | `0x10005fa4` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300000c` | `0x10005faf` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300002c` | `0x10005fba` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000028` | `0x10005fc5` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000000` | `0x10006010` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000000` | `0x1000601b` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000014` | `0x10006026` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000000` | `0x1000602e` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000000` | `0x10006039` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000408` | `0x10006053` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10006064` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000224` | `0x1000607e` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000408` | `0x10006092` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x1000609c` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3010000` | `0x10006106` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000408` | `0x10006252` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10006260` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
