# HP 1020 Engine Status Poll Branch Map

> Routing correction (2026-09-08): [stock registration](queue-routing/registration.md) proves queue 0 is engine and queue 1 is PrintMgr. Older routing interpretations below are historical; event 0x17 and datastore notification 0x2d reach PrintMgr, so their former missing-consumer conclusions are superseded.


This report summarizes `0x10015df8` `hp1020_engine_status_poll_candidate`.

Primary evidence:

- `analysis/status-path/status-decompiled/10015df8_hp1020_engine_status_poll_candidate.c`
- `analysis/status-masks/status-data-refs.tsv`
- `analysis/engine-event-report.md`

## Register Reads

The poller uses `0x10015c68` `hp1020_engine_status_io_candidate` to issue small command IDs and
read 16-bit status values from the engine handshake path.

Observed command/status reads:

| Command | Working role |
|---:|---|
| `1` | primary engine status word |
| `0x20` | secondary status word for `0xf600....` branch |
| `2` | status word for `0xe610....` / `0x20001607` branch |
| `0x16` | substatus word for `0xe6000d..` branch |
| `0x13` | substatus word for `0xe6100b0a` / `0xe6100b0b` branch |

The lower I/O helper uses:

| Address | Value | Working role |
|---:|---:|---|
| `0x1000691c` | `0xb050000c` | engine status/ready register candidate |
| `0x10006928` | `0xb0500004` | engine command/control register candidate |
| `0x10005f20` | `0x00010000` | command/status handshake bit |

## Event Selection

The poller selects an event/status word `uVar6`, stores it at engine state offset `0x60`, and sends
engine queue message `0x17` when the selected word changes or a forced poll requests it.

| Selected event word | Condition in poller | Confidence |
|---:|---|---|
| `0x04800100` | default when primary status passes the `0x4040` check | medium |
| `0xf6000300` | secondary command `0x20`: `(0x800 & status_0x20) != 0` | medium |
| `0xf6000400` | secondary command `0x20`: `(status_0x20 & 0x400) != 0` while `0x800` is clear | medium |
| `0xe6100a01` | command `2`: normal/settled-looking fallback after nested tests | medium |
| `0xe6100800` | command `2`: `0x4000` branch or substatus `0x16` plus `0x40` branch | medium |
| `0x20001607` | command `2`: `(status_2 & 0x424) != 0` | medium |
| `0xe6101100` | command `2`: `(status_2 & 0x1000) != 0` | medium |
| `0xe6100e00` | command `2`: `(status_2 & 0x2000) != 0` | medium |
| `0x80000000` | command `2`: fallback when primary status bit `0x40` is set and status `2` bit `0x200` is clear | low |
| `0xe6000d03` | command `0x16`: substatus has bit `0x10` path | medium |
| `0xe6000d06` | command `0x16`: substatus has bit `0x08` path | medium |
| `0xe6000d04` | command `0x16`: substatus has bit `0x04` path | medium |
| `0xe6100b0a` | command `0x13`: default for `(status_0x13 >> 1) & 0x3f` | medium |
| `0xe6100b0b` | command `0x13`: cases `0x10`, `0x14`, `0x18` | medium |

## Side Effects

When the selected event differs from the previous engine state word at offset `0x60`, the poller:

1. stores the new event word at engine-state offset `0x60`
2. sends engine queue `1` message `0x17`
3. may call `FUN_10015dd0(...)` around transitions from low-16 status `0x0100` to `0x0a04`
4. may trigger video reset dispatch when latched flags at engine-state offsets `0x38`, `0x2c`, or
   `0x3c` and primary status bits change

## Interpretation

This is the strongest current evidence for the bridge from physical engine status bits to firmware
event words. It still does not prove which bit is paper-empty, fuser, cover, toner, or jam. What it
does prove is the shape of the decision tree and which commands/register reads feed each emitted
event word.
