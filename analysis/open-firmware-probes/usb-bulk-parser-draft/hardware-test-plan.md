# USB Bulk Parser Draft Hardware Test Plan

This is the first hardware test plan for the mechanically inert USB bulk OUT
and ZjStream framing draft. It is not a print test.

## Question

Answer only this question:

```text
Can the standalone open firmware expose its endpoint-0 counter descriptor,
receive one 36-byte bulk OUT transfer, and recognize START_DOC plus END_DOC
without entering any page, raster, video, engine, or mechanical path?
```

## Safety Boundary

The harness can send only:

1. `hp1020-usb-bulk-parser-draft.dl`, the custom volatile firmware upload
2. when separately enabled, a fixed `JZJZ + START_DOC + END_DOC` stream

The data stream has two valid big-endian 16-byte headers and no payload bytes.
It contains no `START_PAGE`, `END_PAGE`, JBIG, image, raster, engine, video,
laser, fuser, motor, or paper-feed command.

The harness does not use `HP_LaserJet_1020_Plus`, does not accept
`hp1020queue://localhost`, does not preload the bundled proprietary firmware,
and does not change the installed queue or runtime.

The probe raises Xtensa `INTLEVEL` to 15 at entry because it services the USB
lane by polling and its fallback interrupt table is trap-only. This prevents a
maskable USB interrupt from diverting execution away from the polling loop.

## Prerequisites

Before a real run:

1. Finish the safer stock calibration, idle probe, read-only USB snapshot, and
   endpoint-0 marker stages.
2. Confirm all current offline bulk/parser build reports pass.
3. Make sure no normal print job is active.
4. Connect the printer by USB and freshly power-cycle it.
5. Obtain the explicit direct `usb://` backend URI. Do not substitute the
   working `hp1020queue://localhost` URI.

Do not run a hardware command unless the printer is physically present and the
operator is watching for unexpected mechanical activity.

## Offline Dry Run

Run:

```sh
scripts/run-usb-bulk-parser-draft-hardware-test.sh --dry-run
```

This rebuilds the custom `.dl`, requires the deterministic offline result and
all generated reports to pass, and validates the 36-byte payload structure and
digest. It does not enumerate USB, issue descriptor reads, invoke the USB
backend, upload firmware, or send data.

The expected payload SHA-256 is:

```text
935c947d40c020007ecf88534956defbd9e1764bde63708e025a2897a597978d
```

## Stage 1: Upload And Zero Counter Read

After a fresh power cycle, upload only the custom `.dl`:

```sh
HP1020_ALLOW_USB_BULK_PARSER_UPLOAD=1 \
  scripts/run-usb-bulk-parser-draft-hardware-test.sh \
  --upload \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...'
```

The exact expected product string before any probe data is:

```text
HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000
```

That exact result proves the custom code reached its endpoint-0 response path,
initialized the counters to zero, and returned a live product descriptor. A
quiet printer or a USB backend timeout by itself does not prove execution.

If the exact zero marker is not observed, stop. The harness refuses to send the
optional bulk data in that state.

## Stage 2: Separately Guarded Inert Data

Only after Stage 1 is known to work, start again from a fresh power cycle and
run with both independent opt-ins:

```sh
HP1020_ALLOW_USB_BULK_PARSER_UPLOAD=1 \
HP1020_ALLOW_USB_BULK_PARSER_DATA=1 \
  scripts/run-usb-bulk-parser-draft-hardware-test.sh \
  --upload \
  --send-probe-data \
  --device-uri 'usb://Hewlett-Packard/HP%20LaserJet%201020?serial=...'
```

The harness first requires the exact Stage 1 zero marker. It then sends exactly
36 bytes as one short transfer:

| Offset | Bytes | Meaning |
|---:|---:|---|
| `0x00` | `4` | ASCII `JZJZ` stream magic |
| `0x04` | `16` | `START_DOC`, size `16`, type `0`, no items, signature `0x5a5a` |
| `0x14` | `16` | `END_DOC`, size `16`, type `1`, no items, signature `0x5a5a` |

The exact expected product string afterward is:

```text
HP1020 B=00000024 D=00000001 C=00000002 E=00000000 U=00000000
```

This proves one completed bulk descriptor delivered all `0x24` bytes and the
framing parser recognized two controlled chunks with no errors or unknown
types. It does not exercise or prove printing.

## Outcome Meanings

- Exact zero marker before data: endpoint-0 custom execution is proven; bulk
  receive is not yet proven.
- Exact final marker: bulk receive, descriptor re-arm/completion, byte counting,
  and inert START_DOC/END_DOC framing are proven for this one transfer.
- Zero marker remains unchanged after data: endpoint-0 is still responding, but
  bulk completion or parser handoff is unproven.
- `B=00000024`, `C=00000002`, `E=U=0`, but another `D`: useful evidence that
  bytes and framing worked, but the expected one-descriptor transport shape did
  not; preserve the capture and do not call the exact test passed.
- Nonzero `E` or `U`: descriptor/framing behavior differed from the controlled
  contract; preserve the capture and stop.
- Stock product text, no matching device, or descriptor timeout: custom
  endpoint-0 execution is unproven.
- Silence or no paper movement alone: safety evidence only, not execution proof.

## Stop Conditions

Immediately disconnect power if there is any paper movement, motor, fuser,
laser/scanner, repeated mechanical noise, smoke, odor, or behavior beyond USB
transport. Do not retry repeatedly after a failed or ambiguous result.

## Evidence And Recovery

Real runs default to timestamped directories under:

```text
analysis/open-firmware-probes/usb-bulk-parser-draft/hardware-test-runs/
```

They retain the offline build log, exact inert payload and check, USB backend
stdout/stderr/back-channel files, descriptor JSON/Markdown before and after
data, extracted product strings, exit statuses, and `summary.md`.

After every upload attempt, power-cycle the printer. The custom firmware is
volatile, so power loss clears it and preserves the existing proprietary setup
for normal printing.
