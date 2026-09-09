# HP 1020 Data-Store Subscriber Report

> Routing correction (2026-09-08): [stock registration](queue-routing/registration.md) proves queue 0 is engine and queue 1 is PrintMgr. Older routing interpretations below are historical; event 0x17 and datastore notification 0x2d reach PrintMgr, so their former missing-consumer conclusions are superseded.


Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020DataStoreSubscribers.java`
- `analysis/data-store-subscribers/datastore-subscriber-report.md`
- `analysis/data-store-subscribers/datastore-subscribers.tsv`
- `analysis/data-store-subscribers/decompiled/`

## Main Finding

The indexed firmware data store has a publish/subscribe layer. This is the first clean firmware
mechanism found so far for answering "what code wakes up when this state changes?"

The subscriber table pointer is concrete:

| Pointer word | Points to | Meaning |
|---:|---:|---|
| `0x10006490` | `0x1002c56c` | per-entry data-store subscriber list table |

Two registration helpers populate that table:

| Address | Working label | Meaning |
|---:|---|---|
| `0x10011258` | `hp1020_datastore_register_callback_subscriber_candidate` | registers direct `callback(entry_id, new_value)` subscribers |
| `0x1001135c` | `hp1020_datastore_register_queue_subscriber_candidate` | registers queue-message subscribers |

The write helper at `0x10010fd0` updates an entry, then walks the matching subscriber list. Queue
subscribers receive message `0x2d`; callback subscribers are called directly.

## Known Live Subscriptions

| Entry | Subscriber | Registered by | Meaning |
|---:|---|---|---|
| `0x01` | queue `1` | print manager `0x1000f324` | queue notification for entry changes |
| `0x18` | queue `1` | print manager `0x1000f324` | queue notification for ONLINE changes |
| `0x18` | callback `0x10013764` | control-panel thread `0x100139e4` | ONLINE drives control-panel/LED-ish state |
| `0x19` | callback `0x10013764` | control-panel thread `0x100139e4` | status notification bits drive control-panel/LED-ish state |
| `0x0f` | callback `0x10016318` | engine thread `0x100163b0` | DENSITY maps into engine state byte offset `0x59` |
| `0x10..0x14` | callback `0x100162cc` | engine thread `0x100163b0` | media/status entries map to internal ids `0x200..0x204` |

The callback at `0x100162cc` decompiles cleanly: it maps data-store entries `0x10..0x14` to
internal ids `0x200..0x204`, looks up records through `0x100162b0`, then copies record field `+4`
from the new-value record into the mapped engine record. Ghidra recognizes `0x100162b0` as a tiny
callee but cannot decompile it cleanly with the current Xtensa model, so its role is inferred from
the caller contract.

## Why This Matters

This gives a practical pruning strategy for future work:

```text
state/config write
  -> data-store write helper
  -> subscriber list for that entry
  -> callback or queue message
  -> engine/control-panel/print-manager path
```

That is a better route than trying to understand every firmware function equally. For print/status
analysis, the next high-value static target is the callback/queue fallout from entries with
subscribers, especially `0x18`, `0x19`, and `0x0f..0x14`.

One correction from the follow-up PrintMgr pass: the known queue subscribers registered by PrintMgr
use queue id `1`. The current queue map labels queue id `1` as `engMsgQ`, where message `0x2d`
currently dispatches to the default/no-op block. So this subscriber path should not be assumed to
land in PrintMgr until the queue-id mapping or a queue-0 `0x2d` producer is proven.
