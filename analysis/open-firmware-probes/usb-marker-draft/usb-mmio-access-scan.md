# HP 1020 USB MMIO Access Scan

- allowed mapped USB registers: `15`
- read accesses: `6`
- write accesses: `20`
- fail hits: `0`

| Severity | Access | Register | PC | Instruction | Description |
|---|---|---:|---:|---|---|
| `watch` | `write` | `0xb3000508` | `0x10005cb1` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000510` | `0x10005cbc` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300050c` | `0x10005cc7` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300022c` | `0x10005cd2` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300020c` | `0x10005cdd` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300000c` | `0x10005ce8` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300002c` | `0x10005cf3` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000028` | `0x10005cfe` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000504` | `0x10005d0d` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000508` | `0x10005d18` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000510` | `0x10005d23` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300050c` | `0x10005d2e` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300022c` | `0x10005d39` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300020c` | `0x10005d44` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300000c` | `0x10005d4f` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb300002c` | `0x10005d5a` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000028` | `0x10005d65` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000000` | `0x10005dae` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000000` | `0x10005db9` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `write` | `0xb3000014` | `0x10005dc4` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000000` | `0x10005dcc` | `l32i.n	a9, a8, 0` | mapped USB MMIO read |
| `watch` | `write` | `0xb3000000` | `0x10005dd7` | `s32i.n	a9, a8, 0` | mapped USB MMIO write |
| `watch` | `read` | `0xb3000408` | `0x10005df3` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10005dfd` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000408` | `0x10005e5e` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10005e6c` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
