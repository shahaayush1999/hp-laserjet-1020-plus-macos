# HP 1020 Memory Boundary Scan

- recovered classified memory accesses: `90`
- fail hits: `0`

## Counts

- `local_probe_state` `read`: `15`
- `local_probe_state` `write`: `57`
- `setup_packet_buffer` `read`: `4`
- `status_descriptor_local` `write`: `1`
- `stock_response_state` `write`: `2`
- `usb_bulk_receive_buffer` `read`: `1`
- `usb_bulk_transfer_descriptor` `read`: `1`
- `usb_bulk_transfer_descriptor` `write`: `4`
- `usb_staging_buffer` `write`: `1`
- `usb_transfer_descriptor_ring` `write`: `4`

## Events

| Severity | Kind | Access | PC | Offset | Instruction | Description |
|---|---|---|---:|---:|---|---|
| `watch` | `local_probe_state` | `write` | `0x10005c95` | `0x60` | `s32i	a3, a2, 96` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005c98` | `0x64` | `s32i	a3, a2, 100` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005c9b` | `0x68` | `s32i	a3, a2, 104` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005c9e` | `0x6c` | `s32i	a3, a2, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ca1` | `0x70` | `s32i	a3, a2, 112` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ca4` | `0x74` | `s32i	a3, a2, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ca7` | `0x78` | `s32i	a3, a2, 120` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005caa` | `0x7c` | `s32i	a3, a2, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005cad` | `0x80` | `s32i	a3, a2, 128` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005cb0` | `0x84` | `s32i	a3, a2, 132` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005cb3` | `0x88` | `s32i	a3, a2, 136` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005cb6` | `0x8c` | `s32i	a3, a2, 140` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005cb9` | `0x90` | `s32i	a3, a2, 144` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005cd4` | `0x94` | `s32i	a11, a2, 148` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005d3c` | `0x98` | `s32i	a3, a2, 152` | local probe state buffer |
| `watch` | `usb_bulk_transfer_descriptor` | `write` | `0x10005d4a` | `0x0` | `s32i.n	a3, a2, 0` | stock USB bulk OUT transfer descriptor at 0x90021370 |
| `watch` | `usb_bulk_transfer_descriptor` | `write` | `0x10005d4e` | `0x4` | `s32i.n	a3, a2, 4` | stock USB bulk OUT transfer descriptor at 0x90021370 |
| `watch` | `usb_bulk_transfer_descriptor` | `write` | `0x10005d53` | `0x8` | `s32i.n	a3, a2, 8` | stock USB bulk OUT transfer descriptor at 0x90021370 |
| `watch` | `usb_bulk_transfer_descriptor` | `write` | `0x10005d57` | `0xc` | `s32i.n	a3, a2, 12` | stock USB bulk OUT transfer descriptor at 0x90021370 |
| `watch` | `local_probe_state` | `read` | `0x10005d77` | `0x90` | `l32i	a3, a4, 144` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005d7c` | `0x90` | `s32i	a3, a4, 144` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005da5` | `0x64` | `l32i	a5, a4, 100` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005daa` | `0x64` | `s32i	a5, a4, 100` | local probe state buffer |
| `watch` | `usb_bulk_transfer_descriptor` | `read` | `0x10005db0` | `0x0` | `l32i.n	a3, a2, 0` | stock USB bulk OUT transfer descriptor at 0x90021370 |
| `watch` | `local_probe_state` | `read` | `0x10005dbe` | `0x6c` | `l32i	a5, a4, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005dc3` | `0x6c` | `s32i	a5, a4, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005dc8` | `0x88` | `s32i	a5, a4, 136` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005ddc` | `0x6c` | `l32i	a5, a4, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005de1` | `0x6c` | `s32i	a5, a4, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005de6` | `0x88` | `s32i	a6, a4, 136` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005de9` | `0x60` | `l32i	a5, a4, 96` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005def` | `0x60` | `s32i	a5, a4, 96` | local probe state buffer |
| `watch` | `usb_bulk_receive_buffer` | `read` | `0x10005dfe` | `0x0` | `l8ui	a2, a12, 0` | stock USB bulk OUT receive buffer at 0x900216f0 |
| `watch` | `local_probe_state` | `read` | `0x10005e08` | `0x74` | `l32i	a5, a4, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005e15` | `0x78` | `l32i	a7, a4, 120` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e1e` | `0x78` | `s32i	a7, a4, 120` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e2c` | `0x74` | `s32i	a5, a4, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e31` | `0x78` | `s32i	a5, a4, 120` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e34` | `0x7c` | `s32i	a5, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005e3c` | `0x7c` | `l32i	a7, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e4b` | `0x7c` | `s32i	a7, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e7b` | `0x80` | `s32i	a9, a4, 128` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e7e` | `0x84` | `s32i	a10, a4, 132` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e83` | `0x7c` | `s32i	a7, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e8e` | `0x74` | `s32i	a7, a4, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005e94` | `0x80` | `l32i	a7, a4, 128` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005e99` | `0x80` | `s32i	a7, a4, 128` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005ea2` | `0x84` | `l32i	a8, a4, 132` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005eaa` | `0x70` | `l32i	a7, a4, 112` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005eaf` | `0x70` | `s32i	a7, a4, 112` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005eb5` | `0x68` | `l32i	a7, a4, 104` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005eba` | `0x68` | `s32i	a7, a4, 104` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ec4` | `0x74` | `s32i	a7, a4, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ec9` | `0x7c` | `s32i	a7, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ed2` | `0x74` | `s32i	a7, a4, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ed5` | `0x78` | `s32i	a7, a4, 120` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ed8` | `0x7c` | `s32i	a7, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005edb` | `0x80` | `s32i	a7, a4, 128` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10005ee1` | `0x6c` | `l32i	a7, a4, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ee6` | `0x6c` | `s32i	a7, a4, 108` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005eeb` | `0x74` | `s32i	a7, a4, 116` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005eee` | `0x78` | `s32i	a7, a4, 120` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ef1` | `0x7c` | `s32i	a7, a4, 124` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005ef4` | `0x80` | `s32i	a7, a4, 128` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10005f02` | `0x40` | `s32i	a3, a4, 64` | local probe state buffer |
| `watch` | `stock_response_state` | `write` | `0x10005fcf` | `0x3c` | `s32i.n	a6, a4, 60` | stock USB response state object at 0x100212d4 |
| `watch` | `stock_response_state` | `write` | `0x10005fdd` | `0x40` | `s32i	a3, a4, 64` | stock USB response state object at 0x100212d4 |
| `watch` | `usb_staging_buffer` | `write` | `0x10005fec` | `0x0` | `s8i	a6, a3, 0` | stock USB control-IN staging buffer at 0x90022bd0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005ffb` | `0x0` | `s32i.n	a7, a4, 0` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10005fff` | `0x4` | `s32i.n	a3, a4, 4` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10006004` | `0x8` | `s32i.n	a3, a4, 8` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `usb_transfer_descriptor_ring` | `write` | `0x10006008` | `0xc` | `s32i.n	a3, a4, 12` | stock USB control-IN transfer descriptor ring at 0x900226f0 |
| `watch` | `local_probe_state` | `write` | `0x10006041` | `0x44` | `s32i	a3, a4, 68` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x1000604d` | `0x48` | `s32i	a3, a4, 72` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10006055` | `0x4c` | `s32i	a3, a4, 76` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10006066` | `0x50` | `s32i	a3, a4, 80` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10006083` | `0x8c` | `s32i	a3, a4, 140` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x10006097` | `0x0` | `s32i.n	a3, a4, 0` | local probe state buffer |
| `watch` | `local_probe_state` | `write` | `0x100060a1` | `0x4` | `s32i.n	a3, a4, 4` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x100060a8` | `0x0` | `l8ui	a3, a2, 0` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x100060ae` | `0x8` | `s32i.n	a3, a4, 8` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x100060b9` | `0x1` | `l8ui	a3, a2, 1` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x100060bc` | `0xc` | `s32i.n	a3, a4, 12` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x100060c6` | `0x2` | `l8ui	a3, a2, 2` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x100060c9` | `0x10` | `s32i.n	a3, a4, 16` | local probe state buffer |
| `watch` | `setup_packet_buffer` | `read` | `0x100060cd` | `0x3` | `l8ui	a3, a2, 3` | candidate USB setup packet buffer at 0x90021348 |
| `watch` | `local_probe_state` | `write` | `0x100060d0` | `0x14` | `s32i.n	a3, a4, 20` | local probe state buffer |
| `watch` | `local_probe_state` | `read` | `0x10006147` | `0x60` | `l32i	a3, a2, 96` | local probe state buffer |
| `watch` | `status_descriptor_local` | `write` | `0x10006163` | `0x0` | `s8i	a6, a4, 0` | open bulk-status descriptor local alias at 0x10003400 |
| `watch` | `local_probe_state` | `read` | `0x10006174` | `0x64` | `l32i	a3, a2, 100` | local probe state buffer |
