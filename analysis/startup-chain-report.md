# HP 1020 Startup Chain Notes

This note follows the startup path after the boot ABI pass.

## Current Startup Chain

The firmware startup path currently looks like this:

```text
ELF entry 0x100167a8
  -> pointer at 0x10006a14
  -> 0x10006cd0 low-level CPU/TLB init candidate
  -> RTOS/interrupt scheduler region around 0x10016c5c-0x100188f0
  -> task descriptors and ThreadX-style queues
```

This is a better mental model than "main() starts the printer firmware." The visible ELF entry is a tiny bridge into a lower-level runtime.

## Entry Bridge

`0x100167a8` `hp1020_elf_entry_candidate`:

```c
rsil(1);
wsr(in_INTENABLE,0);
wsr(0,0x11);
rsync();
(*DAT_10006a14)(0x11,DAT_10006a14);
```

The pointer value near `0x10006a14` is:

| Address | Value | Meaning |
|---:|---:|---|
| `0x10006a14` | `0x10006cd0` | low-level CPU/TLB init candidate |
| `0x10006a18` | `0x1001d498` | data/runtime pointer |
| `0x10006a1c` | `0x10016c5c` | runtime wrapper candidate |

## Low-Level Init

`0x10006cd0` looks like the reset-vector class of code, not printer logic.

Observed behavior:

- disables interrupts
- clears `CCOUNT`
- initializes Xtensa window registers
- clears loop and debug registers
- clears exception save registers
- writes instruction/data TLB entries

Ghidra truncates this decompile because some old-Xtensa instructions are not understood cleanly, but the CPU bring-up intent is clear.

This means a custom firmware prototype cannot be just arbitrary C compiled into an ELF. It must either reproduce or safely bypass this CPU/runtime bring-up.

## Interrupt Dispatch

`0x10016d6f` is an interrupt dispatch candidate.

It:

- reads interrupt set / interrupt enable state
- chooses the highest pending interrupt via leading-zero count logic
- calls `handler_table[interrupt_index]`
- finally calls through the function pointer at `0x10006a64`

Relevant descriptor words:

| Address | Value | Meaning |
|---:|---:|---|
| `0x10006a58` | `0x1001861c` | first exception/interrupt entry candidate |
| `0x10006a5c` | `0x00040001` | special-register or interrupt mask constant |
| `0x10006a60` | `0x1001d4ac` | interrupt handler table pointer |
| `0x10006a64` | `0x100187e0` | scheduler/return path candidate |
| `0x10006a68` | `0x1001d4a8` | interrupt accounting/state pointer |

The handler table at `0x1001d4ac` is mostly filled with `0x10017150`, which is likely a default interrupt handler. That is a normal RTOS shape.

## First Scheduler/Context Paths

`0x1001861c`:

- saves low-level CPU state
- stores stack/context pointers
- increments a runtime counter
- first time through, calls `0x10016d6f`

`0x100188f0`:

- waits for a current-thread pointer
- writes exception/special registers from saved thread context
- uses `rfe()` to restore execution

This looks like first-scheduler-start / context-restore logic.

## System Timer Thread

`0x1001788c` `hp1020_system_timer_thread_candidate`:

- walks timer/delay records
- invokes timer callbacks
- updates current thread scheduling state
- calls lower scheduler helpers such as `FUN_100176c8`

Descriptor region:

| Address | Value | Meaning |
|---:|---:|---|
| `0x10006aec` | `0x10005c6c` | string `System Timer Thread` |
| `0x10006af0` | `0x1001788c` | system timer thread entry |
| `0x10006b0c` | `0x424c4f43` | ASCII `BLOC` |
| `0x10006b10` | `0x42595445` | ASCII `BYTE` |
| `0x10006b14` | `0x54485244` | ASCII `THRD` |

`BLOC`, `BYTE`, and `THRD` look like RTOS object signatures/magic values, not printer-specific protocol strings.

## What This Changes

The firmware is now split into:

1. upload wrapper
2. boot/vector/CPU init
3. RTOS runtime services
4. queue-driven printer subsystems
5. engine/video hardware code

That is good news for analysis because the layers are separable.

It also means the realistic minimal prototype target is narrower:

- either preserve the HP/ThreadX-like startup and replace behavior after scheduler startup
- or build a custom ELF that replicates enough vector/interface/runtime shape to boot

The next useful pass is to label RTOS primitives around `0x100175c0` through `0x1001a590`, because those functions explain task creation, scheduler start, queue creation, and timer behavior.

