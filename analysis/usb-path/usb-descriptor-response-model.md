# HP 1020 USB Descriptor Response Model

This is a byte-level model of standard USB `GET_DESCRIPTOR` responses using
the descriptors extracted from the stock firmware. It does not emulate USB
controller state, interrupts, DMA, endpoint setup, or timing.

## Response Cases

| Case | Setup Packet | Response Bytes | Source |
| --- | --- | ---: | --- |
| GET_DESCRIPTOR DEVICE | `80 06 00 01 00 00 12 00` | `18` | stock device descriptor at 0x1001bbe0 |
|  | response | `12 01 00 02 00 00 00 40 f0 03 17 2b 00 01 01 02 03 01` |  |
| GET_DESCRIPTOR CONFIG high-speed-style | `80 06 00 02 00 00 20 00` | `32` | stock config descriptor at 0x100034b0 |
|  | response | `09 02 20 00 01 01 00 c0 31 09 04 00 00 02 07 01 02 00 07 05 01 02 00 02 00 07 05 81 02 00 02 00` |  |
| GET_DESCRIPTOR CONFIG full-speed-style | `80 06 00 02 00 00 20 00` | `32` | stock config descriptor at 0x100034d0 |
|  | response | `09 02 20 00 01 01 00 c0 31 09 04 00 00 02 07 01 02 00 07 05 01 02 40 00 00 07 05 81 02 40 00 00` |  |
| GET_DESCRIPTOR STRING index 1 manufacturer | `80 06 01 03 09 04 ff 00` | `32` | stock ASCII identity string |
|  | response | `20 03 48 00 65 00 77 00 6c 00 65 00 74 00 74 00 2d 00 50 00 61 00 63 00 6b 00 61 00 72 00 64 00` |  |
| GET_DESCRIPTOR STRING index 2 product | `80 06 02 03 09 04 ff 00` | `34` | stock ASCII identity string |
|  | response | `22 03 48 00 50 00 20 00 4c 00 61 00 73 00 65 00 72 00 4a 00 65 00 74 00 20 00 31 00 30 00 32 00 30 00` |  |
| GET_DESCRIPTOR STRING index 0 language | `80 06 00 03 00 00 04 00` | `4` | standard USB English language descriptor model |
|  | response | `04 03 09 04` |  |
| FUTURE OPEN MARKER STRING example | `80 06 02 03 09 04 ff 00` | `38` | not stock firmware; byte model for a future open marker |
|  | response | `26 03 48 00 50 00 31 00 30 00 32 00 30 00 20 00 4f 00 50 00 45 00 4e 00 20 00 4d 00 41 00 52 00 4b 00 45 00 52 00` |  |

## Meaning

This narrows the future open USB marker target to a simple byte contract:

- receive a standard control request on endpoint 0
- recognize descriptor type/index
- return one of these byte strings, clipped to host `wLength`
- avoid all engine/video hardware

The hard part remains the USB controller plumbing around those bytes, not the
descriptor payload itself.

## Current Use

Use this model as a reference when reading the stock USB setup-handler blocks
or when designing a future open firmware USB-only marker. Do not treat it as
a hardware-ready firmware implementation.

