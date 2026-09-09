# Original stop acknowledgements and post-reset RAM tail

90 cases agree between QEMU, the instruction interpreter and explicit packet/field oracles.

- Engine message 15 clears the active/deferred work slots, sets state byte +0x28 and queues acknowledgement 37 to PrintMgr before calling hardware stop at 0x10016098. This acknowledgement cannot by itself establish completed hardware stopping.
- After the explicitly omitted video reset/wait prefix, the original RAM tail decrements nonzero raster references and clears owned list/state slots. The sign-selected linked-list branch additionally subtracts 16 from nonzero cursors and emits release events; the five-slot branch preserves those cursors.
- Video reset selector 1 emits acknowledgement 37 to PrintMgr. Relaying the selected original engine/video packets through original PrintMgr reproduces its two-stage handshake and final JobMgr acknowledgement.

The engine hardware-stop call is a terminal boundary. The entire Video reset/wait prefix is omitted: QEMU executes its original ENTRY, then enters 0x10013e00 with explicitly seeded stack words and video-owned lists. These tests establish conditional RAM bookkeeping and packet content only. They do not prove that reset reaches the tail, which raster lists are owned at cancellation time, DMA quiescence, interrupt scheduling, safe physical stop or recovery.
