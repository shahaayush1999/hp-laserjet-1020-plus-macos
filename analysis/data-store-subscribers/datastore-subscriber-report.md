# HP 1020 Data-Store Subscribers

This pass maps the publish/subscribe side of the indexed firmware data store.

## Mechanism

- subscriber table pointer word: `0x10006490 -> 0x1002c56c`
- `0x10011258` registers a callback subscriber for an entry.
- `0x1001135c` registers a queue subscriber for an entry.
- `0x10010fd0` writes the data-store value, then walks the subscriber list for that entry.

Subscriber records are allocated through runtime service `0x14` and then linked into the per-entry list:

| Record bytes | Meaning |
|---:|---|
| `0x00..0x03` | data-store entry index |
| `0x04..0x07` | queue id for queue subscribers |
| `0x08..0x0b` | callback function pointer for callback subscribers |
| `0x0c..` | intrusive linked-list node |

When a value changes, queue subscribers receive message `0x2d` with entry id, new value, and a type class.
Callback subscribers are called directly as `callback(entry_id, new_value)`.

## Known Subscriber Registrations

| Entry | Kind | Target | Registrar | Meaning |
|---:|---|---|---|---|
| `0x01` | queue | queue `1` | `0x1000f324` `hp1020_print_mgr_thread_candidate` | Print manager registers queue notification |
| `0x18` | queue | queue `1` | `0x1000f324` `hp1020_print_mgr_thread_candidate` | Print manager registers queue notification for ONLINE changes |
| `0x18` | callback | `0x10013764` | `0x100139e4` `hp1020_control_panel_thread_candidate` | Control-panel path updates LED/state bytes for ONLINE |
| `0x19` | callback | `0x10013764` | `0x100139e4` `hp1020_control_panel_thread_candidate` | Control-panel path translates status-notify bits into LED/state bytes |
| `0x0f` | callback | `0x10016318` | `0x100163b0` `hp1020_engine_thread_candidate` | Engine maps DENSITY value into engine state byte at offset 0x59 |
| `0x10` | callback | `0x100162cc` | `0x100163b0` `hp1020_engine_thread_candidate` | Engine callback maps entry to id 0x200 and copies media/status record field |
| `0x11` | callback | `0x100162cc` | `0x100163b0` `hp1020_engine_thread_candidate` | Engine callback maps entry to id 0x201 and copies media/status record field |
| `0x12` | callback | `0x100162cc` | `0x100163b0` `hp1020_engine_thread_candidate` | Engine callback maps entry to id 0x202 and copies media/status record field |
| `0x13` | callback | `0x100162cc` | `0x100163b0` `hp1020_engine_thread_candidate` | Engine callback maps entry to id 0x203 and copies media/status record field |
| `0x14` | callback | `0x100162cc` | `0x100163b0` `hp1020_engine_thread_candidate` | Engine callback maps entry to id 0x204 and copies media/status record field |

## Current Interpretation

- Data-store entries `0x18` and `0x19` are not just PJL status fields; they also drive the control-panel/LED-ish state path.
- The known queue subscribers registered by PrintMgr use queue id `1`; the current queue map labels queue id `1` as `engMsgQ`, where message `0x2d` currently dispatches to the default/no-op block.
- Engine entries `0x0f..0x14` are live configuration/status inputs, because the engine thread registers direct callbacks before entering its receive loop.
- The shared engine callback at `0x100162cc` maps entries `0x10..0x14` to internal ids `0x200..0x204`, looks up both records through `0x100162b0`, then copies record field `+4` from the new value record to the mapped entry record.
- This gives a practical pruning method: for a print/status trace, prioritize entries with subscribers and then follow their callback/queue targets.
