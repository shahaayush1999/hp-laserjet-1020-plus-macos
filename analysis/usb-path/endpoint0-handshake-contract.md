# HP 1020 Endpoint-0 Handshake Contract

This is the current static contract for the stock USB endpoint-0 descriptor
response path. It narrows the future open USB marker from "reverse engineer
USB" to the specific setup buffers and controller writes that still need live
confirmation.

## Short Version

The descriptor bytes and request-selection logic are now understood well enough
for a host-side model. The remaining hardware problem is the endpoint-0 data
stage:

1. observe setup/event readiness,
2. read the setup packet,
3. choose a response pointer and length,
4. program the USB controller registers,
5. kick/ack the transfer and completion bits.

No engine, fuser, motor, paper-feed, or video/raster registers are involved in
this path.

## Setup/Status Gates

The stock path checks two USB controller registers before choosing the descriptor
response setup branch:

| Register | Evidence | Meaning |
|---:|---|---|
| `0xb3000408` | read at `0x1000947c`, tested with literal `0x00006000` | controller speed/state gate |
| `0xb3000400` | read at `0x1000948a`, low two bits tested | setup/status ready gate |

The same gate pattern appears again in the neighboring `0x100095b3` descriptor
block.

## Setup Packet Buffers

The descriptor branch reads setup bytes through a RAM-looking setup packet base:

```text
base + 0x06 -> 0x9002134e
base + 0x07 -> 0x9002134f
```

Those are the standard USB `wLength` bytes. This implies a setup packet base of:

```text
0x90021348
```

Other descriptor code reads setup byte 2 at `0x9002134a`, matching the standard
`wValue` low byte / descriptor index position.

A separate event/setup pointer path reads:

```text
0xb3000214 -> pointer
```

The pointed buffer is then read at `+0..+3`, observed as `0x90022bc0..0x90022bc3`
in static references. The first four bytes are assembled into a word and checked
as:

```text
(event_word & 0xc0000000) == 0x80000000
```

If that comparison fails, the stock path acknowledges event state through
`0xb3000200 |= 0x100`.

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

## Control-IN Sender

Both sequences call `0x10008c24`, currently labeled
`hp1020_usb_control_tx_data_stage_candidate`.

The first visible hardware action in that helper is:

```text
0xb3000000 |= 0x2
```

Then the stock code copies/flushes response bytes and eventually uses transfer
descriptors. Existing notes in `endpoint0-machinery.md` cover that broader data
stage: descriptor records are `0x10` bytes and the stock code later uses a
`0x108` kick pattern on `0xb3000000`.

## What This Changes

The next open USB marker is not blocked by descriptor bytes anymore. It is
blocked by the minimum safe subset of this controller handshake:

- confirm whether open firmware can see setup bytes at `0x90021348`,
- confirm whether `0xb3000214` exposes the event/setup pointer after upload,
- decide which of Sequence A or B matches the uploaded/runtime speed state,
- only then consider a write-capable USB-only marker probe.

The current `usb-register-snapshot` probe deliberately stops before this point:
it reads the mapped USB registers and writes only RAM.
