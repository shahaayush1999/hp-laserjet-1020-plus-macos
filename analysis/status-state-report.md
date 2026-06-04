# HP 1020 Status State Machine Report

This report summarizes the decompiled `0x10010838` `hp1020_status_state_update_candidate`
function and the status-state object it updates.

Primary evidence:

- `analysis/status-path/status-decompiled/10010838_hp1020_status_state_update_candidate.c`
- `analysis/status-masks/status-data-refs.tsv`
- `analysis/status-mask-report.md`

## Status State Object

The status-state object is reached through pointer word `0x100063d8`, whose value is `0x1002adb4`.

Current layout:

| Offset | Width | Working field | Evidence |
|---:|---:|---|---|
| `0x00` | byte/word | status-state flag | written to `0` on high-bit/error fallback; written to `1` on recovery path |
| `0x04` | word | phase/state | compared with `2`, `3`, `4`; written to `2`, `3`, `4` |
| `0x08` | word | current status word | compared against new normalized status; overwritten before event storage |
| `0x0c` | word | pending/highest category status word | stores stronger `0x7c000000` category candidate while phase is `3` |
| `0x10` | word | transition status word | stores `0x1600`-family transition candidate |
| `0x14` | word | source/reason parameter | stores function argument `param_2`; compared in phase `4` |
| `0x18` | byte | pending/subscriber depth | read by StatusMgr; increments/decrements around message cases `0x2e`, `0x2f`, `0x30` |

## Important Masks

| Address | Value | Working meaning |
|---:|---:|---|
| `0x10005f74` | `0xff00` | status-family mask |
| `0x10006418` | `0x1600` | tracked transition/status family |
| `0x1000641c` | `0x160a` | special low-16 status value |
| `0x10006420` | `0x1100` | phase-4 status-family value |
| `0x10005e34` | `0x80000000` | high-bit error/fallback status |
| `0x10006378` | `0x7c000000` | high category/severity mask |
| `0x10005c84` | `0x02000000` | job-manager notification gate |
| `0x10006380` | `0x00100000` | notification subtype selector |
| `0x10005e74` | `0x00020000` | suppresses pending client notification after storage |
| `0x10005f78` | `0x0a00` | job-manager category selector for message payload `3` |
| `0x10006424` | `0x1c01` | alternate job-manager category selector for message payload `3` |

## Transition Behavior

The updater accepts:

```text
param_1 = internal status word
param_2 = source/reason code
```

High-level behavior:

1. Reads current phase at status-state offset `0x04`.
2. Normalizes `param_1` according to phase `2`, `3`, or `4`.
3. If a meaningful state change occurred, writes the new word at offset `0x08`.
4. Stores the word through `0x10010a8c` `hp1020_status_event_store_candidate`.
5. Raises event flag `0x19` with the new word.
6. If notification is not suppressed by mask `0x00020000`, calls `0x10010a3c`
   `hp1020_status_notify_pending_candidate`.

When the new status word has mask `0x02000000`, the updater also sends JobMgr queue `3` message
`0x0f`. The message payload is selected as:

| Condition | Payload |
|---|---:|
| `(status & 0xff00) == 0x0a00` or `(status & 0xffff) == 0x1c01` | `3` |
| `(status & 0x00100000) == 0` | `4` |
| otherwise | `1` |

## Interpretation

This function is a central bridge, not just a logger. It gates whether a hardware-derived status
word becomes:

- stored status history
- event flag `0x19`
- client USTATUS DEVICE notification
- JobMgr queue `3` message `0x0f`

The physical meanings of the masks are still conservative. The strongest current names are
structural: status family, phase, current status word, transition word, high-bit fallback,
notification gate, and suppression mask.
