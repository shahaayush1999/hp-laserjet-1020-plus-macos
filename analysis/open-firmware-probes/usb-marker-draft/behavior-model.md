# HP 1020 USB Marker Draft Behavior Model

This is a host-side model of the marker draft's own setup/gate logic.
It mirrors the assembly-level decision boundary and does not touch hardware.

## Scenario Matrix

| Scenario | Result | Descriptor | Sequence | wLength | Response Bytes | Descriptor Word | Reason |
|---|---|---|---|---:|---:|---:|---|
| product string, sequence A gate, full host length | `marker_response` | `open marker product` | `sequence_a` | 255 | 38 | `0x08000026` |  |
| product string, sequence B gate, full host length | `marker_response` | `open marker product` | `sequence_b` | 255 | 38 | `0x08000026` |  |
| product string, both gates clear | `poll_continue` | `` | `` | 255 |  | `` | neither USB status gate is active; probe keeps polling |
| product string, clipped host length | `marker_response` | `open marker product` | `sequence_a` | 4 | 4 | `0x08000004` |  |
| device descriptor request | `marker_response` | `device` | `sequence_a` | 18 | 18 | `0x08000012` |  |
| configuration descriptor clipped to first 9 bytes | `marker_response` | `configuration` | `sequence_a` | 9 | 9 | `0x08000009` |  |
| language string descriptor | `marker_response` | `language` | `sequence_a` | 4 | 4 | `0x08000004` |  |
| manufacturer string descriptor | `marker_response` | `manufacturer` | `sequence_a` | 255 | 32 | `0x08000020` |  |
| class request | `poll_continue` | `` | `` |  |  | `` | not a standard IN GET_DESCRIPTOR request; probe keeps polling |

## Meaning

- Standard `GET_DESCRIPTOR` requests for device, configuration, language, manufacturer, and product descriptors reach the response path.
- Product string index 2 returns `HP1020 OPEN MARKER` instead of the stock product string.
- Response length is clipped to `min(wLength, descriptor length)`.
- `0xb3000408 & 0x6000` selects Sequence A.
- `0xb3000400 & 0x3` selects Sequence B when Sequence A is not selected.
- Matching requests copy the selected descriptor into the stock control-IN staging buffer `0x90022bd0`.
- The draft builds one four-word descriptor at `0x900226f0`, submits it through `0xb3000014`, and kicks `0xb3000000 |= 0x108`.
- If the setup packet or gate state does not match, the draft keeps polling without programming endpoint-0.
- This avoids the old one-shot false negative where an early non-product request could park the probe forever.

