# Current handoff

Updated: 2026-09-10. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. No printer contact, upload,
installed-printing change or print-driving hardware path occurred.

## Progress and validation

- Current sources pass the full offline suite: **94 consistency checks**.
  Pinned GCC headers/libgcc remain restored with checksum and profile gates.
- Prioritize the stock-supported custom-raster bypass. The stock ELF stores
  datastore 32 = 1; original getter/prepare and separate band fragments select
  the raw buffer with that value. This may defer custom ISA recovery for the
  first printing path. It does not establish complete boot or physical output.
- The aggregate includes 42 bypass cases: 34 raw-buffer selections and eight
  stops before a custom call, plus two constructor relocation fragments.
  These are **not page lifecycles**. Custom callbacks and peripherals never run.
- All 36 native software page lifecycles preserve the stock datastore-32
  descriptor/value before and after processing. This covers ordinary pages,
  multiple documents and split raster input with timing/event controls. It does
  not trace every intermediate write or include VideoThread/engine initialization.
- The separate native matrix retains 26 completed empty-document lifecycles and
  six conditional null reads; all 28 bounded retirement cases pass. Page cases
  still use supplied FIFO consumption/completion, not physical DMA or printing.
- The previous 64-chunk budget stop remains separate evidence; its recorded
  source hashes match the preserved source commit. Completed 64-chunk fixtures
  use the explicit 250,000 cap; other cases retain the 200,000 default.

## Current direction and next evidence

Use the raster-bypass section and native handoff in
`analysis/open-firmware-model/next-evidence.md`. Prefer narrow BPP2/600 callback
bypass while investigating raw-buffer production, consumption and hardware
mode selection. The bypass does not replace the compressed-input hardware path.
The output selector is itself updated from an engine response; its file value
is not a live-mode observation. Complete datastore initialization/writer coverage,
cache visibility, engine timing and output remain unproven. Native admission and
active-work cancellation remain distinct software integration questions; broader
software matrices are not the present priority.

Latest full log: `/tmp/hp1020-full-bypass.log`; it names the child log directory.
Current validation reports match their tested sources and fixtures. Historical
captures and matching source history remain preserved. No research process is running.

## Restrictions and corrections

Offline only: no USB enumeration/contact, queries, uploads, installed-printing
changes or print-driving MMIO. Unknown custom instructions are not inert.
The original empty-document cancellation/END_DOC ordering is resolved; do not
repeat it. Queues: engine 0, PrintMgr 1, JobMgr 3, Video 8, StatusMgr 10.
Boot, automatic IRQs, caches, custom raster code, DMA/engine ownership, physical
printing and power-cycle recovery remain unproven. Passing tests are not output.
