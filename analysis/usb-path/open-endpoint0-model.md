# HP 1020 Open Endpoint-0 Model

This is a host-side model of the pure USB control-request decision logic for a future open firmware marker.
It does not touch or emulate the `0xb300....` USB controller registers.

## What Is Solved

- Decode an 8-byte USB setup packet.
- Recognize standard `GET_DESCRIPTOR` requests.
- Select stock device/config/string descriptors, or an open product-string marker.
- Clip the response to host `wLength`.
- Return `stall` for unsupported requests.

## What Is Not Solved

- setup packet source is narrowed to 0x90021348, but live population after custom upload is unproven
- data-stage descriptor construction is modeled, but completion polling without ThreadX still needs live hardware confirmation
- engine/video MMIO remains out of scope
- this model is safe to run on the host only

## Scenario Matrix

| Speed | Marker | Setup | Result | Bytes | Source / Reason |
|---|---:|---|---|---:|---|
| `full` | `false` | device descriptor `80 06 00 01 00 00 12 00` | `data` | 18 | device |
| `full` | `false` | config header clip `80 06 00 02 00 00 09 00` | `data` | 9 | configuration-full |
| `full` | `false` | full config `80 06 00 02 00 00 20 00` | `data` | 32 | configuration-full |
| `full` | `false` | language string `80 06 00 03 00 00 04 00` | `data` | 4 | string-0 |
| `full` | `false` | manufacturer string `80 06 01 03 09 04 ff 00` | `data` | 32 | string-1 |
| `full` | `false` | product string `80 06 02 03 09 04 ff 00` | `data` | 34 | string-2 |
| `full` | `false` | unsupported class request `21 0a 00 00 00 00 00 00` | `stall` | 0 | unsupported request |
| `full` | `true` | device descriptor `80 06 00 01 00 00 12 00` | `data` | 18 | device |
| `full` | `true` | config header clip `80 06 00 02 00 00 09 00` | `data` | 9 | configuration-full |
| `full` | `true` | full config `80 06 00 02 00 00 20 00` | `data` | 32 | configuration-full |
| `full` | `true` | language string `80 06 00 03 00 00 04 00` | `data` | 4 | string-0 |
| `full` | `true` | manufacturer string `80 06 01 03 09 04 ff 00` | `data` | 32 | string-1 |
| `full` | `true` | product string `80 06 02 03 09 04 ff 00` | `data` | 38 | open-marker-product-string |
| `full` | `true` | unsupported class request `21 0a 00 00 00 00 00 00` | `stall` | 0 | unsupported request |
| `high` | `false` | device descriptor `80 06 00 01 00 00 12 00` | `data` | 18 | device |
| `high` | `false` | config header clip `80 06 00 02 00 00 09 00` | `data` | 9 | configuration-high |
| `high` | `false` | full config `80 06 00 02 00 00 20 00` | `data` | 32 | configuration-high |
| `high` | `false` | language string `80 06 00 03 00 00 04 00` | `data` | 4 | string-0 |
| `high` | `false` | manufacturer string `80 06 01 03 09 04 ff 00` | `data` | 32 | string-1 |
| `high` | `false` | product string `80 06 02 03 09 04 ff 00` | `data` | 34 | string-2 |
| `high` | `false` | unsupported class request `21 0a 00 00 00 00 00 00` | `stall` | 0 | unsupported request |
| `high` | `true` | device descriptor `80 06 00 01 00 00 12 00` | `data` | 18 | device |
| `high` | `true` | config header clip `80 06 00 02 00 00 09 00` | `data` | 9 | configuration-high |
| `high` | `true` | full config `80 06 00 02 00 00 20 00` | `data` | 32 | configuration-high |
| `high` | `true` | language string `80 06 00 03 00 00 04 00` | `data` | 4 | string-0 |
| `high` | `true` | manufacturer string `80 06 01 03 09 04 ff 00` | `data` | 32 | string-1 |
| `high` | `true` | product string `80 06 02 03 09 04 ff 00` | `data` | 38 | open-marker-product-string |
| `high` | `true` | unsupported class request `21 0a 00 00 00 00 00 00` | `stall` | 0 | unsupported request |

## Practical Meaning

The descriptor-response side is now small and deterministic enough to port to assembly later.
The remaining risky work is not choosing bytes; it is proving the narrowed setup-buffer candidate is populated after upload and replacing the stock ThreadX completion wait with a safe USB polling loop.

