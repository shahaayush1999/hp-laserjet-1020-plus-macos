# HP 1020 USB Setup Source Model

This is an offline model. It does not contact the printer.

## Key Result

- likely direct setup-packet base: `0x90021348`
- stock descriptor branch reads offsets: `0x2, 0x4, 0x5, 0x6, 0x7`
- open marker draft reads offsets: `0x0, 0x1, 0x2, 0x3, 0x6, 0x7`
- separate event/envelope pointer register: `0xb3000214`

The vague blocker is now split in two: the direct setup-byte address is probably `0x90021348`, while live hardware still has to prove that this slot is populated after our uploaded firmware starts.

## Stock Firmware Setup Reads

| PC | Address | Offset | Field | Instruction |
|---:|---:|---:|---|---|
| `0x10009498` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x1000949e` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100094aa` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x100094ad` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x10009512` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x10009517` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x10009523` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x10009526` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100095dc` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x100095e2` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x1000969a` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x1000969d` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100095f9` | `0x9002134a` | `0x2` | wValue low / descriptor index | `l8ui a8,a4,0x2` |
| `0x1000961f` | `0x9002134c` | `0x4` | wIndex low | `l8ui a9,a4,0x4` |
| `0x10009631` | `0x9002134d` | `0x5` | wIndex high | `l8ui a8,a4,0x5` |
| `0x10009604` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x10009607` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x10009643` | `0x9002134a` | `0x2` | wValue low / descriptor index | `l8ui a8,a4,0x2` |
| `0x1000964f` | `0x9002134a` | `0x2` | wValue low / descriptor index | `l8ui a8,a4,0x2` |
| `0x10009682` | `0x9002134e` | `0x6` | wLength low | `l8ui a9,a4,0x6` |
| `0x10009688` | `0x9002134f` | `0x7` | wLength high | `l8ui a8,a4,0x7` |
| `0x1000969a` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x1000969d` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100096b5` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x100096b8` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100096c6` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x100096c9` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100096eb` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x100096f1` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |
| `0x100096fd` | `0x9002134e` | `0x6` | wLength low | `l8ui a8,a4,0x6` |
| `0x10009700` | `0x9002134f` | `0x7` | wLength high | `l8ui a9,a4,0x7` |

## Open Marker Draft Reads

| PC | Offset | Field | Instruction |
|---:|---:|---|---|
| `0x10005e25` | `0x0` | bmRequestType | `l8ui	a3, a2, 0` |
| `0x10005e36` | `0x1` | bRequest | `l8ui	a3, a2, 1` |
| `0x10005e43` | `0x2` | wValue low / descriptor index | `l8ui	a3, a2, 2` |
| `0x10005e4a` | `0x3` | wValue high / descriptor type | `l8ui	a3, a2, 3` |
| `0x10005eb7` | `0x6` | wLength low | `l8ui	a3, a11, 6` |
| `0x10005ebe` | `0x7` | wLength high | `l8ui	a3, a11, 7` |

## Event Pointer Boundary

- event pointer register: `0xb3000214`
- signature mask/value: `0xc0000000` / `0x80000000`

0xb3000214 is better treated as an event/envelope pointer. The stock code reads a pointer, then checks a high-bit event signature, rather than using it as the 8-byte setup packet itself.

## Practical Meaning

The current USB marker draft uses the direct 0x90021348 setup-buffer candidate and records bmRequestType, bRequest, wValue, and wLength before any USB writes.

Static analysis narrows the address, but cannot prove that the same RAM slot is populated after our uploaded firmware starts, or which controller gate sequence is live on real hardware.

