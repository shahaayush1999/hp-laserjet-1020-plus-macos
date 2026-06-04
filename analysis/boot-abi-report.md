# HP 1020 Boot ABI Pass

This pass maps the firmware startup shape and the runtime interface table.

Generated artifacts:

- `analysis/ghidra-scripts/MapHp1020BootAbi.java`
- `analysis/boot-abi/boot-abi.md`
- `analysis/boot-abi/decompiled/`

## Main Result

The firmware is not just "some Xtensa code in an ELF." It has a specific boot/runtime shape:

- Xtensa vector sections at `0x10000000`
- `.sys_interface_table` at `0x10000370`
- normal `.rodata`, `.text`, `.data`, and `.bss`
- reset vector code at `0x10100020`
- ELF entry point at `0x100167a8`

That matters for any open firmware experiment because the upload wrapper is only the outer container. The boot ROM likely expects at least some of this internal shape.

## ELF Entry

ELF header entry point:

- `0x100167a8`

Ghidra decompiles it as a small function:

```c
rsil(1);
wsr(in_INTENABLE,0);
wsr(0,0x11);
rsync();
(*DAT_10006a14)(0x11,DAT_10006a14);
```

Interpretation:

- disables or masks interrupts
- writes an Xtensa special register value
- calls through a function pointer / dispatch pointer around `0x10006a14`

This suggests the ELF entry is not the whole C runtime startup. It is a small bridge into an existing startup/runtime path.

## Reset Vector

Reset vector section:

- `0x10100020`
- size `736` bytes

Ghidra only partially decompiles it because the vector code uses low-level Xtensa instructions and some instructions are not understood cleanly by this Ghidra language variant.

Still, the decompile shows real early CPU setup:

- disables interrupt enable
- zeroes `CCOUNT`
- initializes window registers
- clears loop registers
- clears debug/break registers
- writes TLB entries
- touches an MMIO-looking register family around `0xb0800008`
- starts clearing memory ranges

This is useful because it separates "printer app firmware" from "CPU bring-up code."

## System Interface Table

`.sys_interface_table`:

- address: `0x10000370`
- size: `0x12c`
- entries: `75` 32-bit function pointers

Known entries now include:

| Index | Function pointer | Working label |
|---:|---:|---|
| `22` | `0x1001809c` | `threadx_queue_receive_wait_candidate` |
| `23` | `0x100180dc` | `threadx_queue_send_candidate` |
| `28` | `0x100181a4` | `threadx_memory_or_copy_candidate` |
| `40` | `0x100175c0` | `threadx_or_timer_service_candidate` |
| `46` | `0x1001766c` | `threadx_sleep_candidate` |
| `59` | `0x100131b8` | `hp1020_runtime_service_candidate` |
| `60` | `0x10013408` | `hp1020_runtime_service_2_candidate` |
| `61` | `0x100116ec` | `hp1020_system_service_candidate` |
| `62` | `0x10010f54` | `hp1020_event_flag_get_candidate` |
| `63` | `0x10010fd0` | `hp1020_event_flag_set_candidate` |
| `71` | `0x10011258` | `hp1020_register_event_handler_candidate` |
| `73` | `0x1001135c` | `hp1020_register_or_signal_message_candidate` |

The rest are still generic `hp1020_sys_interface_NN_candidate` names.

## Runtime Services

One important table entry is:

- `0x100131b8` `hp1020_runtime_service_candidate`

Its decompile looks like an allocator or memory-block manager:

- aligns requested sizes
- walks block metadata
- calls `threadx_memory_or_copy_candidate`
- manipulates BSS/data state around `0x1002c90c`

This reinforces the idea that the firmware carries a small embedded runtime with ThreadX-style services rather than only printer-specific code.

## Updated Prototype Implication

For a minimal custom firmware experiment, the current best guess is:

1. Keep the HP-style ACL/PJL upload wrapper.
2. Keep a date-prefixed Xtensa ELF.
3. Keep the same broad ELF section/program-header shape.
4. Preserve or intentionally stub the vector/interface-table structure.
5. Do not touch print-engine MMIO until the register semantics are better understood.

The next reverse-engineering step is to trace what the pointer at/near `0x10006a14` actually targets and how early boot transitions into ThreadX/task startup.

