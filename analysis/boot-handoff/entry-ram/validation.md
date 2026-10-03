# One entry through a RAM document

Six continuous cases pass the bounded interpreter and independent QEMU,
followed by the separately frozen raw-capture checker. Each case has one
supplied loaded RAM image and CPU state; no later reset, register repair or
host memory write connects its startup, BSS initialization, page and park.

- CPU/paint profiles: 6; paired checkpoints: 30; actual QEMU park steps: 12.
- Concrete instructions across cases: 9221778; lowest observed SP: `0x10013d30`.
- Full state/memory/mailbox BSS: 129224 bytes; owned stack: 8192 bytes.
- Input: 352 bytes in six supplied RAM fragments; output: 32 literal FF bytes.
- The original document event and pixels precede the explicit finish call.
- Full registers, RAM, stack, guards and inert islands are paired; access
  traces and every debugger command/reply are independently checked.

`validation.json` records exact tested source/tool/target identities.
`capture.tar.gz` and `capture-manifest.json` preserve the full accepted raw
capture, including copied sources and target headers, after /tmp is lost.
Historical build/audit stops and the first successful run remain separate
in `source-snapshots/`; their recorded source hashes are not rewritten.

Privilege, exclusively owned mapped RAM, no asynchronous exceptions, RAM
transport completion and immediate software output completion are supplied.
This establishes no physical boot, loader compatibility, cache/DMA, USB,
controller, engine, printing or power-cycle recovery. The open replacement
cannot print yet.
