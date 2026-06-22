# HP 1020 USB Endpoint-0 Machinery

This is the current offline map of the stock firmware machinery around USB
control endpoint responses. It explains what is known after extracting the
descriptor payload bytes.

## Plain-English Summary

We now know the descriptor bytes the printer advertises. The remaining hard
part is making open firmware receive a USB setup packet and return those bytes.

In the stock firmware, that is not a single function. It is a small USB runtime:

- a USB service thread
- an idle/service helper thread
- an interrupt/event hook
- a ThreadX queue
- transfer records
- DMA/transfer descriptor buffers
- `0xb300....` USB controller register writes

That is why a USB marker is plausible but still not the next safest upload.

## Main Control Flow

```text
0x10008ff0 hp1020_usb2_thread
  initializes USB controller/register state
  registers/arms transfer records through 0x10007c00
  installs interrupt hook for interrupt 4 through 0x1001716c
  enables interrupt 4 through 0x10017184
  creates USB2IdleThread at 0x10009934
  waits on a ThreadX queue for USB events
  dispatches setup/control requests
  calls 0x10008c24 to send control-IN data stages
```

The idle thread is simple:

```text
0x10009934 hp1020_usb2_idle_thread
  loop: call 0x10008f40 forever
```

The interrupt helpers are straightforward:

| Address | Current Role |
|---:|---|
| `0x1001716c` | replace interrupt-vector-table slot for a given interrupt number |
| `0x10017184` | enable an interrupt bit in Xtensa `INTENABLE` |
| `0x100171b0` | disable an interrupt bit in Xtensa `INTENABLE` |

USB uses interrupt `4` in this path.

## Transfer Record Shape

`0x10007c00 hp1020_usb_register_transfer_candidate` allocates/registers transfer
records from a pool. The record stride is `0x58` bytes.

Observed fields:

| Offset | Observed Meaning |
|---:|---|
| `+0x00` | transfer bit/handle snapshot |
| `+0x04` | copied from registration parameter word 2 |
| `+0x08` | copied from registration parameter word 3 |
| `+0x0c` | callback/helper pointer initialized by `0x10008034` |
| `+0x10` | callback/helper pointer initialized by `0x10008034` |
| `+0x14` | callback/helper pointer initialized by `0x10008034` |
| `+0x18` | copied from registration parameter word 4 |
| `+0x1c` | allocated buffer pointer, from `0x10008034` |
| `+0x20` | same allocated buffer pointer initially |
| `+0x24` | initial data length/size parameter |
| `+0x28` | buffer capacity, initialized to `0x400` |
| `+0x2c` | copied from registration parameter word 0 |
| `+0x38` | copied from registration parameter word 1 |
| `+0x3c` | current remaining transfer length, initialized to `0` |
| `+0x40` | current control-IN source pointer / data pointer |
| `+0x44` | zeroed state field |
| `+0x48` | zeroed state field |
| `+0x4c` | zeroed state field |
| `+0x50` | zeroed state field |
| `+0x54` | copied from registration parameter word 5 |

This is enough to understand why a descriptor-response model is only a payload
model. The actual stock response path depends on a registered transfer object.

## Control-IN Data Stage

`0x10008c24 hp1020_usb_control_tx_data_stage_candidate` sends the current
control response.

Observed inputs:

| Source | Meaning |
|---|---|
| transfer state `+0x40` | source data pointer |
| transfer state `+0x3c` | remaining byte count |
| `DAT_10005e9c` | max/chunk size used for transfer descriptors |
| `PTR_DAT_10005e98` | transfer descriptor buffer base |
| `DAT_10005ea0` | hardware-visible descriptor pointer/register |
| `PTR_DAT_10005e18` | ThreadX queue used to wait for transfer completion |

Observed behavior:

1. Set bit `0x2` in `0xb3000000`.
2. Flush/copy source data through helper `0x100173c8` / `0x1001b38c`.
3. Build one or more `0x10`-byte transfer descriptors.
4. Write descriptor base through `DAT_10005ea0`.
5. Set bits `0x108` in `0xb3000000`.
6. Wait on the USB ThreadX queue for completion.
7. Repeat until remaining length reaches zero.

The transfer descriptor shape appears to be:

| Descriptor Offset | Observed Meaning |
|---:|---|
| `+0x00..+0x03` | byte count or byte count plus controller flag/base bit |
| `+0x04..+0x07` | zero |
| `+0x08..+0x0b` | source buffer pointer |
| `+0x0c..+0x0f` | next descriptor pointer or zero |

## Setup Request Dispatch

Inside `USB2Thread`, the standard descriptor path is routed through internal
blocks around:

```text
0x10009476..0x100096e5
```

Important known pieces:

- setup request `0x8006` is standard USB `GET_DESCRIPTOR`
- descriptor payloads are now extracted in `usb-descriptor-extraction.md`
- response byte strings are modeled in `usb-descriptor-response-model.md`
- string descriptor construction around `0x1000964f` converts ASCII identity
  strings to USB UTF-16LE string descriptors

## What This Means For Open Firmware

A minimal open USB marker is not blocked by descriptor bytes anymore. It is
blocked by endpoint-0 machinery:

- bring USB controller into a usable state after ACL upload
- receive setup packets
- identify `GET_DESCRIPTOR`
- point transfer state at a descriptor byte string
- build the controller's transfer descriptors correctly
- kick the right `0xb300` bits
- observe/ack completion without ThreadX or with a minimal replacement loop

The safest near-term path remains:

1. Run the PJL/status query harness with stock firmware.
2. Compare it against the open idle upload.
3. Only if that path cannot discriminate execution, continue toward a USB-only
   open marker.

## Current Blocker

The next step toward an actual open USB marker requires either:

- hardware observation of stock firmware's endpoint-0 events, or
- enough confidence in `0xb300` register semantics to write a polling endpoint-0
  loop without relying on ThreadX.

That is not available yet from static analysis alone.
