# HP 1020 USB MMIO Register Map

This generated map retains saved static references and verifies corrected
meanings against original bytes and the pinned controller-family header.
Its 15-register allowlist and permitted writes are unchanged; no hardware
operation or controller timing is validated here.

## Plain-English Summary

Separate endpoint control requests, status acknowledgement, descriptor
ownership and speed/packet-size configuration. Similar numeric masks at
different addresses are not interchangeable operations.

The important register family is `0xb300....`. Static evidence clusters it
into four groups:

- configured/enumerated speed fields: `0xb3000400`, `0xb3000408`
- descriptor/control register programming: `0xb3000504`, `0xb3000508`, `0xb300050c`, `0xb3000510`
- EP0 IN/OUT control: `0xb3000000`, `0xb3000200`; maximum-packet/buffer words: `0xb300000c`, `0xb3000028`, `0xb300002c`, `0xb300020c`, `0xb300022c`
- ordinary OUT0 descriptor pointer (DESPTR): `0xb3000214`

SETUP uses distinct SUBPTR `0xb3000210`, proven by original initialization
and admission bytes. It is documentation metadata here, not an addition
to this existing hardware allowlist. `setup-ingress.json` records the
separate RAM-only admission/conversion experiment.

## Register Summary

| Register | Working Name | Reads | Writes | Params | Main Meaning |
|---:|---|---:|---:|---:|---|
| `0xb3000000` | EP0 IN control (EPCTL) | 3 | 2 | 0 | Original control requests include 0x2 and 0x108. Family names are F/flush and CNAK plus P/poll demand; bit 0 is S/stall. These are not interrupt acknowledgements. |
| `0xb300000c` | EP0 IN maximum-packet word | 0 | 2 | 0 | Written with 0x40 during descriptor request paths. |
| `0xb3000014` | control-IN descriptor submit register | 0 | 2 | 0 | Written with the transfer descriptor pointer before the 0x108 CNAK/poll-demand request. Original stores are 0x10008d0c and 0x10008f1b. |
| `0xb3000028` | EP1 IN buffer-size word | 0 | 1 | 0 | Endpoint 1 IN +0x08 is buffer-size configuration under the family layout; the stock path writes 0x40. |
| `0xb300002c` | EP1 IN maximum-packet word | 0 | 2 | 0 | Written with 0x40 or 0x200 in descriptor request paths. |
| `0xb3000200` | EP0 OUT control (EPCTL) | 2 | 2 | 0 | Read/modify/write control requests include S/stall bit 0 and CNAK bit 8. CNAK does not acknowledge an interrupt or establish DMA quiescence. |
| `0xb300020c` | EP0 OUT maximum-packet/buffer word | 0 | 2 | 0 | Written with 0x40 in descriptor request paths. |
| `0xb3000214` | EP0 OUT ordinary data/status descriptor pointer (DESPTR) | 1 | 0 | 0 | At 0x10009890 the original reads DESPTR and checks descriptor ownership. SETUP instead uses the distinct SUBPTR register 0xb3000210. |
| `0xb300022c` | EP1 OUT maximum-packet/buffer word | 0 | 2 | 0 | Written with 0x40 or 0x200 in descriptor request paths. |
| `0xb3000400` | device configuration (DEVCFG) | 2 | 0 | 0 | Read before choosing descriptor response source. Low two bits are tested. |
| `0xb3000408` | device status (DEVSTS) | 3 | 0 | 0 | Read and tested against 0x6000 before choosing descriptor response source; the family layout calls these enumerated-speed bits. |
| `0xb3000504` | control endpoint descriptor/config register | 0 | 1 | 0 | Written with a constant/pointer-like value during one descriptor branch. |
| `0xb3000508` | control endpoint descriptor/config register | 0 | 2 | 0 | Written during both device/config descriptor branches. |
| `0xb300050c` | control endpoint descriptor/config register | 0 | 2 | 1 | Written during descriptor branches and passed into the control-IN sender path. |
| `0xb3000510` | control endpoint descriptor/config register | 0 | 2 | 1 | Written during descriptor branches and passed into the control-IN sender path. |

## Write Constants and Bit Operations

| Register | Evidence |
|---:|---|
| `0xb3000000` | `0x10008c3f` ORs `0x2` before write |
| `0xb300000c` | `0x100094fc` writes `0x40`; `0x10009582` writes `0x40` |
| `0xb3000014` | `0x10008d0c` submits pointer `0x900226f0`; `0x10008f1b` submits pointer `0x900226f0` |
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

### `0xb3000000` - EP0 IN control (EPCTL)

Original control requests include 0x2 and 0x108. Family names are F/flush and CNAK plus P/poll demand; bit 0 is S/stall. These are not interrupt acknowledgements.

Open-firmware relevance: separate endpoint control intent from actual completion and safe buffer reuse.

Pointer/literal sources seen before access:

- `0x10005e90` (5)

Representative events:

- `0x10009877` READ in 0x1000985f..0x10009883: `l32i.n a8,a9,0x0`
- `0x1000987f` WRITE in 0x1000985f..0x10009883: `s32i.n a8,a9,0x0`
- `0x10008c35` READ in 0x10008c24..0x10008c4e: `l32i.n a8,a4,0x0`
- `0x10008c3f` WRITE in 0x10008c24..0x10008c4e: `s32i.n a8,a4,0x0`
- `0x10008c4a` READ in 0x10008c24..0x10008c4e: `l32i.n a8,a4,0x0`

### `0xb300000c` - EP0 IN maximum-packet word

Written with 0x40 during descriptor request paths.

Open-firmware relevance: packet-size configuration, not acknowledgement.

Pointer/literal sources seen before access:

- `0x10005e9c` (2)

Representative events:

- `0x100094fc` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a9,0x0`
- `0x10009582` WRITE in 0x10009534..0x10009593: `s32i.n a6,a9,0x0`

### `0xb3000014` - control-IN descriptor submit register

Written with the transfer descriptor pointer before the 0x108 CNAK/poll-demand request. Original stores are 0x10008d0c and 0x10008f1b.

Open-firmware relevance: needed to submit endpoint-0 transfer descriptors without the stock helper.

Pointer/literal sources seen before access:

- `0x10005ea0` (2)

Representative events:

- `0x10008d0c` WRITE in 0x10008c24..0x10008f39: `s32i.n a8,a9,0`
- `0x10008f1b` WRITE in 0x10008c24..0x10008f39: `s32i.n a8,a9,0`

### `0xb3000028` - EP1 IN buffer-size word

Endpoint 1 IN +0x08 is buffer-size configuration under the family layout; the stock path writes 0x40.

Open-firmware relevance: buffer configuration, not acknowledgement or completion.

Representative events:

- `0x10009597` WRITE in 0x10009594..0x100095b2: `s32i.n a6,a9,0x0`

### `0xb300002c` - EP1 IN maximum-packet word

Written with 0x40 or 0x200 in descriptor request paths.

Open-firmware relevance: full/high-speed packet-size configuration.

Pointer/literal sources seen before access:

- `0x10005ee0` (2)

Representative events:

- `0x10009507` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a8,0x0`
- `0x10009590` WRITE in 0x10009534..0x10009593: `s32i.n a6,a8,0x0`

### `0xb3000200` - EP0 OUT control (EPCTL)

Read/modify/write control requests include S/stall bit 0 and CNAK bit 8. CNAK does not acknowledge an interrupt or establish DMA quiescence.

Open-firmware relevance: OUT0 endpoint control is separate from OUT0 status/interrupt acknowledgement.

Pointer/literal sources seen before access:

- `0x10005e24` (4)

Representative events:

- `0x10009865` READ in 0x1000985f..0x10009883: `l32i.n a8,a6,0x0`
- `0x10009870` WRITE in 0x1000985f..0x10009883: `s32i.n a8,a6,0x0`
- `0x10009905` READ in 0x100098f9..0x10009916: `l32i.n a8,a6,0x0`
- `0x1000990f` WRITE in 0x100098f9..0x10009916: `s32i.n a8,a6,0x0`

### `0xb300020c` - EP0 OUT maximum-packet/buffer word

Written with 0x40 in descriptor request paths.

Open-firmware relevance: packet-size/buffer configuration, not acknowledgement.

Pointer/literal sources seen before access:

- `0x10005ee4` (2)

Representative events:

- `0x100094f7` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a8,0x0`
- `0x1000957d` WRITE in 0x10009534..0x10009593: `s32i.n a6,a8,0x0`

### `0xb3000214` - EP0 OUT ordinary data/status descriptor pointer (DESPTR)

At 0x10009890 the original reads DESPTR and checks descriptor ownership. SETUP instead uses the distinct SUBPTR register 0xb3000210.

Open-firmware relevance: do not confuse ordinary OUT0 descriptor completion with SETUP storage.

Pointer/literal sources seen before access:

- `0x10005ef8` (1)

Representative events:

- `0x10009896` READ in 0x10009890..0x100098c1: `l32i.n a11,a8,0x0`

### `0xb300022c` - EP1 OUT maximum-packet/buffer word

Written with 0x40 or 0x200 in descriptor request paths.

Open-firmware relevance: full/high-speed receive packet-size configuration.

Pointer/literal sources seen before access:

- `0x10005f08` (2)

Representative events:

- `0x100094ec` WRITE in 0x100094bc..0x1000950b: `s32i.n a6,a9,0x0`
- `0x10009570` WRITE in 0x10009534..0x10009593: `s32i.n a6,a9,0x0`

### `0xb3000400` - device configuration (DEVCFG)

Read before choosing descriptor response source. Low two bits are tested.

Open-firmware relevance: low two bits select configured speed in the family layout; not SETUP readiness.

Pointer/literal sources seen before access:

- `0x10005df4` (2)

Representative events:

- `0x1000948a` READ in 0x10009484..0x10009491: `l32i.n a8,a8,0x0`
- `0x100095c8` READ in 0x100095c2..0x100095cf: `l32i a8,a8,0x0`

### `0xb3000408` - device status (DEVSTS)

Read and tested against 0x6000 before choosing descriptor response source; the family layout calls these enumerated-speed bits.

Open-firmware relevance: speed-dependent descriptor/configuration selection, not SETUP ownership.

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

A controller adapter still needs distinct ownership and event contracts:

1. Keep configured/enumerated speed fields separate from SETUP ownership.
2. Preserve the original eight wire bytes and distinguish SETUP SUBPTR from ordinary OUT0 DESPTR.
3. Separate endpoint packet-size/buffer configuration from command/status masks.
4. Validate original transfer identity, descriptor completion and errors before publishing a completion event.

The original submission stores are `0x10008d0c` and `0x10008f1b`; older
manual PCs `0x10008ce4`/`0x10008e50` were not the submission stores.
Command intent, wake flags and supplied RAM completion do not establish
DMA/cache behavior, abort completion or safe physical buffer reuse.
Hardware tests still require the existing explicit owner authorization.

## Original Byte Checks

| Address | Bytes | Meaning |
|---:|---|---|
| `0x10005df4` | `b3000400` | original address/value literal |
| `0x10005e68` | `b3000408` | original address/value literal |
| `0x10005ea4` | `00006000` | original address/value literal |
| `0x10005e90` | `b3000000` | original address/value literal |
| `0x10005e24` | `b3000200` | original address/value literal |
| `0x10005ea0` | `b3000014` | original address/value literal |
| `0x10005e98` | `1001bc58` | original address/value literal |
| `0x1001bc58` | `900226f0` | original address/value literal |
| `0x10005e9c` | `b300000c` | original address/value literal |
| `0x10005ee0` | `b300002c` | original address/value literal |
| `0x10005ee4` | `b300020c` | original address/value literal |
| `0x10005f08` | `b300022c` | original address/value literal |
| `0x10005edc` | `b3000028` | original address/value literal |
| `0x10005ef4` | `b3000210` | original address/value literal |
| `0x10005ef8` | `b3000214` | original address/value literal |
| `0x10009476` | `18f27c` | load DEVSTS address literal |
| `0x1000947c` | `8980` | sample DEVSTS |
| `0x1000947e` | `18f289` | load enumerated-speed mask 0x6000 |
| `0x10009484` | `18f25c` | load DEVCFG address literal |
| `0x1000948a` | `8880` | sample DEVCFG |
| `0x1000948c` | `080841` | extract configured-speed low two bits |
| `0x100094e2` | `19f289` | load OUT1 maximum-packet address |
| `0x100094e5` | `c460` | movi.n a6,64: packet-size value |
| `0x100094ec` | `9690` | write OUT1 packet size |
| `0x100094ee` | `18f27d` | load OUT0 maximum-packet address |
| `0x100094f1` | `19f26a` | load IN0 maximum-packet address |
| `0x100094f7` | `9680` | write OUT0 packet size |
| `0x100094fc` | `9690` | write IN0 packet size |
| `0x100094fe` | `18f278` | load IN1 maximum-packet address |
| `0x10009501` | `19f276` | load IN1 buffer-size address |
| `0x10009507` | `9680` | write IN1 packet size |
| `0x10009597` | `9690` | write IN1 buffer size |
| `0x1000935b` | `18f2e6` | SETUP admission loads SUBPTR address |
| `0x10009890` | `18f19a` | ordinary OUT0 admission loads DESPTR address |
| `0x100098f9` | `16f14a` | load OUT0 control address |
| `0x100098fc` | `2a1a00` | movi a10,0x100: CNAK request mask |
| `0x10009909` | `0a8802` | add CNAK to sampled control |
| `0x1000990f` | `9860` | write OUT0 control request |
| `0x10008c2a` | `14f499` | load IN0 control address |
| `0x10008c37` | `c022` | movi.n a2,2: F/flush request mask |
| `0x10008c3f` | `9840` | write IN0 F request |
| `0x10008c74` | `1cf489` | load IN0 descriptor global for zero-length path |
| `0x10008d02` | `88c0` | load descriptor pointer through global |
| `0x10008d04` | `19f467` | load IN0 DESPTR address |
| `0x10008d0c` | `9890` | actual zero-length descriptor submission store |
| `0x10008d13` | `291a08` | movi a9,0x108: CNAK and poll demand |
| `0x10008d30` | `17f45a` | load IN0 descriptor global for nonempty path |
| `0x10008f11` | `19f3e3` | load IN0 DESPTR address |
| `0x10008f14` | `8870` | load descriptor pointer through global |
| `0x10008f1b` | `9890` | actual nonempty descriptor submission store |
| `0x10008f22` | `291a08` | movi a9,0x108: CNAK and poll demand |
