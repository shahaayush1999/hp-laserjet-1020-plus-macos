# HP 1020 Descriptor Reference Pass

This pass searched for generic descriptor initialization code by scanning all functions for references into the static descriptor window:

```text
0x10005f00 .. 0x10006b80
```

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020DescriptorRefs.java`
- `analysis/descriptor-refs/descriptor-refs.md`
- `analysis/descriptor-refs/decompiled/`

## Result

The scan found many descriptor references, but not a clean generic queue-table initializer.

The highest-hit functions are mostly:

- normal task bodies using their own descriptor constants
- video/engine functions using their descriptor/MMIO constant tables
- RTOS scheduler and queue internals using runtime globals

Examples:

| Function | Meaning | Descriptor refs |
|---:|---|---:|
| `0x10014910` | video page preparation | `126` |
| `0x1000e414` | job manager thread | `87` |
| `0x10008ff0` | USB2 thread | `47` |
| `0x10015df8` | engine status poll | `40` |
| `0x100131b8` | runtime allocator/service | `30` |
| `0x100176c8` | scheduler helper | `28` |

This is useful negative evidence. It means the queue table initializer is not obviously a normal function that directly walks descriptor names and writes `0x1002c918`.

## What Was Found

The scan confirms the descriptor-heavy areas already mapped:

- USB descriptor/task region around `0x10005f00`
- job/print/status descriptor region around `0x100062c0`
- delay/data/control-panel descriptor region around `0x10006430`
- video descriptor region around `0x10006760`
- engine descriptor region around `0x10006920`
- scheduler/runtime descriptor region around `0x10006a90`

## Queue Table Status

Still true:

- queue send by ID reads from `0x1002c918 + queue_id * 4`
- queue creation is known: `0x10017f18` / `0x100199a4`
- `Video Queue` object is `0x1002ee38`
- queue `8` strongly points to `Video Queue`

Still not proven:

- the exact write that places `0x1002ee38` into slot `8`

## Updated Search Direction

Further progress on queue slot assignment likely requires one of:

1. tracing boot/runtime initialization functions with better Xtensa support
2. emulating or instrumenting startup enough to observe BSS writes
3. using hardware/live memory observation, if a debug path exists
4. accepting queue `8` as inferred from producer/consumer/descriptors and moving to the next hardware-register semantics pass

