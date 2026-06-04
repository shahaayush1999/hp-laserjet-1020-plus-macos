# HP 1020 PrintMgr 0x2d Fallout Report

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020PrintMgrFallout.java`
- `analysis/printmgr-fallout/printmgr-fallout-report.md`
- `analysis/printmgr-fallout/printmgr-dispatch-table.tsv`
- `analysis/printmgr-fallout/printmgr-dispatch-windows.tsv`
- `analysis/printmgr-fallout/decompiled/`

## Main Finding

The data-store notification message shape is real: queue subscribers receive message `0x2d` with
entry id, new value, and type class. But the currently known queue subscribers registered by
PrintMgr for entries `0x18` and `0x01` use subscriber queue id `1`.

The current queue map labels queue id `1` as `engMsgQ`, not `PrintMgrQueue`. The engine dispatch
table maps message `0x2d` to its default/no-op block. So the subscriber path is not yet proven to
wake PrintMgr.

Separately, PrintMgr has a real `0x2d` dispatch case:

| Message | Target | Meaning |
|---:|---:|---|
| `0x2d` | `0x1000f497` | PrintMgr table case that tests entry/value payload shape |

That case can fall into `0x1000f574`, and `0x1000f574` calls `0x1000fcb0`, which explicitly handles
`message == 0x2d` and `entry == 1`.

## Corrected Interpretation

There are two related but not-yet-joined facts:

```text
data-store write
  -> queue subscriber message 0x2d
  -> known subscriber queue id 1
  -> current queue map: engine queue
  -> current engine dispatch: 0x2d default/no-op
```

```text
PrintMgrQueue message 0x2d
  -> PrintMgr dispatch target 0x1000f497
  -> scheduler/helper 0x1000f574
  -> notification-state helper 0x1000fcb0
  -> possible media/status writeback
```

That means the PrintMgr `0x2d` handler is real, but its queue-0 producer is unresolved.

## Why This Matters

This prevents a bad shortcut: we should not assume every `0x2d` datastore notification reaches
PrintMgr. For future testing, this gives a concrete question: when a real print/status event occurs,
does queue id `1` actually behave as mapped, or is there another producer that sends `0x2d` into
queue id `0`?
