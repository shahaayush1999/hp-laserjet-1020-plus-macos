# HP 1020 USB MMIO Access Scan

- allowed mapped USB registers: `15`
- read accesses: `6`
- write accesses: `20`
- fail hits: `0`

| Severity | Access | Register | PC | Instruction | Description |
|---|---|---:|---:|---|---|
| `watch` | `write` | `0xb3000508` | `0x10005ca5` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000510` | `0x10005cb0` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300050c` | `0x10005cbb` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300022c` | `0x10005cc6` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300020c` | `0x10005cd1` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300000c` | `0x10005cdc` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300002c` | `0x10005ce7` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000028` | `0x10005cf2` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000504` | `0x10005d01` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000508` | `0x10005d0c` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000510` | `0x10005d17` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300050c` | `0x10005d22` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300022c` | `0x10005d2d` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300020c` | `0x10005d38` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300000c` | `0x10005d43` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300002c` | `0x10005d4e` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000028` | `0x10005d59` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000000` | `0x10005da3` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000000` | `0x10005dae` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000014` | `0x10005db9` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000000` | `0x10005dc1` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000000` | `0x10005dcc` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000408` | `0x10005deb` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10005df5` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000408` | `0x10005e56` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10005e64` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
