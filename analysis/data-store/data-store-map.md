# HP 1020 Data-Store Map

This maps the indexed state table used by the helper trio around `0x10011178`.

## Helper Trio

| Address | Working label | Behavior |
|---:|---|---|
| `0x10011178` | `hp1020_datastore_get_value_candidate` | reads an indexed entry and returns an integer value for byte/halfword/word entries |
| `0x100111b4` | `hp1020_datastore_lock_entry_candidate` | locks the matching mutex entry and returns the entry's value pointer |
| `0x100111d8` | `hp1020_datastore_unlock_entry_candidate` | unlocks the matching mutex entry |
| `0x10010f54` | `hp1020_datastore_read_locked_candidate` | copies the indexed entry value into caller storage after locking the entry; callers must release or write back |
| `0x10010fd0` | `hp1020_datastore_write_notify_unlock_candidate` | writes caller storage into the indexed entry, notifies subscribers, then unlocks the entry |

- data descriptor table pointer word: `0x1000647c -> 0x1001ce14`
- lock/mutex table pointer word: `0x10006464 -> 0x1002c0b0`
- data entry size: `0x18`; lock entry size: `0x1c`

## Important Entries

| Index | Type | Current/static value | Pointer string | Working note | Helper uses |
|---:|---:|---|---|---|---:|
| `0x00` | `0` | `` | `` |  | `1` |
| `0x01` | `4` | `` | `` |  | `2` |
| `0x04` | `3` | `` | `` | event-flag slot used by JAMRECOVERY/status flag path | `0` |
| `0x09` | `0` | `` | `` | TIMEOUT status variable backing slot | `1` |
| `0x0a` | `0` | `` | `` | AUTOCONT status variable backing slot | `1` |
| `0x0c` | `0` | `` | `` |  | `2` |
| `0x0d` | `0` | `` | `` | TONEREXP/status variable backing slot | `2` |
| `0x0f` | `0` | `` | `` | DENSITY/status variable backing slot | `1` |
| `0x10` | `1` | `` | `` | SETERROR/status variable backing slot | `3` |
| `0x11` | `1` | `` | `` | MEDIA513/status variable backing slot | `2` |
| `0x12` | `1` | `` | `` | MEDIA514/status variable backing slot | `2` |
| `0x13` | `1` | `` | `` | MEDIA515/status variable backing slot | `2` |
| `0x14` | `1` | `` | `` | MEDIA516/status variable backing slot | `2` |
| `0x18` | `0` | `u8:0` | `` | PJL ONLINE boolean used by USTATUS DEVICE builder | `1` |
| `0x19` | `2` | `u32:0x0` | `` | USB/status notification enable flag | `3` |
| `0x1a` | `4` | `ptr/string:` | `` | PJL DISPLAY string pointer used by USTATUS DEVICE builder | `0` |
| `0x1b` | `2` | `u32:0x0` | `` | StatusMgr USTATUS timing/enable slot | `1` |
| `0x1d` | `4` | `ptr/string:` | `` | PJL INFO capability/state aggregate | `8` |
| `0x1e` | `3` | `ptr/string:HP LaserJet 1020` | `HP LaserJet 1020` | PJL command parser writable aggregate | `0` |
| `0x1f` | `4` | `ptr/string:` | `` | status-code lookup state object pointer | `2` |
| `0x20` | `2` | `u32:0x1` | `` | video/page preparation config value | `1` |
| `0x21` | `0` | `` | `` | TONEREXP/status writable backing slot | `0` |
| `0x22` | `2` | `` | `` | PQENHANCE/status writable backing slot | `0` |
| `0x23` | `0` | `` | `` | LINEAUGMENT/status writable backing slot | `0` |
| `0x24` | `0` | `` | `` | JAMRECOVERY/status alternate backing slot | `1` |
| `0x25` | `0` | `` | `` | PAPERLESS/status variable backing slot | `2` |

## Interpretation

- `DISPLAY="..."` in USTATUS DEVICE is built from data-store entry `0x1a`, not from the numeric `CODE=` conversion table.
- `ONLINE=` in the same response is read through entry `0x18`.
- Status command-table rows such as `PAPERLESS`, `TONEREXP`, and media variables read backing values through this table.
- `0x10010f54` / `0x10010fd0` are the main read-modify-write path for mutable PJL/status backing slots.
- The helper trio is therefore a central firmware state/config API, not just PJL parsing glue.
