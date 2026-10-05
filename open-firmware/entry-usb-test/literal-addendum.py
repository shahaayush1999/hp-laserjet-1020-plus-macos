"""Independent additive USB-entry expectations; authored before runtime C.

No producer imports, source parsing, filesystem access, test or CLI entry.
The original frozen oracle remains a separate unchanged input. A later checker
may call these helpers with its independently sealed352-byte source and actual
ELF symbol addresses. No helper was executed while preparing this draft.
"""
import hashlib

ORIGINAL_ORACLE_SHA256 = "13194a8d608de407cf9c513f59cf5b1a80a1c3cdeac4ea08b71ebb9602272b95"
PUBLIC_HEADER_SHA256 = "7511e5493d89977630eb1493dc4f085f67e72caf38da95df961054bd88f5f55e"
STREAM_SHA256 = "ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d"
CHECKPOINTS = ("after-normalization", "pre-c", "pre-close",
               "pre-final-service", "pre-finish", "park")
MODEL_SNAPSHOTS = ("initial",) + CHECKPOINTS
QEMU_SNAPSHOTS = MODEL_SNAPSHOTS + ("park-step-1", "park-step-2")
CASE_COUNT, PAIRED_SNAPSHOTS, PARK_STEPS = 6, 7, 2
MAX_INSTRUCTIONS = 10_000_000
QEMU_SECONDS, QEMU_COMMANDS, QEMU_LEDGER_BYTES = 120, 4096, 16 * 1024 * 1024
MAX_OUTER_STEPS = 256
STACK = (0x10014020, 0x10016020)
WITNESS_ADDRESS, WITNESS_BYTES = 0x10032830, 9216
COUNTS = (64, 64, 64, 64, 64, 32, 64, 64, 64, 64, 64, 32, 0)
RX_DMA = (0x24681340, 0x24682340, 0x24683340, 0x24684340)
OUT_DESCRIPTOR_DMA = 0x579bdf10
PRIVATE_CORE_BYTES, PRIVATE_ENDPOINT_OFFSET = 68, 52
CORE_HELD = bytes.fromhex("00000500000000000000000000000000")
CORE_IDLE = bytes(16)
PIXELS = bytes.fromhex("ff" * 64)
PRODUCTION_OUTPUT = bytes.fromhex("ff" * 32) + bytes(32768 - 32)
EVENTS = ((2, 1, 0, 1, 0), (2, 2, 1, 1, 0))
GUARD = bytes([0xa7]) * 16
SETUP_RECORD = bytes.fromhex("80000000000000000009010000000000")
SUPPLIED_FACTS = bytes([1])*26 + bytes(2) + bytes([1])*4 + bytes(4) + bytes([1])*4


def be_words(words):
    return b"".join(int(value).to_bytes(4, "big") for value in words)


def fnv(data):
    result = 2166136261
    for value in data:
        result = ((result ^ value) * 16777619) & 0xffffffff
    return result


def slot(sequence):
    if type(sequence) is not int or not 1 <= sequence <= 13:
        raise ValueError("original bulk sequence1..13")
    return (sequence-1) % 4


def cookie(sequence):
    slot(sequence)
    return (sequence+1, 3, 2, sequence, 1)


def packet_payload(sequence, stream):
    if len(stream) != 352 or hashlib.sha256(stream).hexdigest() != STREAM_SHA256:
        raise ValueError("independently frozen input352 differs")
    s = slot(sequence)
    n = COUNTS[sequence-1]
    within = (sequence-1) % 6
    data = b"" if sequence == 13 else stream[within*64:within*64+n]
    return data + bytes(0x80 | ((0x69 ^ (s*0x1d) ^ (i*7)) & 0x7f)
                        for i in range(n, 64))


def completion_descriptor(sequence):
    return be_words((0x88000000 | COUNTS[sequence-1], 0, RX_DMA[slot(sequence)], 0))


def prepared_descriptor(sequence):
    return be_words((0x08000000, 0, RX_DMA[slot(sequence)], 0))


def poison_descriptor(sequence):
    return be_words((0xc35a0000 | slot(sequence), 0x13579bdf, 0xfedcba90, 0x2468ace0))


def poison_prefix(sequence):
    s = slot(sequence)
    return bytes((0xd3 ^ (s*0x29) ^ (i*0x17)) & 255 for i in range(64))


def receive_storage(completed, stream):
    if completed not in (12, 13):
        raise ValueError("bounded checkpoint completion count12/13")
    out = bytearray(4096)
    for sequence in range(1, completed+1):
        at = 1024*slot(sequence)
        out[at:at+64] = packet_payload(sequence, stream)
    return bytes(out)


def device_storage(sequence, stream):
    out = bytearray(144)
    for at in (0, 32, 48, 128):
        out[at:at+16] = GUARD
    out[16:32] = completion_descriptor(sequence)
    out[64:128] = packet_payload(sequence, stream)
    return bytes(out)


def ep0_memory():
    # IN descriptor at+16; OUT descriptor, sink and IN staging remain zero.
    out = bytearray(160)
    out[16:32] = be_words((0x8800ffff, 0, 0xb68ace00, 0))
    return bytes(out)


# Independent ordered original programming block, unchanged from first oracle.
INITIAL_PROGRAM = (
    (1,0x220,0x51,0),(2,0x220,0xa0,0),(1,0x22c,0x80,0),(2,0x22c,0x40,0),
    (1,0x508,0x100000c1,0),(2,0x508,0x020000c1,0),
    (1,0x418,0x00a700a7,0),(2,0x418,0x00a500a7,0),(3,0xffffffff,0,0),
    (1,0x028,0x40,0),(1,0x020,0x51,0),(2,0x020,0xa0,0),
    (1,0x02c,0x80,0),(2,0x02c,0x40,0),
    (1,0x50c,0x100000d1,0),(2,0x50c,0x020000d1,0),
    (1,0x418,0x00a500a7,0),(2,0x418,0x00a500a5,0),(3,0xffffffff,0,0),
)


def logical_rows(before_close=False):
    rows = [(0, i+1, *row) for i, row in enumerate(INITIAL_PROGRAM)]
    for sequence in range(1, 14):
        dma = RX_DMA[slot(sequence)]
        block = (
            (1,0x404,0x34120320,0),(1,0x220,0x60,0),(1,0x22c,0x40,0),
            (1,0x408,0x0000a001,0),(4,dma,64,0),(5,OUT_DESCRIPTOR_DMA,16,0),
            (3,0xffffffff,0,0),(2,0x234,OUT_DESCRIPTOR_DMA,0),
            (3,0xffffffff,0,0),(2,0x220,0x120,0),(3,0xffffffff,0,0),
            (1,0x220,0x20,0),(2,0x404,0x34120324,0),(3,0xffffffff,0,0),
        )
        if not (before_close and sequence == 13):
            block += ((6,OUT_DESCRIPTOR_DMA,16,0),(7,dma,64,0),(8,0,0,0))
        for row in block:
            rows.append((sequence, len(rows)+1, *row))
    return tuple(rows)


def bind_rows(addresses):
    mem = addresses["hp1020_usb_runtime_memory"]
    desc = addresses["hp1020_usb_runtime_out_memory"]
    ep0 = addresses["hp1020_usb_runtime_ep0_memory"]
    rows = [(1,2,1,0,0x80,0,0,ep0+16,ep0+96)]
    for sequence in range(1, 14):
        cpu = mem + 1024*slot(sequence)
        rows.append((*cookie(sequence),cpu,64,desc,cpu))
    return tuple(rows)


def range_rows(addresses, before_close=False):
    mem = addresses["hp1020_usb_runtime_memory"]
    desc = addresses["hp1020_usb_runtime_out_memory"]
    rows = []
    for sequence, ordinal, kind, dma, length, outcome in logical_rows(before_close):
        if kind < 4:
            continue
        cpu = mem + 1024*slot(sequence)
        span = cpu if kind in (4,7) else desc if kind in (5,6) else 0
        rows.append((ordinal,*cookie(sequence),span,cpu,64))
    return tuple(rows)


def witness_storage(stage, addresses, stream):
    if stage not in ("pre-close", "pre-final-service", "pre-finish", "park"):
        raise ValueError("post-initialization actual checkpoint")
    early = stage == "pre-close"
    out = bytearray(9216)
    for at in (0,5776,8144,8672):
        out[at:at+16] = GUARD
    for index, row in enumerate(logical_rows(early)):
        out[16+index*24:16+(index+1)*24] = be_words(row)
    for index, row in enumerate(range_rows(addresses,early)):
        out[5792+index*36:5792+(index+1)*36] = be_words(row)
    for index, row in enumerate(bind_rows(addresses)):
        out[8160+index*36:8160+(index+1)*36] = be_words(row)
    out[8688:8832] = device_storage(12 if early else 13,stream)
    out[8832:8896] = PIXELS
    out[8896:8936] = b"".join(be_words(row) for row in EVENTS)
    return bytes(out)


def dynamic_memory_expectations(stage, addresses, stream):
    early = stage == "pre-close"
    return {
        "receive": receive_storage(12 if early else 13,stream),
        "output": PRODUCTION_OUTPUT,
        "out_descriptor": prepared_descriptor(13) if early else completion_descriptor(13),
        "ep0_memory": ep0_memory(),
        "setup_memory": SETUP_RECORD,
        "witness": witness_storage(stage,addresses,stream),
        "core_endpoint_status": CORE_HELD if stage in ("pre-close","pre-final-service") else CORE_IDLE,
        "provider_callback_before": packet_payload(9,stream),
        "provider_image_cookie": cookie(12 if early else 13),
        "provider_image_slot": 3 if early else 0,
        "provider_device_valid": 0 if early else 1,
        "provider_bulk_cookie": cookie(13),
        "provider_bulk_live": 1 if early else 0,
    }


# Required live values read from actual component bytes; mailbox is secondary.
CHECKPOINT_DELTAS = {
    "pre-close": dict(consumed=12,count=1,stopped=0,document_finished=0,
                      output_finished=0,input_closed=0,fenced=0,bulk_owner=1,
                      out_phase=2,bulk_core_byte=5,close_returns=0,finish_returns=0,
                      completed_acquisitions=12,io_rows=237,range_rows=62),
    "pre-final-service": dict(consumed=12,count=1,stopped=0,document_finished=0,
                      output_finished=0,input_closed=1,fenced=0,bulk_owner=2,
                      out_phase=0,bulk_core_byte=5,close_returns=1,finish_returns=0,
                      completed_acquisitions=13,io_rows=240,range_rows=65),
    "pre-finish": dict(consumed=13,count=0,stopped=0,document_finished=0,
                      output_finished=0,input_closed=1,fenced=0,bulk_owner=0,
                      out_phase=0,bulk_core_byte=0,close_returns=1,finish_returns=0,
                      completed_acquisitions=13,io_rows=240,range_rows=65),
    "park": dict(consumed=13,count=0,stopped=1,document_finished=1,
                      output_finished=1,input_closed=1,fenced=1,bulk_owner=0,
                      out_phase=0,bulk_core_byte=0,close_returns=1,finish_returns=1,
                      completed_acquisitions=13,io_rows=240,range_rows=65),
}

COMMON_LIVE = dict(generation=2,issued=13,quiescent=0,receive_error=0,
    payload_error=0,output_error=0,output_quiescent=0,feed_generation=2,feeding=0,
    parser_documents=2,stream_pages=2,pages_drained=2,documents_completed=2,
    document_first_page=2,copied_rows=8,accepted_rows=8,completed_rows=8,ring_error=0,
    control_epoch=2,active_control_epoch=2,transport_epoch=3,active_transport_epoch=3,
    last_submission_id=14,opened=1,configuration_value=1,prepared=0,busy=0,
    stack_active=0,delivering_live=0,response_owned=0,ep0_out_owner=0,ep0_in_owner=0,
    reset_active=0,reset_parts=0,last_recovery_id=1,current_request_id=0,
    reset_request_id=0,class_request_id=0,reset_transport_epoch=0,
    ep0_out_phase=0,ep0_in_phase=0,program_failed=0,program_completed_mask=3,
    program_selection_mask=3,program_binding_ready=1,publish_failed=0,
    publication_prefix=0xfff,acquire_failed=0,acquisition_prefix=0xf,
    setup_last_sequence=2,setup_last_admitted_sequence=2,setup_pending_kind=0,
    provider_closing=1,provider_callback_depth=0,provider_ep0_live=0,
    provider_recovery_id=1,provider_recovery_generation=1,pixels=64,documents=2,
    bind_rows=14,cancellation_requests=0,cancellation_settlements=0)

# All receive metadata slots are zero except the outstanding slot0 at the first
# two stops. Acquisition changes adapter ownership before class delivery;
# neither acquisition alone nor close_input marks the reservation READY.
OUTSTANDING_RECEIVE_SLOT0 = be_words((13,64,0,0))
RING_SLOTS = be_words((0,0,8,1)) + bytes(48)

