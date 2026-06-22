# HP 1020 USB Marker Draft Behavior Model

This is a host-side model of the marker draft's own setup/gate logic.
It mirrors the assembly-level decision boundary and does not touch hardware.

## Scenario Matrix

| Scenario | Result | Sequence | wLength | Response Bytes | Descriptor Word | Reason |
|---|---|---|---:|---:|---:|---|
| product string, sequence A gate, full host length | `marker_response` | `sequence_a` | 255 | 38 | `0x08000026` |  |
| product string, sequence B gate, full host length | `marker_response` | `sequence_b` | 255 | 38 | `0x08000026` |  |
| product string, both gates clear | `poll_continue` | `` | 255 |  | `` | neither USB status gate is active; probe keeps polling |
| product string, clipped host length | `marker_response` | `sequence_a` | 4 | 4 | `0x08000004` |  |
| device descriptor request | `poll_continue` | `` |  |  | `` | not GET_DESCRIPTOR string index 2; probe keeps polling |
| class request | `poll_continue` | `` |  |  | `` | not GET_DESCRIPTOR string index 2; probe keeps polling |

## Meaning

- Only `GET_DESCRIPTOR` string index 2 reaches the marker response path.
- Response length is clipped to `min(wLength, 38)`.
- `0xb3000408 & 0x6000` selects Sequence A.
- `0xb3000400 & 0x3` selects Sequence B when Sequence A is not selected.
- Matching requests copy the marker descriptor from `0x90003200` into the stock control-IN staging buffer `0x90022bd0`.
- The draft builds one four-word descriptor at `0x900226f0`, submits it through `0xb3000014`, and kicks `0xb3000000 |= 0x108`.
- If the setup packet or gate state does not match, the draft keeps polling without programming endpoint-0.
- This avoids the old one-shot false negative where an early non-product request could park the probe forever.

