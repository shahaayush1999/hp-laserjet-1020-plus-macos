# HP 1020 Status And PJL Fault Path Report

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020StatusPath.java`
- `analysis/status-path/status-path.md`
- `analysis/status-path/status-command-table.tsv`
- `analysis/status-path/status-decompiled/`

## Main Finding

The visible fault/status words are table entries in a PJL/status command table, not direct engine
event names.

The table pointer word is `0x10006148`, and the table base is `0x10003c8c`.
Each entry is `0x24` bytes. Important rows:

| Index | Kind | Name | Entry |
|---:|---:|---|---:|
| `4` | `0x05` | `JAMRECOVERY` | `0x10003d1c` |
| `12` | `0x0d` | `TONEREXP` | `0x10003e3c` |
| `15` | `0x10` | `SETERROR` | `0x10003ea8` |
| `16` | `0x03` | `PAPERLESS` | `0x10003ecc` |
| `18` | `0x12` | `FUSER` | `0x10003f14` |

## Bridging Functions

| Address | Working label | Meaning |
|---:|---|---|
| `0x1000a2a4` | `hp1020_status_word_to_pjl_code_candidate` | converts an internal status word into the numeric PJL `CODE=` value |
| `0x1000b870` | `hp1020_pjl_status_table_get_candidate` | reads values by PJL/status table row |
| `0x1000c8fc` | `hp1020_pjl_status_table_set_candidate` | parses string names and updates stored status/config values |
| `0x10010590` | `hp1020_status_mgr_thread_candidate` | consumes `StatusMgrQueue` messages and calls USTATUS builders |
| `0x10010838` | `hp1020_status_state_update_candidate` | normalizes status words and triggers StatusMgr/PJL-visible notification paths |
| `0x10010a8c` | `hp1020_status_event_store_candidate` | stores status words in a ring-like event buffer |

## Interpretation

The current evidence supports this path:

```text
engine status polling / preflight
  -> internal status/event word
  -> hp1020_status_state_update_candidate
  -> StatusMgrQueue / status event storage
  -> USTATUS DEVICE builders
  -> PJL CODE= / DISPLAY= response text
```

This means `PAPERLESS`, `FUSER`, `TONEREXP`, and `JAMRECOVERY` should not be treated as command
handlers in the engine dispatch table. They are PJL-visible names in a table used by the status
parser/response path.

The next narrow task is to finish naming the masks in `hp1020_status_state_update_candidate` and
connect those masks to the status table rows.
