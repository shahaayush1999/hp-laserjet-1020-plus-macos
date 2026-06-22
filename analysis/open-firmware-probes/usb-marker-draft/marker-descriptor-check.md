# HP 1020 Marker Descriptor Check

- fail hits: `0`
- descriptor vaddr: `0x10003200`
- descriptor bytes: `38`
- descriptor hex: `26 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 4f 00 50 00 45 00 4e 00 20 00 4d 00 41 00 52 00 4b 00 45 00 52 00`

| Severity | Check | Expected | Actual | Description |
|---|---|---:|---:|---|
| `watch` | `descriptor_bytes` | `26 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 4f 00 50 00 45 00 4e 00 20 00 4d 00 41 00 52 00 4b 00 45 00 52 00` | `26 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 4f 00 50 00 45 00 4e 00 20 00 4d 00 41 00 52 00 4b 00 45 00 52 00` | embedded USB string descriptor must equal HP1020 OPEN MARKER |
| `watch` | `descriptor_size` | `38` | `38` | section size must match descriptor length |
| `watch` | `length_constant` | `0x00000026` | `0x00000026` | firmware length constant must match descriptor length |
| `watch` | `hardware_alias_pointer` | `0x90003200` | `0x90003200` | USB response pointer should use the stock 0x90000000 hardware alias convention |
