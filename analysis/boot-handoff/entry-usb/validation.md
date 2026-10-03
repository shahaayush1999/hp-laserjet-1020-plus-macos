# One entry through USB handling and two RAM documents

Six continuous interpreter/QEMU cases passed the separately frozen raw-capture gate.
One supplied initial CPU/image is followed by own normalization, BSS initialization,
actual reusable USB control/bulk handling, two documents and one final drain/finish.
All platform observations, cache-copy behavior, settlement and output consumption
are explicitly supplied RAM inputs. No physical USB or printing is established.

- Cases: 6; paired full checkpoints:42; actual QEMU park steps:12.
- Concrete instructions across cases: 14587680; lowest observed SP: `0x10015cb0`.
- Two352-byte streams produce64 actual FF bytes and two original document events.
- The final outstanding OUT owner is separately observed before close, after
  the supplied final zero-length acquisition, and after actual service/pump.
- Exact accepted source/target/tool identities are retained in validation.json.
- capture.tar.gz and capture-manifest.json retain full raw observations.
- Earlier stops and first captures remain distinct in source-snapshots.

This establishes no actual controller, cache coherence, DMA/IRQ provenance,
hardware loader, cold boot, physical pages, copies or power-cycle recovery.

