# HP 1020 USB Marker Boundary

This records the current answer to: "Can we make the next custom firmware prove
that our code ran by changing a USB-visible marker string?"

## Short Answer

Not yet as a safe first move.

The stock firmware has a clear USB string-descriptor path, but that path depends
on the stock USB stack already being initialized. Our open idle probe does not
run that stack. To make an open-code marker visible to macOS, we would need to
reimplement enough USB control-endpoint bring-up, descriptor DMA, and queue/event
handling to answer host setup packets.

That is doable work, but it is a bigger step than the PJL/status query harness.

`usb-descriptor-extraction.md` now confirms the raw descriptor data behind this:

- device descriptors at `0x1001bbe0` and `0x1001bc00`
- HP vendor ID `0x03f0`
- product ID `0x2b17`, matching the host-observed USB identity
- high-speed and full-speed printer-class configurations at `0x100034b0` and `0x100034d0`

`usb-descriptor-response-model.md` converts those descriptors into exact
`GET_DESCRIPTOR` response byte strings. That gives a future open marker a clear
payload contract, but not the hardware/control-endpoint implementation.

## What Is Mapped

The main stock USB service thread is:

```text
0x10008ff0 hp1020_usb2_thread
```

Important neighboring routines and blocks:

| Address | Current Label | Role |
|---:|---|---|
| `0x10008ff0` | `hp1020_usb2_thread` | main USB init/service loop |
| `0x10009934` | `hp1020_usb2_idle_thread` | tight idle/service thread around helper `0x10008f40` |
| `0x10008c24` | `hp1020_usb_control_tx_data_stage_candidate` | sends control-transfer data stage from buffer + length |
| `0x10007c00` | `hp1020_usb_register_transfer_candidate` | registers/arms a USB transfer object |
| `0x10008fb0` | `hp1020_usb_drain_pending_queue_candidate` | drains pending USB queue/transfer state |
| `0x10009476..0x100096e5` | internal setup-handler blocks | standard descriptor/control request handlers inside USB2Thread |

The stock path touches only the USB MMIO family for this work:

```text
0xb3000000
0xb300000c
0xb3000028
0xb300002c
0xb3000200
0xb300020c
0xb300022c
0xb3000400
0xb3000408
0xb3000504
0xb3000508
0xb300050c
0xb3000510
```

That is inside the "watch but potentially acceptable" USB-only family, not the
engine/video danger families.

## String Descriptor Evidence

The most useful stock marker path is the string descriptor handler around:

```text
0x1000964f
```

It appears to:

1. read a setup-packet byte that acts like a USB string index
2. index an ASCII string pointer table
3. call the firmware string-length helper
4. build a USB string descriptor in a runtime buffer
5. send that buffer through `hp1020_usb_control_tx_data_stage_candidate`

The relevant known identity strings are:

| Address | String |
|---:|---|
| `0x10003490` | `$$DEVICE_ID_STRING$$` |
| `0x1001bf70` | `Hewlett-Packard` |
| `0x1001bf8c` | `HP LaserJet 1020` |
| `0x1001bfb0` | `HP LaserJet 1020` |

The device descriptors use string indexes `1`, `2`, and `3`. Static pointer runs
map indexes `1` and `2` to `Hewlett-Packard` and `HP LaserJet 1020`; the serial
string is likely runtime-generated from USB/device state rather than a fixed
ASCII literal.

This is promising for a marker because a USB string descriptor can prove code is
serving host control requests without moving paper.

## Why This Is Not The Next Hardware Test

Changing a string in stock firmware would not prove our open firmware ran. It
would only prove we can alter HP's existing firmware image.

For the open idle probe, there is no stock USB thread, scheduler setup, queue
object, transfer descriptor setup, or control endpoint response loop. A marker
firmware would need to recreate enough of that before macOS can read a string.

The hard pieces are:

- USB controller reset/configuration sequence
- endpoint 0 setup-packet receive path
- control-IN data-stage descriptor format
- event/interrupt acknowledgement order
- runtime buffer addresses and alignment
- whether the resident boot code leaves USB state usable after ACL download

The descriptor payload bytes are now the easy part. The unresolved work is the
endpoint-0 machinery that receives setup packets and returns those bytes.

The current open idle probe intentionally avoids all of that, which is why it
stayed quiet and safe.

## Safer Next Order

1. Use `scripts/query-hp1020-pjl-status.sh` to calibrate stock HP PJL/back-channel
   response.
2. Compare that against open idle + the same PJL query.
3. If host back-channel works, keep using it as the discriminator.
4. If host back-channel does not work, deepen USB analysis before writing any
   marker firmware.
5. Only then build an open USB marker probe that responds to one descriptor or
   vendor/status request.

## Decision

Do not build or upload a USB marker firmware yet.

The USB string-descriptor path is mapped enough to be the right future target,
but not enough to safely clone into open firmware before the non-printing PJL
query has been tried.
