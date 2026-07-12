# HP 1020 USB Bulk Parser Status Descriptor Check

- status: `pass`
- fail checks: `0`
- descriptor address: `0x10003400`
- descriptor bytes: `124`

| Check | Expected | Actual | Status | Description |
|---|---|---|---|---|
| `descriptor_bytes` | `7c 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 42 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 44 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 43 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 45 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 55 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00` | `7c 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 42 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 44 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 43 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 45 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 20 00 55 00 3d 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00 30 00` | `pass` | ELF contains the exact counter template |
| `descriptor_address` | `0x10003400` | `0x10003400` | `pass` | local writable descriptor address is fixed |
| `descriptor_writable` | `SHF_WRITE` | `flags=0x3` | `pass` | counter digits are patched before each product-string response |
| `length_constant` | `0x7c` | `0x7c` | `pass` | control response length matches the descriptor |
| `local_pointer` | `0x10003400` | `0x10003400` | `pass` | formatter patches the local RAM mapping |
| `hardware_alias` | `0x90003400` | `0x90003400` | `pass` | USB DMA reads the hardware alias |
| `counter_patch_calls` | `all five state/descriptor offsets` | `['write_hex_counter 0x60, 0x14', 'write_hex_counter 0x64, 0x2a', 'write_hex_counter 0x68, 0x40', 'write_hex_counter 0x6c, 0x56', 'write_hex_counter 0x70, 0x6c']` | `pass` | B/D/C/E/U counters are rendered as eight hexadecimal digits |
| `product_selects_status_alias` | `dynamic status alias` | `present` | `pass` | GET_DESCRIPTOR product string exposes current counters |
