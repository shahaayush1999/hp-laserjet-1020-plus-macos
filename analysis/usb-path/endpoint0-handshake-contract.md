# HP 1020 Endpoint-0 Handshake Contract

This authored static contract records the stock USB endpoint-0 descriptor path.
Original SETUP admission and field conversion are separately executed in
`setup-ingress.json`; register names follow the pinned classic Synopsys family
reference. Neither source establishes live HP controller behavior or permits
hardware access. The write sequences below are unchanged evidence, not a new
hardware allowlist.

## Short Version

The descriptor bytes and request-selection logic are now understood well enough
for a host-side model. The remaining hardware problem is the endpoint-0 data
stage:

1. distinguish SETUP from ordinary OUT0 data/status and validate ownership,
2. retain the eight raw setup bytes before returning their descriptor,
3. choose a response pointer and length,
4. program the USB controller registers,
5. distinguish control requests, status acknowledgements and actual completion.

No engine, fuser, motor, paper-feed, or video/raster registers are involved in
this path.

## Descriptor Speed Selection

The stock path checks two USB controller registers before choosing the descriptor
response setup branch:

| Register | Evidence | Meaning |
|---:|---|---|
| `0xb3000408` | read at `0x1000947c`, tested with literal `0x00006000` | DEVSTS enumerated-speed field |
| `0xb3000400` | read at `0x1000948a`, low two bits tested | DEVCFG configured-speed field |

The same gate pattern appears again in the neighboring `0x100095b3` descriptor
block. These are speed-selection fields in the family reference, not SETUP-ready
gates (`amd5536udc.h`:98–103, 140–143).

## Setup Packet Buffers

The file-backed global `0x1001bbc0` contains SETUP-record pointer `0x90021340`.
Original initialization loads it at `0x100091a8` and submits it through OUT0
SUBPTR `0xb3000210` at `0x100091b0`. The eight packet bytes start at record+8:

```text
base + 0x06 -> 0x9002134e
base + 0x07 -> 0x9002134f
```

The initial request-byte address is therefore:

```text
0x90021348
```

Other descriptor code reads setup byte 2 at `0x9002134a`, matching the standard
`wValue` low byte / descriptor index position.

The original prefix reads the status-record pointer through SUBPTR at
`0x10009361`, then admits only:

```text
(status_word & 0xc0000000) == 0x80000000  # owner 2
(status_word & 0x30000000) == 0           # RX status 0
```

It independently reloads global `0x1001bbc0` at `0x1000939c` for the request
bytes. The two pointers are expected to agree; original admission does not
compare them. The bounded experiment supplies ownership and stable bytes and
also exposes this assumption with deliberately mismatched pointers.

Raw USB `wValue`, `wIndex` and `wLength` are little-endian pairs. Before dispatch,
`0x10009399..0x1000940b` reverses only `wIndex` and `wLength` in place. Consequently
the later stock reads see offset 4/6 as the high byte and 5/7 as the low byte;
`wValue` remains in wire order. The open marker reads the raw wire representation.
TinyUSB's `dcd_event_setup_received` must receive the original eight wire bytes,
because it performs its own conversion of all three fields.

The separate path at `0x10009890` reads ordinary OUT0 DESPTR `0xb3000214`, initially
`0x90022bc0`, and checks that descriptor's ownership. It is not the SETUP pointer.
The later `0xb3000200 |= 0x100` requests EP0 OUT CNAK; it is not an interrupt
acknowledgement or proof that DMA stopped. These distinctions correct the older
event/signature terminology.

## Response State Fields

The stock branch writes response metadata into a transfer/control state object.
Static references imply this object base:

```text
0x100212d4
```

Important fields:

| Offset | Static reference | Meaning |
|---:|---:|---|
| `+0x3c` | `0x10021310` | response byte count / remaining length |
| `+0x40` | `0x10021314` | response data pointer |
| `+0x68` | `0x1002133c` | saved endpoint/request flag copied before TX |

## Controller Programming Sequences

The stock `0x10009476` descriptor block has two hardware-programming sequences
after choosing response pointer and length.

Under the family layout, endpoint `+0x0c` holds maximum-packet/buffer configuration
and IN endpoint `+0x08` holds buffer size. Thus the `0x40`/`0x200` writes below are
configuration values, not acknowledgement masks. Their bytes and the existing
allowed sequences are preserved.

### Sequence A

This sequence is used with response pointer `0x9001bbe0` and controller config
constants in the `0x0200....` family.

| Register | Value |
|---:|---:|
| `0xb3000508` | `0x020000c1` |
| `0xb3000510` | `0x020080c1` |
| `0xb300050c` | `0x020000d1` |
| `0xb300022c` | `0x00000040` |
| `0xb300020c` | `0x00000040` |
| `0xb300000c` | `0x00000040` |
| `0xb300002c` | `0x00000040` |
| `0xb3000028` | `0x00000040` |

### Sequence B

This sequence is used with response pointer `0x9001bc00` and controller config
constants in the `0x1000....` family.

| Register | Value |
|---:|---:|
| `0xb3000504` | `0x02000000` |
| `0xb3000508` | `0x100000c1` |
| `0xb3000510` | `0x100080c1` |
| `0xb300050c` | `0x100000d1` |
| `0xb300022c` | `0x00000200` |
| `0xb300020c` | `0x00000040` |
| `0xb300000c` | `0x00000040` |
| `0xb300002c` | `0x00000200` |
| `0xb3000028` | `0x00000040` |

### Data-Stage Submit

After the descriptor-specific setup sequence, the stock control-IN helper
submits the transfer descriptor ring and requests CNAK plus poll demand.

| Register | Value |
|---:|---:|
| `0xb3000014` | `0x900226f0` |
| `0xb3000000` | OR `0x00000108` |

## Control-IN Sender

Both sequences call `0x10008c24`, currently labeled
`hp1020_usb_control_tx_data_stage_candidate`.

The first visible hardware action in that helper requests the family F/flush bit:

```text
0xb3000000 |= 0x2
```

Then the stock code copies response bytes and eventually uses transfer
descriptors. Existing notes in `endpoint0-machinery.md` cover that broader data
stage: descriptor records are `0x10` bytes and the stock code later uses a
`0x108` CNAK/poll-demand pattern on `0xb3000000`. Issuing either control request
does not establish FIFO flush, transfer completion or safe buffer reuse.

The generated `control-in-data-stage.md` resolves the data-stage constants:
descriptor ring `0x900226f0`, staging buffer `0x90022bd0`,
final-descriptor flag `0x08000000`, submit register `0xb3000014`, and the
`0xb3000000 |= 0x108` control request.

## What This Changes

The remaining controller requirements include:

- confirm whether open firmware can see setup bytes at `0x90021348`,
- confirm SETUP SUBPTR and ordinary OUT0 DESPTR lifetimes independently,
- preserve raw setup bytes and original transfer identity before forwarding events,
- decide which of Sequence A or B matches the uploaded/runtime speed state,
- only then consider a write-capable USB-only marker probe.

The `usb-register-snapshot` probe has an existing guarded scope. These naming
corrections do not expand its register set, writes, permissions or hardware plan.
