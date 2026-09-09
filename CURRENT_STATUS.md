# Current handoff

Updated: 2026-09-09. **The open replacement cannot print yet.**
The working HP-based macOS setup is untouched. This is an offline capability
evaluation; the owner consumes progress through chat, not documentation.

## Verified offline

- Corrected BE assembly probes cover idle, endpoint-0 and inert bulk/ZjStream
  framing. None of the corrected builds has live execution proof.
- Bounded C parser and page/band planner execute as compiled Xtensa code in
  synthetic RAM. Pinned toolchains, sanitizers, instruction interpreters and
  strict code/RAM gates support independent checks against QEMU and other oracles.
- Original parser/libc/arithmetic, work construction, selected render paths,
  JobMgr completion/release and stream admission execute. FIFO page completion
  remains an explicit input. PrintMgr cancellation, stop acknowledgements,
  status publication/history and notification ownership also have execution proof.
- Original window handlers, stack construction, voluntary context save/restore,
  kernel initialization, thread creation, priority selection and blocking queues
  run two synthetic tasks without scheduling substitutes.
- Original StatusMgr now runs under that scheduler with original queues and locks.
  Repeated/empty/multi-page notices drain; 26 notices exercise a full 25-message
  queue. Thirty focused cases pass with both priority orders and equality.
  Only a persistent ONLINE subscription remains allocated. Original memory
  allocation/free and startup event waits now remove all runtime host services.
  Notice production still uses prior JobMgr replay, with explicit storage migration.
- Original memory pool passes 93 focused independent-engine cases: alignment,
  preserved live bytes, fragmentation/coalescing, reserve admission and accounting.
  Repeated free reaches a guarded read before the fixture arena; no device fault
  is claimed.
- Latest full aggregate passed both suites (88 consistency checks), including
  original pool and scheduled StatusMgr without runtime host services. Detailed scopes sit beside components; `scripts/validate.sh` is offline-only.

## Corrections to preserve

- Earlier probes contained LE instructions in BE ELF. The old quiet idle upload
  proves nothing. Interpreter BE bit-branch numbering was also corrected.
- Compiler annotations define valid instruction starts; saved decompilation can
  omit whole functions/branches. Execute/check stock bytes before trusting labels.
- `0x1001b668` is unsigned floor division. START_PAGE directly fills VIDEO_Y/RET/
  ECONOMODE at `+0x26/+0x30/+0x32`; `+0x22` is VIDEO_BPP and `+0x12` NBIE.
- Queue 0 is engine, queue 1 PrintMgr, queue 3 JobMgr. Earlier reversed mappings
  produced false missing-consumer conclusions for messages 0x17 and 0x2d.
- Datastore entry locks are 28-byte binary semaphores, distinct from its global
  mutex. Entry 25 stores the current numeric status event, not an enable flag.
- Original render changes pointers before rejecting busy. Nonfinal raster markers
  retain allocation bytes; tested compressed paths ignore them. Logical-clip
  metadata is inconsistent; the narrow planner rejects it and BPP4.

## Next action and limits

**Offline only; no hardware test is authorized.** Extend timed-wait validation (initial
sleep/queue-expiry/early-wakeup experiments pass), then integrate producer
allocation and additional
printing tasks under actual scheduling. Avoid duplicate models and test inflation.

Conditional stock findings remain: delayed empty-document cleanup can remove the
wrong list head; cancellation selector 2 retains a document; selector 4 after
END_DOC reads through null, while earlier acknowledgement retains a child record.
These depend on recorded completion/ownership/order fixtures, not observed printer
faults. Engine acknowledgement precedes hardware stop. The video RAM tail is
verified after an explicitly omitted hardware reset prefix.

QEMU is a different core configuration. Real boot, IRQ/timer delivery, caches,
custom raster instructions, DMA/engine ownership and physical recovery remain
unproven. No printer contact, firmware upload or print-driving MMIO is authorized.
Precise live questions remain in `analysis/open-firmware-model/next-evidence.md`;
the guarded non-printing USB ladder is available only for a future specific request.

Use `analysis/README.md` for evidence and tool recovery. Preserve existing work,
commit coherent checkpoints, push private `main`, and verify sync.
