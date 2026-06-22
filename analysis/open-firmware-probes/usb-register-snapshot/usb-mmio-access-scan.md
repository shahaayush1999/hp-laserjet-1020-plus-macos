# HP 1020 USB MMIO Access Scan

- allowed mapped USB registers: `15`
- read accesses: `14`
- write accesses: `0`
- fail hits: `0`

| Severity | Access | Register | PC | Instruction | Description |
|---|---|---:|---:|---|---|
| `watch` | `read` | `0xb3000000` | `0x10005c96` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb300000c` | `0x10005ca6` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000028` | `0x10005cb6` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb300002c` | `0x10005cc6` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000200` | `0x10005cd6` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb300020c` | `0x10005ce6` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000214` | `0x10005cf6` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb300022c` | `0x10005d06` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000400` | `0x10005d16` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000408` | `0x10005d26` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000504` | `0x10005d36` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000508` | `0x10005d46` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb300050c` | `0x10005d56` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
| `watch` | `read` | `0xb3000510` | `0x10005d66` | `l32i.n	a3, a2, 0` | mapped USB MMIO read |
