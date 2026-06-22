# HP 1020 USB Marker Draft Behavior Model

This is a host-side model of the marker draft's own setup/gate logic.
It mirrors the assembly-level decision boundary and does not touch hardware.

## Scenario Matrix

| Scenario | Result | Sequence | wLength | Response Bytes | Reason |
|---|---|---|---:|---:|---|
| product string, sequence A gate, full host length | `marker_response` | `sequence_a` | 255 | 38 |  |
| product string, sequence B gate, full host length | `marker_response` | `sequence_b` | 255 | 38 |  |
| product string, both gates clear | `no_match` | `` | 255 |  | neither USB status gate is active |
| product string, clipped host length | `marker_response` | `sequence_a` | 4 | 4 |  |
| device descriptor request | `no_match` | `` |  |  | not GET_DESCRIPTOR string index 2 |
| class request | `no_match` | `` |  |  | not GET_DESCRIPTOR string index 2 |

## Meaning

- Only `GET_DESCRIPTOR` string index 2 reaches the marker response path.
- Response length is clipped to `min(wLength, 38)`.
- `0xb3000408 & 0x6000` selects Sequence A.
- `0xb3000400 & 0x3` selects Sequence B when Sequence A is not selected.
- If neither gate is active, the draft parks without programming endpoint-0.

