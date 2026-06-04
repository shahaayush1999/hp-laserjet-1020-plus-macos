# HP 1020 Status Mask And Constant Report

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020StatusMasks.java`
- `analysis/status-masks/status-mask-map.md`
- `analysis/status-masks/status-data-refs.tsv`

## Main Finding

The status path now has a small set of concrete literal-pool constants worth naming.
The most useful function is `0x10010838` `hp1020_status_state_update_candidate`; it compares and
stores masked status words before triggering StatusMgr/PJL notifications.

## Key Constants

| Address | Value | Seen in | Current meaning |
|---:|---:|---|---|
| `0x10005f74` | `0xff00` | status code converter, status updater | low/mid status field mask |
| `0x10006418` | `0x1600` | status updater | status subfamily value |
| `0x1000641c` | `0x160a` | status updater | status subfamily value used in equality check |
| `0x10006420` | `0x1100` | status updater | status subfamily value |
| `0x10005e34` | `0x80000000` | status updater, engine poller | generic high-bit/error/fallback status word |
| `0x10006378` | `0x7c000000` | status updater | high-bit severity/category mask |
| `0x10005c84` | `0x02000000` | status updater | notification/job-facing status mask |
| `0x10005e74` | `0x00020000` | status updater, preflight | suppress/filter mask in notification path |
| `0x10006018` | `0x2711` | status word to PJL code | default PJL code base/value |
| `0x1000601c` | `0xa028` | status word to PJL code | PJL code base for mapped fault/status values |
| `0x10006014` | `0x1001be40` | status code offset lookup | pointer to 20-entry halfword-pair table |

The engine poller still emits full event/status words such as `0xe6100a01`, `0xe6101100`,
`0xfe001401`, `0xf6000300`, and `0xf6000400`. The status updater then folds selected words into
the PJL-facing status state.

## Interpretation

This pass reduced the next naming problem from "the whole firmware" to a compact status vocabulary:
`0xff00`, `0x1600`, `0x160a`, `0x1100`, `0x7c000000`, `0x80000000`, and the PJL code bases
`0x2711` / `0xa028`.

The PJL code path is now more concrete: mapped fault/status values use `0xa028` plus an offset
from the table at `0x1001be40`, producing codes such as `41000`, `41002`, `41009`, and `41034`.

The remaining hard part is not finding the functions anymore; it is proving which physical
condition each mask represents.
