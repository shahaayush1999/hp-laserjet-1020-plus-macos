"""Independent literals for continuous entry-owned USB runtime; UNEXECUTED.

Frozen before reading/writing the new runtime or provider implementation.
No producer imports, file I/O, emulator or execution entry point. These are
source-derived acceptance requirements, not claims about physical USB.
Provider mailbox/CPU-layout/padding details require a separate public contract.
"""

SCENARIO = "raw-configuration-two-documents-final-out-zlp"
MAIN = (0x10003000, 0x100351e0)
ENTRY = 0x100167a8
RAW_CONFIGURATION = bytes.fromhex("0009010000000000")
SETUP_RECORD = bytes.fromhex("80000000000000000009010000000000")
BUS_RESET_SEQUENCE, SETUP_SEQUENCE = 1, 2
INITIAL_RECOVERY_TICKET = (1, 1)
EP0_CONFIGURATION_COOKIE = (1, 2, 1, 0, 0x80)
DOCUMENT_EVENTS = ((2, 1, 0, 1), (2, 2, 1, 1))
PIXELS = bytes.fromhex("ff" * 64)
FRAGMENT_LENGTHS = (64, 64, 64, 64, 64, 32, 64, 64, 64, 64, 64, 32, 0)
DATA_BYTES = 704
BULK_SUBMISSIONS = 13
DCD_SUBMISSIONS = 14
CANCELLATIONS = 0
CLOSE_INPUT_CALLS, FINISH_CALLS = 1, 1

# Existing independent352-byte fixture, also specified by chunk/item literals
# in hp1020-entry-literal-oracle-20261003.py. This is not new runtime output.
STREAM_SHA256 = "ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d"
STREAM = bytes.fromhex(
    "4a5a4a5a00000034000000000000000300245a5a0000000c000101000000"
    "00000000000c00020100000000010000000c0000010000000000000000ac"
    "000000020000000d009c5a5a0000000c00170100000000000000000c0011"
    "0100000000100000000c00120100000000080000000c0010010000000002"
    "0000000c000c0100000000200000000c000d0100000000080000000c0007"
    "0100000000010000000c00080100000002580000000c0009010000000258"
    "0000000c00050100000000070000000c00040100000000010000000c0003"
    "0100000000090000000c0006010000000001000000240000000400000000"
    "00005a5a000001000000002000000008000000041000035c000000280000"
    "00050000000000005a5afd98ff02ff020000000000000000000000000000"
    "0000000000000010000000060000000000005a5a00000010000000030000"
    "000000005a5a00000010000000010000000000005a5a"
)

# Exact original identities are observed from actual bind callbacks, then
# compared against these expectations. Runtime must not synthesize cookies.
def bulk_cookie(sequence):
    if type(sequence) is not int or not 1 <= sequence <= 13:
        raise ValueError("bulk sequence1..13")
    return (sequence + 1, 3, 2, sequence, 1)


def fragment(sequence):
    if type(sequence) is not int or not 1 <= sequence <= 13:
        raise ValueError("bulk sequence1..13")
    if sequence == 13:
        return b""
    within = (sequence - 1) % 6
    return STREAM[64*within:64*within + FRAGMENT_LENGTHS[sequence - 1]]


def slot(sequence):
    if type(sequence) is not int or not 1 <= sequence <= 13:
        raise ValueError("bulk sequence1..13")
    return (sequence - 1) % 4


# Explicit labels copied from the pre-implementation publication/acquisition
# independent profile. They do not equal or translate newly linked CPU pointers.
DESCRIPTOR_DMA = 0x579bdf10
RECEIVE_DMAS = (0x24681340, 0x24682340, 0x24683340, 0x24684340)
SETUP_DMA = 0x79bdf130
EP0_OUT_DESCRIPTOR_DMA, EP0_IN_DESCRIPTOR_DMA = 0x13579bd0, 0xa468ace0
EP0_OUT_PACKET_DMA, EP0_IN_PACKET_DMA = 0x3579bdf0, 0xb68ace00


def descriptor_words(sequence, completed=False):
    count = FRAGMENT_LENGTHS[sequence - 1] if completed else 0
    return ((0x88000000 if completed else 0x08000000) | count,
            0, RECEIVE_DMAS[slot(sequence)], 0)


EP0_PREPARED_WORDS = (0x08000000, 0, 0xb68ace00, 0)
# Independent supplied IN actual length0; low16 is deliberately not a count.
EP0_COMPLETION_WORDS = (0x8800ffff, 0, 0xb68ace00, 0)
EP0_IN_ACTUAL_KNOWN, EP0_IN_ACTUAL = 1, 0

# These semantic fields must be read from original production state at the
# FIRST ACTUAL close_input symbol entry, not a workload's after-the-fact label.
BEFORE_CLOSE = dict(
    generation=2, issued=13, consumed=12, count=1, stopped=0, quiescent=0,
    receive_error=0, document_finished=0, output_finished=0, output_error=0,
    output_quiescent=0, payload_error=0, feed_generation=2, feeding=0,
    parser_documents=2, stream_pages=2, pages_drained=2,
    documents_completed=2, document_first_page=2,
    input_closed=0, fenced=0, control_epoch=2, active_control_epoch=2,
    transport_epoch=3, active_transport_epoch=3, last_submission_id=14,
    opened=1, configuration_value=1, reset_active=0, reset_parts=0,
    last_recovery_id=1, class_request_id=0, current_request_id=0,
    ep0_out_owner=0, ep0_in_owner=0, bulk_owner=1, bulk_core_busy=1,
    out_phase=2, publication_failed=0, acquisition_failed=0,
    pixel_bytes=64, document_callback_count=2,
    successful_bulk_publications=13, successful_bulk_acquisitions=12,
    close_input_entered_before=0, finish_entered_before=0,
)
FINAL_COOKIE = (14, 3, 2, 13, 1)
# After acquisition13: OUT FREE, adapter PENDING; the same reservation is
# still count1 until actual TinyUSB service marks it READY and pump releases it.
AFTER_FINAL_ACQUIRE = dict(
    generation=2, issued=13, consumed=12, count=1,
    bulk_owner=2, out_phase=0, input_closed=1, stopped=0,
    parser_documents=2, stream_pages=2, documents_completed=2, pixel_bytes=64,
)
PARK = dict(
    generation=2, issued=13, consumed=13, count=0, stopped=1, quiescent=0,
    receive_error=0, document_finished=1, output_finished=1, output_error=0,
    output_quiescent=0, payload_error=0, feed_generation=2, feeding=0,
    parser_documents=2, stream_pages=2, pages_drained=2,
    documents_completed=2, document_first_page=2,
    input_closed=1, fenced=1, control_epoch=2, active_control_epoch=2,
    transport_epoch=3, active_transport_epoch=3, last_submission_id=14,
    opened=1, configuration_value=1, reset_active=0, reset_parts=0,
    last_recovery_id=1, class_request_id=0, current_request_id=0,
    ep0_out_owner=0, ep0_in_owner=0, bulk_owner=0, bulk_core_busy=0,
    out_phase=0, publication_failed=0, acquisition_failed=0,
    pixel_bytes=64, document_callback_count=2,
    successful_bulk_publications=13, successful_bulk_acquisitions=13,
    close_input_calls=1, finish_calls=1, cancellation_calls=0,
)
# Each page reuses the same ring storage: the mailbox accumulates64 FF bytes,
# but the full32768-byte production output allocation contains only32 FF then0.
PRODUCTION_OUTPUT = bytes.fromhex("ff" * 32) + bytes(32768 - 32)

# Logical-hook rows: (kind, offset/DMA, observed/attempted value/length, outcome).
# No result is a hardware proof. Reads are supplied independently of writes.
PROGRAM_INITIAL = (
    (1, 0x220, 0x51, 0), (2, 0x220, 0xa0, 0),
    (1, 0x22c, 0x80, 0), (2, 0x22c, 0x40, 0),
    (1, 0x508, 0x100000c1, 0), (2, 0x508, 0x020000c1, 0),
    (1, 0x418, 0x00a700a7, 0), (2, 0x418, 0x00a500a7, 0),
    (3, 0xffffffff, 0, 0),
    (1, 0x028, 0x40, 0), (1, 0x020, 0x51, 0),
    (2, 0x020, 0xa0, 0), (1, 0x02c, 0x80, 0), (2, 0x02c, 0x40, 0),
    (1, 0x50c, 0x100000d1, 0), (2, 0x50c, 0x020000d1, 0),
    (1, 0x418, 0x00a500a7, 0), (2, 0x418, 0x00a500a5, 0),
    (3, 0xffffffff, 0, 0),
)


def publication_trace(sequence):
    dma = RECEIVE_DMAS[slot(sequence)]
    return (
        (1, 0x404, 0x34120320, 0), (1, 0x220, 0x60, 0),
        (1, 0x22c, 0x40, 0), (1, 0x408, 0x0000a001, 0),
        (4, dma, 64, 0), (5, DESCRIPTOR_DMA, 16, 0),
        (3, 0xffffffff, 0, 0), (2, 0x234, DESCRIPTOR_DMA, 0),
        (3, 0xffffffff, 0, 0), (2, 0x220, 0x120, 0),
        (3, 0xffffffff, 0, 0), (1, 0x220, 0x20, 0),
        (2, 0x404, 0x34120324, 0), (3, 0xffffffff, 0, 0),
    )


def acquisition_trace(sequence):
    return ((6, DESCRIPTOR_DMA, 16, 0),
            (7, RECEIVE_DMAS[slot(sequence)], 64, 0), (8, 0, 0, 0))


def successful_logical_trace():
    # 19 +13*(14+3) =240. Close_input precedes acquisition13.
    rows = list(PROGRAM_INITIAL)
    for sequence in range(1, 14):
        rows.extend(publication_trace(sequence))
        rows.extend(acquisition_trace(sequence))
    return tuple(rows)


LOGICAL_HOOK_COUNTS = {1: 74, 2: 47, 3: 54, 4: 13, 5: 13, 6: 13, 7: 13, 8: 13}
LOGICAL_ROWS_BEFORE_CLOSE, LOGICAL_ROWS_AT_PARK = 237, 240
PUBLICATION_PREFIX, ACQUISITION_PREFIX = 0xfff, 0xf
# In this RAW configuration profile, no CSR_DONE grant or automatic-status
# pseudo-owner exists. No closing endpoint-program trace is needed to end input.
FORBIDDEN_ACTIONS = (
    "CSR_DONE", "automatic-status", "per-document-close", "per-document-finish",
    "runtime-reinitialize", "unrequested-cancel", "host-repair-after-entry",
    "descriptor-bit-derived-quiescence",
)

PAINTS = ((0xa5, 0x5a), (0xcc, 0x96))
CPU_PROFILES = (
    dict(name="ordinary-privilege", ps=0, intenable=0, windowbase=0,
         windowstart=1, sar=0, lbeg=0, lend=0, lcount=0),
    dict(name="dirty-window3", ps=0x70302, intenable=1, windowbase=3,
         windowstart=0x89, sar=37, lbeg=0x10035080, lend=0x100350a0, lcount=17),
    dict(name="dirty-window7-excm", ps=0x50711, intenable=2, windowbase=7,
         windowstart=0xc1, sar=63, lbeg=0x100350c0, lend=0x100350e0, lcount=65535),
)


def physical_ars(profile_index):
    if profile_index not in (0, 1, 2):
        raise ValueError("CPU profile")
    return tuple(0x8a000001 + profile_index*0x100000 + i*0x10101 for i in range(32))


PENDING_PUBLIC_PROVIDER_CONTRACT = (
    "mailbox field indices and full mutable layout/witness offsets",
    "actual linked CPU descriptor/payload addresses, guards and stack bounds",
    "event framing and bounded polling/tick counts",
    "source payload padding and exact source-to-CPU hook effects",
    "EP0 supplied visibility/stability/actual-length facts and trace encoding",
    "whether proposed asymmetric DMA labels are retained verbatim",
)

