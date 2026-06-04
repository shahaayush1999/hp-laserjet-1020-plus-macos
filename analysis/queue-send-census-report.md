# HP 1020 Queue Send Census Report

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020QueueSendCensus.java`
- `analysis/queue-send-census/queue-send-census.md`
- `analysis/queue-send-census/queue-send-sites.tsv`
- `analysis/queue-send-census/decompiled/`

## Main Finding

The global queue-send census found `55` queue-send call sites across recovered functions.

For PrintMgrQueue / queue `0`, the statically proven constant messages are:

- `0x18` startup/restart
- `0x0d`
- `0x0b`
- `0x1a`
- `0x4a`
- `0x11`

The pass found `0` direct static sends of message `0x2d` to queue `0`.

The only proven queue-send site that emits message `0x2d` is the data-store writer
`0x10010fd0`; it sends through a queue id read from the subscriber record, not through a direct
constant queue argument.

## Interpretation

This strengthens the corrected PrintMgr result:

```text
PrintMgr has a real 0x2d handler
but static send-site census does not find a direct queue-0 0x2d producer
```

So the remaining explanation is one of:

- a dynamic subscriber queue id points to PrintMgr in a path not yet proven by the queue map
- a computed/dynamic producer sends queue `0`, message `0x2d` in a way this static pass cannot resolve
- the PrintMgr `0x2d` case is defensive/shared-state code that is rarely or never used in the normal print path

The practical next reverse-engineering target is to follow the known queue `0` messages, especially
`0x0b`, `0x0d`, `0x11`, `0x18`, and `0x1a`, because they are now stronger proven PrintMgr inputs
than `0x2d`.
