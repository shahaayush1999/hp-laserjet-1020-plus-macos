# HP 1020 USB/Download Path Pass

Date: 2026-06-04

## Result

The USB/download path is now mapped one layer deeper than the initial label pass.

Generated output:

```text
analysis/usb-path/usb-path-map.md
analysis/usb-path/internal-blocks.md
analysis/usb-path/decompiled-neighbors/
```

The important change is that `USB2Thread` is no longer just "large unknown USB code." It is visibly a USB control-transfer service loop with request decoding, descriptor/data-stage handling, ThreadX queue waits, and hardware/MMIO register writes.

## Current Function Labels

High-confidence or useful working labels:

```text
10008ff0 hp1020_usb2_thread
10009934 hp1020_usb2_idle_thread
1000ad44 hp1020_acl_download
1000cdb0 hp1020_pjl_echo_matcher
10008c24 hp1020_usb_control_tx_data_stage_candidate
10007c00 hp1020_usb_register_transfer_candidate
10008fb0 hp1020_usb_drain_pending_queue_candidate
10011178 hp1020_get_config_value_candidate
10017d28 threadx_queue_receive_candidate
10018274 threadx_thread_create_candidate
```

The ThreadX labels are based on call shape:

- `10018274` checks thread pointer, stack size, priority range, preemption threshold, and then calls a lower-level creator. In `USB2Thread` it is used to create `USB2IdleThread`.
- `10017d28` checks a queue-like object and wait/suspension constraints before calling a lower-level receive function.

## USB2Thread Behavior

`USB2Thread` performs setup/init first, then creates `USB2IdleThread`:

```text
threadx_thread_create_candidate(
  name = USB2IdleThread,
  entry = 0x10009934,
  stack = 0x10021388,
  stack_size = 0x200,
  priority = 0x1f,
  preemption_threshold = 0x1f,
  auto_start = 1
)
```

Then it enters a permanent service loop:

- waits on a queue/control object via `threadx_queue_receive_candidate`
- reads a setup/control packet from a DMA/control buffer
- checks request type/request value words
- handles standard/class/vendor-looking USB setup requests
- builds response descriptors or short response buffers
- sends response data via `hp1020_usb_control_tx_data_stage_candidate`
- acknowledges/arms hardware by writing MMIO registers

## USB Request Constants

The literal table near `0x10005f64` resolves these constants:

```text
0xa100
0x2102
0x8006
0xc100
0xa101
0xc101
```

`0x8006` is the standard USB `GET_DESCRIPTOR` request shape.

`0x2102` is a class/interface OUT request shape, likely `SET_REPORT` or a related class control transfer.

`0xa100`, `0xa101`, `0xc100`, and `0xc101` are vendor/class IN request shapes used by this device.

There is also a seven-entry jump table at `0x10003500` used from the `0x8006` handling path:

```text
10003500: 10009476
10003504: 100095b3
10003508: 100095f6
1000350c: 10009859
10003510: 10009859
10003514: 100096af
10003518: 100096e5
```

Those are likely individual descriptor/request blocks, but Ghidra currently treats them as internal labels inside `USB2Thread`, not standalone functions. A forced function split at those addresses mislabels the containing `USB2Thread` function, so the next pass should analyze them as basic blocks inside `0x10008ff0`, not as separate functions.

The internal-block extractor confirms the useful shape:

```text
10009476 reads b3000408 and gates on mask 0x00006000
100095b3 reads b3000408 and gates on mask 0x00006000
100095f6 reads setup byte at 0x9002134a
10009859 is a tiny block that sets a response length/status value to 1
100096af writes response pointer 0x1001bbd0 and caps wLength at 0x000a
100096e5 writes response pointer 0x1001bc20 and caps wLength at 0x0020
```

That strongly suggests the jump-table entries are `GET_DESCRIPTOR` response blocks keyed by descriptor index/type.

Two descriptor payloads are now identified:

```text
1001bbd0: 0a 06 00 02 00 00 00 40 01 00
```

This is a 10-byte USB device-qualifier descriptor shape:

- `bLength = 0x0a`
- `bDescriptorType = 0x06`
- `bcdUSB = 0x0200`
- `bMaxPacketSize0 = 0x40`
- `bNumConfigurations = 1`

```text
1001bc20: 09 07 20 00 01 01 00 c0 31
          09 04 00 00 02 07 01 02 00
          07 05 01 02 40 00 00
          07 05 81 02 40 00 00
```

This is a 32-byte USB configuration descriptor tree:

- configuration descriptor: total length 0x20, one interface, self-powered-ish attributes `0xc0`, max power `0x31`
- interface descriptor: class `0x07`, subclass `0x01`, protocol `0x02` which matches USB printer-class style
- endpoint `0x01`: bulk OUT, 64-byte packet
- endpoint `0x81`: bulk IN, 64-byte packet

So this printer firmware exposes a USB printer-class interface with bulk IN/OUT endpoints, and `USB2Thread` handles at least the control endpoint descriptor traffic.

## MMIO/Register Candidates

Several Ghidra `DAT_10005eXX` names are not RAM variables. They are literal pointers to hardware/MMIO-looking addresses.

Important resolved constants:

```text
DAT_10005e90 -> 0xb3000000
DAT_10005e9c -> 0xb300000c
DAT_10005ea0 -> 0xb3000014
DAT_10005e88 -> 0xb3000020
DAT_10005edc -> 0xb3000028
DAT_10005ee0 -> 0xb300002c
DAT_10005e24 -> 0xb3000200
DAT_10005ee4 -> 0xb300020c
DAT_10005ef4 -> 0xb3000210
DAT_10005ef8 -> 0xb3000214
DAT_10005e70 -> 0xb3000220
DAT_10005f08 -> 0xb300022c
DAT_10005e60 -> 0xb3000234
DAT_10005df4 -> 0xb3000400
DAT_10005ea8 -> 0xb3000404
DAT_10005eb8 -> 0xb3000410
DAT_10005e00 -> 0xb3000418
DAT_10005ebc -> 0xb3000504
DAT_10005ec0 -> 0xb3000508
DAT_10005ed0 -> 0xb300050c
DAT_10005ec8 -> 0xb3000510
DAT_10005eac -> 0xb3010000
```

Working interpretation:

- `0xb3000000` to `0xb3000520` is probably the USB controller register block.
- `0xb3010000` looks like a related controller/status block or global USB control register.
- repeated `memw()` around these writes is strong evidence that these are hardware registers, not ordinary RAM.

The firmware also uses `0x9002....` addresses through RAM pointer tables. Those look more like SRAM/DMA buffers or descriptors:

```text
PTR_DAT_10005ee8 -> 0x1001bbc0 -> 0x90021340
PTR_DAT_10005eec -> 0x1001bc60 -> 0x90022bc0
PTR_DAT_10005e98 -> 0x1001bc58 -> 0x900226f0
PTR_DAT_10005e94 -> 0x1001bc64 -> 0x90022bd0
PTR_DAT_10005e44 -> 0x1001bc40 -> 0x900216f0
PTR_DAT_10005e2c -> 0x1001bc48 -> 0x90021370
```

## ACL Download Dispatch

`agiACLDownload` at `0x1000ad44` is small:

```c
*DAT_10005e70 |= 0x80;
puVar2 = *(undefined4 **)PTR_DAT_10006068;
*DAT_10005e24 |= 0x80;
(*(code *)*puVar2)(0, param_1);
```

Resolved:

```text
PTR_DAT_10006068 -> 0x1001be90
0x1001be90      -> 0x10000350
```

`0x10000350` lines up with the zero-sized `bootcode_interface_table` area rather than a normal firmware-local function. Current interpretation: ACL download hands off into a resident bootcode/interface table after setting USB/control bits.

That matters because the actual firmware loading/ACL path may depend on code already present in the printer boot ROM, not only this uploaded ELF payload.

## What This Means For The Estimate

The USB path map moved faster than the previous estimate. We have the first useful USB/download path map in the same session as the initial labeling pass.

The next hard part is not finding the path. It is assigning precise semantics to the hardware registers and the descriptor buffers.

Updated estimate:

- USB/download first map: done.
- Analyze and label the seven internal GET_DESCRIPTOR/jump-table blocks: likely hours.
- Produce a useful USB register/buffer map: likely 1-2 focused days.
- Trace actual host-to-firmware ACL/download handoff end-to-end: likely 1-3 focused days, with the caveat that boot ROM table behavior may remain partially opaque.
- Replacement firmware timeline remains much longer because this hardware-register map has to become correct enough to drive a real printer safely.

## Next Step

Analyze the seven jump-table target blocks inside `USB2Thread`:

```text
10009476
100095b3
100095f6
10009859
100096af
100096e5
```

Then label which USB descriptor or request each block serves. Do not force-create them as standalone functions unless the function boundary problem is fixed first.

Known so far:

- `100096af`: device-qualifier descriptor response.
- `100096e5`: configuration/interface/endpoint descriptor response.
- `10009476`: descriptor response path that writes either `0x9001bbe0` or `0x9001bc00` into the response-data pointer, depending on USB controller state. These look like runtime descriptor buffers, not static `.data` payloads.
- `100095b3`: similar runtime-buffer descriptor response path; needs one more pass to separate the exact descriptor type.
- `100095f6`: reads setup byte 2, then branches into string/config-like descriptor handling. It writes response pointers including `0x10021380` and `0x10022b70`, which are RAM/BSS-region buffers.
- `10009859`: short one-byte response path.

Static descriptor data now identified:

```text
1001bc00: 12 01 00 02 00 00 00 40 f0 03 17 2b 00 01 01 02 03 01
```

This is a USB device descriptor:

- USB 2.0
- max packet size 64
- vendor ID `0x03f0` HP
- product ID `0x2b17`
- manufacturer string index 1
- product string index 2
- serial/config string index 3/1 depending on field

Plain ASCII identity strings are also present in `.data`:

```text
1001bf70 Hewlett-Packard
1001bf8c HP LaserJet 1020
1001bfb0 HP LaserJet 1020
1001bfd4 ACL.PRINTER
```
- remaining blocks need the same block-level treatment and pointer/length extraction.
