# HP 1020 Queue Table Initializer Search

This pass searched for direct evidence of the runtime queue-ID table initializer.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020QueueTableInit.java`
- `analysis/queue-table-init/queue-table-init.md`
- `analysis/queue-table-init/decompiled/`

## Target

The queue send wrapper uses this runtime table:

```text
queue_control_block = *(0x1002c918 + queue_id * 4)
```

The goal was to find static code that writes queue object pointers into that table, especially:

```text
slot 8 -> 0x1002ee38  // Video Queue object
```

## Result

No direct static initializer write to `0x1002c918` was found in the Ghidra instruction scan.

Hits found:

| Function | Meaning |
|---:|---|
| `0x10013620` | wrapper that calls indexed queue send |
| `0x10013658` | wrapper that calls indexed queue send |
| `0x10013668` | indexed send function; reads `0x1002c918 + queue_id * 4` |
| `0x10017f18` | queue-create wrapper; calls queue-create core |

Interpretation:

- `0x10013668` is the only direct static user of the `0x1002c918` base found so far.
- Queue table population is likely indirect: a descriptor initialization routine may receive the table base through a pointer, or the boot/runtime code may copy descriptor groups into that table without embedding `0x1002c918` as an immediate at each write.
- Queue creation itself is confirmed, but queue-ID slot assignment is not yet proven by a direct write.

## Current Queue 8 Status

Queue `8` is still strongly likely to be `Video Queue`:

- producer: `0x10013d4c` sends message `0x0b` to queue `8`
- consumer: `0x10013c18` receives from `0x1002ee38`
- descriptor cluster ties `0x1002ee38` to `Video Queue` and `tVideo`

Remaining missing proof:

- the indirect initializer that places `0x1002ee38` into table slot `8`

## Next Search Direction

The next better search is not more direct `0x1002c918` scanning. It is descriptor-loop mapping:

1. Identify functions that walk descriptor regions around `0x100062c0` through `0x10006790`.
2. Find calls to `threadx_queue_create_candidate` via direct call or system-interface-table index `18`.
3. Track the queue object pointer and queue-name pointer arguments.
4. Track where queue object pointers are stored after creation.

