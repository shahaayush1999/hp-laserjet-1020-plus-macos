# HP 1020 Status And PJL Fault Path Report

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020StatusPath.java`
- `analysis/status-path/status-path.md`
- `analysis/status-path/status-command-table.tsv`
- `analysis/status-path/status-code-offset-table.tsv`
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
| `0x1000a280` | `hp1020_status_code_offset_lookup_candidate` | looks up the offset added to PJL status-code base `0xa028` |
| `0x1000a2a4` | `hp1020_status_word_to_pjl_code_candidate` | converts an internal status word into the numeric PJL `CODE=` value |
| `0x1000b870` | `hp1020_pjl_status_table_get_candidate` | reads values by PJL/status table row |
| `0x1000c8fc` | `hp1020_pjl_status_table_set_candidate` | parses string names and updates stored status/config values |
| `0x10010590` | `hp1020_status_mgr_thread_candidate` | consumes `StatusMgrQueue` messages and calls USTATUS builders |
| `0x10010838` | `hp1020_status_state_update_candidate` | normalizes status words and triggers StatusMgr/PJL-visible notification paths |
| `0x10010a8c` | `hp1020_status_event_store_candidate` | stores status words in a ring-like event buffer |

## PJL Code Offset Table

`0x1000a2a4` uses a second table through pointer word `0x10006014`.
The table base is `0x1001be40`, with 20 entries. Each entry is two big-endian halfwords:

```text
input/status index -> PJL CODE offset
```

Mapped fault/status values use base `0xa028` (`41000`) plus the table offset.
Examples:

| Input | Offset | PJL CODE |
|---:|---:|---:|
| `0x0000` | `0x00` | `41000` |
| `0x0001` | `0x02` | `41002` |
| `0x0005` | `0x03` | `41003` |
| `0x0025` | `0x09` | `41009` |
| `0x0103` | `0x1f` | `41031` |
| `0x0106` | `0x22` | `41034` |

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
connect those masks to the status table rows and offset-table inputs.
