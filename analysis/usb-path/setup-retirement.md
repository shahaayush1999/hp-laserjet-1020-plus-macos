# Original SETUP retirement and OUT0 rearm intent

Original post-dispatch tail, conditional on supplied a2 stall intent, a3 zero, globals and ordinary RAM control images. Exact SETUP-status return, separate owner-only OUT0 header reset, CNAK command intent and idle-latch clear; all mutable RAM, registers and ordered reads/writes agree in both engines.

50 conditional tail profiles and32 pre-peripheral guard profiles per engine;15 excluded PCs. These are zero completed physical transfers.

No ENTRY, request admission/dispatch, sender, IRQ, event wait, timer, cache, controller or physical USB operation executes. Four original peripheral-address literals are redirected only in private executor RAM. Stores are plain RAM writes, not W1C or self-clearing hardware commands. This tail preserves an existing S bit; CNAK does not prove stall clearing or transfer settlement. Mismatched observed/target record controls expose a supplied original pointer assumption, not a recommended port policy. Owner-only OUT0 rearm does not validate RX/count or establish safe reuse. Current SETUP bytes and older EP0 packet ownership remain separate responsibilities. Physical mapping, event ordering, rearm, stalls/toggles, cancellation, boot and printing remain unproved.
