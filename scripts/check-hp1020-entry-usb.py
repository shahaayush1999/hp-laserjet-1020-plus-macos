#!/usr/bin/env python3
"""Independent capture-only continuous USB-entry checker; stdlib, never target/producer imports.

Literal expectations were frozen before candidate execution. This checks saved
evidence, not physical boot or a second CPU implementation. See README.md for
the deliberately bounded ISA trace decoding and provenance limitations.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import posixpath
import re
import struct

MAIN = 0x10003000
ENTRY = 0x100167a8
DOCUMENT = (0x10010000, 13512)
MEMORY = (0x10016800, 114704)
MAILBOX = (0x10016060, 1024)
STACK = (0x10014020, 8192)
DATA_SENTINEL = (0x10016500, 256)
WITNESS = (0x10032830, 9216)
REGIONS = ((MAIN, 0x321e0), (0x10000000, 0x184), (0x10000200, 0x3c),
           (0x10000270, 0xe0), (0x10000370, 0x12c),
           (0x10100020, 0x2e4), (0x10100320, 0xc))
PHASES = ('initial', 'after-normalization', 'pre-c', 'pre-close',
          'pre-final-service', 'pre-finish', 'park')
QPHASES = PHASES + ('park-step-1', 'park-step-2')
CP_SYMBOLS = ('hp1020_entry_after_normalization', 'hp1020_entry_before_c',
    'hp1020_tusb_adapter_close_input', 'hp1020_udc_publish_service',
    'hp1020_tusb_adapter_finish', 'hp1020_entry_park')
CPU = (
 dict(name='ordinary-privilege',ps=0,intenable=0,windowbase=0,windowstart=1,sar=0,lbeg=0,lend=0,lcount=0),
 dict(name='dirty-window3',ps=0x70302,intenable=1,windowbase=3,windowstart=0x89,sar=37,
      lbeg=0x10035080,lend=0x100350a0,lcount=17),
 dict(name='dirty-window7-excm',ps=0x50711,intenable=2,windowbase=7,windowstart=0xc1,sar=63,
      lbeg=0x100350c0,lend=0x100350e0,lcount=65535))
PAINTS = ((0xa5,0x5a),(0xcc,0x96))
GDB = dict(pc=0,lbeg=33,lend=34,lcount=35,sar=36,windowbase=38,windowstart=39,ps=42,intenable=110)
SENTINEL = bytes.fromhex('31527394b5d6f718395a7b9cbddeff20') * 16
BIE = bytes.fromhex('000001000000002000000008000000041000035cfd98ff02ff02')
BACKEND_HASH = '8fe170ab6161d47d17ef93eb6c25622878e00dc2d4747cfd70073a0fd777b5e2'
ORACLE_HASH = '13194a8d608de407cf9c513f59cf5b1a80a1c3cdeac4ea08b71ebb9602272b95'
ADDENDUM_HASH = '0e22d0fba0e9e031fb0d55d8e538938f79792a8cd6058ae9fee39c067bde935e'
LAYOUT_HASH = 'd752b452320d4d040bbd5a061aa72b192097db846372d3634b821a325a7efd1e'
HEADER_HASH = '7511e5493d89977630eb1493dc4f085f67e72caf38da95df961054bd88f5f55e'
EFFECTIVE_USBD_HASH = '8bf699c1522d65301a4c63e2bfa529d302d3955b8cd18dd1602d7ace441a62dc'
LIBGCC_HASH = 'e57e97f0f5679a83f5a394d94fe024973f05d32be292293b247e647e567c4e32'
LIBGCC_BYTES = 878846
LIBGCC_MEMBERS = {
    '_udivsi3.o': (2612, '6e2ed6774b25c833f8071872d6f7b699838e22f625bdb215cd21eea34a96814a'),
    '_umodsi3.o': (2368, 'f7cb9b22bf91ae5b5f40f06a9c2ad1d4e16ea5a7e7be8631e7f2595d89c3e5ee')}
PRIMARY = {
    'provenance.json': 'a207e83239270e8cd09763a9b96e80e733745e2e74d70cd44337ee27dc88f100',
    'target/xtensa/gdbstub.c': '132bb55cd6203ec5ac22f4ce2611447f225306abd6c8c4b06367b08a65ac42c1',
    'target/xtensa/core-test_kc705_be/gdb-config.c.inc': '3bca88cfe97be52026d9e9762328f293a7892407014a775a221d2262abb0e70c',
    'target/xtensa/core-test_kc705_be/core-isa.h': '449fcb676f9c05ae143749e619c4edcac3e07f590f086a58e1de0cd844f1d2cb',
    'target/xtensa/core-test_kc705_be.c': '9113b65e67095cd0697788530c3c1ed9d64628645828b6ec06e575f43be07a97'}
# Target32 ABI: owner40 at20/60/100/140, delivering40 at180; all older
# fields after owners move by40. programming_dirty ends at369, then alignment
# puts in_result28 at372, pointer at400, length at404 and flags at406/407.
# Document union is max(output13380,pump13312), after receive92. Its added
# ticket8/offset4 move payload_error to13500, flags to13504 and size to13512.
OBJECTS = ((1, 'hp1020_usb_runtime_document', 13512, 4), (2, 'hp1020_usb_runtime_memory', 114704, 16), (3, 'hp1020_usb_runtime_printer', 56, 4), (4, 'hp1020_usb_runtime_adapter', 408, 4), (5, 'hp1020_usb_runtime_out', 64, 4), (6, 'hp1020_usb_runtime_out_memory', 16, 16), (7, 'hp1020_usb_runtime_ep0', 136, 4), (8, 'hp1020_usb_runtime_ep0_memory', 160, 16), (9, 'hp1020_usb_runtime_setup', 80, 4), (10, 'hp1020_usb_runtime_program', 88, 4), (11, 'hp1020_usb_runtime_publisher', 140, 4), (12, 'hp1020_usb_runtime_acquirer', 152, 4), (13, 'hp1020_usb_runtime_provider', 204, 4), (14, 'hp1020_usb_runtime_mailbox', 1024, 4), (15, 'hp1020_usb_runtime_witness', 9216, 4), (16, 'hp1020_usb_runtime_setup_memory', 16, 1))
FIELDS = ((1, 1, 'receive.generation', 68, 4), (2, 1, 'receive.issued', 72, 4), (3, 1, 'receive.consumed', 76, 4), (4, 1, 'receive.count', 80, 4), (5, 1, 'receive.stopped', 88, 1), (6, 1, 'receive.quiescent', 89, 1), (7, 1, 'receive.error', 84, 4), (8, 1, 'finished', 13504, 1), (9, 1, 'output.finished', 13469, 1), (10, 1, 'output.error', 13464, 4), (11, 1, 'output_quiescent', 13505, 1), (12, 1, 'payload_error', 13500, 4), (13, 1, 'feed_generation', 13484, 4), (14, 1, 'output.stream.parser.documents', 4720, 4), (15, 1, 'output.stream.pages', 13248, 4), (16, 1, 'output.pages_drained', 13452, 4), (17, 1, 'output.documents_completed', 13456, 4), (18, 1, 'output.document_first_page', 13460, 4), (19, 1, 'output.ring.copied_rows', 13316, 4), (20, 1, 'output.ring.accepted_rows', 13320, 4), (21, 1, 'output.ring.completed_rows', 13324, 4), (22, 1, 'output.ring.error', 13328, 4), (23, 1, 'output.ring.slots', 13332, 64), (24, 2, 'receive.data', 0, 4096), (25, 2, 'output.stream', 4096, 77840), (26, 2, 'output.slots', 81936, 32768), (27, 4, 'control_epoch', 304, 4), (28, 4, 'active_control_epoch', 308, 4), (29, 4, 'transport_epoch', 312, 4), (30, 4, 'active_transport_epoch', 316, 4), (31, 4, 'last_submission_id', 300, 4), (32, 4, 'opened', 356, 1), (33, 4, 'configuration_value', 360, 1), (34, 4, 'input_closed', 358, 1), (35, 4, 'fenced', 357, 1), (36, 4, 'prepared', 359, 1), (37, 4, 'busy', 354, 1), (38, 4, 'stack_active', 355, 1), (39, 4, 'delivering_live', 366, 1), (40, 4, 'response_owned', 365, 1), (41, 4, 'owners[0].state', 50, 1), (42, 4, 'owners[1].state', 90, 1), (43, 4, 'owners[2].state', 130, 1), (44, 4, 'owners[2].cookie.id', 100, 4), (45, 4, 'owners[2].cookie.epoch', 104, 4), (46, 4, 'owners[2].cookie.generation', 108, 4), (47, 4, 'owners[2].cookie.sequence', 112, 4), (48, 4, 'owners[2].cookie.endpoint', 116, 1), (49, 4, 'owners[2].buffer', 120, 4), (50, 4, 'owners[2].length', 128, 2), (51, 4, 'owners[2].actual', 124, 4), (52, 3, 'reset_active', 50, 1), (53, 3, 'reset_parts', 51, 1), (54, 3, 'last_recovery_id', 36, 4), (55, 3, 'current_request_id', 28, 4), (56, 3, 'reset_request_id', 40, 4), (57, 4, 'class_request_id', 332, 4), (58, 4, 'reset_transport_epoch', 328, 4), (59, 5, 'phase', 58, 1), (60, 5, 'buffer.cpu', 16, 4), (61, 5, 'buffer.dma', 20, 4), (62, 5, 'descriptor.cpu', 4, 4), (63, 5, 'descriptor.dma', 8, 4), (64, 5, 'cookie.id', 28, 4), (65, 5, 'cookie.epoch', 32, 4), (66, 5, 'cookie.generation', 36, 4), (67, 5, 'cookie.sequence', 40, 4), (68, 5, 'cookie.endpoint', 44, 1), (69, 7, 'slots[0].phase', 62, 1), (70, 7, 'slots[1].phase', 126, 1), (71, 10, 'failed', 83, 1), (72, 10, 'completed_mask', 84, 1), (73, 10, 'selection_mask', 85, 1), (74, 10, 'binding_ready', 86, 1), (75, 11, 'failed', 137, 1), (76, 11, 'prefix', 100, 4), (77, 12, 'failure_valid', 149, 1), (78, 12, 'last.prefix', 40, 4), (79, 9, 'last_sequence', 48, 4), (80, 9, 'last_admitted_sequence', 68, 4), (81, 9, 'pending_kind', 78, 1), (82, 13, 'bulk.live', 60, 1), (83, 13, 'closing', 114, 1), (84, 13, 'finished', 115, 1), (85, 13, 'bulk.original', 52, 4), (86, 13, 'bulk.requested', 56, 4), (87, 13, 'ep0.live', 28, 1), (88, 13, 'recovery.recovery_id', 64, 4), (89, 13, 'recovery.generation', 68, 4), (90, 13, 'steps', 100, 4), (91, 15, 'io', 16, 5760), (92, 15, 'ranges', 5792, 2340), (93, 15, 'binds', 8160, 504), (94, 15, 'device', 8688, 144), (95, 15, 'pixels', 8832, 64), (96, 15, 'documents', 8896, 40), (97, 16, 'WHOLE_ARRAY', 0, 16), (98, 14, 'words', 0, 1024), (99, 1, 'feeding', 13506, 1), (100, 13, 'callback_depth', 88, 4), (101, 9, 'capture.record', 16, 16))
LAYOUT_WORDS = (0x4850554c,1,457,16,101)+tuple(v for i,n,z,a in OBJECTS for v in (i,z,a))+tuple(v for i,o,n,a,z in FIELDS for v in (i,o,a,z))
FIXED = {
    '.WindowVectors.text': (0x10000000, 0x180, 1, 6),
    '.KernelExceptionVector.literal': (0x10000180, 4, 1, 2),
    '.KernelExceptionVector.text': (0x10000200, 0x1c, 1, 6),
    '.UserExceptionVector.literal': (0x1000021c, 4, 1, 2),
    '.UserExceptionVector.text': (0x10000220, 0x1c, 1, 6),
    '.DoubleExceptionVector.text': (0x10000270, 0xe0, 1, 6),
    '.sys_interface_table': (0x10000370, 0x12c, 1, 2),
    '.runtime_sentinel': (*DATA_SENTINEL,1,3), '.runtime_stack': (*STACK,8,3),
    '.runtime_mailbox': (*MAILBOX,8,3), '.runtime_memory': (*MEMORY,8,3),
    '.runtime_witness': (*WITNESS,8,3), '.entry_island': (0x10016780,0x60,1,6),
    '.ResetVector.text': (0x10100020, 0x2e0, 1, 6),
    '.DebugExceptionVector.literal': (0x10100300, 4, 1, 2),
    '.DebugExceptionVector.text': (0x10100320, 0xc, 1, 6)}


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def path(root, name):
    need(isinstance(name, str) and name and not Path(name).is_absolute(), 'relative capture path')
    p = (root / name).resolve()
    need(p.is_relative_to(root.resolve()), 'capture path escaped root')
    return p


def raw(root, name, limit=256 * 1024 * 1024):
    p = path(root, name)
    need(p.is_file() and p.stat().st_size <= limit, 'bounded captured file: ' + name)
    return p.read_bytes()


def js(root, name):
    return json.loads(raw(root, name, 32 * 1024 * 1024))


def digest_shape(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def seal_tree(root, directory, expected):
    need(isinstance(expected, dict) and expected, 'nonempty ' + directory + ' seal')
    actual = {str(p.relative_to(root / directory)) for p in (root / directory).rglob('*') if p.is_file()}
    need(actual == set(expected), 'exact ' + directory + ' file set')
    for name, digest in expected.items():
        need(digest_shape(digest) and sha(raw(root, directory + '/' + name)) == digest,
             directory + ' bytes differ: ' + name)


def inside(address, size, spans):
    return type(address) is int and type(size) is int and 0 < size <= 0x100000000 - address and any(
        a <= address and address + size <= a + n for a, n in spans)


def part(images, address, size):
    for a, data in images.items():
        if a <= address and address + size <= a + len(data):
            return bytes(data[address - a:address - a + size])
    raise ValueError('capture slice outside seven regions')


def put(images, address, value):
    for a, data in images.items():
        if a <= address and address + len(value) <= a + len(data):
            data[address - a:address - a + len(value)] = value
            return
    raise ValueError('replayed write outside seven regions')


def input_literal():
    def item(k, v):
        return struct.pack('>IHBBI', 12, k, 1, 0, v)
    def chunk(k, data=b'', count=0, reserved=0):
        return struct.pack('>IIIHH', len(data) + 16, k, count, reserved, 0x5a5a) + data
    doc = b''.join(item(k, v) for k, v in ((1, 0), (2, 1), (0, 0)))
    page = b''.join(item(k, v) for k, v in ((23, 0), (17, 16), (18, 8), (16, 2),
        (12, 32), (13, 8), (7, 1), (8, 600), (9, 600), (5, 7), (4, 1), (3, 9), (6, 1)))
    return (b'JZJZ' + chunk(0, doc, 3, 36) + chunk(2, page, 13, 156) +
            chunk(4, BIE[:20]) + chunk(5, BIE[20:] + bytes(18)) +
            chunk(6) + chunk(3) + chunk(1))



STREAM_SHA256 = "ad339333c0d37ee41da13849184caebec4b55d8f913eb30f9565e30cd33a062d"
CHECKPOINTS = ("after-normalization", "pre-c", "pre-close",
               "pre-final-service", "pre-finish", "park")
MODEL_SNAPSHOTS = ("initial",) + CHECKPOINTS
QEMU_SNAPSHOTS = MODEL_SNAPSHOTS + ("park-step-1", "park-step-2")
CASE_COUNT, PAIRED_SNAPSHOTS, PARK_STEPS = 6, 7, 2
MAX_INSTRUCTIONS = 10_000_000
QEMU_SECONDS, QEMU_COMMANDS, QEMU_LEDGER_BYTES = 120, 4096, 16 * 1024 * 1024
MAX_OUTER_STEPS = 256
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



class Elf:
    """Read linked bytes and layout independently; no objdump or producer API."""
    def __init__(self, data):
        self.data = data
        need(data[:7] == b'\x7fELF\x01\x02\x01' and len(data) >= 52, 'ELF32 BE header')
        h = struct.unpack_from('>HHIIIIIHHHHHH', data, 16)
        typ, machine, version, entry, po, so, flags, hs, ps, pn, ss, sn, si = h
        need((typ, machine, version, entry, hs, ps, ss) == (2, 94, 1, ENTRY, 52, 32, 40), 'linked ELF identity')
        need(0 < sn <= 1024 and si < sn and so + sn * 40 <= len(data) and po + pn * 32 <= len(data), 'ELF table bounds')
        headers = [struct.unpack_from('>10I', data, so + 40 * i) for i in range(sn)]
        st = headers[si]
        names = data[st[4]:st[4] + st[5]]
        self.sections = {}
        for s in headers:
            need(s[0] < len(names) and (s[1] == 8 or s[4] + s[5] <= len(data)), 'ELF section bounds')
            name = names[s[0]:].split(b'\0', 1)[0].decode('ascii')
            need(name not in self.sections, 'unique ELF section name')
            self.sections[name] = s
        self.alloc = {k: s for k, s in self.sections.items() if s[2] & 2 and s[5]}
        need(set(self.alloc) == set(FIXED) | {'.text', '.rodata', '.bss', '.data'}, 'exact allocated object set')
        for name, wanted in FIXED.items():
            s = self.alloc[name]
            need((s[3], s[5], s[1], s[2]) == wanted, 'fixed ELF object ' + name)
        t, r = self.alloc['.text'], self.alloc['.rodata']
        need(t[1] == r[1] == 1 and t[2] == 6 and r[2] == 2 and t[3] == 0x10003000 and
             t[5] > 0 and r[5] > 0 and t[3] + t[5] <= r[3] and r[3] % 4 == 0 and
             r[3] + r[5] <= 0x1000ffe0, 'read-only code budget')
        b, d = self.alloc['.bss'], self.alloc['.data']
        need(b[3] == 0x10010000 and 13512 <= b[5] <= 16352 and b[5]%4 == 0 and
             (b[1],b[2]) == (8,3), 'actual bounded generic BSS extent')
        need(d[3] == 0x100164a0 and 0 < d[5] <= 96 and
             (d[1],d[2]) == (1,3), 'actual bounded generic initialized data')
        self.zero = ((b[3],b[5]),MAILBOX,MEMORY,WITNESS)
        self.initialized_data = (d[3],d[5])
        self.mutable = self.zero+(STACK,self.initialized_data)
        spans = sorted((s[3], s[3] + s[5]) for s in self.alloc.values())
        need(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'allocated overlap')
        self.loads = []
        for i in range(pn):
            k, off, va, pa, fs, ms, pf, al = struct.unpack_from('>8I', data, po + 32 * i)
            if k != 1:
                continue
            need(pa == va and 0 <= fs <= ms and inside(va, ms, REGIONS) and off + fs <= len(data), 'load extent')
            self.loads.append(dict(address=va, physical=pa, offset=off, filesz=fs, memsz=ms, flags=pf, align=al))
        need(len(self.loads) == 15, 'exact fifteen load segments')
        loads = sorted((x['address'], x['address'] + x['memsz']) for x in self.loads)
        need(all(a[1] <= b[0] for a, b in zip(loads, loads[1:])), 'load overlap')
        for s in self.alloc.values():
            owners = [x for x in self.loads if x['address'] <= s[3] and s[3] + s[5] <= x['address'] + x['memsz']]
            need(len(owners) == 1, 'allocated load owner')
            p = owners[0]
            need(p['flags'] == (4 | (2 if s[2] & 1 else 0) | (1 if s[2] & 4 else 0)) or
                 s[2] == 2 and p['flags'] == 5, 'load permission shape')
            if s[1] != 8:
                need(s[3] + s[5] <= p['address'] + p['filesz'] and s[4] == p['offset'] + s[3] - p['address'], 'section file mapping')
            else:
                need(p['filesz'] == 0 and p['address'] == s[3] and p['memsz'] == s[5], 'no broad NOBITS zero-load')
        syms = [s for s in headers if s[1] == 2]
        need(len(syms) == 1 and syms[0][9] == 16 and syms[0][5] % 16 == 0, 'static symbol table')
        st = syms[0]; strings = headers[st[6]]
        names = data[strings[4]:strings[4] + strings[5]]
        self.symbols = {}
        for off in range(st[4], st[4] + st[5], 16):
            ni, value, size, info, other, index = struct.unpack_from('>IIIBBH', data, off)
            if not ni:
                continue
            name = names[ni:].split(b'\0', 1)[0].decode('ascii')
            self.symbols.setdefault(name, []).append((value, size, info, index))
        self.read_spans = [(s[3], s[5]) for s in self.alloc.values()]
        need(self.file(*DATA_SENTINEL) == SENTINEL, 'file-backed sentinel')
        self.instructions = {}
        prop = self.sections['.xt.prop']
        need(prop[1] == 1 and prop[2] == 0 and prop[5] % 12 == 0 and prop[5], 'Xtensa property metadata')
        properties = list(struct.iter_unpack('>III', data[prop[4]:prop[4] + prop[5]]))
        occupied = []
        for a, n, f in properties:
            need(f & ~0x3ffff == 0 and not f & 0x20000, 'ordinary PC-relative instruction properties')
            if not n:
                continue
            need(inside(a, n, self.read_spans), 'property allocation')
            occupied.append((a, a + n))
            kind = f & 7
            if kind == 6:
                # Pinned GAS get_frag_property_flags sets DATA for the initially
                # empty no-transform fragment, then INSN for its actual code.
                # Admit only the independently decoded CALL0 + terminal J pair;
                # no arbitrary mixed property becomes executable by this rule.
                need(f == 0x2906 and a == self.symbol('hp1020_entry_before_c') and
                     n == 6 and self.symbol('hp1020_entry_park') == a + 3,
                     'one exact no-transform CALL0/park property')
                call = int.from_bytes(self.file(a, 3), 'big')
                need(call & 0xfc0000 == 0x500000 and
                     ((a & ~3) + 4 + signed18(call & 0x3ffff) * 4) & 0xffffffff ==
                     self.symbol('hp1020_usb_runtime_c') and
                     jump_target(a + 3, self.file(a + 3, 3)) == a + 3,
                     'actual mixed property contains only linked CALL0/self-J')
            elif kind != 2:
                continue
            need(inside(a, n, [(s[3], s[5]) for s in self.alloc.values() if s[2] & 4]), 'code property permission')
            pc = a
            while pc < a + n:
                nibble = self.file(pc, 1)[0] >> 4
                width = 3 if nibble < 8 else 2 if nibble < 14 else 0
                need(width and pc + width <= a + n and pc not in self.instructions, 'bounded independent instruction width')
                self.instructions[pc] = self.file(pc, width)
                pc += width
        occupied.sort()
        need(all(a[1] <= b[0] for a, b in zip(occupied, occupied[1:])), 'overlapping properties')

    def symbol(self, name, width=None):
        items = self.symbols.get(name, [])
        need(items and len({x[0] for x in items}) == 1, 'unambiguous symbol ' + name)
        if width is not None:
            need(all(x[1] == width for x in items), 'symbol extent ' + name)
        return items[0][0]

    def file(self, address, count):
        owners = [s for s in self.alloc.values() if s[1] != 8 and s[3] <= address and address + count <= s[3] + s[5]]
        need(len(owners) == 1, 'unique file-backed bytes')
        s = owners[0]; off = s[4] + address - s[3]
        return self.data[off:off + count]


def signed18(n):
    return n - 0x40000 if n & 0x20000 else n


def jump_target(pc, code):
    n = int.from_bytes(code, 'big')
    need(len(code) == 3 and n & 0xfc0000 == 0x600000, 'actual direct J encoding')
    return (pc + 4 + signed18(n & 0x3ffff)) & 0xffffffff



def cpu_initial(profile):
    result = {k: v for k, v in CPU[profile].items() if k != 'name'}
    result.update(pc=ENTRY, physical_ar=[0x8a000001 + profile * 0x100000 + i * 0x10101 for i in range(32)])
    return result


def registers(value, qemu=False):
    alias = 'logical_a' if qemu else 'logical_ar'
    need(set(value) == set(GDB) | {'physical_ar', alias}, 'exact register capture fields')
    out = dict(value); out['logical_ar'] = out.pop(alias)
    need(all(type(out[n]) is int and 0 <= out[n] <= 0xffffffff for n in GDB), 'u32 register observations')
    need(len(out['physical_ar']) == 32 and len(out['logical_ar']) == 16 and out['windowbase'] < 8, 'complete window observation')
    need(all(type(v) is int and 0 <= v <= 0xffffffff for v in out['physical_ar']), 'u32 physical ARs')
    need(out['logical_ar'] == [out['physical_ar'][(4 * out['windowbase'] + i) % 32] for i in range(16)], 'physical/logical register aliases')
    return out


def snapshots(folder, rows, labels, qemu=False):
    need([r['name'] for r in rows] == list(labels), 'exact ordered snapshot matrix')
    images = {}
    for item in rows:
        label = item['name']
        need(item == js(folder, label + '/snapshot.json') and item['status'] == 'complete', 'actual snapshot metadata')
        need(item['registers'] == js(folder, label + '/registers.json'), 'register-file seal')
        registers(item['registers'], qemu)
        need([(r['start'], r['bytes']) for r in item['regions']] == list(REGIONS), 'full ordered region set')
        images[label] = {}
        for row, (a, n) in zip(item['regions'], REGIONS):
            expected = f'{label}/region-{a:08x}-{n:08x}.bin'
            need(row['path'] == expected and row['captured_bytes'] == n, 'canonical full region identity')
            data = raw(folder, expected)
            need(len(data) == n and sha(data) == row['sha256'], 'raw region byte seal')
            images[label][a] = data
    return images


def protected(initial, actual, writable):
    for a, old in initial.items():
        now = actual[a]
        need(len(now) == len(old), 'protected region size')
        for i, (x, y) in enumerate(zip(old, now)):
            need(x == y or inside(a + i, 1, writable), f'protected byte changed at{a + i:#x}')



class Ledger:
    """Independent exact successful-command transcript, not the adapter guard."""
    def __init__(self, folder, report):
        seal = report['host_intervention_ledger']
        need(seal['path'] == 'host-interventions.jsonl', 'canonical host ledger')
        data = raw(folder, seal['path'], 16 * 1024 * 1024)
        need(sha(data) == seal['sha256'] and len(data) == seal['bytes'] and data.endswith(b'\n'), 'ledger raw seal')
        self.rows = [json.loads(line) for line in data.splitlines()]
        need(len(self.rows) == seal['lines'] and all(r['ledger_index'] == i for i, r in enumerate(self.rows)), 'complete indexed ledger')
        self.index = 0; self.commands = 0

    def take(self, kind):
        need(self.index < len(self.rows), 'missing ledger event ' + kind)
        row = self.rows[self.index]; self.index += 1
        need(row['kind'] == kind, 'unexpected ledger kind before ' + kind)
        return row

    def command(self, cmd, phase, action, expected=None):
        request = self.take('gdb-request')
        need(request['command'] == cmd and request['command_index'] == self.commands and
             request['phase'] == phase and request['action'] == action, 'exact permitted debugger command envelope')
        reply = self.take('gdb-reply')
        need(reply['command_index'] == self.commands and isinstance(reply['reply'], str), 'complete command/reply pairing')
        self.commands += 1
        value = reply['reply']
        if expected is not None:
            need(value == expected, 'actual debugger reply mismatch')
        return value

    def read(self, address, count, expected):
        value = self.command(f'm{address:x},{count:x}', 'observe', 'read-memory')
        need(len(value) == count * 2 and bytes.fromhex(value) == expected, 'debugger memory reply vs saved raw bytes')

    def reg(self, number, expected):
        value = self.command(f'p{number:x}', 'observe', 'read-register')
        need(len(value) == 8 and int(value, 16) == expected, 'debugger register reply vs saved register')

    def snapshot(self, item, images):
        label = item['name']; start = self.take('snapshot-start')
        need(start['name'] == label, 'snapshot marker order')
        regs = item['registers']
        for name, number in GDB.items():
            self.reg(number, regs[name])
        for i, v in enumerate(regs['physical_ar'], 1):
            self.reg(i, v)
        for i, v in enumerate(regs['logical_a'], 124):
            self.reg(i, v)
        for a, n in REGIONS:
            for off in range(0, n, 4096):
                count = min(4096, n - off)
                self.read(a + off, count, images[label][a][off:off + count])
        end = self.take('snapshot-end')
        need(end['name'] == label and end['status'] == 'complete', 'completed snapshot marker')


def qemu_ledger(folder, q, images, supplied, checkpoints, source_map, elf):
    need(q['runtime_write_spans'] == [[a,a+n] for a,n in elf.mutable], 'QEMU exact split write policy')
    need(type(q['elapsed_seconds']) in (int,float) and q['elapsed_seconds'] >= 0, 'recorded QEMU duration')
    need(q['status'] == 'pass' and q == js(folder, 'result.json'), 'actual QEMU result')
    need(q['checkpoints'] == [[n, a] for n, a in checkpoints.items()], 'QEMU actual checkpoint identities')
    need(q['source_sha256'] == js(folder, 'source/sha256.json'), 'QEMU source manifest')
    for name, digest in q['source_sha256'].items():
        need(digest_shape(digest) and sha(raw(folder, 'source/' + name)) == digest, 'actual QEMU captured source bytes')
    expected_sources = {'hp1020_entry_qemu.py': source_map['scripts/hp1020_entry_qemu.py'],
                        'hp1020_entry_usb_qemu.py': source_map['scripts/hp1020_entry_usb_qemu.py'],
                        'hp1020_qemu_ram.py': BACKEND_HASH,
                        **{'qemu-primary/' + k: v for k, v in PRIMARY.items()}}
    need(q['source_sha256'] == expected_sources, 'independent QEMU source closure')
    actual_sources = {str(p.relative_to(folder / 'source')) for p in (folder / 'source').rglob('*') if p.is_file()}
    need(actual_sources == set(expected_sources) | {'sha256.json'}, 'exact QEMU saved source files')
    identity = q['qemu']
    need(identity['version'] == 'QEMU emulator version 11.1.1' and identity['core'] == 'test_kc705_be' and identity['machine'] == 'sim' and digest_shape(identity['binary_sha256']), 'actual selected emulator identity')
    args = identity['args']
    need(len(args) == 19 and args[1:-1] == ['-M', 'sim', '-cpu', 'test_kc705_be', '-m', '1G',
         '-nodefaults', '-display', 'none', '-serial', 'none', '-monitor', 'none', '-nic', 'none', '-S', '-gdb'] and
         args[-1].startswith('unix:/tmp/hp1020-qemu-') and args[-1].endswith('/gdb.sock,server=on,wait=off'), 'isolated stopped sim launch')
    need(js(folder, 'input/registers.json') == supplied and js(folder, 'input/checkpoints.json') == q['checkpoints'], 'QEMU exact supplied inputs')
    need(len(q['initial_regions']) == 7, 'QEMU initial region records')
    for row, (a, n) in zip(q['initial_regions'], REGIONS):
        need(row['start'] == a and row['bytes'] == n and row['path'] == f'input/region-{a:08x}-{n:08x}.bin', 'QEMU original region identity')
        value = raw(folder, row['path'])
        need(value == images['initial'][a] and sha(value) == row['sha256'], 'actual QEMU initial supplied bytes')
    ledger = Ledger(folder, q)
    admit = ledger.take('admitted-input')
    need(admit['registers'] == supplied and admit['checkpoints'] == q['checkpoints'] and admit['region_sha256'] == q['initial_regions'], 'actual admitted input ledger')
    ledger.command('qSupported', 'constructor', 'bootstrap')
    for cmd in ('Hg0', 'Z0,23000000,1', 'z0,23000000,1'):
        ledger.command(cmd, 'constructor', 'bootstrap', 'OK')
    seed_count = 0
    for a, n in REGIONS:
        data = images['initial'][a]
        for off in range(0, n, 4096):
            chunk = data[off:off + 4096]
            ledger.command(f'M{a + off:x},{len(chunk):x}:' + chunk.hex(), 'seed', 'initial-seed', 'OK')
            seed_count += 1
    for name in ('windowbase', 'windowstart', 'ps', 'intenable', 'lbeg', 'lend', 'lcount', 'sar'):
        ledger.command(f'P{GDB[name]:x}={supplied[name]:08x}', 'seed', 'initial-seed', 'OK'); seed_count += 1
    for i, v in enumerate(supplied['physical_ar'], 1):
        ledger.command(f'P{i:x}={v:08x}', 'seed', 'initial-seed', 'OK'); seed_count += 1
    ledger.command(f'P0={ENTRY:08x}', 'seed', 'initial-seed', 'OK'); seed_count += 1
    locked = ledger.take('initial-state-locked')
    need(locked['seed_commands'] == seed_count == q['initial_seed_commands'] and locked['gdb_commands'] == ledger.commands, 'one complete seed before lock')
    ledger.snapshot(q['snapshots'][0], images)
    for item, (label, address) in zip(q['snapshots'][1:7], checkpoints.items()):
        code = part(images['initial'], address, 3)
        ledger.command(f'Z0,{address:x},1', 'observe', 'add-breakpoint', 'OK')
        ledger.read(address, 3, code)
        reply = ledger.command('c', 'observe', 'continue-current-pc')
        need(reply.startswith('T05'), 'actual continue stop')
        ledger.reg(0, address)
        ledger.snapshot(item, images)
        ledger.command(f'z0,{address:x},1', 'observe', 'remove-breakpoint', 'OK')
        ledger.read(address, 3, code)
    park = checkpoints['park']; code = part(images['initial'], park, 3)
    ledger.read(park, 3, code)
    need(q['park_instruction_hex'] == code.hex() and jump_target(park, code) == park, 'real terminal self-J bytes')
    for item in q['snapshots'][7:]:
        need(ledger.command('s', 'observe', 'single-step-park').startswith('T05'), 'actual park step stop')
        ledger.snapshot(item, images)
    cleanup = ledger.take('process-cleanup')
    need({k: v for k, v in cleanup.items() if k not in ('kind', 'ledger_index')} == q['cleanup'], 'actual cleanup ledger')
    need(not q['cleanup']['errors'] and q['cleanup']['still_running'] is False and q['cleanup']['returncode'] is not None, 'child stopped and reaped')
    end = ledger.take('adapter-finished')
    need(end['status'] == 'pass' and end.get('error') is None and ledger.index == len(ledger.rows) and ledger.commands == q['gdb_commands'] <= 4096, 'complete ledger without hidden traffic')
    need(q['reset_calls'] == q['call_helpers'] == q['memory_or_register_writes_after_lock'] == 0 and q['resume_attempted'] is True and q['checkpoint_stop_observed'] is True, 'declared counters agree with independently reconstructed ledger')



# Independent names map to the manually frozen target32 table, not runtime
# diagnostics. Every table word is checked against actual ELF const bytes first.
LIVE_FIELDS = dict(generation=1,issued=2,consumed=3,count=4,stopped=5,quiescent=6,
 receive_error=7,document_finished=8,output_finished=9,output_error=10,
 output_quiescent=11,payload_error=12,feed_generation=13,parser_documents=14,
 stream_pages=15,pages_drained=16,documents_completed=17,document_first_page=18,
 copied_rows=19,accepted_rows=20,completed_rows=21,ring_error=22,
 control_epoch=27,active_control_epoch=28,transport_epoch=29,active_transport_epoch=30,
 last_submission_id=31,opened=32,configuration_value=33,input_closed=34,fenced=35,
 prepared=36,busy=37,stack_active=38,delivering_live=39,response_owned=40,
 ep0_out_owner=41,ep0_in_owner=42,bulk_owner=43,reset_active=52,reset_parts=53,
 last_recovery_id=54,current_request_id=55,reset_request_id=56,class_request_id=57,
 reset_transport_epoch=58,out_phase=59,ep0_out_phase=69,ep0_in_phase=70,
 program_failed=71,program_completed_mask=72,program_selection_mask=73,
 program_binding_ready=74,publish_failed=75,publication_prefix=76,acquire_failed=77,
 acquisition_prefix=78,setup_last_sequence=79,setup_last_admitted_sequence=80,
 setup_pending_kind=81,provider_closing=83,provider_ep0_live=87,
 provider_recovery_id=88,provider_recovery_generation=89,feeding=99,
 provider_callback_depth=100)
UNITS = ('hp1020_usb_runtime','hp1020_usb_runtime_ram','hp1020_usb_runtime_layout',
 'hp1020_udc_publish','hp1020_udc_program','hp1020_udc_ep0','hp1020_udc_out',
 'hp1020_udc_setup','hp1020_tusb_adapter','hp1020_usb_printer','hp1020_usb_receive',
 'hp1020_usb_document','hp1020_image','hp1020_image_page','hp1020_image_stream',
 'hp1020_image_ring','hp1020_image_output','hp1020_image_pump','hp1020_semantic','hp1020_page_plan',
 'target-memory','memory','jbig85','jbig_ar','tusb','usbd','tusb_fifo')
ENTRY_NAMES = ('hp1020_usb_runtime_c','hp1020_usb_document_init',
 'hp1020_usb_document_init_documents','hp1020_tusb_adapter_init',
 'hp1020_udc_setup_bus_reset','hp1020_udc_setup_offer','hp1020_udc_setup_dispatch',
 'hp1020_udc_ep0_take_submission','hp1020_udc_ep0_observe',
 'hp1020_tusb_adapter_pending_reset','hp1020_tusb_adapter_ack_reset',
 'hp1020_tusb_adapter_finish_reset','hp1020_tusb_adapter_pump',
 'hp1020_usb_document_restart','tusb_rhport_init','hp1020_udc_publish_arm_out',
 'hp1020_udc_acquire_packet','hp1020_udc_publish_service',
 'hp1020_tusb_adapter_close_input','hp1020_tusb_adapter_finish')


def scalar(images, address, width=4):
    return int.from_bytes(part(images,address,width),'big')


def check_legacy_document(images,address):
    need(part(images,address+13488,12)==bytes(12) and
         part(images,address+13507,2)==bytes(2),
         'legacy entry profile keeps cooperative cursor and mode unused')


def object_addresses(elf):
    out={}
    for ident,name,size,align in OBJECTS:
        at=elf.symbol(name,size)
        need(at%align == 0,'actual object alignment: '+name)
        fixed={1:DOCUMENT,2:MEMORY,14:MAILBOX,15:WITNESS}
        if ident in fixed:
            need((at,size)==fixed[ident],'fixed actual runtime object '+name)
        else:
            need(inside(at,size,(elf.zero[0],)),'actual separate generic BSS object '+name)
        if ident in (6,8,16):
            need(at%16==0,'DMA-facing stationary CPU allocation16 alignment')
        out[name]=at
    spans=sorted((at,at+size) for _,name,size,_ in OBJECTS for at in (out[name],))
    need(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])),'no production object aliases')
    need(elf.symbol('_usbd_dev',68)%4==0 and inside(elf.symbol('_usbd_dev'),68,(elf.zero[0],)),
         'actual private core68 within generic state')
    out['_usbd_dev']=elf.symbol('_usbd_dev')
    return out


def field(images, addresses, ident):
    i,obj,name,off,width=FIELDS[ident-1]
    need(i==ident,'independent field indexing')
    at=addresses[OBJECTS[obj-1][1]]+off
    return scalar(images,at,width) if width<=4 else part(images,at,width)


def cookie_bytes(words):
    return be_words(words[:4])+bytes([words[4]])+bytes(3)


def actual_cookie(images,at):
    return tuple(scalar(images,at+4*i) for i in range(4))+(scalar(images,at+16,1),)


def core_status(images,addresses):
    return part(images,addresses['_usbd_dev']+52,16)


def make_initial(elf,fills):
    images={a:bytearray((i*29+(a>>4)+0x67)&255 for i in range(n)) for a,n in REGIONS}
    for p in elf.loads:
        if p['filesz']:
            put(images,p['address'],elf.data[p['offset']:p['offset']+p['filesz']])
    for a,n in elf.zero:put(images,a,bytes([fills[0]])*n)
    put(images,STACK[0],bytes([fills[1]])*STACK[1])
    return {a:bytes(b) for a,b in images.items()}


def private_getter(elf):
    # Independent target32 proof: L32R a10,base; EXTUI endpoint nibble;
    # ADDX2 a9,a9,a10; EXTUI direction; ADD.N; MEMW; L8UI a2,a9,52;
    # EXTUI bit0; RET.N. The relocation's actual word must equal _usbd_dev.
    at=elf.symbol('usbd_edpt_busy',25); code=elf.file(at,25)
    need(code[0]==0x1a and code[3:]==bytes.fromhex(
        '0309430a9909037340a3990c0200229034020240d00f'),
        'actual private-core getter instruction shape/load52/mask1')
    target=(((at+3)&~3)+(int.from_bytes(code[1:3],'big')-0x10000)*4)&0xffffffff
    need(int.from_bytes(elf.file(target,4),'big')==elf.symbol('_usbd_dev',68),
         'getter actual base literal points to actual private core68')


def check_live(images,addresses,stage,source):
    d=CHECKPOINT_DELTAS[stage]
    expected={**COMMON_LIVE,**d}
    for name,ident in LIVE_FIELDS.items():
        need(field(images,addresses,ident)==expected[name],f'{stage}: actual {name}')
    early=stage=='pre-close';held=stage in ('pre-close','pre-final-service')
    want=dynamic_memory_expectations(stage,addresses,source)
    mem=addresses['hp1020_usb_runtime_memory'];doc=addresses['hp1020_usb_runtime_document']
    check_legacy_document(images,doc)
    adapter=addresses['hp1020_usb_runtime_adapter'];out=addresses['hp1020_usb_runtime_out']
    provider=addresses['hp1020_usb_runtime_provider'];acq=addresses['hp1020_usb_runtime_acquirer']
    need(part(images,mem,4096)==want['receive'],'full4096 actual receive allocation/padding/tails')
    need(part(images,mem+81936,32768)==want['output'],'full32768 actual production output allocation')
    need(part(images,addresses['hp1020_usb_runtime_out_memory'],16)==want['out_descriptor'],
         'actual final descriptor body/status/count')
    need(part(images,addresses['hp1020_usb_runtime_ep0_memory'],160)==want['ep0_memory'],
         'full160 EP0 allocation, independent IN lowffff and real ZLP staging')
    need(part(images,addresses['hp1020_usb_runtime_setup_memory'],16)==SETUP_RECORD and
         field(images,addresses,101)==SETUP_RECORD,'original raw SETUP and immutable captured bytes')
    need(part(images,*WITNESS)==want['witness'],'full9216 independent trace/range/bind/device/pixels/events/guards')
    need(core_status(images,addresses)==want['core_endpoint_status'],'actual private BUSY/CLAIMED endpoint array')
    need(scalar(images,addresses['_usbd_dev']+24,1)==1 and
         scalar(images,addresses['_usbd_dev']+29,1)==1,'actual private connected/configuration')
    need(field(images,addresses,23)==RING_SLOTS,'actual four output ring slots')
    need(part(images,doc+4,64)==(OUTSTANDING_RECEIVE_SLOT0+bytes(48) if held else bytes(64)),
         'actual receive reservation metadata independent of owner/completion flags')
    if held:
        need(actual_cookie(images,adapter+100)==cookie(13) and
             scalar(images,adapter+120)==mem and scalar(images,adapter+128,2)==64 and
             scalar(images,adapter+124)==0,'original final retained adapter owner and zero actual')
    else:
        need(part(images,adapter+100,40)==bytes(40),'adapter owner really released after service')
    need(part(images,adapter+20,80)==bytes(80),'both EP0 owner records retired')
    need(scalar(images,out+4)==addresses['hp1020_usb_runtime_out_memory'] and
         scalar(images,out+8)==OUT_DESCRIPTOR_DMA and scalar(images,out+12)==16,
         'stationary descriptor CPU/DMA span retained across retirement')
    if early:
        need(actual_cookie(images,out+28)==cookie(13) and
             tuple(scalar(images,out+16+4*i) for i in range(3))==(mem,RX_DMA[0],64),
             'original EXPOSED OUT cookie/CPU span')
    else:
        need(part(images,out+16,32)==bytes(32),'retirement clears OUT buffer/cookie only after actual acquisition')
    need(actual_cookie(images,provider)==(1,2,1,0,0x80) and
         part(images,provider+20,8)==bytes(8) and part(images,provider+28,4)==bytes((0,0,255,0)),
         'retained original EP0 NULL/zero record, no live/cancel')
    need(actual_cookie(images,provider+32)==cookie(13) and
         scalar(images,provider+52)==mem and scalar(images,provider+56)==64 and
         part(images,provider+60,4)==bytes((int(early),0,0,0)),
         'independently retained final provider cookie/CPU/length/phase')
    need(part(images,provider+64,8)==be_words((1,1)) and
         tuple(scalar(images,provider+72+4*i) for i in range(7))==(13,74,5,13,0,15,0),
         'provider original recovery and read/callback cursors')
    need(0<scalar(images,provider+100)<=256,'bounded provider steps')
    need(part(images,provider+112,4)==bytes((1,int(not early),1,int(stage=='park'))),
         'provider initialization/source-valid/closing/finished flags')
    need(part(images,provider+116,64)==want['provider_callback_before'],
         'publication before-copy witness is previous slot0 data')
    need(actual_cookie(images,provider+180)==want['provider_image_cookie'] and
         scalar(images,provider+200)==want['provider_image_slot'],
         'old source image identity is distinct from newly armed owner')
    completed=12 if early else 13
    need(actual_cookie(images,acq+20)==cookie(completed) and scalar(images,acq+40)==15 and
         scalar(images,acq+60)==0 and scalar(images,acq+64,1)==3 and scalar(images,acq+65,1)==1 and
         part(images,acq+66,16)==completion_descriptor(completed),
         'actual acquisition diagnostic retains original accepted identity/snapshot')
    need(part(images,acq+84,64)==bytes(64) and part(images,acq+148,2)==b'\1\0',
         'no first failure fabricated/cleared')


def mailbox(images,addresses,stage,elf,initial,source):
    mb=part(images,*MAILBOX);w=list(struct.unpack('>256I',mb));d=CHECKPOINT_DELTAS[stage]
    done=stage=='park';early=stage=='pre-close';n=12 if early else 13
    need(w[0:3]==[0x48505552,1,2 if done else 1] and w[4:8]==[0]*4 and w[128:]==[0]*128,
         'mailbox identity/success/error/tail')
    need(w[8:15]==[elf.zero[0][1],114704,1024,9216,256,elf.initialized_data[1],
                       fnv(part(initial,*elf.initialized_data))],
         'all initial scan counts and actual file-backed generic-data digest')
    need(0<w[15]<=256 and w[15]==scalar(images,addresses['hp1020_usb_runtime_provider']+100),
         'bounded observed outer-step counter')
    fixed={16:1,17:1,18:1,19:1,22:13,23:13,24:1,25:n,26:n,27:1,28:1,29:1,
           30:1,31:1,32:1,33:1,34:d['close_returns'],35:d['finish_returns'],36:0,37:0,
           38:d['io_rows'],39:d['range_rows'],40:14,41:n,42:n,43:64,44:2,45:2,46:2,
           47:2,48:0,49:0,50:0,51:74,52:d['range_rows'],53:0,54:15,55:0,
           60:1,61:1,62:14,63:3,64:2,65:13,66:1,67:0,68:237,69:64,70:2,
           115:704,116:n*64,117:n*16,118:74,119:47,120:54,121:13,122:13,
           123:n,124:n,125:n,126:1}
    if not early:fixed.update({71:2,72:1,73:12,74:0,127:1})
    else:fixed.update({71:0,72:0,73:0,74:0,127:0})
    for i,v in fixed.items():need(w[i]==v,f'{stage}: secondary mailbox word{i}')
    need(0<w[20]<=256 and 0<w[21]<=256,'bounded actual service/pump counts')
    if done:
        need(w[3]==13 and w[57]==0 and w[58]==0 and w[59]==0,'successful final API results')
        wit=part(images,*WITNESS)
        need(w[75:81]==[fnv(receive_storage(13,source)),fnv(PRODUCTION_OUTPUT),fnv(PIXELS),
              fnv(wit[16:5776]),fnv(wit[5792:8132]),fnv(wit[8160:8664])],
             'complete secondary digests independently derived from literal bytes')
        mapping=(1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,34,35,27,28,29,30,31,
                 41,42,43,59)
        want=[field(images,addresses,i) for i in mapping]+[0,field(images,addresses,71),
                 field(images,addresses,75),field(images,addresses,77),
                 field(images,addresses,76),field(images,addresses,78)]
        need(w[81:115]==want,'final mailbox reflects independently read production bytes')
    return w


def semantic_snapshots(rows,images,initial,supplied,cps,source,elf,addresses,qemu=False):
    for item in rows:
        label=item['name'];regs=registers(item['registers'],qemu);actual=images[label]
        if label=='initial':
            need({k:v for k,v in regs.items() if k!='logical_ar'}==supplied and actual==initial,
                 'exact one supplied image and all incoming physical registers')
            continue
        stage='park' if label.startswith('park-step') else label
        need(regs['pc']==cps[stage],'actual linked checkpoint PC')
        allowed=() if stage=='after-normalization' else elf.zero if stage=='pre-c' else elf.mutable
        protected(initial,actual,allowed)
        need(part(actual,*DATA_SENTINEL)==SENTINEL,'immutable sentinel retained')
        for name,value in dict(ps=15,intenable=0,windowbase=0,windowstart=1,lbeg=0,lend=0,lcount=0).items():
            need(regs[name]==value,'continuous normalized CPU '+name)
        if stage in ('after-normalization','pre-c','park'):
            need(regs['physical_ar'][1]==sum(STACK),'own stack restored/top before C')
        if stage in ('after-normalization','pre-c'):
            need(regs['sar']==0,'normalized SAR before C')
            need(part(actual,*elf.initialized_data)==part(initial,*elf.initialized_data),
                 'generic initialized bytes preserved through startup')
        if stage=='pre-c':
            need(all(part(actual,a,n)==bytes(n) for a,n in elf.zero),'all four exact used BSS spans zero')
        if stage in CHECKPOINT_DELTAS:
            check_live(actual,addresses,stage,source)
            mailbox(actual,addresses,stage,elf,initial,source)
            if stage in ('pre-close','pre-finish'):
                need(regs['physical_ar'][2]==addresses['hp1020_usb_runtime_adapter'],
                     'actual close/finish argument identifies the original adapter')
            elif stage=='pre-final-service':
                need(regs['physical_ar'][2]==addresses['hp1020_usb_runtime_publisher'],
                     'actual service argument identifies original publisher')


def gunzip(root, name, limit):
    # CRC validation is supplied by gzip; the evidence seal is over raw records.
    with gzip.open(path(root, name), 'rb') as f:
        data = f.read(limit + 1)
    need(len(data) <= limit, 'bounded decompressed trace')
    return data


def memory_instruction(code):
    nibble = code[0] >> 4
    if nibble in (8, 9):
        return (1 if nibble == 8 else 2, 4)
    if nibble == 1:
        return (1, 4)
    if nibble == 2:
        return {0: (1, 1), 1: (1, 2), 2: (1, 4), 9: (1, 2),
                4: (2, 1), 5: (2, 2), 6: (2, 4)}.get(code[1] & 15)
    return None


def model_trace(folder, model, images, elf, cps, addresses, source, forbidden):
    steps = gunzip(folder, 'traces/steps.bin.gz', 40_000_000)
    accesses = gunzip(folder, 'traces/accesses.bin.gz', 200_000_000)
    need(len(steps) % 4 == 0 and len(accesses) % 20 == 0 and steps, 'complete bounded trace records')
    need(sha(steps) == model['step_sha256'] and sha(accesses) == model['access_sha256'], 'raw uncompressed trace seals')
    pcs = [p[0] for p in struct.iter_unpack('>I', steps)]
    need(len(pcs) == model['instructions'] <= 10_000_000 and len(set(pcs)) == model['visited_instructions'], 'instruction trace counters')
    need(pcs[0] == ENTRY and pcs.count(ENTRY) == 1 and pcs[-2:] == [cps['park']] * 2 and
         all(pcs.count(at) == (2 if name == 'park' else 1) for name, at in cps.items()
             if name != 'pre-final-service'),
         'one entry, unique close/finish and two actual park iterations')
    need(jump_target(ENTRY, elf.instructions[ENTRY]) == pcs[1] == elf.symbol('hp1020_entry_normalize'), 'actual initial jump target')
    need(jump_target(cps['park'], elf.instructions[cps['park']]) == cps['park'], 'literal self-J target')
    ram = {a: bytearray(b) for a, b in images['initial'].items()}
    cursor = 0; counts = Counter(); widths = Counter(); seen = []; minimum = None
    pre_c_index = pcs.index(cps['pre-c'])
    call_index = 0; call_stack = []
    entry_cursor=0; selected={elf.symbol(n):n for n in ENTRY_NAMES}
    need(len(selected)==len(ENTRY_NAMES),'unambiguous selected actual function entries')
    entries=model['actual_entry_events']; acquired=0; awaiting_service=False
    checkpoints_index={}
    scanned=set();first_global_write=False
    prior_entry_names=[]
    service_indices=[]; acquire_indices=[]; pump_indices=[]
    counts_at={}; entry_counts=Counter()

    for i, pc in enumerate(pcs):
        need(pc in elf.instructions, 'executed PC is an annotated actual instruction boundary')
        code = elf.instructions[pc]
        need(code not in (b'\0\0\0', bytes.fromhex('d60f')), 'excluded illegal instruction executed')
        if i and pc in selected:
            need(entry_cursor<len(entries),'missing actual selected function-entry event')
            event=entries[entry_cursor];entry_cursor+=1;name=selected[pc]
            need(event['name']==name and event['pc']==pcs[i-1] and event['target']==pc and
                 event['instruction']==i and STACK[0]<=event['sp']<=sum(STACK) and event['sp']%16==0 and
                 len(event['arguments'])==6 and all(type(x)is int and 0<=x<=0xffffffff for x in event['arguments']),
                 'actual natural function-entry event tied to raw instruction transition')
            check_entry(event,ram,addresses,source,entry_counts,acquired,awaiting_service)
            entry_counts[name]+=1;prior_entry_names.append(name)
            if name=='hp1020_udc_acquire_packet':
                acquired+=1;awaiting_service=True;acquire_indices.append(i)
            if name=='hp1020_udc_publish_service':
                service_indices.append(i)
                if awaiting_service:awaiting_service=False
            if name=='hp1020_tusb_adapter_pump':pump_indices.append(i)
        for label, at in cps.items():
            if label=='pre-final-service' and 'pre-close' not in seen:continue
            if pc == at and label not in seen:
                need(label == tuple(cps)[len(seen)], 'trace checkpoint order')
                need({a: bytes(b) for a, b in ram.items()} == images[label], 'replayed bytes at ' + label)
                seen.append(label)
                checkpoints_index[label]=i
                counts_at[label]=entry_counts.copy()

        kind = memory_instruction(code)
        if kind:
            need(cursor + 20 <= len(accesses), 'missing memory access for actual memory instruction')
            chunk = accesses[cursor:cursor + 20]
            need(chunk[1:4] == bytes(3), 'access-record zero padding')
            k, at, address, size, value = struct.unpack('>B3xIIII', chunk)
            need(at == pc and (k, size) == kind and address % size == 0, 'access matches actual memory instruction')
            need(inside(address, size, elf.read_spans), 'no read/write in guard/gap/external/MMIO range')
            started = 'pre-c' in seen and i > pre_c_index
            if inside(address, size, (STACK,)):
                need(started, 'no inherited stack access')
                minimum = address if minimum is None else min(minimum, address)
            if started and not first_global_write:
                if k==1:
                    scanned.update(x for x in range(address,address+size) if inside(x,1,elf.zero+(DATA_SENTINEL,elf.initialized_data)))
                elif not inside(address,size,(STACK,)):
                    need(all(x in scanned for a,n in elf.zero+(DATA_SENTINEL,elf.initialized_data) for x in range(a,a+n)),
                         'every zero-span/sentinel/initialized-data byte actually read before first global C write')
                    first_global_write=True
            if k == 1:
                need(int.from_bytes(part(ram, address, size), 'big') == value, 'read record differs from actual preceding RAM')
                if code[0] >> 4 == 1:
                    immediate = int.from_bytes(code[1:], 'big') - 0x10000
                    target = (((pc + 3) & ~3) + immediate * 4) & 0xffffffff
                    need(address == target, 'actual L32R pointer')
            else:
                allowed = elf.mutable if started else elf.zero if 'after-normalization' in seen else ()
                need(inside(address, size, allowed), 'phase write permission before effect')
                put(ram, address, (value & ((1 << (8 * size)) - 1)).to_bytes(size, 'big'))
            counts['read' if k == 1 else 'write'] += 1
            widths[('read' if k == 1 else 'write') + '/' + str(size)] += 1
            cursor += 20
        word = int.from_bytes(code, 'big')
        if len(code) == 3 and word & 0xfc0000 == 0x600000:
            need(jump_target(pc, code) == (pcs[i + 1] if i + 1 < len(pcs) else cps['park']),
                 'actual direct J target in step trace')
        direct_call = len(code) == 3 and word & 0xfc0000 == 0x500000
        indirect_call = len(code) == 3 and word & 0xff0fff == 0x030000
        is_return = code in (bytes.fromhex('020000'), bytes.fromhex('d00f'))
        if direct_call or indirect_call or is_return:
            need(i + 1 < len(pcs) and call_index < len(model['calls']), 'actual call/return evidence')
            event = model['calls'][call_index]; call_index += 1
            need(event['pc'] == pc and event['target'] == pcs[i + 1] and STACK[0] <= event['sp'] <= STACK[0] + STACK[1] and event['sp'] % 16 == 0, 'actual call location/target and owned aligned stack')
            if is_return:
                need(call_stack and event['kind'] == 'return' and event['depth'] == len(call_stack), 'real return has caller')
                previous = call_stack.pop()
                need(event['target'] == previous['return_pc'] and event['sp'] == previous['sp'], 'original call return/stack')
            else:
                need('pre-c' in seen and event['kind'] == 'call' and event['return_pc'] == pc + len(code) and event['depth'] == len(call_stack) + 1, 'real own call record')
                if call_index == 1:
                    need(pc == cps['pre-c'] and event['target'] == elf.symbol('hp1020_usb_runtime_c'), 'first and only entry-to-C call')
                if direct_call:
                    target = ((pc & ~3) + 4 + signed18(word & 0x3ffff) * 4) & 0xffffffff
                    need(event['target'] == target, 'literal CALL0 target')
                call_stack.append(event)
    need(cursor == len(accesses) and call_index == len(model['calls']) and not call_stack, 'complete memory/call traces')
    need(seen == list(PHASES[1:]) == model['checkpoints'], 'all six staged actual trace checkpoints')
    need({a: bytes(b) for a, b in ram.items()} == images['park'], 'all replayed final bytes equal capture')
    need(dict(counts) == model['access_count'] and dict(widths) == model['access_widths'], 'actual access counters')
    need(minimum == model['minimum_stack_access'] and minimum is not None, 'independent lowest stack access')
    need(STACK[0] <= model['minimum_sp'] <= minimum and model['owned_stack_bytes'] == 8192, 'bounded SP witness')
    need(model['terminal_self_branch_executions'] == 2 and model['terminal_self_branch_statically_checked'] is True,
         'terminal evidence matches actual trace/bytes')
    need(model['no_external_stack'] is True and model['host_runtime_mutations'] == 0, 'model declared scope')
    need(first_global_write,'actual initialization performed after complete initial scan')
    need(pcs.count(elf.symbol('hp1020_usb_document_finish'))==1 and
         pcs.index(elf.symbol('hp1020_usb_document_finish'))>checkpoints_index['pre-finish'],
         'only one production document EOF, after the sole adapter finish entry')
    check_forbidden_entries(pcs,forbidden)
    need(entry_cursor==len(entries) and not awaiting_service and acquired==13,
         'complete original entry/acquisition/service evidence')
    need(model['actual_close_entries']==model['actual_finish_entries']==1 and
         model['zero_spans']==[list(x) for x in elf.zero] and
         model['owned_stack']==list(STACK) and model['initialized_data_span']==list(elf.initialized_data),
         'model declared entries and dynamic exact memory policy')
    close=checkpoints_index['pre-close'];service=checkpoints_index['pre-final-service']
    finish=checkpoints_index['pre-finish']
    need(acquire_indices[-2]<close<acquire_indices[-1]<service<finish and
         not any(close<x<service for x in service_indices) and
         any(service<x<finish for x in pump_indices),
         'natural close then final original acquisition then NEXT service then empty pump/finish')
    expected_counts={'hp1020_usb_runtime_c':1,'hp1020_usb_document_init_documents':1,
        'hp1020_tusb_adapter_init':1,'hp1020_udc_setup_bus_reset':1,
        'hp1020_udc_setup_offer':1,'hp1020_udc_setup_dispatch':1,
        'hp1020_udc_ep0_take_submission':1,'hp1020_udc_ep0_observe':1,
        'hp1020_tusb_adapter_ack_reset':3,'hp1020_tusb_adapter_finish_reset':1,
        'hp1020_usb_document_restart':1,'tusb_rhport_init':1,
        'hp1020_udc_publish_arm_out':13,'hp1020_udc_acquire_packet':13,
        'hp1020_tusb_adapter_close_input':1,'hp1020_tusb_adapter_finish':1}
    for name,n in expected_counts.items():need(entry_counts[name]==n,'natural call count: '+name)
    need(entry_counts['hp1020_usb_document_init']<=1 and
         1<=entry_counts['hp1020_tusb_adapter_pending_reset']<=256,
         'single document initialization and bounded recovery query')
    need(16<=entry_counts['hp1020_udc_publish_service']<=256 and
         13<=entry_counts['hp1020_tusb_adapter_pump']<=256,
         'bounded complete ordinary service/pump schedule')
    for stage in ('pre-close','pre-final-service','pre-finish','park'):
        w=struct.unpack('>256I',part(images[stage],*MAILBOX));seen_counts=counts_at[stage]
        # Counters count returned calls; the actual observed entry has not run.
        pending_service=int(stage=='pre-final-service')
        need(w[20]==seen_counts['hp1020_udc_publish_service']-pending_service and
             w[21]==seen_counts['hp1020_tusb_adapter_pump'],
             stage+': mailbox actual service/pump returns match entry trace')
    special = [('intenable', 0xe4, 0), ('lcount', 2, 0), ('lbeg', 0, 0),
               ('lend', 1, 0), ('ps', 0xe6, 15), ('windowbase', 0x48, 0), ('windowstart', 0x49, 1)]
    need(len(model['special_writes']) == len(special), 'seven explicit startup SR writes')
    for event, (name, number, value) in zip(model['special_writes'], special):
        at = event['pc']
        need(event == dict(pc=at, name=name, value=value) and
             elf.instructions.get(at) == bytes((2, number, 0x31)) and pcs.count(at) == 1 and
             elf.symbol('hp1020_entry_normalize') <= at < cps['after-normalization'],
             'actual one-shot admitted WSR prefix')




def prior_receive(sequence,source):
    value=bytearray(4096)
    for k in range(1,sequence):
        at=1024*slot(k);value[at:at+64]=packet_payload(k,source)
    return value


def check_entry(event,ram,a,source,counts,acquired,awaiting_service):
    name=event['name'];args=event['arguments'];adapter=a['hp1020_usb_runtime_adapter']
    document=a['hp1020_usb_runtime_document'];out=a['hp1020_usb_runtime_out']
    mem=a['hp1020_usb_runtime_memory'];provider=a['hp1020_usb_runtime_provider']
    context={'hp1020_usb_document_init':document,'hp1020_usb_document_init_documents':document,
      'hp1020_tusb_adapter_init':adapter,'hp1020_udc_setup_bus_reset':a['hp1020_usb_runtime_setup'],
      'hp1020_udc_setup_offer':a['hp1020_usb_runtime_setup'],
      'hp1020_udc_setup_dispatch':a['hp1020_usb_runtime_setup'],
      'hp1020_udc_ep0_take_submission':a['hp1020_usb_runtime_ep0'],
      'hp1020_udc_ep0_observe':a['hp1020_usb_runtime_ep0'],
      'hp1020_tusb_adapter_pending_reset':adapter,'hp1020_tusb_adapter_ack_reset':adapter,
      'hp1020_tusb_adapter_finish_reset':adapter,'hp1020_tusb_adapter_pump':adapter,
      'hp1020_usb_document_restart':document,'hp1020_udc_publish_arm_out':a['hp1020_usb_runtime_publisher'],
      'hp1020_udc_acquire_packet':a['hp1020_usb_runtime_acquirer'],
      'hp1020_udc_publish_service':a['hp1020_usb_runtime_publisher'],
      'hp1020_tusb_adapter_close_input':adapter,'hp1020_tusb_adapter_finish':adapter}
    if name in context:need(args[0]==context[name],'natural API entry exact original object: '+name)
    if name in ('hp1020_usb_document_init','hp1020_usb_document_init_documents'):
        need(args[1]==mem and counts['hp1020_udc_setup_bus_reset']==0,
             'single original full-memory initialization before reset')
    if name=='hp1020_udc_setup_bus_reset':
        need(args[1:3]==[1,0] and counts['hp1020_tusb_adapter_init']==1,
             'original shared sequence1/full-speed reset after adapter initialization')
    if name=='hp1020_udc_setup_offer':
        need(inside(args[1],32,(STACK,)),'immutable SETUP observation is owned local RAM')
        need(part(ram,args[1],28)==be_words((2,0x79bdf130,0))+SETUP_RECORD,
             'actual raw SETUP observation identity, wire bytes, no endpoint fault')
        need(counts['hp1020_udc_setup_bus_reset']==1,'configuration after actual reset')
    if name=='hp1020_udc_setup_dispatch':
        need(args[1]==2 and args[2]&0xffffff==0x010101 and args[3]==1 and
             counts['hp1020_udc_setup_offer']==1,'same captured sequence2 and separate true capture/stall facts')
    if name=='hp1020_udc_ep0_take_submission':
        need(args[1:5]==[1,2,1,0] and args[5]>>24==0x80 and
             actual_cookie(ram,adapter+60)==(1,2,1,0,0x80),
             'ordinary IN0 status proposal uses original NULL/zero cookie')
        need(scalar(ram,adapter+80)==0 and scalar(ram,adapter+88,2)==0,
             'original zero-length status buffer remains NULL')
    if name=='hp1020_udc_ep0_observe':
        need(inside(args[1],40,(STACK,)) and actual_cookie(ram,args[1])==(1,2,1,0,0x80) and
             part(ram,args[1]+20,20)==be_words((0x8800ffff,0,0xb68ace00,0,0)),
             'actual EP0 copied observation independent lowffff/fault0')
        need(args[2:4]==[0x01010101,0] and counts['hp1020_udc_ep0_take_submission']==1,
             'separate visibility/settlement and actual-known0 supplied after real proposal')
    if name=='hp1020_tusb_adapter_ack_reset':
        parts=(1,2,4);index=counts[name]
        need(index<3 and args[1:4]==[1,1,parts[index]] and
             counts['hp1020_udc_ep0_observe']==1 and part(ram,adapter+20,80)==bytes(80),
             'original three separate promises in order after genuine status delivery')
    if name=='hp1020_tusb_adapter_finish_reset':
        need(args[1:3]==[1,1] and counts['hp1020_tusb_adapter_ack_reset']==3,
             'same recovery ticket after all promises')
    if name=='hp1020_usb_document_restart':
        need(counts['hp1020_tusb_adapter_finish_reset']==1 and scalar(ram,document+68)==1,
             'only production recovery transitions initial generation1')
    if name=='hp1020_udc_publish_arm_out':
        k=counts[name]+1
        need(k<=13 and not awaiting_service and acquired==k-1 and
             scalar(ram,document+68)==2 and scalar(ram,document+72)==k-1 and
             scalar(ram,document+76)==k-1 and scalar(ram,document+80)==0 and
             scalar(ram,adapter+130,1)==0 and scalar(ram,out+58,1)==0,
             'arm only after prior original completion/service/pump, generation2')
        need(counts['hp1020_tusb_adapter_finish_reset']==1 and
             counts['hp1020_tusb_adapter_close_input']==0,'all actual arming before close')
    if name=='hp1020_udc_acquire_packet':
        k=counts[name]+1;s=slot(k);cpu=mem+1024*s
        need(k<=13 and not awaiting_service and counts['hp1020_udc_publish_arm_out']==k,
             'one acquisition per genuinely armed packet')
        need(args[1:5]==list(cookie(k)[:4]) and args[5]>>24==1,
             'original cookie is passed by value to acquisition, not retagged')
        # call0 passes the seventh and eighth arguments in the owned outgoing
        # stack area. Only the three facts bytes are meaningful struct fields.
        need(scalar(ram,event['sp'])==0 and part(ram,event['sp']+5,3)==b'\1\1\1',
             'separate endpoint fault0 and all three acquisition prerequisites')
        need(actual_cookie(ram,adapter+100)==cookie(k) and scalar(ram,adapter+130,1)==1 and
             scalar(ram,adapter+120)==cpu and scalar(ram,adapter+128,2)==64 and
             actual_cookie(ram,out+28)==cookie(k) and scalar(ram,out+58,1)==2,
             'actual EXPOSED original descriptor and DCD owner before acquisition')
        need(tuple(scalar(ram,document+off) for off in (68,72,76,80))==(2,k,k-1,1),
             'one original reservation before acquisition')
        need(actual_cookie(ram,provider+32)==cookie(k) and actual_cookie(ram,provider+180)==cookie(k) and
             scalar(ram,provider+200)==s and scalar(ram,provider+113,1)==1,
             'independent installed device-image identity before hook work')
        poisoned=prior_receive(k,source);poisoned[s*1024:s*1024+64]=poison_prefix(k)
        need(part(ram,mem,4096)==bytes(poisoned) and
             part(ram,a['hp1020_usb_runtime_out_memory'],16)==poison_descriptor(k),
             'exact CPU poison and untouched other receive bytes before acquisition')
        need(part(ram,WITNESS[0]+8688,144)==device_storage(k,source),
             'separate guarded device source before acquisition')
        if k==13:
            need(counts['hp1020_tusb_adapter_close_input']==1,'final ZLP acquired only after actual close')
        else:need(counts['hp1020_tusb_adapter_close_input']==0,'ordinary data acquired before close')
    if name=='hp1020_udc_publish_service' and awaiting_service:
        k=acquired;cpu=mem+1024*slot(k)
        need(actual_cookie(ram,adapter+100)==cookie(k) and scalar(ram,adapter+130,1)==2 and
             scalar(ram,adapter+120)==cpu and scalar(ram,adapter+124)==COUNTS[k-1] and
             scalar(ram,adapter+128,2)==64 and scalar(ram,out+58,1)==0,
             'actual acquisition retires transport only and retains exact PENDING adapter owner')
        need(core_status(ram,a)==CORE_HELD and
             tuple(scalar(ram,document+off) for off in (68,72,76,80))==(2,k,k-1,1),
             'unserviced original reservation and genuine core BUSY remain')
        need(part(ram,mem,4096)==bytes(prior_receive(k+1,source)) and
             part(ram,a['hp1020_usb_runtime_out_memory'],16)==completion_descriptor(k),
             'complete actual cache effects before ordinary service')
    if name=='hp1020_tusb_adapter_pump' and acquired:
        need(not awaiting_service,'pump cannot bypass pending original USB completion')
    if name=='hp1020_tusb_adapter_close_input':
        need(acquired==12 and counts['hp1020_udc_publish_arm_out']==13,
             'two END_DOC boundaries precede sole close with final arm outstanding')
    if name=='hp1020_tusb_adapter_finish':
        need(acquired==13 and not awaiting_service and counts['hp1020_tusb_adapter_close_input']==1,
             'sole finish follows final successful ordinary ZLP delivery')


def check_sources(root,report,source_root):
    sources=js(root,'source-sha256.json')
    need(sources==report['source_sha256'],'actual source manifest/report binding')
    seal_tree(root,'source',sources);seal_tree(root,'target',report['target_sha256'])
    prefix='open-firmware/entry-usb-test/'
    fixed={prefix+'independent-literals.py':ORACLE_HASH,prefix+'literal-addendum.py':ADDENDUM_HASH,
        prefix+'expected-layout.json':LAYOUT_HASH,prefix+'hp1020_usb_runtime_contract.h':HEADER_HASH,
        prefix+'CONTRACT.md':'61f527c6f6cf8cf5d9359ac9526cc4b6e99bdf16585946b183595cf2d4ae4e45',
        prefix+'layout-objects.tsv':'c1c49c7743960ae63fd22d7cb1fdf7d4dfd04904ba2d6e8a200e3a9068b8b681',
        prefix+'layout-fields.tsv':'11aec456c976988eb039258b4d4e4ef163fc098f1e8eb19900817f6f3dcded3f',
        'scripts/hp1020_qemu_ram.py':BACKEND_HASH,
        'scripts/hp1020_entry_qemu.py':'4ef9ffcfac58a326b68df526c8ddec93868cf18cf85eae76682a30ab9cf9d080',
        'scripts/hp1020_entry_machine.py':'a125a4cbda453d7521ab8e57e0a17ebff7c2429187936725ed597515410079f3',
        'scripts/hp1020_xtensa_call0.py':'ed2924d8e46c0e553fe079a5ecdfff77dc40f1aa228588d9a86c39ce98769480',
        'scripts/hp1020_xtensa_properties.py':'8a98e5ba3ead469cd431a06260e78c836993348d878ae96595d0b622538d0280',
        'open-firmware/tinyusb-device/tusb_config.h':'895c6599700b09f84be46ce74ac75f3974ce3b277d98f233134a54aea637616a'}
    fixed['scripts/check-hp1020-entry-usb.py']=sha(Path(__file__).read_bytes())
    fixed.update({'open-firmware/entry-ram-test/references/qemu-primary/'+n:h for n,h in PRIMARY.items()})
    for name,digest in fixed.items():need(sources.get(name)==digest,'frozen independent/shared source '+name)
    required=('scripts/validate-hp1020-entry-usb.py','scripts/build-hp1020-entry-usb-target.sh',
      'scripts/hp1020_entry_usb_machine.py','scripts/hp1020_entry_usb_qemu.py',
      'scripts/hp1020_entry_usb_audit.py',prefix+'startup.S',prefix+'runtime.ld',
      prefix+'hp1020_usb_runtime.c',prefix+'hp1020_usb_runtime_ram.c',prefix+'hp1020_usb_runtime_layout.c',
      'open-firmware/image-pump/hp1020_image_pump.h',
      'open-firmware/udc-out/hp1020_udc_acquire.h',
      'open-firmware/tinyusb-device/patches/protocol-compatibility.patch')
    need(set(required)<=set(sources),'required runtime/audit/observer and original component closure')
    for unit in UNITS:
        matches=[n for n in sources if n.endswith('/'+unit+'.c')]
        need(matches,'complete compiled C source closure: '+unit)
    if source_root is not None:
        live=Path(source_root).resolve()
        for name,digest in sources.items():need(sha(raw(live,name))==digest,'live source changed: '+name)
    return sources


def selected_ar_members(data):
    """Decode the pinned ordinary GNU ar container, without invoking a tool."""
    need(data[:8]==b'!<arch>\n','captured libgcc is an ordinary ar archive')
    pos=8;count=0;names=None;selected={}
    while pos<len(data):
        count+=1
        need(count<=4096 and pos+60<=len(data),'bounded complete ar member header')
        header=data[pos:pos+60]
        need(header[58:60]==b'`\n','ar member header terminator')
        length=header[48:58].strip()
        need(re.fullmatch(rb'[0-9]+',length) is not None,'decimal ar member length')
        size=int(length);start=pos+60;end=start+size
        need(end<=len(data),'ar member bytes stay inside captured archive')
        payload=data[start:end];name=header[:16].rstrip(b' ')
        if name==b'//':
            need(names is None,'one GNU ar long-name table')
            names=payload
        elif name not in (b'/',b'/SYM64/'):
            if name.startswith(b'/'):
                need(names is not None and re.fullmatch(rb'/[0-9]+',name) is not None,
                     'supported GNU ar name reference')
                index=int(name[1:])
                need(index<len(names) and (index==0 or names[index-1:index]==b'\n'),
                     'ar long-name reference starts at an actual name')
                stop=names.find(b'/\n',index)
                need(stop>=index,'terminated GNU ar long name')
                name=names[index:stop]
            else:
                need(name.endswith(b'/'),'supported GNU ar short name')
                name=name[:-1]
            decoded=name.decode('ascii')
            need(decoded and '/' not in decoded and '\\' not in decoded and
                 not any(c.isspace() for c in decoded),'plain ar member basename')
            if decoded in LIBGCC_MEMBERS:
                need(decoded not in selected,'exactly one copy of each selected archive member')
                selected[decoded]=payload
        pos=end
        if size&1:
            need(pos<len(data) and data[pos:pos+1]==b'\n','ar even-byte padding')
            pos+=1
    need(pos==len(data) and set(selected)==set(LIBGCC_MEMBERS),
         'complete bounded archive and both required selected members')
    return selected


def archive_path_alias(value):
    # Compare saved names without resolving a disposable original path on this host.
    need(isinstance(value,str) and posixpath.isabs(value),'absolute original library path')
    value=posixpath.normpath(value)
    if value.startswith(('/tmp/','/var/')):value='/private'+value
    return value


def check_libgcc(root,report,tools):
    prefix='libgcc/'
    actual={n[len(prefix):] for n in report['target_sha256'] if n.startswith(prefix)}
    need(actual=={'libgcc.a','manifest.json',*LIBGCC_MEMBERS},
         'exact captured archive, manifest and two selected-member files')
    archive=raw(root,'target/libgcc/libgcc.a',LIBGCC_BYTES)
    need(len(archive)==LIBGCC_BYTES and sha(archive)==LIBGCC_HASH,
         'exact independently pinned complete compiler library bytes')
    original=tools['libgcc']
    need(original['sha256']==LIBGCC_HASH and
         archive_path_alias(original['path'])==original['path'],
         'captured library matches the actual canonical compiler-selected tool identity')
    manifest=js(root,'target/libgcc/manifest.json')
    expected=dict(schema='hp1020-entry-usb-libgcc-v1',
        archive=dict(file='libgcc.a',original_path=original['path'],sha256=LIBGCC_HASH,bytes=LIBGCC_BYTES),
        members={name:dict(file=name,sha256=digest,bytes=size)
                 for name,(size,digest) in LIBGCC_MEMBERS.items()})
    need(manifest==expected,'exact source-bound archive/member provenance manifest')
    extracted=selected_ar_members(archive)
    for name,(size,digest) in LIBGCC_MEMBERS.items():
        member=raw(root,'target/libgcc/'+name,size)
        need(len(member)==size and sha(member)==digest and member==extracted[name],
             'selected member is the original archive payload: '+name)
    linkmap=raw(root,'target/entry-usb.map').decode('utf-8')
    references=re.findall(r'([^\s()]+\.a)\(([^\s()]+)\)',linkmap)
    need(references and len(references)==len(re.findall(r'\.a\(',linkmap)),
         'all actual link-map library/member references are recognized')
    need({(archive_path_alias(library),name) for library,name in references}==
         {(original['path'],name) for name in LIBGCC_MEMBERS},
         'actual linked compiler-library selection is exactly the two captured original members')
    loads=[line[5:].strip() for line in linkmap.splitlines() if line.startswith('LOAD ')]
    normalized=[archive_path_alias(name) for name in loads]
    need(len(normalized)==len(UNITS)+2 and len(set(normalized))==len(normalized),
         'exact unique27 ordinary objects and one archive LOAD count')
    libraries=[name for name in normalized if name.endswith('.a')]
    objects=[name for name in normalized if name.endswith('.o')]
    need(libraries==[original['path']] and len(objects)==len(UNITS)+1 and
         {posixpath.basename(name) for name in objects}=={u+'.o' for u in UNITS}|{'startup.o'} and
         len({posixpath.dirname(name) for name in objects})==1,
         'actual LOAD inputs are exactly the captured ordinary object names and original library')


def check_tools(root,report,sources):
    tools=js(root,'tool-closure.json');need(tools==report['tool_closure'],'tool closure/report')
    for name in ('compiler','assembler','linker','objdump','nm','readelf','libgcc',
        'gcc-selected-cc1','gcc-selected-as','gcc-selected-ld','gcc-selected-collect2'):
        need(digest_shape(tools[name]['sha256']) and isinstance(tools[name]['path'],str),
             'recorded actual subordinate compiler/tool '+name)
    for name in ('configuration','specs','search-directories'):
        need(sha(raw(root,'compiler-'+name+'.txt'))==tools['compiler-'+name],'compiler config seal')
    headers=tools['compiler_headers'];need(headers,'nonempty captured external compiler/source closure')
    for item in headers.values():need(sha(raw(root,item['snapshot']))==item['sha256'],'actual dependency bytes')
    dep_files={n for n in report['target_sha256'] if n.endswith('.d')}
    need(dep_files=={u+'.d' for u in UNITS},'exact26 compiled dependency records')
    for suffix in ('.o','.su'):
        actual={n for n in report['target_sha256'] if n.endswith(suffix)}
        expected={u+suffix for u in UNITS}|({'startup.o'} if suffix=='.o' else set())
        if suffix=='.o':expected|={'libgcc/'+n for n in LIBGCC_MEMBERS}
        need(actual==expected,
             'exact compiled object/stack-usage closure '+suffix)
    check_libgcc(root,report,tools)
    for name in dep_files:
        text=raw(root,'target/'+name).decode().replace('\\\n',' ')
        need(':' in text,'compiler dependency rule')
        for dependency in text.split(':',1)[1].split():
            dependency=posixpath.normpath(dependency)
            source_matches=[p for p in sources if dependency.endswith('/'+p)]
            target_matches=[p for p in report['target_sha256'] if dependency.endswith('/analysis/boot-handoff/entry-usb/target/'+p)]
            aliases={dependency}
            if dependency.startswith(('/tmp/','/var/')):aliases.add('/private'+dependency)
            need(len(source_matches)==1 or len(target_matches)==1 or aliases&set(headers),
                 'each actual compiler dependency preserved: '+dependency)
    eff=raw(root,'target/effective-source.json')
    need(sha(eff)=='3802581dbca63da449c1d7e1241c745f8db51a9d68273e9c78b1044f69bfd88c',
         'pinned unchanged effective TinyUSB manifest')
    effective=json.loads(eff)['effective_sha256']
    for name,digest in effective.items():
        if name=='LICENSE':
            need(sources['vendor/tinyusb-0.21.0/LICENSE']==digest,'upstream license retained')
            continue
        matches=[r for n,r in headers.items() if n.endswith('/'+name)]
        need(len(matches)==1 and matches[0]['sha256']==digest,
             'actual captured effective dependency agrees with pinned source: '+name)
    return tools


FORBIDDEN_UNITS = {
    'hp1020_udc_setup_offer_offload': 'hp1020_udc_setup.o',
    'hp1020_udc_setup_dispatch_offload': 'hp1020_udc_setup.o',
    'hp1020_tusb_adapter_take_auto_status': 'hp1020_tusb_adapter.o',
    'hp1020_udc_out_cancelled': 'hp1020_udc_out.o',
    'hp1020_udc_ep0_cancelled': 'hp1020_udc_ep0.o'}


def input_forbidden_definitions(data,filename):
    """Independent ET_REL table read; no audit import or target instruction."""
    need(len(data)>=52 and data[:7]==b'\x7fELF\x01\x02\x01','original shortcut input ELF32BE')
    h=struct.unpack_from('>HHIIIIIHHHHHH',data,16)
    typ,machine,version,entry,po,so,flags,hs,ps,pn,ss,sn,si=h
    need((typ,machine,version,entry,po,pn,hs,ss)==(1,94,1,0,0,0,52,40) and
         ps in (0,32) and flags&~0x300==0 and 0<sn<4096 and si<sn and
         so>=52 and so+40*sn<=len(data),'original shortcut input table envelope')
    headers=[struct.unpack_from('>10I',data,so+40*i) for i in range(sn)]
    need(headers[0]==(0,)*10,'original shortcut input null section')
    def section_bytes(index,kind):
        need(0<=index<sn,'original shortcut section index')
        s=headers[index]
        need(s[1]==kind and s[4]+s[5]<=len(data),'original shortcut section bytes')
        return data[s[4]:s[4]+s[5]]
    def string(table,index):
        need(0<=index<len(table),'original shortcut string offset')
        end=table.find(b'\0',index)
        need(end>=index,'original shortcut string terminator')
        return table[index:end].decode('ascii')
    names=section_bytes(si,3)
    section_names=[string(names,s[0]) for s in headers]
    need(len(set(section_names))==sn,'original shortcut unique input sections')
    tables=[i for i,s in enumerate(headers) if s[1]==2]
    need(len(tables)==1,'original shortcut one symbol table')
    st=headers[tables[0]];symbols=section_bytes(tables[0],2)
    need(st[9]==16 and st[5]>0 and st[5]%16==0,'original shortcut symbol shape')
    strings=section_bytes(st[6],3);definitions=[]
    for offset in range(0,len(symbols),16):
        ni,value,size,info,other,index=struct.unpack_from('>IIIBBH',symbols,offset)
        name=string(strings,ni)
        if name not in FORBIDDEN_UNITS or index==0:
            continue
        need(filename==FORBIDDEN_UNITS[name] and info==0x12 and other==0 and 0<index<sn,
             'original shortcut definition owner/type: '+name)
        s=headers[index]
        need(section_names[index]=='.text.'+name and s[1:4]==(1,6,0) and
             s[8]==4 and s[5]>0 and s[4]+s[5]<=len(data) and
             0<size and value+size<=s[5],'original shortcut defining section/extent: '+name)
        definitions.append(dict(name=name,input_object=filename,input_sha256=sha(data),
            section=section_names[index],section_index=index,section_bytes=s[5],
            section_sha256=sha(data[s[4]:s[4]+s[5]]),symbol_offset=value,symbol_bytes=size))
    return definitions


def forbidden_shortcut_policy(root,elf):
    """Missing linked entries require their original definition and GC proof."""
    definitions=[]
    for filename in sorted({unit+'.o' for unit in UNITS}|{'startup.o'}):
        definitions.extend(input_forbidden_definitions(raw(root,'target/'+filename),filename))
    text=raw(root,'target/entry-usb.map').decode('utf-8')
    starts=list(re.finditer(r'^Discarded input sections$',text,re.M))
    ends=list(re.finditer(r'^Memory Configuration$',text,re.M))
    need(len(starts)==len(ends)==1 and starts[0].end()<ends[0].start(),
         'one bounded discarded-input map block')
    begin,end=starts[0].end(),ends[0].start()
    row_pattern=r'^ (\.[^\s]+)[ \t]*(?:\n[ \t]+)?0x([0-9a-fA-F]+)[ \t]+0x([0-9a-fA-F]+)[ \t]+([^\n]+)$'
    rows=[]
    for match in re.finditer(row_pattern,text,re.M):
        section,address,size,owner=match.groups()
        rows.append(dict(section=section,address=int(address,16),bytes=int(size,16),
            owner=owner.strip(),discarded=begin<=match.start() and match.end()<=end,
            line=text.count('\n',0,match.start())+1))
    loads=[archive_path_alias(line[5:].strip()) for line in text.splitlines() if line.startswith('LOAD ')]
    result={}
    for name,filename in FORBIDDEN_UNITS.items():
        original=[row for row in definitions if row['name']==name]
        need(len(original)==1,'one original shortcut definition: '+name)
        record=original[0]
        owners=[p for p in loads if posixpath.basename(p)==filename]
        need(len(owners)==1,'one original shortcut object LOAD: '+name)
        matching=[row for row in rows if row['section']==record['section'] and
                  archive_path_alias(row['owner'])==owners[0]]
        if name in elf.symbols:
            items=elf.symbols[name]
            need(len(items)==1 and items[0][2]==0x12 and items[0][1]>0 and items[0][3]!=0,
                 'retained shortcut must be an actual defined function: '+name)
            entry=elf.symbol(name)
            need(entry in elf.instructions and not any(row['discarded'] for row in matching),
                 'retained shortcut actual instruction and no conflicting discard: '+name)
            result[name]=dict(record,disposition='retained',entry=entry)
        else:
            need(len(matching)==1 and matching[0]['discarded'] and matching[0]['address']==0 and
                 matching[0]['bytes']==record['section_bytes'],
                 'absent shortcut requires exact original discarded section: '+name)
            result[name]=dict(record,disposition='discarded',entry=None,
                              discarded_map_line=matching[0]['line'],input_load=owners[0])
    return result


def check_forbidden_entries(pcs,forbidden):
    need(set(forbidden)==set(FORBIDDEN_UNITS),'all five explicit shortcut policies')
    for name,record in forbidden.items():
        if record['disposition']=='retained':
            need(type(record['entry']) is int and record['entry'] not in pcs,
                 'no typed offload/auto ACK/cancel shortcut: '+name)
        else:
            need(record['disposition']=='discarded' and record['entry'] is None,
                 'only explicit original GC proof can replace a linked entry: '+name)


def check_capture(capture_root,source_root=None):
    """Read only; no producer/oracle imports, target execution or source repair."""
    try:
        root=Path(capture_root).resolve();report=js(root,'validation.json')
        need(report['status']=='pass' and report['candidate_execution'] is True and
             report['independent_capture_gate_present'] is True and not any(k in report for k in
             ('error','source_seal_error','publication_error')),'complete successful execution and unchanged inputs')
        sources=check_sources(root,report,source_root);check_tools(root,report,sources)
        source=input_literal()
        need(len(source)==352 and sha(source)==STREAM_SHA256 and raw(root,'input/small-black.zjs')==source,
             'exact independent352-byte host stream')
        provenance=js(root,'input/provenance.json')
        need(provenance==report['input'] and provenance==dict(
            source='analysis/boot-handoff/entry-ram/fixtures/small-black.zjs',
            input_sha256=STREAM_SHA256,bytes=352,independent_literal_match=True),
            'source fixture provenance, not producer expected output')
        elf_data=raw(root,'target/entry-usb.elf');elf=Elf(elf_data)
        addresses=object_addresses(elf);private_getter(elf)
        forbidden=forbidden_shortcut_policy(root,elf)
        need(js(root,'elf-loads.json')==elf.loads,'actual file-only ELF load metadata')
        need(elf.file(elf.symbol('hp1020_usb_runtime_input',352),352)==source,'actual linked const input')
        need(elf.file(elf.symbol('hp1020_usb_runtime_setup_record',16),16)==SETUP_RECORD,
             'actual immutable source SETUP16')
        need(elf.file(elf.symbol('hp1020_usb_runtime_supplied',40),40)==SUPPLIED_FACTS,
             'all immutable independently supplied prerequisites and separate IN actual0')
        need(elf.symbol('hp1020_usb_runtime_sentinel',256)==DATA_SENTINEL[0], 'actual fixed data sentinel')
        table=elf.symbol('hp1020_usb_runtime_layout',457*4);table_bytes=elf.file(table,457*4)
        need(tuple(struct.unpack('>457I',table_bytes))==LAYOUT_WORDS and
             inside(table,457*4,((elf.alloc['.rodata'][3],elf.alloc['.rodata'][5]),)),
             'every compiler-layout word equals the independent manual table')
        expected_layout_hashes={n:sources['open-firmware/entry-usb-test/'+n] for n in
                               ('layout-objects.tsv','layout-fields.tsv')}
        need(js(root,'layout-witness.json')==dict(status='pass',address=table,words=list(LAYOUT_WORDS),
             sha256=sha(table_bytes),expected_sha256=expected_layout_hashes),'actual layout witness seal')
        cps=dict(zip(PHASES[1:],(elf.symbol(n) for n in CP_SYMBOLS)))
        need(len(set(cps.values()))==6 and js(root,'checkpoints.json')==[[n,a] for n,a in cps.items()] and
             all(a in elf.instructions for a in cps.values()),'six exact actual linked checkpoint boundaries')
        audit=js(root,'linked-audit.json')
        need(audit==report['linked_audit'] and audit['target_sha256']==sha(elf_data) and
             audit['target_bytes']==len(elf_data) and audit['entry']==ENTRY and
             audit['audit_source_sha256']==sources['scripts/hp1020_entry_usb_audit.py'],
             'exact target/source-bound linked admission audit')
        need(sha(raw(root,'annotated-disassembly.txt'))==audit['disassembly_sha256'],
             'annotated-disassembly preserved exact byte seal')
        need(audit['zero_spans']==[list(x) for x in elf.zero] and
             audit['owned_stack']==list(STACK) and audit['initialized_data_span']==list(elf.initialized_data),
             'audit exact original ELF-derived split memory policy')
        need(len(report['cases'])==6,'six independently fixed CPU/paint cases')
        dirs=set();total_steps=0
        for index,case in enumerate(report['cases']):
            pi=index//2;fills=PAINTS[index%2]
            name=f'{index:02d}-{CPU[pi]["name"]}-{fills[0]:02x}';dirs.add(name)
            folder=root/'cases'/name
            need(case==js(folder,'case.json') and case['case']==name and case['status']=='pass' and
                 case['cpu_profile']==CPU[pi] and case['paints']==list(fills) and
                 case['paired_checkpoints']==7,'literal independent CPU/paint matrix')
            supplied=cpu_initial(pi)
            need(js(folder,'initial-registers.json')==supplied,'distinct supplied32 physical ARs')
            initial=make_initial(elf,fills);model=case['model'];q=case['qemu']
            need(model==js(folder/'model','result.json') and model['status']=='pass' and
                 model['snapshots']==js(folder/'model','snapshots.json'),'raw model metadata binding')
            mi=snapshots(folder/'model',model['snapshots'],PHASES)
            qi=snapshots(folder/'qemu',q['snapshots'],QPHASES,True)
            semantic_snapshots(model['snapshots'],mi,initial,supplied,cps,source,elf,addresses)
            semantic_snapshots(q['snapshots'],qi,initial,supplied,cps,source,elf,addresses,True)
            for m,n in zip(model['snapshots'],q['snapshots'][:7]):
                need(registers(m['registers'])==registers(n['registers'],True) and mi[m['name']]==qi[n['name']],
                     'all paired actual CPU/register/whole-region bytes')
            for n in q['snapshots'][7:]:
                need(n['registers']==q['snapshots'][6]['registers'] and qi[n['name']]==qi['park'],
                     'two actual unchanged native self-park steps')
            painted=part(mi['park'],*STACK);changed=[i for i,b in enumerate(painted) if b!=fills[1]]
            wanted=dict(initial_byte=fills[1],changed_bytes=len(changed),
                        lowest_changed_address=STACK[0]+min(changed) if changed else None)
            need(changed and {k:case['stack_paint'][k] for k in wanted}==wanted and
                 isinstance(case['stack_paint'].get('limitation'),str),'independent complete own-stack paint witness')
            model_trace(folder/'model',model,mi,elf,cps,addresses,source,forbidden)
            qemu_ledger(folder/'qemu',q,qi,supplied,cps,sources,elf)
            total_steps+=model['instructions']
        need({p.name for p in (root/'cases').iterdir() if p.is_dir()}==dirs,'exact raw case directory set')
        return True,dict(cases=6,paired_checkpoints=42,qemu_park_steps=12,model_instructions=total_steps,
           target_sha256=sha(elf_data),forbidden_shortcuts=forbidden,
           scope='Saved whole RAM/CPU, original cookies, independent commands/pixels, access replay and debugger transcript; no physical USB/boot/printing proof.')
    except Exception as error:
        return False,dict(error=type(error).__name__+': '+str(error))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_root');parser.add_argument('--source-root')
    args=parser.parse_args();ok,detail=check_capture(args.capture_root,args.source_root)
    print(json.dumps(dict(ok=ok,detail=detail),sort_keys=True,indent=2))
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':main()
