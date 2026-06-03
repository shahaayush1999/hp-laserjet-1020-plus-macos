# HP 1020 Firmware Labeling Pass

Date: 2026-06-04

## Result

The first obvious-labeling pass is complete enough to change the estimate.

We are no longer at "can this be analyzed?" The firmware is analyzable, and the main task/handler skeleton is visible:

- `0x10008ff0` is the `USB2Thread` handler.
- `0x10009934` is the `USB2IdleThread` handler.
- `0x1000ad44` is the `agiACLDownload` handler.
- `0x1000cdb0` is tied to `@PJL ECHO` scanning.
- `0x1000b3f8` builds a PJL/status-style result containing `PARSEERROR`/page fields.
- `0x1000bd04` builds device capability/status output for trays, paper, languages, resolution, bits per pixel, and `USTATUS`.
- `0x1001788c` is the `System Timer Thread` handler.

The generated report is:

```text
analysis/labeled/labeled-functions.md
```

Decompiler exports for labeled seed functions are in:

```text
analysis/labeled/decompiled/
```

## Descriptor Tables

The most important discovery is that many interesting strings are not referenced directly by ordinary code. They live in descriptor tables. The table-aware pass recovered the useful handler links.

Important anchors:

```text
10005f14 USB2IdleThread  -> 10009934
10005fc4 USB2Thread      -> 10008ff0
10006054 agiACLDownload  -> 1000ad44
10006730 initTimer       -> 100138fc
10006aec System Timer Thread -> 1001788c
```

This is why the first script found only two functions. It was looking for normal code xrefs. The firmware uses tables for task/handler registration.

## Conservative Helper Labels

The pass also labels a few helpers from repeated usage:

```text
10007430 hp1020_format_into_buffer_candidate
100169d4 hp1020_strlen_like
1001693c hp1020_copy_string_candidate
1001b544 hp1020_append_string_to_buffer_candidate
1000dc00 hp1020_alloc_buffer_candidate
1000d6b0 hp1020_pjl_read_or_poll_candidate
```

These names are intentionally conservative. They are useful for reading decompiler output, but they are not final reverse-engineered names.

## Subsystem Clusters

The automated cluster pass produced these rough neighborhoods:

- USB/download cluster: 3 seed functions, 79 functions through call depth 2.
- PJL/status cluster: 1 seed function, 41 functions through call depth 2.
- Device-state cluster: 2 seed functions, 61 functions through call depth 2.
- ThreadX/RTOS diagnostics cluster: 6 seed functions, 98 functions through call depth 2.

These clusters overlap, which is expected: response building, string formatting, task control, and status reporting are shared across subsystems.

## Early Behavioral Read

`USB2Thread` is large and hardware-heavy. Its decompiler output shows lots of `memw()` barriers and writes through pointer-like globals. That strongly suggests memory-mapped USB/device registers or DMA/control structures.

`USB2IdleThread` is tiny:

```c
do {
  func_0x10008f40();
} while (true);
```

That looks like an idle/service loop around a nearby USB helper.

`agiACLDownload` is small:

```c
*control |= 0x80;
(*(code *)*handler_table)(0, param_1);
```

That looks like a download/dispatch wrapper: set a hardware/control bit, then call through a function table.

`@PJL ECHO` logic at `0x1000cdb0` is a recognizer loop. It computes the length of the target string, repeatedly polls/reads input, compares bytes, and returns an error-ish value when the stream ends or mismatches.

`0x1000b3f8` and `0x1000bd04` are not low-level print-engine code. They are response/status builders.

## Estimate Update

The original "1-2 days for obvious function labeling and call clustering" was too conservative for this environment. The first useful version was reachable in hours.

What changed:

- Tooling works.
- Ghidra's Xtensa support is good enough when forced.
- Descriptor tables gave us clean handler names quickly.
- The firmware contains useful strings and table structure.

What did not change:

- Hardware semantics remain the hard part.
- `USB2Thread` already shows register/DMA-style code that will need careful hardware mapping.
- Ghidra emits p-code warnings for a couple of functions, so not every decompile is trustworthy.
- Replacement firmware is still a hardware validation project, not just a labeling project.

Current practical estimate:

- Obvious labels/clusters: first pass done.
- Better USB/download path map: likely 1-3 more focused days, not 2-5.
- Major subsystem map: probably closer to 4-8 focused days than 1-2 weeks if we keep automating.
- Reliable replacement firmware: still months, because the unknowns are physical printer behavior and hardware registers.

## Next Step

The next valuable step is a focused `USB2Thread` pass:

- label the direct callees of `0x10008ff0`
- identify which globals are hardware registers versus RAM structures
- split setup, transfer, interrupt/status, and dispatch paths
- trace `agiACLDownload` through its indirect function-table call

That is the point where analysis shifts from "naming obvious things" to "understanding the actual USB/download control path."

