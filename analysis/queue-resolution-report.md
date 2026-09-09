# Queue resolution

The earlier narrative was superseded by the [constructor registration audit](queue-routing/registration.md). It reversed queue IDs 0 and 1 and inferred several false missing-consumer paths.

Use the [current evidence](queue-routing/registration.md). Queue 1 is PrintMgr; queue 0 is engine. Datastore message `0x2d` and engine/video event `0x17` reach PrintMgr. Raw dispatch tables and decompiler captures remain beside their generators.
