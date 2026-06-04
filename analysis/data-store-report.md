# HP 1020 Firmware Data-Store Report

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020DataStore.java`
- `analysis/data-store/data-store-map.md`
- `analysis/data-store/data-store-table.tsv`
- `analysis/data-store/data-store-helper-uses.tsv`
- `analysis/data-store/data-store-decompiled/`

## Main Finding

The helper group around `0x10011178` and `0x10010f54` is a central indexed firmware state/config
API, not just a small PJL helper:

| Address | Working label | Meaning |
|---:|---|---|
| `0x10011178` | `hp1020_datastore_get_value_candidate` | returns byte/halfword/word values from indexed data-store entries |
| `0x100111b4` | `hp1020_datastore_lock_entry_candidate` | locks the indexed mutex entry and returns the entry value pointer |
| `0x100111d8` | `hp1020_datastore_unlock_entry_candidate` | unlocks the indexed mutex entry |
| `0x10010f54` | `hp1020_datastore_read_locked_candidate` | copies an indexed entry into caller storage after locking it |
| `0x10010fd0` | `hp1020_datastore_write_notify_unlock_candidate` | writes an indexed entry, notifies subscribers, then unlocks it |

The descriptor pointers are now concrete:

| Pointer word | Points to | Meaning |
|---:|---:|---|
| `0x1000647c` | `0x1001ce14` | data descriptor table, entry size `0x18` |
| `0x10006464` | `0x1002c0b0` | per-entry mutex/lock table, entry size `0x1c` |
| `0x10006490` | `0x1002c56c` | per-entry subscriber list table |

The data descriptor table currently maps entries `0x00` through `0x25`.
The subscriber side is mapped separately in `analysis/data-store-subscriber-report.md`.

## Status-Relevant Entries

| Index | Type | Current/static value | Current interpretation |
|---:|---:|---|---|
| `0x18` | `0` | `u8:0` | `ONLINE=` boolean used by the USTATUS DEVICE builder |
| `0x19` | `2` | `u32:0x0` | USB/status notification enable flag |
| `0x1a` | `4` | pointer/string slot | `DISPLAY="..."` string pointer used by the USTATUS DEVICE builder |
| `0x1b` | `2` | `u32:0x0` | StatusMgr USTATUS timing/enable slot |
| `0x1d` | `4` | pointer/string slot | PJL INFO capability/state aggregate |
| `0x1e` | `3` | `HP LaserJet 1020` | PJL command/config response string aggregate |
| `0x1f` | `4` | pointer/string slot | status-code lookup state object pointer |
| `0x21` | `0` | runtime byte slot | TONEREXP/status writable backing slot |
| `0x22` | `2` | runtime word slot | PQENHANCE/status writable backing slot |
| `0x23` | `0` | runtime byte slot | LINEAUGMENT/status writable backing slot |
| `0x24` | `0` | runtime byte slot | JAMRECOVERY/status alternate backing slot |
| `0x25` | `0` | runtime byte slot | PAPERLESS/status variable backing slot |

## Interpretation

`CODE=` and `DISPLAY=` are now separated:

```text
status word
  -> 0x1000a2a4
  -> numeric PJL CODE=

data-store entry 0x1a
  -> 0x1000b624
  -> DISPLAY="..."
```

So the numeric `410xx` status-code table does not directly carry the display text.
Display text is held in a mutable data-store slot.

The generated helper-use TSV is useful for navigation, but it is instruction-window based. Treat the
data descriptor table itself as strong evidence and the use counts as hints to nearby code paths.
