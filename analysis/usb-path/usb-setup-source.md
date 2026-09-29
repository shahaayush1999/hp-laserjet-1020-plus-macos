# HP 1020 USB Setup Source Model

This is an offline model. It does not contact the printer.

## Key Result

- file-backed initial request-byte address: `0x90021348`
- stock descriptor branch reads offsets: `0x2, 0x4, 0x5, 0x6, 0x7`
- open marker draft reads offsets: `0x0, 0x1, 0x2, 0x3, 0x6, 0x7`
- SETUP descriptor pointer register (SUBPTR): `0xb3000210`
- ordinary OUT0 descriptor pointer register (DESPTR): `0xb3000214`

Original initialization submits the SETUP record from global 0x1001bbc0 to OUT0 SUBPTR. The file-backed global is 0x90021340; request bytes are at record+8. Admission later reads status through SUBPTR but independently reloads the global for request fields. Pointer correspondence and stable ownership therefore need an explicit adapter contract.

Raw USB wValue/wIndex/wLength are little-endian pairs. Original 0x10009399..0x1000940b reverses wIndex and wLength in place before the listed stock dispatch reads. It preserves wValue bytes. The open marker reads raw bytes; its labels remain wire order. TinyUSB dcd_event_setup_received needs the original eight wire bytes, not the stock converted record.

## Stock Firmware Setup Reads

| PC | Address | Offset | Field | Instruction |
|---:|---:|---:|---|---|
| `0x10009498` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x1000949e` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100094aa` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x100094ad` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x10009512` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x10009517` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x10009523` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x10009526` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100095dc` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x100095e2` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x1000969a` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x1000969d` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100095f9` | `0x9002134a` | `0x2` | wValue low / descriptor index | `l8ui a8,a4,0x2` |
| `0x1000961f` | `0x9002134c` | `0x4` | wIndex high (after stock conversion) | `l8ui a9,a4,0x4` |
| `0x10009631` | `0x9002134d` | `0x5` | wIndex low (after stock conversion) | `l8ui a8,a4,0x5` |
| `0x10009604` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x10009607` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x10009643` | `0x9002134a` | `0x2` | wValue low / descriptor index | `l8ui a8,a4,0x2` |
| `0x1000964f` | `0x9002134a` | `0x2` | wValue low / descriptor index | `l8ui a8,a4,0x2` |
| `0x10009682` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a9,a4,0x6` |
| `0x10009688` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a8,a4,0x7` |
| `0x1000969a` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x1000969d` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100096b5` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x100096b8` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100096c6` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x100096c9` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100096eb` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x100096f1` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |
| `0x100096fd` | `0x9002134e` | `0x6` | wLength high (after stock conversion) | `l8ui a8,a4,0x6` |
| `0x10009700` | `0x9002134f` | `0x7` | wLength low (after stock conversion) | `l8ui a9,a4,0x7` |

## Open Marker Draft Reads

| PC | Offset | Field | Instruction |
|---:|---:|---|---|
| `0x10005e25` | `0x0` | bmRequestType | `l8ui	a3, a2, 0` |
| `0x10005e36` | `0x1` | bRequest | `l8ui	a3, a2, 1` |
| `0x10005e43` | `0x2` | wValue low / descriptor index | `l8ui	a3, a2, 2` |
| `0x10005e4a` | `0x3` | wValue high / descriptor type | `l8ui	a3, a2, 3` |
| `0x10005eb7` | `0x6` | wLength low | `l8ui	a3, a11, 6` |
| `0x10005ebe` | `0x7` | wLength high | `l8ui	a3, a11, 7` |

## Descriptor Admission Boundary

- owner mask/value: `0xc0000000` / `0x80000000`
- RX mask/value: `0x30000000` / `0x00000000`

SETUP uses SUBPTR 0xb3000210 and requires owner 2 plus RX status 0. DESPTR 0xb3000214 belongs to the separate ordinary OUT0 data/status descriptor. The high status bits denote descriptor ownership, not an event signature.

Original literals, initialization stores and the full admission/conversion body are byte-gated. The separate `setup-ingress.json` execution report checks supplied records in RAM; this generator does not execute hardware or reproduce a USB lifecycle.

## Practical Meaning

The current USB marker draft uses the direct 0x90021348 setup-buffer candidate and records bmRequestType, bRequest, wValue, and wLength before any USB writes.

Static analysis narrows the address, but cannot prove that the same RAM slot is populated after our uploaded firmware starts, or which controller gate sequence is live on real hardware.

