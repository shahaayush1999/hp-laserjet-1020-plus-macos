# Independent literal trace data for the first programming fixture.
# No imports, producer calls, hardware state model or source-derived constants.
# A row is (kind, logical offset, returned/attempted logical word, I/O result).
# kind: read=1, write=2, order=3; result: OK=0, NOT_PERFORMED=1, UNKNOWN=2.
# The fixture adds caller-event/call ordinals; those are not peripheral values.

PROGRAM_OUT_INITIAL = (
    (1, 0x220, 0x00000051, 0),
    (2, 0x220, 0x000000a0, 0),
    (1, 0x22c, 0x00000080, 0),
    (2, 0x22c, 0x00000040, 0),
    (1, 0x508, 0x100000c1, 0),
    (2, 0x508, 0x020000c1, 0),
    (1, 0x418, 0x00a700a7, 0),
    (2, 0x418, 0x00a500a7, 0),
    (3, 0xffffffff, 0, 0),
)

PROGRAM_IN_INITIAL = (
    (1, 0x028, 0x00000040, 0),
    (1, 0x020, 0x00000051, 0),
    (2, 0x020, 0x000000a0, 0),
    (1, 0x02c, 0x00000080, 0),
    (2, 0x02c, 0x00000040, 0),
    (1, 0x50c, 0x100000d1, 0),
    (2, 0x50c, 0x020000d1, 0),
    (1, 0x418, 0x00a500a7, 0),
    (2, 0x418, 0x00a500a5, 0),
    (3, 0xffffffff, 0, 0),
)

# Repeated selection reads the independently supplied existing 64-byte words.
# 0x61 is bulk type + read-only NAK + STALL. The open command clears S in its
# written word, but successful hardware halt/DATA0 defaults remain a new fact.
PROGRAM_OUT_RESELECT = (
    (1, 0x220, 0x00000061, 0),
    (2, 0x220, 0x000000a0, 0),
    (1, 0x22c, 0x00000040, 0),
    (2, 0x22c, 0x00000040, 0),
    (1, 0x508, 0x020000c1, 0),
    (2, 0x508, 0x020000c1, 0),
    (1, 0x418, 0x00a700a7, 0),
    (2, 0x418, 0x00a500a7, 0),
    (3, 0xffffffff, 0, 0),
)

PROGRAM_IN_RESELECT = (
    (1, 0x028, 0x00000040, 0),
    (1, 0x020, 0x00000061, 0),
    (2, 0x020, 0x000000a0, 0),
    (1, 0x02c, 0x00000040, 0),
    (2, 0x02c, 0x00000040, 0),
    (1, 0x50c, 0x020000d1, 0),
    (2, 0x50c, 0x020000d1, 0),
    (1, 0x418, 0x00a500a7, 0),
    (2, 0x418, 0x00a500a5, 0),
    (3, 0xffffffff, 0, 0),
)

# SI has no preceding core close; keep its supplied already-unmasked IRQ word
# distinct from repeated SC1's mask-after-close observation.
PROGRAM_OUT_SI = (
    (1, 0x220, 0x00000061, 0),
    (2, 0x220, 0x000000a0, 0),
    (1, 0x22c, 0x00000040, 0),
    (2, 0x22c, 0x00000040, 0),
    (1, 0x508, 0x020000c1, 0),
    (2, 0x508, 0x020000c1, 0),
    (1, 0x418, 0x00a500a5, 0),
    (2, 0x418, 0x00a500a5, 0),
    (3, 0xffffffff, 0, 0),
)

PROGRAM_IN_SI = (
    (1, 0x028, 0x00000040, 0),
    (1, 0x020, 0x00000061, 0),
    (2, 0x020, 0x000000a0, 0),
    (1, 0x02c, 0x00000040, 0),
    (2, 0x02c, 0x00000040, 0),
    (1, 0x50c, 0x020000d1, 0),
    (2, 0x50c, 0x020000d1, 0),
    (1, 0x418, 0x00a500a5, 0),
    (2, 0x418, 0x00a500a5, 0),
    (3, 0xffffffff, 0, 0),
)

PROGRAM_CLOSE_HALTED = (
    (1, 0x418, 0x00a500a5, 0),
    (2, 0x418, 0x00a700a7, 0),
    (1, 0x220, 0x00000061, 0),
    (2, 0x220, 0x000000a1, 0),
    (2, 0x234, 0, 0),
    (1, 0x020, 0x00000061, 0),
    (2, 0x020, 0x000000a1, 0),
    (2, 0x034, 0, 0),
    (3, 0xffffffff, 0, 0),
)

PROGRAM_CLOSE_UNHALTED = (
    (1, 0x418, 0x00a500a5, 0),
    (2, 0x418, 0x00a700a7, 0),
    (1, 0x220, 0x00000060, 0),
    (2, 0x220, 0x000000a0, 0),
    (2, 0x234, 0, 0),
    (1, 0x020, 0x00000060, 0),
    (2, 0x020, 0x000000a0, 0),
    (2, 0x034, 0, 0),
    (3, 0xffffffff, 0, 0),
)

PROGRAM_GRANT = (
    (1, 0x404, 0x34120320, 0),
    (3, 0xffffffff, 0, 0),
    (2, 0x404, 0x34122320, 0),
    (3, 0xffffffff, 0, 0),
)
PROGRAM_GRANT_RDE_WAIT = ((1, 0x404, 0x34120324, 0),)
PROGRAM_FIFO_MISMATCH = PROGRAM_OUT_INITIAL + ((1, 0x028, 0x00000020, 0),)

# Explicit failure prefixes; no successful suffix may be synthesized or run.
PROGRAM_FIRST_READ_FAILURE = ((1, 0x220, 0, 1),)
PROGRAM_IN_MPS_UNCERTAIN = PROGRAM_OUT_INITIAL + PROGRAM_IN_INITIAL[:4] + (
    (2, 0x02c, 0x00000040, 2),)
PROGRAM_CLOSE_POINTER_UNCERTAIN = PROGRAM_CLOSE_UNHALTED[:4] + (
    (2, 0x234, 0, 2),)
PROGRAM_SI_IN_MASK_NOT_PERFORMED = PROGRAM_OUT_SI + PROGRAM_IN_SI[:8] + (
    (2, 0x418, 0x00a500a5, 1),)
PROGRAM_GRANT_PRE_ORDER_FAILURE = PROGRAM_GRANT[:1] + ((3, 0xffffffff, 0, 1),)
PROGRAM_GRANT_WRITE_UNCERTAIN = PROGRAM_GRANT[:2] + ((2, 0x404, 0x34122320, 2),)
PROGRAM_GRANT_POST_ORDER_FAILURE = PROGRAM_GRANT[:3] + ((3, 0xffffffff, 0, 2),)

PROGRAM_PROFILE_NAMES = (
    'program/sc1-grant-and-page',
    'program/repeated-sc1-owned',
    'program/si-explicit-programming',
    'program/sc0-and-reset-history',
    'program/stale-held-grant',
    'program/fifo-mismatch-cleanup',
    'program/read-then-partial-write-failure',
    'program/void-close-failure',
    'program/si-write-failure',
    'program/grant-pre-order-failure',
    'program/grant-write-uncertain',
    'program/grant-post-order-failure',
)


def programming_profiles():
    # Full-speed packet64, printer interface0 only for this supplied profile.
    return [(name, fill, 64, 0) for name in PROGRAM_PROFILE_NAMES for fill in (0, 204)]
