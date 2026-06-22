# USB Marker Draft Hardware Test Plan

This is a later-stage custom firmware test plan for the USB marker draft.

It is not a print test. It uploads only the open USB marker draft and sends no
PDF, PostScript, ZjStream, engine, video, motor, fuser, or paper-feed data.

## Goal

Answer one narrow question:

```text
Can open firmware use only the mapped USB endpoint-0 registers to expose a
different product-string descriptor such as HP1020 OPEN MARKER?
```

## Current Offline Evidence

The draft currently passes these static gates:

- HP-shaped boot-probe layout profile
- general safety scan: no engine/video/function failures
- USB probe contract: only mapped `0xb300....` USB registers
- USB MMIO access scan: mapped USB reads/writes only
- endpoint-0 sequence scan: USB writes match the extracted stock endpoint-0 contract

The draft still has an important unresolved assumption:

```text
setup packet base 0x90021348 and response state base 0x100212d4 are valid after
custom firmware upload without the full stock USB runtime.
```

That assumption is exactly what hardware must prove or disprove.

## Expected Outcomes

Good outcome:

- upload completes or times out only after bytes are sent
- printer stays mechanically quiet
- macOS USB identity changes or disappears until power cycle
- a host descriptor read can observe `HP1020 OPEN MARKER`

Useful failure:

- upload succeeds but host still sees the stock descriptor
- upload succeeds but the device disappears until power cycle
- CUPS USB backend reports a USB transfer error

Stop condition:

- any paper-feed, motor, scanner/laser, or fuser behavior
- repeated mechanical noise
- anything beyond USB-level behavior

## Recovery

Power-cycle the printer. The HP 1020 loses uploaded firmware on power loss, so
this should clear the test state.

## Test Order

Do not start with this marker draft. The safer order is:

1. Confirm normal stock firmware preload still works.
2. Confirm the open idle probe still uploads quietly.
3. Optionally run the read-only USB register snapshot probe.
4. Only then consider this write-capable USB marker draft.

This plan exists so the write-capable step is ready when needed, not because it
should be run automatically.
