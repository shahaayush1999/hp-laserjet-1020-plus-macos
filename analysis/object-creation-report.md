# HP 1020 Object Creation Pass

This pass maps RTOS object creation and validation around queues and threads.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020ObjectCreation.java`
- `analysis/object-creation/object-creation.md`
- `analysis/object-creation/decompiled/`

## Main Result

Queue creation is now identified:

| Function | Working name |
|---:|---|
| `0x10017f18` | `threadx_queue_create_candidate` |
| `0x100199a4` | `threadx_queue_create_core_candidate` |

`0x10017f18` has the expected create-wrapper shape:

- rejects null queue object
- rejects an object already marked `QUEU`
- validates message word size: `1`, `2`, `4`, `8`, or `0x10`
- validates backing storage length
- rejects invalid caller context
- delegates to `0x100199a4`

`0x100199a4` initializes the queue object:

- stores queue name
- stores message size
- computes queue capacity from storage length and message size
- initializes read/write pointers
- initializes suspended thread lists
- writes `QUEU` into the first queue object word
- links the queue into a global queue list

## Queue API Group

The queue-related system-interface group is now:

| Function | Working name |
|---:|---|
| `0x10017f18` | queue create |
| `0x10017f90` | queue delete |
| `0x10017fc8` | queue operation candidate |
| `0x10018000` | queue operation candidate |
| `0x10018040` | queue operation candidate |
| `0x1001807c` | queue operation candidate |
| `0x1001809c` | queue receive |
| `0x100180dc` | queue send |

The middle queue operations need final names, but they all validate `QUEU` and delegate to lower queue routines.

## Thread Creation

Thread creation wrapper:

- `0x10018274` `threadx_thread_create_candidate`

Observed behavior:

- rejects null thread object
- rejects object already marked `THRD`
- validates stack pointer and entry function
- requires stack size at least `200`
- validates priority and preemption threshold
- validates caller context
- delegates to `0x1001a610`

Ghidra currently cannot decompile `0x1001a610` usefully with the installed Xtensa language; it truncates immediately on an old-Xtensa instruction.

## Video Queue Descriptor Evidence

The video queue cluster is stronger now:

| Address | Value | Meaning |
|---:|---:|---|
| `0x1000676c` | `0x1002ee38` | video queue object pointer |
| `0x10006778` | `0x100056f0` | string region containing `Video Queue` |
| `0x10006784` | `0x100056fc` | string `tVideo` |
| `0x10006788` | `0x10013c18` | video thread entry |

This supports the existing queue map:

- queue `8`: `Video Queue` candidate
- consumer: `0x10013c18` `hp1020_video_thread_candidate`
- queue object: `0x1002ee38`

What remains unresolved is the runtime table assignment:

```text
queue_control_block = *(0x1002c918 + queue_id * 4)
```

We still need the initializer that writes `0x1002ee38` into slot `8`.

## Updated Next Step

The next high-value pass is to find the runtime queue table initializer:

- search for writes to `0x1002c918`
- search for writes to `0x1002c918 + N * 4`
- map static descriptor groups into queue table slots
- verify queue `8` from table assignment rather than producer/consumer inference

