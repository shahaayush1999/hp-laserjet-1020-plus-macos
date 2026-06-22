# HP 1020 USB MMIO Register Map

This is a generated map of USB-controller register evidence from
`analysis/usb-path/internal-blocks.md`. It narrows the open-firmware
USB-marker problem to the registers the stock endpoint-0 path actually
touches.

## Plain-English Summary

The descriptor bytes are no longer the mystery. The remaining USB work is
figuring out the small controller handshake around setup packets and
control-IN responses.

The important register family is `0xb300....`. Static evidence clusters it
into four groups:

- setup/status gates: `0xb3000400`, `0xb3000408`
- descriptor/control register programming: `0xb3000504`, `0xb3000508`, `0xb300050c`, `0xb3000510`
- event/ack/kick registers: `0xb3000000`, `0xb300000c`, `0xb3000028`, `0xb300002c`, `0xb3000200`, `0xb300020c`, `0xb300022c`
- setup/event buffer pointer: `0xb3000214`

## Register Summary

| Register | Working Name | Reads | Writes | Params | Main Meaning |
|---:|---|---:|---:|---:|---|
| `0xb3000000` | main USB command/status kick | 3 | 2 | 0 | Read/modify/write control bits. Evidence includes bit 0x2 before control-IN staging and bit 0x1 after setup completion; decompiler also shows 0x108 to start transfer descriptors. |
| `0xb300000c` | endpoint/request ack register | 0 | 2 | 0 | Written with 0x40 during descriptor request paths. |
| `0xb3000014` | control-IN descriptor submit register | 0 | 2 | 0 | Written with the transfer descriptor ring pointer before the 0x108 control-IN kick. |
| `0xb3000028` | post-response ack/kick register | 0 | 1 | 0 | Written after descriptor-specific setup and before calling the control-IN sender. |
| `0xb300002c` | endpoint/request ack register | 0 | 2 | 0 | Written with 0x40 or 0x200 in descriptor request paths. |
| `0xb3000200` | USB event/interrupt ack register | 2 | 2 | 0 | Read/modify/write with event bits 0x1 and 0x100. |
| `0xb300020c` | endpoint/request ack register | 0 | 2 | 0 | Written with 0x40 in descriptor request paths. |
| `0xb3000214` | USB event/setup buffer pointer | 1 | 0 | 0 | Read as a pointer, then dereferenced as bytes that are compared against an event signature. |
| `0xb300022c` | endpoint/request ack register | 0 | 2 | 0 | Written with 0x40 or 0x200 in descriptor request paths. |
| `0xb3000400` | control/setup status gate | 2 | 0 | 0 | Read before choosing descriptor response source. Low two bits are tested. |
| `0xb3000408` | control/setup status gate | 3 | 0 | 0 | Read and tested against a mask before choosing descriptor response source. |
| `0xb3000504` | control endpoint descriptor/config register | 0 | 1 | 0 | Written with a constant/pointer-like value during one descriptor branch. |
| `0xb3000508` | control endpoint descriptor/config register | 0 | 2 | 0 | Written during both device/config descriptor branches. |
| `0xb300050c` | control endpoint descriptor/config register | 0 | 2 | 1 | Written during descriptor branches and passed into the control-IN sender path. |
| `0xb3000510` | control endpoint descriptor/config register | 0 | 2 | 1 | Written during descriptor branches and passed into the control-IN sender path. |

## Write Constants and Bit Operations

| Register | Evidence |
|---:|---|
| `0xb3000000` | `0x10008c3f` ORs `0x2` before write |
| `0xb300000c` | `0x100094fc` writes `0x40`; `0x10009582` writes `0x40` |
| `0xb3000014` | `0x10008ce4` submits pointer `0x900226f0`; `0x10008e50` submits pointer `0x900226f0` |
| `0xb3000028` | no immediate constant inferred from local block |
| `0xb300002c` | `0x10009507` writes `0x40`; `0x10009590` writes `0x200` |
| `0xb3000200` | `0x1000990f` ORs `0x100` before write |
| `0xb300020c` | `0x100094f7` writes `0x40`; `0x1000957d` writes `0x40` |
| `0xb3000214` | no immediate constant inferred from local block |
| `0xb300022c` | `0x100094ec` writes `0x40`; `0x10009570` writes `0x200` |
| `0xb3000400` | no immediate constant inferred from local block |
| `0xb3000408` | no immediate constant inferred from local block |
| `0xb3000504` | no immediate constant inferred from local block |
| `0xb3000508` | no immediate constant inferred from local block |
| `0xb300050c` | no immediate constant inferred from local block |
| `0xb3000510` | no immediate constant inferred from local block |

## Per-Register Details

### `0xb3000000` - main USB command/status kick

Read/modify/write control bits. Evidence includes bit 0x2 before control-IN staging and bit 0x1 after setup completion; decompiler also shows 0x108 to start transfer descriptors.

Open-firmware relevance: core endpoint-0 bring-up and transmit kick.

Pointer/literal sources seen before access:

- `0x10005e90` (5)

Representative events:

- `0x10009877` READ in 0x1000985f..0x10009883: `l32i.n a8,a9,0x0`
- `0x1000987f` WRITE in 0x1000985f..0x10009883: `s32i.n a8,a9,0x0`
- `0x10008c35` READ in 0x10008c24..0x10008c4e: `l32i.n a8,a4,0x0`
- `0x10008c3f` WRITE in 0x10008c24..0x10008c4e: `s32i.n a8,a4,0x0`
- `0x10008c4a` READ in 0x10008c24..0x10008c4e: `l32i.n a8,a4,0x0`

### `0xb300000c` - endpoint/request ack register

Written with 0x40 during descriptor request paths.

Open-firmware relevance: likely needed to acknowledge/advance setup handling.

Pointer/literal sources seen before access:

- `0x10005e9c` (2)

Representative events:

- `0x100094fc` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a9,0x0`
- `0x10009582` WRITE in 0x10009534..0x10009593: `s32i.n a6,a9,0x0`

### `0xb3000014` - control-IN descriptor submit register

Written with the transfer descriptor ring pointer before the 0x108 control-IN kick.

Open-firmware relevance: needed to submit endpoint-0 transfer descriptors without the stock helper.

Pointer/literal sources seen before access:

- `0x10005ea0` (2)

Representative events:

- `0x10008ce4` WRITE in 0x10008c24..0x10008eef: `*DAT_10005ea0 = *(undefined4 *)PTR_DAT_10005e98`
- `0x10008e50` WRITE in 0x10008c24..0x10008eef: `*DAT_10005ea0 = *(undefined4 *)PTR_DAT_10005e98`

### `0xb3000028` - post-response ack/kick register

Written after descriptor-specific setup and before calling the control-IN sender.

Open-firmware relevance: likely needed after preparing a descriptor response.

Representative events:

- `0x10009597` WRITE in 0x10009594..0x100095b2: `s32i.n a6,a9,0x0`

### `0xb300002c` - endpoint/request ack register

Written with 0x40 or 0x200 in descriptor request paths.

Open-firmware relevance: likely tied to full-speed/high-speed or direction-specific completion.

Pointer/literal sources seen before access:

- `0x10005ee0` (2)

Representative events:

- `0x10009507` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a8,0x0`
- `0x10009590` WRITE in 0x10009534..0x10009593: `s32i.n a6,a8,0x0`

### `0xb3000200` - USB event/interrupt ack register

Read/modify/write with event bits 0x1 and 0x100.

Open-firmware relevance: needed to acknowledge controller events without the stock interrupt/thread queue.

Pointer/literal sources seen before access:

- `0x10005e24` (4)

Representative events:

- `0x10009865` READ in 0x1000985f..0x10009883: `l32i.n a8,a6,0x0`
- `0x10009870` WRITE in 0x1000985f..0x10009883: `s32i.n a8,a6,0x0`
- `0x10009905` READ in 0x100098f9..0x10009916: `l32i.n a8,a6,0x0`
- `0x1000990f` WRITE in 0x100098f9..0x10009916: `s32i.n a8,a6,0x0`

### `0xb300020c` - endpoint/request ack register

Written with 0x40 in descriptor request paths.

Open-firmware relevance: likely needed to clear/advance control endpoint state.

Pointer/literal sources seen before access:

- `0x10005ee4` (2)

Representative events:

- `0x100094f7` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a8,0x0`
- `0x1000957d` WRITE in 0x10009534..0x10009593: `s32i.n a6,a8,0x0`

### `0xb3000214` - USB event/setup buffer pointer

Read as a pointer, then dereferenced as bytes that are compared against an event signature.

Open-firmware relevance: plausible source of setup/event packet metadata.

Pointer/literal sources seen before access:

- `0x10005ef8` (1)

Representative events:

- `0x10009896` READ in 0x10009890..0x100098c1: `l32i.n a11,a8,0x0`

### `0xb300022c` - endpoint/request ack register

Written with 0x40 or 0x200 in descriptor request paths.

Open-firmware relevance: likely tied to endpoint request acknowledgement.

Pointer/literal sources seen before access:

- `0x10005f08` (2)

Representative events:

- `0x100094ec` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a9,0x0`
- `0x10009570` WRITE in 0x10009534..0x10009593: `s32i.n a6,a9,0x0`

### `0xb3000400` - control/setup status gate

Read before choosing descriptor response source. Low two bits are tested.

Open-firmware relevance: likely tells whether a setup/status condition is ready.

Pointer/literal sources seen before access:

- `0x10005df4` (2)

Representative events:

- `0x1000948a` READ in 0x10009484..0x10009491: `l32i.n a8,a8,0x0`
- `0x100095c8` READ in 0x100095c2..0x100095cf: `l32i a8,a8,0x0`

### `0xb3000408` - control/setup status gate

Read and tested against a mask before choosing descriptor response source.

Open-firmware relevance: likely selects the active descriptor/config branch.

Pointer/literal sources seen before access:

- `0x10005e68` (3)

Representative events:

- `0x1000947c` READ in 0x10009476..0x10009483: `l32i.n a9,a8,0x0`
- `0x100095b9` READ in 0x100095b3..0x100095c1: `l32i a9,a8,0x0`
- `0x10009714` READ in 0x1000970e..0x1000971d: `l32i.n a9,a8,0x0`

### `0xb3000504` - control endpoint descriptor/config register

Written with a constant/pointer-like value during one descriptor branch.

Open-firmware relevance: part of stock setup response register programming.

Pointer/literal sources seen before access:

- `0x10005ebc` (1)

Representative events:

- `0x10009548` WRITE in 0x10009534..0x10009593: `s32i.n a9,a11,0x0`

### `0xb3000508` - control endpoint descriptor/config register

Written during both device/config descriptor branches.

Open-firmware relevance: part of stock setup response register programming.

Pointer/literal sources seen before access:

- `0x10005ec0` (2)

Representative events:

- `0x100094cd` WRITE in 0x100094bc..0x1000950b: `s32i.n a8,a9,0x0`
- `0x1000954d` WRITE in 0x10009534..0x10009593: `s32i.n a8,a10,0x0`

### `0xb300050c` - control endpoint descriptor/config register

Written during descriptor branches and passed into the control-IN sender path.

Open-firmware relevance: part of stock setup response register programming.

Pointer/literal sources seen before access:

- `0x10005ed0` (2)

Representative events:

- `0x100094dd` WRITE in 0x100094bc..0x1000950b: `s32i.n a8,a10,0x0`
- `0x100095a1` PARAM in 0x10009594..0x100095b2: `call8 0x10008c24`
- `0x10009563` WRITE in 0x10009534..0x10009593: `s32i.n a8,a10,0x0`

### `0xb3000510` - control endpoint descriptor/config register

Written during descriptor branches and passed into the control-IN sender path.

Open-firmware relevance: part of stock setup response register programming.

Pointer/literal sources seen before access:

- `0x10005ec8` (2)

Representative events:

- `0x100094d8` WRITE in 0x100094bc..0x1000950b: `s32i.n a9,a11,0x0`
- `0x100095a1` PARAM in 0x10009594..0x100095b2: `call8 0x10008c24`
- `0x1000955e` WRITE in 0x10009534..0x10009593: `s32i.n a9,a11,0x0`

## What This Changes

This does not make a printer-side USB marker automatic, but it turns the
unknown from "reverse engineer USB" into a smaller checklist:

1. Poll/read `0xb3000400` and `0xb3000408` to identify setup readiness.
2. Confirm whether `0xb3000214` exposes an event/setup buffer after host enumeration.
3. Program the `0xb3000504..0xb3000510` group only after matching stock conditions.
4. Kick/ack with the observed `0x40`, `0x200`, `0x1`, `0x100`, and `0x108` patterns.

Until those register semantics are tested on hardware, an open USB marker is
still a controller-handshake problem rather than a descriptor-payload problem.
