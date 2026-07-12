# HP 1020 USB Bulk Configuration Descriptor Check

- status: `pass`
- fail checks: `0`

| Check | Expected | Actual | Status | Description |
|---|---|---|---|---|
| `descriptor_section_address` | `0x10003300` | `0x10003300` | `pass` | fixed local descriptor table address |
| `descriptor_section_size` | `0x78` | `0x78` | `pass` | device, two configurations, language, and manufacturer descriptors fit exactly |
| `high_speed_config_shape` | `09 02 20 00 / 32 bytes` | `09 02 20 00 / 32 bytes` | `pass` | high-speed configuration is complete |
| `full_speed_config_shape` | `09 02 20 00 / 32 bytes` | `09 02 20 00 / 32 bytes` | `pass` | full-speed configuration is complete |
| `high_speed_bulk_packets` | `[512, 512]` | `[512, 512]` | `pass` | both high-speed bulk endpoints advertise 512 bytes |
| `full_speed_bulk_packets` | `[64, 64]` | `[64, 64]` | `pass` | both full-speed bulk endpoints advertise 64 bytes |
| `high_speed_alias` | `0x90003314` | `0x90003314` | `pass` | DMA alias matches high-speed descriptor |
| `full_speed_alias` | `0x90003334` | `0x90003334` | `pass` | DMA alias matches full-speed descriptor |
| `speed_bit_branch` | `b3010000 bit 0 chooses full speed` | `present` | `pass` | configuration response follows the same speed bit as bulk endpoint setup |
