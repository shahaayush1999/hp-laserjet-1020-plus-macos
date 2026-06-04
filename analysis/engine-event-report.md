# HP 1020 Engine Event `0x17` Payload Map

This pass narrows the engine queue message `0x17`. It is not just a bare message ID: the firmware sends a four-word message where word 0 is `0x17` and word 1 carries a status/event code.

Working layout:

```text
word0 = 0x17
word1 = status/event code
word2 = 0
word3 = 0
```

The complete event-code table is in `analysis/engine-events/engine-0x17-events.tsv`.

## Main Senders

| Sender | Role | Event-code source |
|---:|---|---|
| `0x10015c68` `hp1020_engine_status_io_candidate` | engine status/control I/O | timeout/failure code `0xfe001401` |
| `0x10015df8` `hp1020_engine_status_poll_candidate` | status polling and state transition detector | computed status code from engine registers |
| `0x100160a8` `hp1020_engine_preflight_candidate` | engine preflight/startup wait | preflight start `0xe6101100`, timeout `0xfe001401` |
| `0x10013d4c` `hp1020_video_reset_dispatch_candidate` | video reset/error bridge into engine queue | fixed video reset codes |

## Concrete Event Codes

| Event code | Source | Working interpretation |
|---:|---|---|
| `0xfe001401` | status I/O and preflight | command/preflight timeout or failure |
| `0xe6101100` | preflight and status poll | engine preflight/status transition |
| `0xe6100a01` | status poll | ready/ok-looking status transition |
| `0xf6000300` | status poll | status register `0x20` bitmask branch |
| `0xf6000400` | status poll | status register `0x20` bit `0x400` branch |
| `0xe6100800` | status poll | engine status register `2` mask branch |
| `0x20001607` | status poll | engine status register `2` bits `0x424` branch |
| `0xe6100e00` | status poll | engine status register `2` mask branch |
| `0x80000000` | status poll | fallback/unknown status |
| `0xe6000d03` | status poll | substatus register `0x16` branch |
| `0xe6000d06` | status poll | substatus register `0x16` branch |
| `0xe6000d04` | status poll | substatus register `0x16` branch |
| `0xe6100b0a` | status poll | register `0x13` default subcase |
| `0xe6100b0b` | status poll | register `0x13` cases `0x10`, `0x14`, `0x18` |
| `0xe6e01201` | video reset dispatch | video reset case `3` |
| `0xe6e01202` | video reset dispatch | video reset case `4` |
| `0xeee01b02` | video reset dispatch | video reset case `5` |
| `0xeee01b04` | video reset dispatch | video reset case `6` |
| `0xeee01b01` | video reset dispatch | video reset cases `2` and `7` |

## Why This Matters

This turns engine message `0x17` from "some status event" into a structured event family. That matters because `0x17` is emitted by both the engine hardware polling path and the video reset path, so it is probably the bridge between hardware state and the rest of the print pipeline.

## Consumer Status

Important negative finding: the recovered `hp1020_engine_message_dispatch_candidate` switch does not currently show a `case 0x17`.

Confirmed engine dispatch cases remain:

- `0x0b`
- `0x0d`
- `0x0f`
- `0x11`
- `0x18`
- `0x19`
- `0x1a`
- `0x40`

So `0x17` is a proven produced message, but its direct consumer is not yet proven. Current possibilities:

- Ghidra missed or simplified an Xtensa switch branch.
- `0x17` intentionally wakes the engine queue and falls through a default/no-op path after side effects elsewhere.
- Queue `1` has an additional consumer/dispatch path not yet mapped.
- Some `0x17` events should actually be interpreted as event-registry payloads and not ordinary engine dispatch work.

The adjacent event registry at `0x10006490` is separate. It registers event IDs such as `0x0f` through `0x14` and emits callback/`0x2d` style notifications, but it does not by itself explain the engine queue `0x17` path.

Queue receive search currently supports only one `engMsgQ` receiver:

```text
0x100163b0 hp1020_engine_thread_candidate
  threadx_queue_receive_wait_candidate(PTR_DAT_100069bc, &message, 0x32)
```

So the likely unresolved point is inside or immediately around the engine-thread dispatch path, not a second obvious queue consumer.

The event names are still conservative. The next useful step is to trace queue `1` consumers and all references to message word `0x17`, then connect these event codes to outward PJL/status strings like `PAPERLESS`, `TONEREXP`, `FUSER`, and `JAM`.
