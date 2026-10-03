"""Unexecuted independent literal oracle for the first OUT1 publisher.

Frozen before reading the new production C or runner results. No imports,
producer calls, MMIO model or physical effects. API enum values/field order are
from the separately frozen public header, not implementation behavior.

Rows: (kind, logical offset or explicit DMA, observed/attempted value, outcome).
The fixture adds input-event and one-based absolute all-hook ordinal.
Kinds: READ1, WRITE2, ORDER3, RX_PREP4, DESCRIPTOR_BIDIR5.
ORDER uses offset ffffffff/value0. Failed READ reports value0, regardless of its
independently supplied poisoned input word. Writes never generate read values.
"""

CONTRACT_SHA256 = '39a4f942b986e74b48668c1e49449c5fa04312c6833e574c007b1d781ff60ee9'
PUBLIC_HEADER_SHA256 = '044c5c6f1113680d51c2a52dcb830d8ea073cf0345b7b686cd98bd72b0b65bdc'

OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR, PREFLIGHT_ERROR = 0, 1, 2, 3, 4, 5, 6
IO_OK, IO_NOT_PERFORMED, IO_UNKNOWN = 0, 1, 2
DESCRIPTOR_DMA = 0x579bdf10
RECEIVE_DMA = (0x24681340, 0x24682340, 0x24683340, 0x24684340)
FACT_FIELDS = (
    'io_profile', 'receive_dma_idle', 'register_window_stable',
    'global_receive_ready', 'cnak_window_safe', 'mapping_lease', 'cache_range_safe',
)
FACTS_ALL = (1, 1, 1, 1, 1, 1, 1)

# Reviewed masks, recorded as evidence, never imported from production.
DEVCTL_REQUIRED = 0x00000220
DEVCTL_FORBIDDEN = 0x0000fcd7
DEVCTL_PRESERVED = 0xffff0328

# Both independent, plausible positive profiles preserve nontrivial length
# fields. Base enables BREN but not TDE; alternate preserves TDE without BREN.
# The MPS upper word is intentionally opaque; only low16 defines MPS here.
PUBLISH_CNAK_SLOT0 = (
    (1, 0x404, 0x34120320, 0),
    (1, 0x220, 0x00000060, 0),
    (1, 0x22c, 0x00000040, 0),
    (1, 0x408, 0x0000a001, 0),
    (4, 0x24681340, 64, 0),
    (5, 0x579bdf10, 16, 0),
    (3, 0xffffffff, 0, 0),
    # take_submission occurs here, emits NO hook row and exposes once.
    (2, 0x234, 0x579bdf10, 0),
    (3, 0xffffffff, 0, 0),
    (2, 0x220, 0x00000120, 0),
    (3, 0xffffffff, 0, 0),
    (1, 0x220, 0x00000020, 0),
    (2, 0x404, 0x34120324, 0),
    (3, 0xffffffff, 0, 0),
)
PUBLISH_NO_CNAK_SLOT0 = (
    (1, 0x404, 0xa55a0228, 0),
    (1, 0x220, 0x00000020, 0),
    (1, 0x22c, 0xa55a0040, 0),
    (1, 0x408, 0x0002a001, 0),
    (4, 0x24681340, 64, 0),
    (5, 0x579bdf10, 16, 0),
    (3, 0xffffffff, 0, 0),
    (2, 0x234, 0x579bdf10, 0),
    (3, 0xffffffff, 0, 0),
    (2, 0x404, 0xa55a022c, 0),
    (3, 0xffffffff, 0, 0),
)
SUCCESS_CNAK_PREFIX = 0x00000fff
SUCCESS_NO_CNAK_PREFIX = 0x00000c7f


def publication_trace(slot=0, cnak=True):
    """Only the independent explicit RX label varies with existing queue slot."""
    if type(slot) is not int or slot not in (0, 1, 2, 3):
        raise ValueError('expected actual existing receive slot 0..3')
    rows = list(PUBLISH_CNAK_SLOT0 if cnak else PUBLISH_NO_CNAK_SLOT0)
    rows[4] = (4, RECEIVE_DMA[slot], 64, 0)
    return tuple(rows)


def prepared_descriptor_words(slot):
    if type(slot) is not int or slot not in (0, 1, 2, 3):
        raise ValueError('expected actual existing receive slot 0..3')
    return (0x08000000, 0, RECEIVE_DMA[slot], 0)


def supplied_reads(trace, failed_word=0xd3a569c7):
    """Independent script; a failed read's poison is not an observed value."""
    return tuple((offset, value if outcome == 0 else failed_word, outcome)
                 for kind, offset, value, outcome in trace if kind == 1)


# Every forbidden DEVCTL bit is a separate refusal; positive bits are exercised
# by the two literal full traces above. Rows stop immediately at the bad read.
DEVCTL_REFUSALS = (
    ('missing-mode', 0x34120120),
    ('missing-be', 0x34120300),
    ('resume', 0x34120321),
    ('reserved-bit1', 0x34120322),
    ('rde-already-enabled', 0x34120324),
    ('descriptor-update', 0x34120330),
    ('buffer-fill', 0x34120360),
    ('threshold', 0x341203a0),
    ('soft-disconnect', 0x34120720),
    ('simulation-scale', 0x34120b20),
    ('device-nak', 0x34121320),
    ('csr-done-command', 0x34122320),
    ('rx-flush-command', 0x34124320),
    ('reserved-bit15', 0x34128320),
)
OUTCTL_REFUSALS = (
    ('control-type', 0x00000000),
    ('iso-type', 0x00000010),
    ('interrupt-type', 0x00000030),
    ('stall', 0x00000021),
    ('flush', 0x00000022),
    ('snoop', 0x00000024),
    ('poll', 0x00000028),
    ('snak-intent', 0x000000a0),
    ('cnak-intent', 0x00000120),
    ('rrdy', 0x00000220),
    ('send-null', 0x00000420),
    ('close-descriptor', 0x00000820),
    ('unproved-upper-bit', 0x00010020),
)
MPS_REFUSALS = (
    ('zero', 0x00000000), ('short63', 0x0000003f),
    ('long65', 0x00000041), ('high-speed512', 0x00000200),
)
FIFO_REFUSALS = (('not-empty', 0x00002001), ('zero-status', 0x00000000))


def register_refusals():
    """33 loop controls in ONE case; each must leave reservation state intact."""
    result = []
    for name, word in DEVCTL_REFUSALS:
        result.append((name, ((1, 0x404, word, 0),), WAIT))
    for name, word in OUTCTL_REFUSALS:
        result.append((name, PUBLISH_CNAK_SLOT0[:1] + ((1, 0x220, word, 0),), WAIT))
    for name, word in MPS_REFUSALS:
        result.append((name, PUBLISH_CNAK_SLOT0[:2] + ((1, 0x22c, word, 0),), WAIT))
    for name, word in FIFO_REFUSALS:
        result.append((name, PUBLISH_CNAK_SLOT0[:3] + ((1, 0x408, word, 0),), WAIT))
    return result


def fact_refusals():
    """21 controls: missing and malformed2/255 for each exact fact byte.

    CNAK0 with NAK1 reads only DEVCTL and OUTCTL before WAIT; the other missing
    facts and ALL nonbooleans reject before any I/O. The separate no-CNAK success
    profile must actually set CNAK-safe0 and prove it is not required there.
    """
    result = []
    for index, field in enumerate(FACT_FIELDS):
        for bad in (0, 2, 255):
            values = list(FACTS_ALL)
            values[index] = bad
            trace = PUBLISH_CNAK_SLOT0[:2] if index == 4 and bad == 0 else ()
            result.append((field + '-' + str(bad), tuple(values), trace,
                           WAIT if bad == 0 else INVALID))
    return result


def preflight_read_failures():
    """8 controls, both failure outcomes at each of four pre-reservation reads."""
    result = []
    for ordinal in (1, 2, 3, 4):
        offset = PUBLISH_CNAK_SLOT0[ordinal - 1][1]
        for outcome in (1, 2):
            trace = PUBLISH_CNAK_SLOT0[:ordinal - 1] + ((1, offset, 0, outcome),)
            result.append(('read-' + str(ordinal) + '-' + str(outcome), trace,
                           supplied_reads(trace), PREFLIGHT_ERROR))
    return result


# Name, all-hook ordinal within CNAK trace, failed outcome, last successful
# prefix, OUT phase (PREPARED1 / EXPOSED2), exposed flag, public operation enum.
# There are TEN actual post-bind hook boundaries, not fourteen: four reads
# happen before reservation. Header operation enum differs from trace kind.
POST_BIND_FAILURES = (
    ('rx-cache-failure',           5, 2, 0x001, 1, 0, 1),
    ('descriptor-cache-failure',   6, 1, 0x003, 1, 0, 2),
    ('memory-order-failure',       7, 2, 0x007, 1, 0, 3),
    ('desptr-write-uncertain',     8, 2, 0x01f, 2, 1, 5),
    ('desptr-order-failure',       9, 1, 0x03f, 2, 1, 3),
    ('cnak-write-uncertain',      10, 2, 0x07f, 2, 1, 5),
    ('cnak-order-failure',        11, 1, 0x0ff, 2, 1, 3),
    ('cnak-readback-io-failure',  12, 2, 0x1ff, 2, 1, 6),
    ('rde-write-uncertain',       13, 2, 0x3ff, 2, 1, 5),
    ('rde-order-failure',         14, 2, 0x7ff, 2, 1, 3),
)


def post_bind_failure(name, slot=0, outcome=None):
    """Literal successful prefix plus one attempted failing operation, no suffix.

    outcome override exposes the alternate IO1/2 vector without claiming it is
    included in the bounded40-case matrix. No special-register effect is modeled.
    """
    chosen = None
    for vector in POST_BIND_FAILURES:
        if vector[0] == name:
            chosen = vector
            break
    if chosen is None:
        raise ValueError('unknown independently specified failure')
    _, ordinal, default, prefix, phase, exposed, operation = chosen
    failed = default if outcome is None else outcome
    if failed not in (1, 2):
        raise ValueError('a failure must be NOT_PERFORMED1 or UNKNOWN2')
    full = publication_trace(slot, True)
    kind, offset, value, _ = full[ordinal - 1]
    trace = full[:ordinal - 1] + ((kind, offset, 0 if kind == 1 else value, failed),)
    if kind in (4, 5):
        location = dict(offset=0xffffffff, attempted_value=0, dma=offset, bytes=value)
    else:
        location = dict(offset=offset, attempted_value=0 if kind == 1 else value,
                        dma=0, bytes=0)
    return dict(trace=trace, reads=supplied_reads(trace), ordinal=ordinal,
                prefix=prefix, phase=phase, exposed=exposed, operation=operation,
                io_result=failed, out_result=0, result=FAULT, location=location)


NAK_STILL_SET = PUBLISH_CNAK_SLOT0[:11] + ((1, 0x220, 0x00000060, 0),)
NAK_STILL_SET_FAILURE = dict(prefix=0x1ff, phase=2, exposed=1,
                             operation=7, io_result=0, out_result=0, result=FAULT,
                             location=dict(offset=0x220, attempted_value=0x60,
                                           dma=0, bytes=0))

# API probes use allocated receive slots and 16-bit lengths only; wrong pointer
# metadata must not be implemented by inventing/dereferencing an invalid CPU
# address. All are out of the synchronous wrapper window, so reject pre-bind.
DIRECT_CALLBACK_PROBES = (
    (0, 0x01, 0, 64),  # otherwise correct, but outside the real callback window
    (1, 0x01, 0, 64),  # wrong rhport
    (0, 0x81, 0, 64),  # wrong direction; must not index a slot from endpoint
    (0, 0x00, 1, 0),   # EP0 is not this publisher
    (0, 0x01, 2, 0),   # invalid OUT capacity
    (0, 0x01, 3, 65),  # exceeds supported packet size
)

PROFILE_NAMES = (
    'publish/cnak-and-page',
    'publish/no-cnak-and-page',
    'publish/preflight-facts',
    'publish/preflight-registers',
    'publish/preflight-read-failures',
    'publish/progress-barriers',
    'publish/callback-authority',
    'publish/cleanup-original-cookie',
    'publish/cancel-and-descriptor-reuse',
    'publish/nak-still-set',
    'publish/rx-cache-failure',
    'publish/descriptor-cache-failure',
    'publish/memory-order-failure',
    'publish/desptr-write-uncertain',
    'publish/desptr-order-failure',
    'publish/cnak-write-uncertain',
    'publish/cnak-order-failure',
    'publish/cnak-readback-io-failure',
    'publish/rde-write-uncertain',
    'publish/rde-order-failure',
)


def publication_profiles():
    return [(name, fill, 64, 0) for name in PROFILE_NAMES for fill in (0, 204)]


def expected_final_generation(name):
    if name not in PROFILE_NAMES:
        raise ValueError('unknown publication profile')
    if name in PROFILE_NAMES[:7]:
        return 2
    return 3


# Every case finishes exactly ONE new32x8 black page, one document, and no page
# from a cancelled prefix. These are independently known pixels, not a hash of
# the production decoder's result. The existing JBIG reference check stays too.
EXPECTED_PAGE_PIXELS = b'\xff' * 32
EXPECTED_FINAL_DOCUMENTS = 1
EXPECTED_FINAL_PAGES = 1

# Stable old-fixture diagnostics used for ownership oracles. New publication64
# is appended after432; it does not replace the independently existing ledger.
BASE_GENERATION, BASE_ISSUED, BASE_CONSUMED, BASE_RX_COUNT = 32, 33, 34, 35
BASE_STOPPED, BASE_QUIESCENT = 36, 37
BASE_RECOVERY, BASE_RECOVERY_GENERATION, BASE_RESET_ACTIVE, BASE_RESET_PARTS = 42, 43, 44, 45
BASE_SUBMISSIONS, BASE_WIRE_BYTES, BASE_PIXELS, BASE_DOCUMENT_CALLS = 17, 24, 50, 90
OUT_PHASE, OUT_CANCEL, OUT_COOKIE_BEGIN, OUT_ADAPTER_OWNER_PACKED = 2, 3, 16, 44
ADAPTER_OWNER_NONE, ADAPTER_OWNER_DCD, ADAPTER_OWNER_PENDING = 0, 1, 2

# Critical inequalities/identity expectations are authored in the adjacent
# plan, not inferred from report labels or backend failure fields. In particular
# a successfully bound failure adds one issued/reserved slot; publication cleanup
# preserves that NONZERO count and does not advance generation or reset promises.
