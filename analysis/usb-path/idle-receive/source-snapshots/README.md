# Original idle receive evidence snapshots

These archives retain the exact sources and raw captures from 2026-09-29.
Each adjacent JSON manifest records the archive SHA256 and every regular
member's SHA256. Archive paths are relative to the capture root. `run.log`
contains the corresponding unmodified terminal log.

- `passed-58-cases.tar.gz`: the successful interpreter/QEMU run from
  `/tmp/hp1020-usb-idle-receive-57er5ibi`, with 58 conditional cases and 62
  helper invocations per engine, six unredirected-register rejection cases per
  engine, and 15 excluded-code controls. It includes all before/expected/after
  bytes, event observations, case inputs, the exact generated report, the
  13-file source closure, stock ELF and run 2 log.
- `first-private-socket-stop.tar.gz`: the initial attempt from
  `/tmp/hp1020-usb-idle-receive-4s864gwn`. It stopped before cases because QEMU
  could not create its private debugger socket in the sandbox. The archive
  retains the source closure and run 1 traceback; there was no case report.
  The identical validator subsequently passed with the local-socket permission.

Both runs used validator SHA256
`78e45de26d58e171539a09b105ec4ca720b53004b25decfda046a2718b772401`.
No source correction separated them. No disposable host executable was present
to omit; the original stock ELF is evidence and remains included.

The passing observations concern original instruction behavior against guarded
RAM and explicitly supplied interrupt/delay services. A supplied RDE-clear
word is followed by the original RDE-set operation. This is not an observed
hardware race, a stop acknowledgement, DMA quiescence or physical USB traffic.
