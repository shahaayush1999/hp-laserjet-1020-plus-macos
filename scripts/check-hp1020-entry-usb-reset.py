#!/usr/bin/env python3
"""Independent saved-evidence gate for one continuous SOFT_RESET race.

Static unexecuted draft. Frozen literals precede the new runtime implementation.
Only the hash-pinned prior independent gate is imported for neutral readers;
no target, producer, saved oracle or new observer/audit module is imported.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import posixpath
import re
import struct

BASE_SHA256 = '77d10cf9f24db9776743613aeddb4c58640829257a8222346ef1b0fb23f13720'
_base_file = Path(__file__).with_name('check-hp1020-entry-usb.py')
if hashlib.sha256(_base_file.read_bytes()).hexdigest() != BASE_SHA256:
    raise ValueError('neutral independent helper bytes changed')
_spec = importlib.util.spec_from_file_location('hp1020_reset_independent_readers', _base_file)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
need, sha, raw, js, part, put, inside = B.need, B.sha, B.raw, B.js, B.part, B.put, B.inside
be_words, scalar, actual_cookie = B.be_words, B.scalar, B.actual_cookie

# Begin exact text of frozen semantic V2 (not an imported or producer oracle).
"""Independent continuous SOFT_RESET requirements; static/unexecuted.

No producer imports, file I/O or execution entry point. Source identities are
predictions for comparisons against genuine binds, never runtime input cookies.
Public witness byte offsets/stop selectors require a separate frozen amendment.
"""

PROFILE = "raw-soft-reset-late-success-fresh-document-reused-stale-cookie"
PAINTS = ((0xa5, 0x5a), (0xcc, 0x96))
CPU = dict(name="ordinary-privilege", ps=0, intenable=0, windowbase=0,
           windowstart=1, sar=0, lbeg=0, lend=0, lcount=0)
PHYSICAL_AR32 = tuple(0x8a000001 + i * 0x10101 for i in range(32))
ENTRY, STACK_BYTES = 0x100167a8, 8192
LIMITS = dict(model_instructions=10000000, qemu_seconds=120,
              qemu_commands=4096, qemu_ledger_bytes=16*1024*1024)

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
CHUNKS = ((0,4,"magic"), (4,56,"start-doc"), (56,228,"start-page"),
          (228,264,"BIH"), (264,304,"BID"), (304,320,"end-JBIG"),
          (320,336,"end-page"), (336,352,"end-doc"))
CUT_BYTES = 320
RAW_CONFIGURATION = bytes.fromhex("0009010000000000")
RAW_SOFT_RESET = bytes.fromhex("2102000000000000")
RESET_RECORD = bytes.fromhex("80000000000000002102000000000000")
INGRESS_SEQUENCES = (1,2,3)
RECOVERY_TICKETS = ((1,1), (2,2))
CONFIG_STATUS = (1,2,1,0,0x80)
RESET_STATUS = (8,3,3,0,0x80)
OLD_HELD = (7,3,2,6,1)
REUSED_CURRENT = (10,4,3,2,1)
FINAL_OUT = (15,4,3,7,1)

# (scope, original cookie, physical receive-slot index, source offset, count,
#  admitted through receive_complete_data). The discarded old SUCCESS is false;
#  the fresh final zero-length packet is true but makes no parser feed.
PACKETS = (
    (1, (2,3,2,1,1), 0, 0,   64, True),
    (2, (3,3,2,2,1), 1, 64,  64, True),
    (3, (4,3,2,3,1), 2, 128, 64, True),
    (4, (5,3,2,4,1), 3, 192, 64, True),
    (5, (6,3,2,5,1), 0, 256, 64, True),
    (6, (7,3,2,6,1), 1, 320, 32, False),
    (7, (9,4,3,1,1), 0, 0,   64, True),
    (8, (10,4,3,2,1),1, 64,  64, True),
    (9, (11,4,3,3,1),2, 128, 64, True),
    (10,(12,4,3,4,1),3, 192, 64, True),
    (11,(13,4,3,5,1),0, 256, 64, True),
    (12,(14,4,3,6,1),1, 320, 32, True),
    (13,(15,4,3,7,1),2, 352,  0, True),
)
BIND_COOKIES = (CONFIG_STATUS,) + tuple(p[1] for p in PACKETS[:6]) + (
    RESET_STATUS,) + tuple(p[1] for p in PACKETS[6:])
SUCCESSFUL_RECEIVE_COMPLETIONS = tuple((p[1][2], p[1][3], p[4])
                                     for p in PACKETS if p[5])
NONEMPTY_FEEDS = tuple((p[1][2], p[1][3], STREAM[p[3]:p[3]+p[4]])
                      for p in PACKETS if p[5] and p[4])
DOCUMENT_EVENT = (3,1,0,1)
WITNESS_EVENT_ROWS = ((3,1,0,1,0), (0,0,0,0,0))
PIXELS = bytes.fromhex("ff"*32)
WITNESS_PIXELS = PIXELS + bytes(32)
PRODUCTION_OUTPUT = PIXELS + bytes(32768-32)
COUNTS = dict(binds=15, bulk_publications=13, bulk_acquisitions_ok=13,
              bulk_acquisitions_stale=1, acquired_bytes=704, fed_bytes=672,
              visibility_payload_bytes=832, visibility_descriptor_bytes=208,
              receive_complete_data=12, receive_release=12, nonempty_feed=11,
              queued_cancel_callbacks=1, out_cancel_mark_ok=1,
              out_cancel_mark_stale=1, cancellation_settlements=0,
              document_restarts=2, ep0_status_callbacks=2,
              ring_accept=1, ring_complete=1, document_callbacks=1,
              close_input=1, finish=1, conditional_wait=4, conditional_stale=2)

DESCRIPTOR_DMA = 0x579bdf10
RECEIVE_DMAS = (0x24681340,0x24682340,0x24683340,0x24684340)
SETUP_DMA = 0x79bdf130
EP0_IN_DESCRIPTOR_DMA, EP0_IN_PACKET_DMA = 0xa468ace0, 0xb68ace00
EP0_PREPARED_WORDS = (0x08000000,0,EP0_IN_PACKET_DMA,0)
EP0_COMPLETION_WORDS = (0x8800ffff,0,EP0_IN_PACKET_DMA,0)
EP0_ACTUAL_KNOWN, EP0_ACTUAL = 1,0

def payload_image(scope):
    p = PACKETS[scope-1]
    _, _, slot, start, count, _ = p
    return STREAM[start:start+count] + bytes(
        0x80 | ((0x69 ^ (slot*0x1d) ^ (i*7)) & 0x7f)
        for i in range(count,64))

def completed_descriptor(scope):
    p = PACKETS[scope-1]
    return (0x88000000 | p[4], 0, RECEIVE_DMAS[p[2]], 0)

def cpu_poison(slot):
    return ((0xc35a0000|slot,0x13579bdf,0xfedcba90,0x2468ace0),
            bytes((0xd3 ^ slot*0x29 ^ i*0x17) & 0xff for i in range(64)))

def receive_memory(successful_scope):
    """After acquisition(s), never a fabricated effect of restart or stale replay."""
    data = bytearray(4096)
    for scope in range(1,successful_scope+1):
        slot = PACKETS[scope-1][2]
        data[slot*1024:slot*1024+64] = payload_image(scope)
    return bytes(data)

FINAL_RECEIVE_PREFIX_SCOPES = (11,12,13,10)

# Four WAIT calls require a reset ticket; two STALE calls require the exact old
# cookie. Public refusal-row layout must keep those identity domains separate.
REFUSALS = (
    ("finish-owned", "printer", 1, (2,2), 0),
    ("receive-DCD", "printer", 1, (2,2), 1),
    ("receive-PENDING", "printer", 1, (2,2), 1),
    ("finish-missing-transport", "printer", 1, (2,2), 0),
    ("reused-old-acquisition", "OUT", 2, OLD_HELD, 0),
    ("reused-old-cancel-mark", "OUT", 2, OLD_HELD, 0),
)

CUT_320 = dict(generation=2, issued=6, consumed=5, count=1,
    stopped=0, quiescent=0, receive_error=0, output_quiescent=0,
    parser_documents=1, parser_page_count=1, parser_raster_count=1,
    parser_document_open=1, parser_phase=4, parser_framing=1,
    parser_page_complete=0, stream_active=1, jbig_ended=1, stream_bands=1,
    stream_rows=8, payload_consumed=6, padding=18, stream_pages=0,
    output_active=1, output_page_index=0, pages_drained=0,
    documents_completed=0, document_first_page=0,
    ring_stride=4, ring_rows=8, ring_capacity_rows=2048, ring_slot_bytes=8192,
    ring_producer=1, ring_selection=0, ring_completion=0,
    ring_copied=8, ring_accepted=0, ring_completed=0, ring_slot0_state=1,
    pixel_bytes=0, document_callbacks=0, bulk_owner=1, out_phase=2,
    core_out1=5, control_epoch=2, active_control_epoch=2,
    transport_epoch=3, active_transport_epoch=3, last_submission_id=7)
RESET_OWNED = dict(CUT_320, stopped=1, receive_error=7,
    control_epoch=3, active_control_epoch=3, transport_epoch=4,
    fenced=1, input_closed=1, reset_transport_epoch=4,
    reset_id=2, reset_generation=2, reset_active=1, reset_parts=0,
    last_recovery_id=2, class_request_id=1, current_request_id=1,
    current_action=3, current_issued=0, deferred=1, deferred_epoch=3,
    owner_cancel_requested=1, out_cancel_requested=1, ep0_in_owner=0)
LATE_PENDING = dict(RESET_OWNED, bulk_owner=2, out_phase=0,
                    out_cancel_requested=0, owner_actual=32,
                    owner_result=0, owner_expected_cancel=0)
DRAINED = dict(RESET_OWNED, bulk_owner=0, out_phase=0, core_out1=0,
               owner_cancel_requested=0, out_cancel_requested=0)
TWO_PROMISES = dict(DRAINED, quiescent=1, output_quiescent=1, reset_parts=3)
BEFORE_SECOND_RESTART = dict(TWO_PROMISES, reset_parts=7)
RESET_METADATA_CLEARED = dict(generation=3, issued=0, consumed=0, count=0,
    stopped=0, quiescent=0, receive_error=0, output_quiescent=0,
    parser_documents=0, parser_page_count=0, stream_pages=0,
    stream_active=0, output_active=0, pages_drained=0,
    documents_completed=0, document_first_page=0,
    ring_copied=0, ring_accepted=0, ring_completed=0,
    feed_generation=0, feeding=0, document_finished=0, output_finished=0)
REUSE = dict(generation=3, issued=2, consumed=1, count=1, stopped=0,
    quiescent=0, receive_error=0, control_epoch=3, active_control_epoch=3,
    transport_epoch=4, active_transport_epoch=4, last_submission_id=10,
    bulk_owner=1, out_phase=2, core_out1=5,
    reset_active=0, reset_parts=0, parser_documents=1, parser_page_count=0,
    stream_pages=0, pages_drained=0, documents_completed=0,
    output_active=0, ring_copied=0, ring_accepted=0, ring_completed=0,
    pixel_bytes=0, document_callbacks=0)
BEFORE_CLOSE = dict(generation=3, issued=7, consumed=6, count=1,
    stopped=0, quiescent=0, receive_error=0, output_quiescent=0,
    feed_generation=3, feeding=0, document_finished=0, output_finished=0,
    parser_documents=1, stream_pages=1, pages_drained=1,
    documents_completed=1, document_first_page=1, ring_copied=8,
    ring_accepted=8, ring_completed=8, ring_slot0_state=0,
    input_closed=0, fenced=0, control_epoch=3, active_control_epoch=3,
    transport_epoch=4, active_transport_epoch=4, last_submission_id=15,
    opened=1, configuration_value=1, reset_active=0, reset_parts=0,
    class_request_id=1, current_request_id=1, last_request_id=1,
    current_action=4, current_issued=1, last_recovery_id=2,
    ep0_in_owner=0, ep0_out_owner=0, class_ep0_live=0,
    class_ep0_request_id=0, response_owned=0, bulk_owner=1,
    core_out1=5, out_phase=2, pixel_bytes=32, document_callbacks=1)
BEFORE_FINAL_SERVICE = dict(BEFORE_CLOSE, input_closed=1,
    bulk_owner=2, out_phase=0, owner_actual=0, owner_result=0)
BEFORE_FINISH = dict(BEFORE_CLOSE, input_closed=1, consumed=7, count=0,
                    bulk_owner=0, out_phase=0, core_out1=0)
PARK = dict(BEFORE_FINISH, stopped=1, fenced=1,
            document_finished=1, output_finished=1)

# Logical hooks only: reads are independent supplies, not simulated write effects.
PROGRAM_INITIAL = (
    (1,0x220,0x51,0),(2,0x220,0xa0,0),
    (1,0x22c,0x80,0),(2,0x22c,0x40,0),
    (1,0x508,0x100000c1,0),(2,0x508,0x020000c1,0),
    (1,0x418,0x00a700a7,0),(2,0x418,0x00a500a7,0),
    (3,0xffffffff,0,0),(1,0x028,0x40,0),(1,0x020,0x51,0),
    (2,0x020,0xa0,0),(1,0x02c,0x80,0),(2,0x02c,0x40,0),
    (1,0x50c,0x100000d1,0),(2,0x50c,0x020000d1,0),
    (1,0x418,0x00a500a7,0),(2,0x418,0x00a500a5,0),
    (3,0xffffffff,0,0),
)

def publication_rows(scope):
    dma = RECEIVE_DMAS[PACKETS[scope-1][2]]
    return ((1,0x404,0x34120320,0),(1,0x220,0x60,0),
            (1,0x22c,0x40,0),(1,0x408,0x0000a001,0),
            (4,dma,64,0),(5,DESCRIPTOR_DMA,16,0),(3,0xffffffff,0,0),
            (2,0x234,DESCRIPTOR_DMA,0),(3,0xffffffff,0,0),
            (2,0x220,0x120,0),(3,0xffffffff,0,0),(1,0x220,0x20,0),
            (2,0x404,0x34120324,0),(3,0xffffffff,0,0))

def acquisition_rows(scope):
    return ((6,DESCRIPTOR_DMA,16,0),
            (7,RECEIVE_DMAS[PACKETS[scope-1][2]],64,0),(8,0,0,0))

def logical_rows():
    rows = [(0,i+1,*r) for i,r in enumerate(PROGRAM_INITIAL)]
    for scope in range(1,14):
        for row in publication_rows(scope) + acquisition_rows(scope):
            rows.append((scope,len(rows)+1,*row))
    return tuple(rows)

LOGICAL_COUNTS = {1:74,2:47,3:54,4:13,5:13,6:13,7:13,8:13}
LOGICAL_ROWS, RANGE_ROWS = 240,65
# Reset at scope6 before its acquisition adds no hook rows. Stale replay after
# publication8 similarly adds none. These totals bind phase checks independently.
TRACE_CUTS = dict(old_320_armed=118, old_late_acquired=121,
                 fresh_reused_armed=152, before_close=237, final=240)
RANGE_CUTS = dict(old_320_armed=27, old_late_acquired=30,
                 fresh_reused_armed=37, before_close=62, final=65)
FORBIDDEN = (
    "old receive_complete_data(2,6)", "old semantic feed[320:352]",
    "out_cancelled", "ep0_cancelled", "adapter_cancelled",
    "offload capture/dispatch/automatic status", "CSR_DONE",
    "direct receive restart outside class", "runtime reinitialize",
    "per-document EOF", "host write/forced PC after initial entry seed",
)
# End frozen semantic V2. Preserve status cookie before additive state map.
RESET_STATUS_COOKIE = RESET_STATUS
# Begin exact text of frozen public-layout/natural-stop literal addendum.
"""Static independent layout/stop additions, not an executable validator.

No imports, producer code, files, result data or entry point. Semantic V2 remains
unchanged and supplies stream/cookies/phase semantics. These literals add only
the approved public schema, exact natural ordering and source-derived contexts.
"""

SEMANTIC_V2_SHA256 = "aab93eba1de9c9123e9344d8bb5fc642b690e7ac4b02c2fc3fd5efa4d501b333"
PUBLIC_HEADER_SHA256 = "a73a3904b094126e811f6d26249ab93d3d71cae7f5e0c00cedd10e77addc4679"
PUBLIC_MANIFEST_SHA256 = "ac39294692cfdadbc35151facc3911d1fb42521b278e5a9d26f727cb3012f991"
LAYOUT_HEADER = (0x4850554c, 2, 525, 16, 118)
OBJECTS = (
    (1,13496,4),(2,114704,16),(3,56,4),(4,408,4),(5,64,4),
    (6,16,16),(7,136,4),(8,160,16),(9,80,4),(10,88,4),(11,140,4),
    (12,152,4),(13,224,4),(14,1024,4),(15,9216,4),(16,16,1),
)
# Replace only these existing manual field rows; retain every other1..101 row.
REPLACED_FIELDS = ((93,15,8160,540),(94,15,8720,144),
                   (95,15,8864,64),(96,15,8928,40))
ADDED_FIELDS = (
    (102,13,204,4),(103,13,208,4),(104,13,212,4),(105,13,216,4),
    (106,13,220,1),(107,13,61,1),(108,5,59,1),(109,15,8968,216),
    (110,4,348,4),(111,4,132,1),(112,4,133,1),(113,3,24,4),
    (114,3,48,1),(115,3,49,1),(116,3,52,1),(117,3,32,4),
    (118,4,364,1),
)
WITNESS = dict(bytes=9216, head_guard=(0,16), io=(16,5760),
    io_guard=(5776,16), ranges=(5792,2340), range_padding=(8132,12),
    range_guard=(8144,16), binds=(8160,540), bind_padding=(8700,4),
    bind_guard=(8704,16), device=(8720,144), pixels=(8864,64),
    documents=(8928,40), checks=(8968,216), reserved=(9184,32))
DEVICE = dict(guard0=(0,16), descriptor=(16,16), guard1=(32,16),
              guard2=(48,16), payload=(64,64), guard3=(128,16))
GUARD_BYTE = 0xa7
PROVIDER_RESET_COOKIE = (204,20)
PROVIDER_RESET_PADDING = (221,3)
MAILBOX_ADDITIONS = {128:6,129:2}
MAILBOX_RESERVED = (130,126)

# operation/domain/result then five original semantic identity words/detail.
# Domain2 is printer-return; domain8 is OUT-return. Identity kind is separate.
CHECK_ROWS = (
    (1,2,1,2,2,0,0,0,0),
    (2,2,1,2,2,0,0,0,1),
    (3,2,1,2,2,0,0,0,1),
    (4,2,1,2,2,0,0,0,0),
    (5,8,2,7,3,2,6,1,0),
    (6,8,2,7,3,2,6,1,0),
)
CHECK_IDENTITY_KINDS = ("RESET_TICKET",)*4 + ("ORIGINAL_COOKIE",)*2
CHECK_FUNCTIONS = (
    "hp1020_tusb_adapter_finish_reset", "hp1020_tusb_adapter_ack_reset",
    "hp1020_tusb_adapter_ack_reset", "hp1020_tusb_adapter_finish_reset",
    "hp1020_udc_acquire_packet", "hp1020_udc_out_request_cancel",
)

# The startup normalizer/park labels are the existing audited assembly symbols.
# Symbols are names, not supplied PCs: actual addresses come from the sealed ELF.
# Columns: label, function/startup role, check rows, I/O rows, ranges, binds.
STOPS = (
    ("after-normalization", "after-normalization", None,None,None,None),
    ("pre-c", "hp1020_usb_runtime_c", 0,0,0,0),
    ("pre-initial-status", "hp1020_udc_ep0_take_submission", 0,19,0,1),
    ("pre-reset-offer", "hp1020_udc_setup_offer", 0,118,27,7),
    ("pre-cancel-mark", "hp1020_udc_out_request_cancel", 0,118,27,7),
    ("pre-receive-owned", "hp1020_tusb_adapter_ack_reset", 1,118,27,7),
    ("pre-late-service", "hp1020_udc_publish_service", 3,121,30,7),
    ("pre-receive-drained", "hp1020_tusb_adapter_ack_reset", 3,121,30,7),
    ("pre-restart", "hp1020_usb_document_restart", 4,121,30,7),
    ("pre-reset-status", "hp1020_udc_ep0_take_submission", 4,121,30,8),
    ("pre-fresh-arm", "hp1020_udc_publish_arm_out", 4,121,30,8),
    ("pre-fresh-service", "hp1020_udc_publish_service", 4,138,35,9),
    ("pre-reuse-arm", "hp1020_udc_publish_arm_out", 4,138,35,9),
    ("pre-stale-acquire", "hp1020_udc_acquire_packet", 4,152,37,10),
    ("pre-stale-cancel", "hp1020_udc_out_request_cancel", 5,152,37,10),
    ("post-stale-pair", "hp1020_usb_runtime_ram_install_bulk", 6,152,37,10),
    ("pre-close", "hp1020_tusb_adapter_close_input", 6,237,62,15),
    ("pre-final-service", "hp1020_udc_publish_service", 6,240,65,15),
    ("pre-finish", "hp1020_tusb_adapter_finish", 6,240,65,15),
    ("park", "park", 6,240,65,15),
)
ROLE_ARGUMENTS = {
    "pre-initial-status": dict(original=(1,2,1,0,0x80)),
    "pre-reset-offer": dict(sequence=3,record_hex="80000000000000002102000000000000"),
    "pre-cancel-mark": dict(original=(7,3,2,6,1)),
    "pre-receive-owned": dict(ticket=(2,2),part=1),
    "pre-receive-drained": dict(ticket=(2,2),part=1),
    "pre-reset-status": dict(original=(8,3,3,0,0x80)),
    "pre-stale-acquire": dict(original=(7,3,2,6,1),fault=0),
    "pre-stale-cancel": dict(original=(7,3,2,6,1)),
    "post-stale-pair": dict(original=(10,4,3,2,1),offset=64,count=64),
}
PAIRED_SNAPSHOTS = 21
QEMU_SNAPSHOTS = 23
PARK_STEPS = 2
CORE_STOP_LABELS = ("after-normalization","pre-c","pre-close",
                   "pre-final-service","pre-finish","park")
OUTER_CONTEXT = dict(adapter_busy=0,adapter_stack_active=0,provider_callback_depth=0)
RESTART_CONTEXT = dict(adapter_busy=1,adapter_stack_active=0,provider_callback_depth=0)

PRIVATE_CORE = dict(bytes=68,ep_status_offset=52,ep_status_bytes=16,
                    busy=1,stalled=2,claimed=4,ep0_in=53,bulk_out1=54)
CORE_IDLE = bytes(16)
CORE_EP0_IN = bytes.fromhex("00010000000000000000000000000000")
CORE_BULK_OUT = bytes.fromhex("00000500000000000000000000000000")
CORE_STATUS_BY_STOP = {
    "pre-c":CORE_IDLE,
    "pre-initial-status":CORE_EP0_IN,
    "pre-reset-offer":CORE_BULK_OUT,
    "pre-cancel-mark":CORE_BULK_OUT,
    "pre-receive-owned":CORE_BULK_OUT,
    "pre-late-service":CORE_BULK_OUT,
    "pre-receive-drained":CORE_IDLE,
    "pre-restart":CORE_IDLE,
    "pre-reset-status":CORE_EP0_IN,
    "pre-fresh-arm":CORE_IDLE,
    "pre-fresh-service":CORE_BULK_OUT,
    "pre-reuse-arm":CORE_IDLE,
    "pre-stale-acquire":CORE_BULK_OUT,
    "pre-stale-cancel":CORE_BULK_OUT,
    "post-stale-pair":CORE_BULK_OUT,
    "pre-close":CORE_BULK_OUT,
    "pre-final-service":CORE_BULK_OUT,
    "pre-finish":CORE_IDLE,
    "park":CORE_IDLE,
}

# Additional source-derived predicates at the new explicit stops. Semantic V2
# owns CUT_320, RESET_OWNED, LATE_PENDING, DRAINED, REUSE and final phase maps.
INITIAL_STATUS = dict(generation=1,issued=0,consumed=0,count=0,
    stopped=1,receive_error=0,control_epoch=2,active_control_epoch=2,
    transport_epoch=3,active_transport_epoch=3,last_submission_id=1,
    ep0_in_owner=1,ep0_in_phase=1,bulk_owner=0,out_phase=0,
    original_buffer=0,requested=0,allocation=64,reset_active=1,
    last_recovery_id=1,reset_parts=0,class_request_id=0,response_owned=0)
ADMITTED_BEFORE_MARK = dict(generation=2,issued=6,consumed=5,count=1,
    stopped=1,receive_error=7,control_epoch=3,active_control_epoch=2,
    transport_epoch=4,active_transport_epoch=3,bulk_owner=1,out_phase=2,
    owner_cancel_requested=1,out_cancel_requested=0,provider_cancel_requested=1,
    fenced=1,input_closed=1,pending_destructive=0,ep0_in_owner=0)
RESET_STATUS = dict(generation=3,issued=0,consumed=0,count=0,stopped=0,
    receive_error=0,quiescent=0,output_quiescent=0,
    control_epoch=3,active_control_epoch=3,transport_epoch=4,active_transport_epoch=4,
    last_submission_id=8,ep0_in_owner=1,ep0_in_phase=1,
    original_buffer=0,requested=0,allocation=64,bulk_owner=0,out_phase=0,
    reset_active=0,reset_parts=0,last_recovery_id=2,class_request_id=1,
    current_request_id=1,last_request_id=1,current_action=4,current_issued=1,
    class_ep0_live=1,class_ep0_request_id=1,response_owned=1,deferred=0)
FRESH_FIRST_ARM = dict(generation=3,issued=0,consumed=0,count=0,
    ep0_in_owner=0,bulk_owner=0,out_phase=0,provider_bulk_live=0,
    class_ep0_live=0,class_ep0_request_id=0,response_owned=0,last_submission_id=8)
FRESH_FIRST_PENDING = dict(generation=3,issued=1,consumed=0,count=1,
    bulk_owner=2,out_phase=0,owner_actual=64,owner_result=0,
    original=(9,4,3,1,1),last_submission_id=9,parser_documents=0)
FRESH_SECOND_ARM = dict(generation=3,issued=1,consumed=1,count=0,
    bulk_owner=0,out_phase=0,last_submission_id=9,parser_documents=1,
    stream_pages=0,pages_drained=0,documents_completed=0)

SAVED_CANCEL_COOKIE = (7,3,2,6,1)
NEW_REUSED_COOKIE = (10,4,3,2,1)
RESET_RECORD = bytes.fromhex("80000000000000002102000000000000")
RESET_WIRE = bytes.fromhex("2102000000000000")
FINAL_SOURCE = (352,0)
POISON_MULTIPLIERS = (0x29,0x17)
PADDING_MULTIPLIERS = (0x1d,7)
BEFORE_RESTART_MEMORY_PRESERVED_BYTES = 114704
OUTPUT_CALLBACK_BEFORE_RESET = 0
FINAL_PIXELS = bytes.fromhex("ff"*32) + bytes(32)
FINAL_EVENTS = ((3,1,0,1,0),(0,0,0,0,0))

SUPPLEMENTAL_FINAL_COUNTS = dict(check_rows=6,cancel_api_calls=2,
    actual_request_cancel_callbacks=1,cancellation_settlements=0,
    acquire_attempts=14,acquire_ok=13,acquire_stale=1,
    document_restart_entries=2,status_callbacks=2,
    receive_promises=2,output_promises=2,transport_promises=2,recovery_finishes=2,
    actual_close_entries=1,actual_finish_entries=1,
    payload_visibility_bytes=832,descriptor_visibility_bytes=208,input_consumed=672)

LIMITS = dict(model_instructions=10000000,qemu_seconds=120,
              qemu_commands=4096,qemu_ledger_bytes=16777216)
CAPTURE_GEOMETRY = dict(main_bytes=205280,island_bytes=1724,
    bytes_per_snapshot=207004,memory_chunks=57,register_reads=57,
    snapshot_read_commands=2622,initial_seed_commands=98,bootstrap_commands=4,
    memory_hex_and_seed_bytes=9936192)
# End frozen additive literals. The checking algorithms below are new/local.

PREFIX = 'open-firmware/entry-usb-reset-test/'
CHECKPOINTS = tuple(row[0] for row in STOPS)
MODEL_PHASES = ('initial',) + CHECKPOINTS
QEMU_PHASES = MODEL_PHASES + ('park-step-1','park-step-2')
OBJECT_ROWS = tuple((i,B.OBJECTS[i-1][1],n,a) for i,n,a in OBJECTS)
FIELD_ROWS = {i:(obj,name,off,width) for i,obj,name,off,width in B.FIELDS}
for i,obj,off,width in REPLACED_FIELDS:
    FIELD_ROWS[i] = (obj,FIELD_ROWS[i][1],off,width)
for i,obj,off,width in ADDED_FIELDS:
    FIELD_ROWS[i] = (obj,'reset-contract-field-'+str(i),off,width)
TABLE_WORDS = LAYOUT_HEADER + tuple(v for i,n,a in OBJECTS for v in (i,n,a)) + tuple(
    v for i,(obj,name,off,width) in FIELD_ROWS.items() for v in (i,obj,off,width))
SETUP_CONFIGURATION = bytes.fromhex('80000000000000000009010000000000')
FACTS = bytes([1])*26 + bytes(2) + bytes([1])*4 + bytes(4) + bytes([1])*4
GUARD = bytes([0xa7])*16
ALL_ROWS = logical_rows()

# Extra manual offsets from unchanged production declarations. Public table
# already freezes document.output at92, stream13192, ring112 and parser8796.
# page192*16+raster12*128=4608; parser phase4668/framing8784/doc-open8786.
EXTRA_FIELDS = {
 'parser_page_count':(1,4712,4),'parser_raster_count':(1,4716,4),
 'parser_phase':(1,4760,4),'parser_framing':(1,8876,1),
 'parser_document_open':(1,8878,1),'parser_page_complete':(1,157,1),
 'stream_active':(1,13280,1),'jbig_ended':(1,13281,1),
 'stream_bands':(1,13252,4),'stream_rows':(1,13256,4),
 'payload_consumed':(1,13260,4),'padding':(1,13264,4),
 'ring_stride':(1,13288,4),'ring_rows':(1,13292,4),
 'ring_capacity_rows':(1,13296,4),'ring_slot_bytes':(1,13300,4),
 'ring_producer':(1,13304,4),'ring_selection':(1,13308,4),
 'ring_completion':(1,13312,4),'ring_slot0_state':(1,13332,4),
 'output_page_index':(1,13448,4),'output_active':(1,13468,1),
 'reset_id':(3,16,4),'reset_generation':(3,20,4),'last_request_id':(3,24,4),'current_action':(3,48,1),'current_issued':(3,49,1),
 'class_ep0_live':(3,52,1),'class_ep0_request_id':(3,32,4),
 'deferred':(4,364,1),'deferred_epoch':(4,320,4),
 'owner_cancel_requested':(4,132,1),'owner_expected_cancel':(4,133,1),
 'owner_actual':(4,124,4),'owner_result':(4,131,1),
 'out_cancel_requested':(5,59,1),'pending_destructive':(4,363,1),
 'provider_bulk_live':(13,60,1),'provider_cancel_requested':(13,61,1),
 'ep0_in_phase':(7,126,1),
}
LIVE = dict(B.LIVE_FIELDS,ring_copied=19,ring_accepted=20,ring_completed=21,
    adapter_busy=37,adapter_stack_active=38)
PHASE_MAP = {
 'pre-initial-status':INITIAL_STATUS,'pre-reset-offer':CUT_320,
 'pre-cancel-mark':ADMITTED_BEFORE_MARK,'pre-receive-owned':RESET_OWNED,
 'pre-late-service':LATE_PENDING,'pre-receive-drained':DRAINED,
 'pre-restart':BEFORE_SECOND_RESTART,'pre-reset-status':RESET_STATUS,
 'pre-fresh-arm':FRESH_FIRST_ARM,'pre-fresh-service':FRESH_FIRST_PENDING,
 'pre-reuse-arm':FRESH_SECOND_ARM,'pre-stale-acquire':REUSE,
 'pre-stale-cancel':REUSE,'post-stale-pair':REUSE,
 'pre-close':BEFORE_CLOSE,'pre-final-service':BEFORE_FINAL_SERVICE,
 'pre-finish':BEFORE_FINISH,'park':PARK,
}
# (current scope, latest installed/completed image scope, successfully acquired).
PHASE_STORAGE = {
 'pre-initial-status':(0,0,0),'pre-reset-offer':(6,5,5),
 'pre-cancel-mark':(6,5,5),'pre-receive-owned':(6,5,5),
 'pre-late-service':(6,6,6),'pre-receive-drained':(6,6,6),
 'pre-restart':(6,6,6),'pre-reset-status':(6,6,6),
 'pre-fresh-arm':(7,6,6),'pre-fresh-service':(7,7,7),
 'pre-reuse-arm':(8,7,7),'pre-stale-acquire':(8,7,7),
 'pre-stale-cancel':(8,7,7),'post-stale-pair':(8,7,7),
 'pre-close':(13,12,12),'pre-final-service':(13,13,13),
 'pre-finish':(13,13,13),'park':(13,13,13),
}
EXTRA_API_NAMES = ('hp1020_udc_out_request_cancel',
 'hp1020_usb_runtime_ram_reset_observation','hp1020_usb_runtime_ram_install_bulk',
 'hp1020_usb_runtime_ram_check','hp1020_usb_receive_complete_data',
 'hp1020_usb_receive_release','hp1020_image_output_feed',
 'hp1020_image_ring_accept','hp1020_image_ring_complete',
 'dcd_edpt0_status_complete','driver_xfer','document_out',
 'request_cancel','output','document_event')
API_NAMES = B.ENTRY_NAMES + EXTRA_API_NAMES


def obj(a,i): return a[OBJECT_ROWS[i-1][1]]

def field(ram,a,i):
    o,n,off,z = FIELD_ROWS[i]
    return scalar(ram,obj(a,o)+off,z) if z<=4 else part(ram,obj(a,o)+off,z)

def object_addresses(elf):
    a={}
    for i,name,n,align in OBJECT_ROWS:
        at=elf.symbol(name,n)
        need(at%align==0,'separate target object alignment: '+name)
        fixed={1:B.DOCUMENT,2:B.MEMORY,14:B.MAILBOX,15:B.WITNESS}
        need((at,n)==fixed[i] if i in fixed else inside(at,n,(elf.zero[0],)),
             'target object extent: '+name)
        if i in (6,8,16):need(at%16==0,'stationary DMA-facing CPU alignment')
        a[name]=at
    spans=sorted((a[name],a[name]+n) for i,name,n,align in OBJECT_ROWS)
    need(all(x[1]<=y[0] for x,y in zip(spans,spans[1:])),'distinct stationary objects')
    at=elf.symbol('_usbd_dev',68)
    need(at%4==0 and inside(at,68,(elf.zero[0],)),'private core68 within actual BSS')
    a['_usbd_dev']=at
    return a


def expected_bind_rows(a):
    status=lambda c:(*c,0,0,obj(a,8)+16,obj(a,8)+96)
    rows=[status(CONFIG_STATUS)]
    for scope,c,s,off,n,admitted in PACKETS:
        if scope==7:rows.append(status(RESET_STATUS_COOKIE))
        cpu=obj(a,2)+s*1024
        rows.append((*c,cpu,64,obj(a,6),cpu))
    return tuple(rows)


def expected_ranges(a):
    rows=[]
    for scope,ordinal,kind,dma,n,outcome in ALL_ROWS:
        if kind not in (4,5,6,7,8):continue
        c=PACKETS[scope-1][1];slot=PACKETS[scope-1][2];cpu=obj(a,2)+slot*1024
        span=0 if kind==8 else obj(a,6) if kind in (5,6) else cpu
        rows.append((ordinal,*c,span,cpu,64))
    return tuple(rows)


def device_image(scope):
    d=bytearray(144)
    for at in (0,32,48,128):d[at:at+16]=GUARD
    if scope:
        d[16:32]=be_words(completed_descriptor(scope));d[64:128]=payload_image(scope)
    return bytes(d)


def expected_witness(label,a):
    row=next(x for x in STOPS if x[0]==label)
    _,_,checks,io,ranges,binds=row
    scope,image,completed=PHASE_STORAGE[label]
    out=bytearray(9216)
    for at in (0,5776,8144,8704):out[at:at+16]=GUARD
    for at,records in ((16,ALL_ROWS[:io]),(5792,expected_ranges(a)[:ranges]),
                       (8160,expected_bind_rows(a)[:binds]),(8968,CHECK_ROWS[:checks])):
        data=be_words(v for record in records for v in record)
        out[at:at+len(data)]=data
    out[8720:8864]=device_image(image)
    if label in ('pre-close','pre-final-service','pre-finish','park'):
        out[8864:8928]=FINAL_PIXELS
        out[8928:8968]=be_words(v for record in FINAL_EVENTS for v in record)
    return bytes(out)


def expected_out_descriptor(label):
    scope,image,completed=PHASE_STORAGE[label]
    if not scope:return bytes(16)
    exposed=label in ('pre-reset-offer','pre-cancel-mark','pre-receive-owned',
                     'pre-stale-acquire','pre-stale-cancel','post-stale-pair','pre-close')
    if exposed:return be_words((0x08000000,0,RECEIVE_DMAS[PACKETS[scope-1][2]],0))
    return be_words(completed_descriptor(completed))


def live_value(ram,a,name):
    if name in LIVE:return field(ram,a,LIVE[name])
    if name in EXTRA_FIELDS:
        o,off,z=EXTRA_FIELDS[name];return scalar(ram,obj(a,o)+off,z)
    if name=='core_out1':return scalar(ram,a['_usbd_dev']+54,1)
    if name=='pixel_bytes':return scalar(ram,obj(a,14)+43*4)
    if name=='document_callbacks':return scalar(ram,obj(a,14)+47*4)
    if name=='original_buffer':return scalar(ram,obj(a,4)+80)
    if name=='requested':return scalar(ram,obj(a,4)+88,2)
    if name=='allocation':return scalar(ram,obj(a,7)+88)
    if name=='original':return actual_cookie(ram,obj(a,4)+100)
    raise ValueError('unmapped independent semantic field '+name)


def status_memory(label):
    b=bytearray(160)
    if label=='pre-initial-status' or label=='pre-reset-status':
        b[16:32]=be_words(EP0_PREPARED_WORDS)
    else:b[16:32]=be_words(EP0_COMPLETION_WORDS)
    return bytes(b)


def production_parts(ram,a,elf,allow_class=False):
    # Exclude only provider from generic BSS. Everything else, including private
    # TinyUSB globals and padding, remains part of the production comparison.
    start,n=elf.zero[0];p=obj(a,13)
    chunks=[(start,p-start),(p+224,start+n-p-224),B.MEMORY,elf.initialized_data]
    result=[]
    for at,z in chunks:
        if not z:continue
        data=bytearray(part(ram,at,z))
        if allow_class:
            c=obj(a,4)+348
            if at<=c and c+4<=at+z:data[c-at:c-at+4]=bytes(4)
        result.append((at,bytes(data)))
    return tuple(result)


def check_live(ram,a,label,elf):
    for name,want in PHASE_MAP[label].items():
        need(live_value(ram,a,name)==want,label+': original field '+name)
    context=RESTART_CONTEXT if label=='pre-restart' else OUTER_CONTEXT
    for name,want in context.items():need(live_value(ram,a,name)==want,label+': context '+name)
    need(part(ram,a['_usbd_dev']+52,16)==CORE_STATUS_BY_STOP[label],label+': actual core endpoint bytes')
    need(part(ram,obj(a,15),9216)==expected_witness(label,a),label+': complete independent witness bytes')
    scope,image,completed=PHASE_STORAGE[label]
    need(part(ram,obj(a,2),4096)==receive_memory(completed),label+': full receive prefixes and tails')
    need(part(ram,obj(a,6),16)==expected_out_descriptor(label),label+': actual production descriptor16')
    need(part(ram,obj(a,8),160)==status_memory(label),label+': stationary EP0 memory including untouched sink/staging')
    expected_setup=SETUP_CONFIGURATION if label=='pre-initial-status' else RESET_RECORD
    need(part(ram,obj(a,16),16)==expected_setup,label+': original SETUP CPU record')
    saved=bytes(20) if label in ('pre-initial-status','pre-reset-offer') else B.cookie_bytes(OLD_HELD)
    need(part(ram,obj(a,13)+204,20)==saved,label+': immutable original cancellation cookie and zero padding')
    if label!='pre-initial-status':
        need(part(ram,obj(a,2)+81936,32768)==PRODUCTION_OUTPUT,label+': retained/fresh original32FF output allocation')
    else:need(part(ram,obj(a,2)+81936,32768)==bytes(32768),'no decoded output at initial configuration')
    # The pristine old page becomes READY before reset; no consumer completes it.
    if label in ('pre-reset-offer','pre-cancel-mark','pre-receive-owned','pre-late-service',
                 'pre-receive-drained','pre-restart'):
        need(field(ram,a,23)==be_words((1,0,8,1))+bytes(48),label+': original READY ring slot is retained')
    if label in ('pre-close','pre-final-service','pre-finish','park'):
        need(field(ram,a,23)==be_words((0,0,8,1))+bytes(48),label+': fresh slot was actually completed')
    for name in ('program_failed','publish_failed','acquire_failed','payload_error','output_error'):
        need(live_value(ram,a,name)==0,label+': no hidden component error '+name)
    need(field(ram,a,72)==3 and field(ram,a,73)==3 and field(ram,a,74)==1,
         label+': unchanged actual endpoint programming binding')
    if scope and label not in ('pre-fresh-arm','pre-reuse-arm'):
        # Exact cookie and original pointer remain in the fixture ledger even
        # after live becomes0; component retirement may clear only its own copy.
        current=PACKETS[scope-1]
        need(actual_cookie(ram,obj(a,13)+32)==current[1] and
             scalar(ram,obj(a,13)+52)==obj(a,2)+current[2]*1024 and
             scalar(ram,obj(a,13)+56)==64,label+': original retained transport ledger')
    if label in ('pre-stale-acquire','pre-stale-cancel','post-stale-pair'):
        need(actual_cookie(ram,obj(a,4)+100)==REUSED_CURRENT and actual_cookie(ram,obj(a,5)+28)==REUSED_CURRENT,
             label+': current reused owner is distinct from saved old cookie')
        need(scalar(ram,obj(a,4)+120)==obj(a,2)+1024 and scalar(ram,obj(a,5)+20)==0x24682340,
             label+': exact physical CPU/DMA slot reuse')


def check_mailbox(ram,a,label,elf,initial):
    w=struct.unpack('>256I',part(ram,obj(a,14),1024))
    need(w[0]==0x48505552 and w[1]==2 and w[4:8]==(0,0,0,0),label+': actual success/error witness')
    need(w[8:14]==(elf.zero[0][1],114704,1024,9216,256,elf.initialized_data[1]),'whole actual initial scan extents')
    need(w[14]==B.fnv(part(initial,*elf.initialized_data)) and 0<w[15]<=256 and
         w[16:18]==(1,1),'one first-use initialization and bounded steps')
    need(all(w[i]==0 for i in (37,48,49,50,53,55)) and w[130:]==(0,)*126,
         label+': no cancellation settlement/failed callback/bounds/stall/reserved data')
    spec=next(x for x in STOPS if x[0]==label)
    need(w[38:41]==(spec[3],spec[4],spec[5]) and w[128]==spec[2],label+': append counts agree with raw rows')
    if label=='park':
        fixed={2:2,3:13,18:1,19:2,22:13,23:13,24:2,25:14,26:13,
          27:2,28:2,29:2,30:2,31:2,32:2,33:2,34:1,35:1,36:1,
          41:13,42:13,43:32,44:1,45:1,46:1,47:1,51:74,52:65,54:15,
          58:0,59:0,60:2,61:2,62:15,63:4,64:3,65:7,66:1,67:2,
          68:237,69:32,70:1,71:2,72:1,73:6,74:0,115:672,116:832,
          117:208,118:74,119:47,120:54,121:13,122:13,123:13,124:13,
          125:13,126:1,127:1,128:6,129:2}
        for i,v in fixed.items():need(w[i]==v,'final independently fixed mailbox word'+str(i))
        actual=(part(ram,obj(a,2),4096),part(ram,obj(a,2)+81936,32768),
                part(ram,obj(a,15)+8864,64),part(ram,obj(a,15)+16,5760),
                part(ram,obj(a,15)+5792,2340),part(ram,obj(a,15)+8160,540))
        need(w[75:81]==tuple(B.fnv(x) for x in actual),'final hashes agree with independently checked bytes')
        mapping=(1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,34,35,27,28,29,30,31,41,42,43,59)
        want=tuple(field(ram,a,i) for i in mapping)+(scalar(ram,a['_usbd_dev']+54,1)&1,
             field(ram,a,71),field(ram,a,75),field(ram,a,77),field(ram,a,76),field(ram,a,78))
        need(w[57]==0 and w[81:115]==want,'final secondary state matches actual production bytes')
    else:need(w[2]==1,'runtime still active before park')


def semantic_snapshots(rows,images,initial,supplied,cps,elf,a,qemu=False):
    need(images['initial']==initial,'exact painted/file-overlaid initial RAM')
    r0=B.registers(rows[0]['registers'],qemu)
    need({k:v for k,v in r0.items() if k!='logical_ar'}==supplied,'actual initial CPU readback')
    normalized=dict(ps=15,intenable=0,windowbase=0,windowstart=1,lbeg=0,lend=0,lcount=0)
    for item in rows[1:]:
        label=item['name'];r=B.registers(item['registers'],qemu)
        wanted=cps['park'] if label.startswith('park-step-') else cps[label]
        need(r['pc']==wanted and all(r[k]==v for k,v in normalized.items()),label+': normalized actual CPU')
        need(B.STACK[0]<=r['logical_ar'][1]<=sum(B.STACK),label+': owned SP')
        allowed=() if label=='after-normalization' else elf.mutable
        B.protected(initial,images[label],allowed)
        if label in ('after-normalization','pre-c'):
            need(r['logical_ar'][1]==sum(B.STACK),label+': exact established own stack')
            need(r['sar']==0,label+': startup clears SAR before ordinary C may use it')
        if label=='park' or label.startswith('park-step-'):
            need(r['logical_ar'][1]==sum(B.STACK),'normal original return restores owned stack top')
        if label=='after-normalization':need(images[label]==initial,'no RAM mutation in stack-free prefix')
        elif label=='pre-c':
            for at,n in elf.zero:need(part(images[label],at,n)==bytes(n),'actual full BSS zero before C')
            need(part(images[label],*B.STACK)==part(initial,*B.STACK),'startup leaves stack paint')
            need(part(images[label],*elf.initialized_data)==part(initial,*elf.initialized_data),'loaded generic data survives startup')
        elif not label.startswith('park-step-'):
            check_live(images[label],a,label,elf);check_mailbox(images[label],a,label,elf,initial)
    need(part(images['pre-restart'],*B.MEMORY)==part(images['pre-reset-status'],*B.MEMORY),
         'actual generation restart preserves entire114704 memory')
    ref=production_parts(images['pre-stale-acquire'],a,elf)
    for label in ('pre-stale-cancel','post-stale-pair'):
        need(production_parts(images[label],a,elf)==ref,'stale pair preserves all production/private RAM')
    for label in ('park-step-1','park-step-2'):
        if label in images:need(images[label]==images['park'],'actual native park RAM unchanged')


class ApiContract:
    """Semantic checks at actual instructions, independently of mailbox claims."""
    def __init__(self,a,elf):
        self.a=a;self.elf=elf;self.count=Counter();self.returned=Counter()
        self.pending={};self.history=[];self.successes=0;self.awaiting=0
        self.complete=[];self.release=[];self.feeds=[];self.waits=[];self.stales=[]
        self.last_check=None;self.provider_cancels=0;self.driver=[]
        self.services=[];self.pumps=[];self.acquire_indices=[]

    def entry(self,e,ram,index):
        a=self.a;name=e['name'];args=e['arguments'];c=self.count;ordinal=c[name]
        need(self.last_check is None or name=='hp1020_usb_runtime_ram_check',
             'refusal evidence is recorded before another selected production operation')
        d,ad,out,p,m=(obj(a,i) for i in (1,4,5,13,2))
        data={'event':e,'result':None,'preserve':False,'class_only':False}
        contexts={'hp1020_usb_document_init':d,'hp1020_usb_document_init_documents':d,
          'hp1020_tusb_adapter_init':ad,'hp1020_udc_setup_bus_reset':obj(a,9),
          'hp1020_udc_setup_offer':obj(a,9),'hp1020_udc_setup_dispatch':obj(a,9),
          'hp1020_udc_ep0_take_submission':obj(a,7),'hp1020_udc_ep0_observe':obj(a,7),
          'hp1020_tusb_adapter_pending_reset':ad,'hp1020_tusb_adapter_ack_reset':ad,
          'hp1020_tusb_adapter_finish_reset':ad,'hp1020_tusb_adapter_pump':ad,
          'hp1020_usb_document_restart':d,'hp1020_udc_publish_arm_out':obj(a,11),
          'hp1020_udc_acquire_packet':obj(a,12),'hp1020_udc_publish_service':obj(a,11),
          'hp1020_tusb_adapter_close_input':ad,'hp1020_tusb_adapter_finish':ad,
          'hp1020_udc_out_request_cancel':out,'hp1020_usb_receive_complete_data':d,
          'hp1020_usb_receive_release':d,'hp1020_image_output_feed':d+92,
          'hp1020_image_ring_accept':d+13284,'hp1020_image_ring_complete':d+13284}
        if name in contexts:need(args[0]==contexts[name],'actual original object argument: '+name)
        if name in ('hp1020_usb_document_init','hp1020_usb_document_init_documents'):
            need(args[1]==m and c['hp1020_udc_setup_bus_reset']==0,'first-use full original memory initialization')
        if name=='hp1020_udc_setup_bus_reset':
            need(args[1:3]==[1,0] and c['hp1020_tusb_adapter_init']==1,'original ingress1/full-speed reset')
        if name=='hp1020_udc_setup_offer':
            seq,record=((2,SETUP_CONFIGURATION),(3,RESET_RECORD))[ordinal] if ordinal<2 else (None,None)
            need(seq is not None and inside(args[1],32,(B.STACK,)) and
                 part(ram,args[1],28)==be_words((seq,0x79bdf130,0))+record,
                 'actual immutable SETUP observation and original shared ingress')
            if ordinal:need(self.successes==5 and scalar(ram,d+76)==5 and c['hp1020_udc_publish_arm_out']==6,
                            'reset offer follows exactly320 consumed bytes and held old sixth transfer')
            data['result']=0
        if name=='hp1020_udc_setup_dispatch':
            need(ordinal<2 and args[1]==ordinal+2 and args[2]&0xffffff==0x010101 and args[3]==1 and
                 c['hp1020_udc_setup_offer']==ordinal+1,'retained ingress and independent capture/stall facts')
            data['result']=0
        if name=='hp1020_udc_ep0_take_submission':
            cookie=(CONFIG_STATUS,RESET_STATUS_COOKIE)[ordinal] if ordinal<2 else None
            need(cookie is not None and args[1:5]==list(cookie[:4]) and args[5]>>24==0x80 and
                 actual_cookie(ram,ad+60)==cookie and scalar(ram,ad+80)==0 and scalar(ram,ad+88,2)==0,
                 'real NULL/zero EP0 status proposal with exact original cookie')
            need(scalar(ram,ad+354,1)==0 and scalar(ram,ad+355,1)==0 and scalar(ram,p+88)==0,
                 'status take occurs only after callbacks/API unwind')
            data['result']=0
        if name=='hp1020_udc_ep0_observe':
            cookie=(CONFIG_STATUS,RESET_STATUS_COOKIE)[ordinal] if ordinal<2 else None
            need(cookie is not None and inside(args[1],40,(B.STACK,)) and
                 actual_cookie(ram,args[1])==cookie and
                 part(ram,args[1]+20,20)==be_words((0x8800ffff,0,0xb68ace00,0,0)) and
                 args[2:4]==[0x01010101,0],
                 'original status observation, opaque descriptor count and separately supplied actual0')
            data['result']=0
        if name=='hp1020_tusb_adapter_ack_reset':
            schedule=((1,1,1,0),(1,1,2,0),(1,1,4,0),(2,2,1,1),
                      (2,2,1,1),(2,2,1,0),(2,2,2,0),(2,2,4,0))
            need(ordinal<len(schedule),'bounded genuine recovery promises')
            x,y,part_,result=schedule[ordinal]
            need(args[1:4]==[x,y,part_],'same original recovery ticket/part in actual call0 args')
            data['result']=result
            if result:
                data.update(preserve=True,class_only=True,check=ordinal-1)
                need(scalar(ram,ad+130,1)==(1 if ordinal==3 else 2),
                     'RECEIVE WAIT protects actual DCD then PENDING owner')
            if ordinal==5:need(len(self.driver)==6 and scalar(ram,ad+130,1)==0 and
                              scalar(ram,d+76)==5 and scalar(ram,d+80)==1,
                              'receive promise only after original late callback was drained/discarded')
        if name=='hp1020_tusb_adapter_finish_reset':
            schedule=((1,1,0),(2,2,1),(2,2,1),(2,2,0))
            need(ordinal<len(schedule),'bounded finish-reset calls')
            x,y,result=schedule[ordinal]
            need(args[1:3]==[x,y],'finish uses original reset ticket')
            data['result']=result
            if result:data.update(preserve=True,class_only=True,check=1 if ordinal==1 else 4)
            if ordinal==2:need(scalar(ram,obj(a,3)+51,1)==3,'missing transport permission remains missing')
        if name=='hp1020_usb_document_restart':
            need(ordinal<2 and scalar(ram,d+68)==ordinal+1 and scalar(ram,ad+354,1)==1,
                 'exact two production generation restarts inside original recovery')
            data['result']=0;data['memory_before']=part(ram,m,114704)
        if name=='hp1020_udc_publish_arm_out':
            need(ordinal<13 and not self.awaiting and self.successes==ordinal and
                 not c['hp1020_tusb_adapter_close_input'],'arm only after prior acquisition/drain, before sole close')
            scope,cookie,slot,off,n,admitted=PACKETS[ordinal]
            need(tuple(scalar(ram,d+x) for x in (68,72,76,80))==
                 (cookie[2],cookie[3]-1,cookie[3]-1,0) and
                 scalar(ram,ad+130,1)==0 and scalar(ram,out+58,1)==0,
                 'preflight before new reservation at correct original generation')
            data['result']=0
        if name=='hp1020_usb_runtime_ram_install_bulk':
            need(ordinal<13,'exact13 supplied source images')
            scope,cookie,slot,off,n,_=PACKETS[ordinal]
            need(args[:4]==list(cookie[:4]) and args[4]>>24==1 and args[5]==off and
                 scalar(ram,e['sp'])==n,'original by-value cookie/source offset/count at actual image install')
            need(actual_cookie(ram,out+28)==cookie and scalar(ram,out+58,1)==2,
                 'supplied image installed only for actual EXPOSED current owner')
            if scope==8:need(c['hp1020_usb_runtime_ram_check']==6,'reuse source remains untouched until both stale calls return')
            data['result']=1
        if name=='hp1020_udc_acquire_packet':
            stale=ordinal==7;scope=ordinal if ordinal>7 else ordinal+1
            cookie=OLD_HELD if stale else PACKETS[scope-1][1]
            need(ordinal<14 and args[1:5]==list(cookie[:4]) and args[5]>>24==1,
                 'exact original acquisition cookie, including old replay without relabeling')
            need(scalar(ram,e['sp'])==0 and part(ram,e['sp']+5,3)==b'\1\1\1',
                 'call0 stack endpoint fault0 and separate true capture facts')
            if stale:
                need(actual_cookie(ram,ad+100)==REUSED_CURRENT and actual_cookie(ram,out+28)==REUSED_CURRENT,
                     'stale metadata is tested only after genuine same-slot current reuse')
                data.update(result=2,preserve=True,check=5)
            else:
                scope,cookie,slot,off,n,_=PACKETS[scope-1]
                need(self.successes==scope-1 and not self.awaiting and c['hp1020_udc_publish_arm_out']==scope,
                     'one successful acquisition per original actual arm')
                need(actual_cookie(ram,ad+100)==cookie and scalar(ram,ad+130,1)==1 and
                     actual_cookie(ram,out+28)==cookie and scalar(ram,out+58,1)==2 and
                     scalar(ram,ad+120)==m+slot*1024 and scalar(ram,ad+128,2)==64,
                     'actual retained original DCD/EXPOSED owner')
                need(actual_cookie(ram,p+180)==cookie and scalar(ram,p+200)==slot and scalar(ram,p+113,1)==1,
                     'separate source image retains original identity')
                poisoned=bytearray(receive_memory(scope-1));poisoned[slot*1024:slot*1024+64]=cpu_poison(slot)[1]
                need(part(ram,m,4096)==bytes(poisoned) and part(ram,obj(a,6),16)==be_words(cpu_poison(slot)[0]) and
                     part(ram,obj(a,15)+8720,144)==device_image(scope),
                     'exact isolated CPU poison and separate immutable source before actual hooks')
                need(c['hp1020_tusb_adapter_close_input']==int(scope==13),'final successful ZLP is after sole close')
                data.update(result=0,scope=scope,core_before=part(ram,a['_usbd_dev']+52,16),
                            receive_before=part(ram,d,92),reset_before=part(ram,ad+316,44))
                self.acquire_indices.append(e['instruction'])
        if name=='hp1020_udc_out_request_cancel':
            need(ordinal<2 and args[1:5]==list(OLD_HELD[:4]) and args[5]>>24==1,
                 'actual cancellation request always uses saved original cookie')
            data['result']=0 if ordinal==0 else 2
            if ordinal==0:
                need(self.provider_cancels==1 and actual_cookie(ram,out+28)==OLD_HELD and
                     scalar(ram,ad+132,1)==1,'queued cancellation came from actual original owner callback')
            else:data.update(preserve=True,check=6)
        if name=='request_cancel' and e['target']==scalar(ram,ad+12):
            need(args[0]==p and args[1:5]==list(OLD_HELD[:4]) and args[5]>>24==1 and
                 actual_cookie(ram,ad+100)==OLD_HELD and scalar(ram,ad+130,1)==1,
                 'genuine ops.request_cancel callback with original DCD owner')
            self.provider_cancels+=1
        if name=='hp1020_udc_publish_service':
            self.services.append(e['instruction'])
            if self.awaiting:
                scope=self.awaiting;cookie=PACKETS[scope-1][1];n=PACKETS[scope-1][4]
                need(actual_cookie(ram,ad+100)==cookie and scalar(ram,ad+130,1)==2 and
                     scalar(ram,ad+124)==n and scalar(ram,out+58,1)==0 and
                     scalar(ram,a['_usbd_dev']+54,1)==5,
                     'actual original PENDING owner/core BUSY survives until real service')
                data['draining']=scope
        if name=='driver_xfer':
            scope=len(self.driver)+1;need(scope<=13,'exact actual bulk driver callbacks')
            _,cookie,slot,off,n,admitted=PACKETS[scope-1]
            need(args[:4]==[0,1,0,n] and scalar(ram,ad+366,1)==1 and
                 actual_cookie(ram,ad+180)==cookie and scalar(ram,ad+204)==n and
                 scalar(ram,ad+213,1)==0,'real SUCCESS delivery carries original cookie, never fake cancelled success')
            if scope==6:
                need(scalar(ram,ad+357,1)==1 and scalar(ram,d+88,1)==1,
                     'late old delivery is fenced before any receive admission')
                data['discard_before']=(part(ram,d,13496),part(ram,m,114704),len(self.complete),len(self.feeds))
            self.driver.append(scope);data['result']=1
        if name=='hp1020_usb_receive_complete_data':
            wanted=SUCCESSFUL_RECEIVE_COMPLETIONS[len(self.complete)] if len(self.complete)<12 else None
            need(wanted is not None and args[1:4]==list(wanted),'normalized completion excludes late old q6, preserves final ZLP')
            self.complete.append(wanted);data['result']=0
        if name=='hp1020_usb_receive_release':
            wanted=SUCCESSFUL_RECEIVE_COMPLETIONS[len(self.release)] if len(self.release)<12 else None
            need(wanted is not None and args[1:3]==list(wanted[:2]),'release only exact admitted original reservation')
            self.release.append(wanted);data['result']=0
        if name=='hp1020_image_output_feed':
            wanted=NONEMPTY_FEEDS[len(self.feeds)] if len(self.feeds)<11 else None
            need(wanted is not None,'no old late bytes/ZLP invent extra parser feed')
            gen,seq,value=wanted;slot=(seq-1)%4
            need(args[1:3]==[m+slot*1024,len(value)] and part(ram,args[1],len(value))==value and
                 scalar(ram,d+13484)==gen and scalar(ram,d+13494,1)==1,
                 'actual bounded original-generation byte feed')
            self.feeds.append((gen,seq));data['result']=0
        if name=='hp1020_tusb_adapter_pump':
            need(not self.awaiting,'pump cannot bypass an actual pending transport completion')
            self.pumps.append(e['instruction'])
        if name in ('hp1020_image_ring_accept','hp1020_image_ring_complete'):
            need(ordinal==0 and args[1]==0 and scalar(ram,d+68)==3 and
                 not c['hp1020_tusb_adapter_close_input'],'only fresh output slot accepted/completed before close')
            data['result']=0
        if name=='output':
            need(ordinal==0 and args[:3]==[d+13396,d+13284,p] and scalar(ram,d+68)==3 and
                 not c['hp1020_tusb_adapter_close_input'] and part(ram,m+81936,32)==PIXELS,
                 'one genuine fresh exact-pixel output callback before close')
            data['result']=0
        if name=='document_out':
            need(ordinal==0 and args[1]==d and part(ram,args[0],12)==be_words((1,0,1)) and
                 scalar(ram,d+13484)==3 and scalar(ram,d+13494,1)==1,
                 'one original parser document boundary within fresh feed')
            data['result']=0
        if name=='document_event':
            need(ordinal==0 and args[1]==p and part(ram,args[0],16)==be_words(DOCUMENT_EVENT) and
                 not c['hp1020_tusb_adapter_close_input'],'one fresh original generation/document/page callback before EOF')
            data['result']=0
        if name=='dcd_edpt0_status_complete':
            need(ordinal<2 and args[0]==0 and part(ram,args[1],8)==
                 (bytes.fromhex('0009000100000000') if ordinal==0 else RAW_SOFT_RESET),
                 'genuine standard/class status completion request identity')
        if name=='hp1020_usb_runtime_ram_check':
            need(ordinal<6 and self.last_check==ordinal+1 and
                 part(ram,args[0],36)==be_words(CHECK_ROWS[ordinal]),
                 'checked-return row follows exact real return and original identity')
            self.last_check=None;data['result']=1
        if name=='hp1020_tusb_adapter_close_input':
            need(ordinal==0 and self.successes==12 and c['hp1020_udc_publish_arm_out']==13 and
                 c['document_event']==1,'sole close follows fresh END_DOC with final original OUT held')
            data['result']=0
        if name=='hp1020_tusb_adapter_finish':
            need(ordinal==0 and self.successes==13 and not self.awaiting and
                 len(self.release)==12 and c['hp1020_tusb_adapter_close_input']==1,
                 'sole finish only after actual final callback plus empty reservation pump')
            data['result']=0
        if data['preserve']:
            data['before']=production_parts(ram,a,self.elf,data['class_only'])
            data['witness_before']=part(ram,obj(a,15),9216)
        self.pending[index]=data;self.history.append((e['instruction'],name,index));c[name]+=1

    def returned_event(self,e,ram):
        index=e['entry_event_index'];need(index in self.pending,'actual selected return has original selected entry')
        data=self.pending.pop(index);name=data['event']['name'];r=e['result'];a=self.a
        if data['result'] is not None:need(r==data['result'],'actual API return differs: '+name)
        if data['preserve']:
            need(production_parts(ram,a,self.elf,data['class_only'])==data['before'] and
                 part(ram,obj(a,15),9216)==data['witness_before'],
                 'WAIT/STALE returned without production/storage/diagnostic mutation: '+name)
            self.last_check=data['check']
            (self.waits if r==1 else self.stales).append(index)
        if 'memory_before' in data:
            need(part(ram,obj(a,2),114704)==data['memory_before'],'generation restart preserves all original memory')
        if 'scope' in data:
            scope=data['scope'];cookie=PACKETS[scope-1][1];n=PACKETS[scope-1][4];d=obj(a,1);ad=obj(a,4)
            need(actual_cookie(ram,ad+100)==cookie and scalar(ram,ad+130,1)==2 and scalar(ram,ad+124)==n and
                 scalar(ram,obj(a,5)+58,1)==0 and part(ram,d,92)==data['receive_before'] and
                 part(ram,ad+316,44)==data['reset_before'] and part(ram,a['_usbd_dev']+52,16)==data['core_before'],
                 'acquisition only queues exact original success; no callback/core/recovery retirement')
            need(part(ram,obj(a,2),4096)==receive_memory(scope) and
                 part(ram,obj(a,6),16)==be_words(completed_descriptor(scope)),
                 'actual visibility effects before original acquisition returns')
            self.successes+=1;self.awaiting=scope
        if 'draining' in data:
            need(len(self.driver)>=data['draining'],'service genuinely dispatched original callback before progress')
            need(scalar(ram,obj(a,4)+130,1)==0 and scalar(ram,a['_usbd_dev']+54,1)==0,
                 'service retires exact pending owner and core BUSY')
            self.awaiting=0
        if 'discard_before' in data:
            d,m,n,f=data['discard_before']
            need(part(ram,obj(a,1),13496)==d and part(ram,obj(a,2),114704)==m and
                 len(self.complete)==n and len(self.feeds)==f,
                 'late fenced SUCCESS callback discarded without receive admission/feed/output')
        self.returned[name]+=1

    def access(self,kind,address,size):
        for data in self.pending.values():
            if not data['preserve']:continue
            if inside(address,size,(B.STACK,)):continue
            if kind==2:
                allowed=((obj(self.a,4)+354,1),(obj(self.a,4)+348,4)) if data['class_only'] else ((obj(self.a,5)+57,1),)
                need(inside(address,size,allowed),
                     'WAIT/STALE performs no hidden write except admitted transient busy/class result')
            elif not data['class_only']:
                blocked=(B.MEMORY,(obj(self.a,6),16),(obj(self.a,8),160),
                         (obj(self.a,15),9216),(obj(self.a,16),16))
                need(not any(at<address+size and address<at+n for at,n in blocked),
                     'stale original metadata never reads reused DMA/payload/source-image storage')

    def finish(self,images):
        expected={'hp1020_usb_runtime_c':1,'hp1020_usb_document_init_documents':1,
          'hp1020_tusb_adapter_init':1,'hp1020_udc_setup_bus_reset':1,
          'hp1020_udc_setup_offer':2,'hp1020_udc_setup_dispatch':2,
          'hp1020_udc_ep0_take_submission':2,'hp1020_udc_ep0_observe':2,
          'hp1020_tusb_adapter_ack_reset':8,'hp1020_tusb_adapter_finish_reset':4,
          'hp1020_usb_document_restart':2,'tusb_rhport_init':1,
          'hp1020_udc_publish_arm_out':13,'hp1020_udc_acquire_packet':14,
          'hp1020_udc_out_request_cancel':2,'hp1020_usb_runtime_ram_install_bulk':13,
          'hp1020_usb_runtime_ram_reset_observation':1,'hp1020_usb_runtime_ram_check':6,
          'hp1020_usb_receive_complete_data':12,'hp1020_usb_receive_release':12,
          'hp1020_image_output_feed':11,'hp1020_image_ring_accept':1,'hp1020_image_ring_complete':1,
          'driver_xfer':13,'document_out':1,'document_event':1,'output':1,
          'dcd_edpt0_status_complete':2,'hp1020_tusb_adapter_close_input':1,'hp1020_tusb_adapter_finish':1}
        for name,n in expected.items():need(self.count[name]==n and self.returned[name]==n,'actual entry/return count: '+name)
        need(not self.pending and self.successes==13 and not self.awaiting and
             len(self.waits)==4 and len(self.stales)==2 and self.last_check is None and
             self.provider_cancels==1,'complete reset/old-owner/stale sequence with no fabricated settlement')
        need(self.count['hp1020_usb_document_init']<=1 and
             1<=self.count['hp1020_tusb_adapter_pending_reset']<=256 and
             18<=self.count['hp1020_udc_publish_service']<=256 and
             12<=self.count['hp1020_tusb_adapter_pump']<=256,'bounded ordinary service/query/pump work')
        w=struct.unpack('>256I',part(images['park'],*B.MAILBOX))
        need(w[20]==self.returned['hp1020_udc_publish_service'] and w[21]==self.returned['hp1020_tusb_adapter_pump'],
             'final mailbox counts genuine returned service/pump calls')


def selected_api_entries(elf):
    selected={};found=set()
    for name in API_NAMES:
        for address,size,info,index in elf.symbols.get(name,[]):
            if info&15==2 and size and index:
                need(address in elf.instructions,'selected actual function starts at instruction: '+name)
                selected.setdefault(address,set()).add(name);found.add(name)
    need(found==set(API_NAMES),'every required natural API has a real linked definition')
    return {at:sorted(names) for at,names in selected.items()}


def model_trace(folder,model,images,elf,cps,a,forbidden):
    """Independent RAM/access/call-boundary replay, not a second CPU engine."""
    steps=B.gunzip(folder,'traces/steps.bin.gz',40_000_000)
    access=B.gunzip(folder,'traces/accesses.bin.gz',200_000_000)
    need(steps and len(steps)%4==0 and len(access)%20==0,'bounded complete raw trace records')
    need(sha(steps)==model['step_sha256'] and sha(access)==model['access_sha256'],'uncompressed exact trace seals')
    pcs=[x[0] for x in struct.iter_unpack('>I',steps)]
    need(len(pcs)==model['instructions']<=10_000_000 and len(set(pcs))==model['visited_instructions'],
         'actual instruction counters and unchanged instruction budget')
    need(pcs[0]==ENTRY and pcs.count(ENTRY)==1 and pcs[-2:]==[cps['park']]*2,
         'one original entry and two terminal actual park steps')
    need(B.jump_target(ENTRY,elf.instructions[ENTRY])==pcs[1]==elf.symbol('hp1020_entry_normalize'),
         'initial entry jump reaches own normalizer')
    need(B.jump_target(cps['park'],elf.instructions[cps['park']])==cps['park'],'actual terminal self jump')
    B.check_forbidden_entries(set(pcs),forbidden)
    ram={at:bytearray(b) for at,b in images['initial'].items()}
    selected=selected_api_entries(elf);api=ApiContract(a,elf)
    rows=model['reset_api_events'];erow=0;ci=0;frames=[];pending_returns=[]
    cursor=0;counts=Counter();widths=Counter();seen=[];minimum=None
    checkpoints_index={};counts_at={};old_entries=[];scanned=set();global_write=False
    pre_c_index=pcs.index(cps['pre-c']);observations=model['reset_observations']
    need(model['reset_observation_schema']=='hp1020-entry-usb-reset-observation-v1' and
         model['reset_cursor_convention']=='completed instructions/accesses before target; causing PC at instruction-1' and
         model['reset_host_target_calls']==model['reset_host_target_mutations']==0,
         'closed observational schema and declared no host call/mutation')
    for i,pc in enumerate(pcs):
        need(pc in elf.instructions,'actual executed instruction boundary')
        code=elf.instructions[pc]
        need(code not in (b'\0\0\0',bytes.fromhex('d60f')),'excluded instruction never executed')
        # Returns and then possible tail/call entries share the exact completed
        # instruction/access cursor. Their physical frame is reconstructed here.
        for entry_index,frame in pending_returns:
            need(erow<len(rows),'missing actual return event')
            e=rows[erow];erow+=1;original=rows[entry_index]
            want=dict(kind='return',entry_event_index=entry_index,name=original['name'],
                pc=pcs[i-1],target=pc,instruction=i,access_index=cursor//20,
                sp=frame['sp'],call_ledger_index=frame['ledger'],depth=frame['depth'])
            need(all(e.get(k)==v for k,v in want.items()) and set(e)==set(want)|{'result'} and
                 type(e['result'])is int and 0<=e['result']<=0xffffffff,
                 'return record tied to original physical CALL/RET frame')
            api.returned_event(e,ram)
        pending_returns=[]
        if i and pc in selected:
            need(frames,'natural selected entry must retain an actual original caller')
            f=frames[-1];previous=elf.instructions[pcs[i-1]];w=int.from_bytes(previous,'big')
            transfer=('call0' if len(previous)==3 and w&0xfc0000==0x500000 else
                      'callx0' if len(previous)==3 and w&0xff0fff==0x030000 else
                      'j' if len(previous)==3 and w&0xfc0000==0x600000 else
                      'jx' if len(previous)==3 and w&0xff0fff==0x0a0000 else None)
            need(transfer is not None,'selected function requires actual call or admitted tail jump')
            transfer_reg=previous[1]>>4 if transfer in ('callx0','jx') else None
            for name in selected[pc]:
                need(erow<len(rows),'missing actual selected entry')
                e=rows[erow];idx=erow;erow+=1
                want=dict(kind='entry',name=name,pc=pcs[i-1],target=pc,instruction=i,
                    access_index=cursor//20,return_pc=f['return_pc'],call_pc=f['pc'],
                    call_ledger_index=f['ledger'],depth=f['depth'],transfer=transfer,
                    transfer_register=transfer_reg,transfer_value=pc if transfer_reg is not None else None)
                need(all(e.get(k)==v for k,v in want.items()) and set(e)==set(want)|{'arguments','sp'} and
                     B.STACK[0]<=e['sp']<=sum(B.STACK) and e['sp']%16==0 and
                     len(e['arguments'])==6 and all(type(x)is int and 0<=x<=0xffffffff for x in e['arguments']),
                     'entry record tied to actual code/caller/stack/cursor')
                if transfer_reg==1:need(e['sp']==pc,'indirect a1 operand agrees with original SP')
                if transfer_reg is not None and 2<=transfer_reg<=7:
                    need(e['arguments'][transfer_reg-2]==pc,'indirect operand agrees with unchanged actual argument register')
                f['entries'].append(idx);api.entry(e,ram,idx)
                if name in B.ENTRY_NAMES:
                    old_entries.append({k:e[k] for k in ('name','pc','target','instruction','arguments','sp')})
        # Observe first occurrence of ONLY the next selected natural address.
        # Earlier legitimate same-address calls remain fully replayed; no hit of
        # a currently armed role is skipped by counters or expected state.
        if len(seen)<20:
            label=list(cps)[len(seen)]
            if pc==cps[label]:
                need(observations[len(seen)]==dict(label=label,address=pc,instruction=i,access_index=cursor//20),
                     'actual ordered stop cursor bound to raw trace')
                need({at:bytes(v) for at,v in ram.items()}==images[label],'complete replayed RAM at '+label)
                regs=next(r['registers'] for r in model['snapshots'] if r['name']==label)
                for e in rows[:erow][::-1]:
                    if e['instruction']!=i:break
                    if e['kind']=='entry':need(e['sp']==B.registers(regs)['logical_ar'][1] and
                        e['arguments']==B.registers(regs)['logical_ar'][2:8],
                        'paired actual CPU snapshot binds natural argument registers')
                seen.append(label);checkpoints_index[label]=i;counts_at[label]=api.returned.copy()
        kind=B.memory_instruction(code)
        if kind:
            need(cursor+20<=len(access),'missing actual memory instruction effect')
            chunk=access[cursor:cursor+20];need(chunk[1:4]==bytes(3),'raw access padding')
            k,at,address,size,value=struct.unpack('>B3xIIII',chunk)
            need(at==pc and (k,size)==kind and address%size==0 and inside(address,size,elf.read_spans),
                 'instruction-width/alignment and exact RAM admission')
            api.access(k,address,size)
            started='pre-c' in seen and i>pre_c_index
            if inside(address,size,(B.STACK,)):
                need(started,'no inherited-stack access before own C call')
                minimum=address if minimum is None else min(minimum,address)
            if started and not global_write:
                if k==1:
                    scanned.update(x for x in range(address,address+size)
                        if inside(x,1,elf.zero+(B.DATA_SENTINEL,elf.initialized_data)))
                elif not inside(address,size,(B.STACK,)):
                    need(all(x in scanned for start,n in elf.zero+(B.DATA_SENTINEL,elf.initialized_data)
                         for x in range(start,start+n)),'all initial BSS/data/sentinel bytes scanned before first global C mutation')
                    global_write=True
            if k==1:
                need(int.from_bytes(part(ram,address,size),'big')==value,'actual read sees preceding replayed bytes')
                if code[0]>>4==1:
                    immediate=int.from_bytes(code[1:],'big')-0x10000
                    need(address==(((pc+3)&~3)+immediate*4)&0xffffffff,'actual PC-relative literal read')
            else:
                allowed=elf.mutable if started else elf.zero if 'after-normalization' in seen else ()
                need(inside(address,size,allowed),'phase-specific memory write before effect')
                put(ram,address,(value&((1<<(8*size))-1)).to_bytes(size,'big'))
            counts['read' if k==1 else 'write']+=1;widths[('read' if k==1 else 'write')+'/'+str(size)]+=1
            cursor+=20
        word=int.from_bytes(code,'big')
        if len(code)==3 and word&0xfc0000==0x600000:
            need(B.jump_target(pc,code)==(pcs[i+1] if i+1<len(pcs) else cps['park']),'direct J has literal actual target')
        direct=len(code)==3 and word&0xfc0000==0x500000
        indirect=len(code)==3 and word&0xff0fff==0x030000
        ret=code in (bytes.fromhex('020000'),bytes.fromhex('d00f'))
        if direct or indirect or ret:
            need(i+1<len(pcs) and ci<len(model['calls']),'complete actual call/return ledger')
            e=model['calls'][ci];ledger=ci;ci+=1
            need(e['pc']==pc and e['target']==pcs[i+1] and B.STACK[0]<=e['sp']<=sum(B.STACK) and e['sp']%16==0,
                 'actual call/return instruction target and own stack')
            if ret:
                need(frames and e['kind']=='return' and e['depth']==len(frames),'return retains original caller')
                f=frames.pop();need(e['target']==f['return_pc'] and e['sp']==f['sp'],'actual original return PC/SP')
                pending_returns=[(idx,f) for idx in reversed(f['entries'])]
            else:
                need('pre-c' in seen and e['kind']=='call' and e['return_pc']==pc+len(code) and
                     e['depth']==len(frames)+1,'admitted actual call0 frame')
                if ledger==0:need(pc==cps['pre-c'] and e['target']==elf.symbol('hp1020_usb_runtime_c'),'sole real startup CALL0 into C')
                if direct:need(e['target']==((pc&~3)+4+B.signed18(word&0x3ffff)*4)&0xffffffff,'exact encoded CALL0 target')
                frames.append(dict(e,ledger=ledger,entries=[]))
    need(cursor==len(access) and ci==len(model['calls']) and erow==len(rows) and
         not frames and not pending_returns,'no missing/extra access/call/selected-return evidence')
    need(seen==list(CHECKPOINTS)==model['reset_checkpoints'] and len(observations)==20 and
         model['checkpoints']==list(B.PHASES[1:]),'complete20 ordered reset and six unchanged guard checkpoints')
    need(old_entries==model['actual_entry_events'],'old selected API ledger remains an exact subset')
    need({at:bytes(v) for at,v in ram.items()}==images['park'],'complete final replay equals actual capture')
    need(dict(counts)==model['access_count'] and dict(widths)==model['access_widths'] and
         minimum==model['minimum_stack_access'] and minimum is not None and
         B.STACK[0]<=model['minimum_sp']<=minimum and model['owned_stack_bytes']==8192,
         'independent actual access counts/widths/own-stack high water')
    need(global_write and model['terminal_self_branch_executions']==2 and
         model['terminal_self_branch_statically_checked'] is True and model['no_external_stack'] is True and
         model['host_runtime_mutations']==0 and model['actual_close_entries']==model['actual_finish_entries']==1,
         'actual startup/park/single-lifecycle scope')
    need(model['zero_spans']==[list(x) for x in elf.zero] and model['owned_stack']==list(B.STACK) and
         model['initialized_data_span']==list(elf.initialized_data),'exact interpreter memory policy')
    close,service,finish=(checkpoints_index[x] for x in ('pre-close','pre-final-service','pre-finish'))
    need(api.acquire_indices[-2]<close<api.acquire_indices[-1]<service<finish and
         not any(close<x<service for x in api.services) and any(service<x<finish for x in api.pumps),
         'healthy final original ZLP acquisition then NEXT service then empty pump and sole finish')
    for label in CHECKPOINTS[2:]:
        w=struct.unpack('>256I',part(images[label],*B.MAILBOX));actual=counts_at[label]
        need(w[20]==actual['hp1020_udc_publish_service'] and w[21]==actual['hp1020_tusb_adapter_pump'],
             label+': actual returned service/pump counters')
    api.finish(images)
    special=(('intenable',0xe4,0),('lcount',2,0),('lbeg',0,0),('lend',1,0),
             ('ps',0xe6,15),('windowbase',0x48,0),('windowstart',0x49,1))
    need(len(model['special_writes'])==7,'seven admitted original startup special writes')
    for e,(name,num,value) in zip(model['special_writes'],special):
        at=e['pc'];need(e==dict(pc=at,name=name,value=value) and elf.instructions.get(at)==bytes((2,num,0x31)) and
            pcs.count(at)==1 and elf.symbol('hp1020_entry_normalize')<=at<cps['after-normalization'],
            'exact one-shot CPU normalization encoding and value')
    return dict(api_entries=dict(api.count),api_returns=dict(api.returned),
                wait_returns=4,stale_returns=2,provider_cancel_callbacks=1)


# Immutable aliases of neutral reader constants; the imported module is never
# modified and none of its healthy semantic/schedule functions is called.
REGIONS,GDB,PRIMARY,BACKEND_HASH=B.REGIONS,B.GDB,B.PRIMARY,B.BACKEND_HASH
digest_shape,jump_target=B.digest_shape,B.jump_target
Ledger=B.Ledger
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
                        'hp1020_entry_usb_reset_qemu.py': source_map['scripts/hp1020_entry_usb_reset_qemu.py'],
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
    for item, (label, address) in zip(q['snapshots'][1:21], checkpoints.items()):
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
    for item in q['snapshots'][21:]:
        need(ledger.command('s', 'observe', 'single-step-park').startswith('T05'), 'actual park step stop')
        ledger.snapshot(item, images)
    cleanup = ledger.take('process-cleanup')
    need({k: v for k, v in cleanup.items() if k not in ('kind', 'ledger_index')} == q['cleanup'], 'actual cleanup ledger')
    need(not q['cleanup']['errors'] and q['cleanup']['still_running'] is False and q['cleanup']['returncode'] is not None, 'child stopped and reaped')
    end = ledger.take('adapter-finished')
    need(end['status'] == 'pass' and end.get('error') is None and ledger.index == len(ledger.rows) and ledger.commands == q['gdb_commands'] <= 4096, 'complete ledger without hidden traffic')
    need(q['reset_calls'] == q['call_helpers'] == q['memory_or_register_writes_after_lock'] == 0 and q['resume_attempted'] is True and q['checkpoint_stop_observed'] is True, 'declared counters agree with independently reconstructed ledger')




UNITS,LIBGCC_MEMBERS=B.UNITS,B.LIBGCC_MEMBERS
seal_tree=B.seal_tree
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
            target_matches=[p for p in report['target_sha256'] if dependency.endswith('/analysis/boot-handoff/entry-usb-reset/target/'+p)]
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


def check_sources(root,report,source_root):
    sources=js(root,'source-sha256.json')
    need(sources==report['source_sha256'],'original report/source manifest binding')
    seal_tree(root,'source',sources);seal_tree(root,'target',report['target_sha256'])
    fixed={PREFIX+'independent-literals.py':'aab93eba1de9c9123e9344d8bb5fc642b690e7ac4b02c2fc3fd5efa4d501b333',
      PREFIX+'literal-addendum.py':'277d718f1ce3dab15ae0aeab1fb29cf1033d0f6151389b0333ae2fc242735682',
      PREFIX+'hp1020_usb_runtime_contract.h':'a73a3904b094126e811f6d26249ab93d3d71cae7f5e0c00cedd10e77addc4679',
      PREFIX+'CONTRACT.md':'18864eee6bb95581e99429da8d2fac039e635ef365ce02f91a8d1d122c17a123',
      PREFIX+'AMENDMENT.md':'500b2e451e8eba1641fc0a1389bd1d44c9c3825de0a4ee61403ce794cec89c35',
      PREFIX+'ACCEPTANCE.md':'26c0fc71d2bfbf027f2298288970a86fb77676c925bc1e51ea76f9a0d2dd96e2',
      PREFIX+'ADDENDUM.md':'7f317b61e98080b4a42a3f2295367b7d1262d90a39412d2f9fca935a7f5a8439',
      PREFIX+'layout-objects.tsv':'eab95464e854493bade7fce68dbe645c4e6f9c4a899ac0a6b0a043118519d154',
      PREFIX+'layout-fields.tsv':'c9b745359ce934e3b2b992f3bb5a0323e17d69a22eba30acf7586ecc8c384201',
      PREFIX+'startup.S':'c8271bbea0fdc7ed4ffb4c18469a15d91170d26c948d41e3706e8ed95922bad6',
      PREFIX+'runtime.ld':'235934f043f7b18741a1db960fd8a129d64e5075dad55b8aca87c2988348d74d',
      PREFIX+'LIBRARY_SELECTION.md':'e5d344e4afe2817186960ef3108a7f82baf0089f2e333e012f950994b7be7fdd',
      'scripts/check-hp1020-entry-usb.py':BASE_SHA256,
      'scripts/check-hp1020-entry-usb-reset.py':sha(Path(__file__).read_bytes()),
      'scripts/hp1020_qemu_ram.py':BACKEND_HASH,
      'scripts/hp1020_entry_qemu.py':'4ef9ffcfac58a326b68df526c8ddec93868cf18cf85eae76682a30ab9cf9d080',
      'scripts/hp1020_entry_machine.py':'46cc66fc2ac1c22201ef6a33ee13eba4a54087bb416ccc1b8726aae2d2c98b07',
      'scripts/hp1020_entry_usb_machine.py':'377cdd771447a4d69040a5624ef1fafc7593fea50fc471ccd7f8a0ff1077466a',
      'scripts/hp1020_entry_usb_qemu.py':'c92b92947955f1ba68ac20a941689af6421c50d389d7e3c02a40ff0642ff9a8c',
      'scripts/hp1020_entry_usb_reset_machine.py':'416da967974ac555b6365f3ba52e46bdac32650426fb06856ba8ff0f9a20c083',
      'scripts/hp1020_entry_usb_reset_qemu.py':'10784d56e54277919b788f83ef6195628b77667e804b869ac9bf69d99ec7a862',
      'scripts/hp1020_xtensa_call0.py':'ed2924d8e46c0e553fe079a5ecdfff77dc40f1aa228588d9a86c39ce98769480',
      'scripts/hp1020_xtensa_properties.py':'8a98e5ba3ead469cd431a06260e78c836993348d878ae96595d0b622538d0280',
      'open-firmware/tinyusb-device/tusb_config.h':'895c6599700b09f84be46ce74ac75f3974ce3b277d98f233134a54aea637616a'}
    fixed.update({
      'open-firmware/udc-out/hp1020_udc_out.c':'63361d26de832654eeb75f3a87248d1badb08d074419ff870880127e6d7ba91c',
      'open-firmware/udc-publish/hp1020_udc_publish.c':'d3cfe2bc668f6028990872bbfd6ad87065d0f989d433962025ba7bdb3456fc25',
      'open-firmware/udc-program/hp1020_udc_program.c':'24d0cd6abef20a9962a293ff308605f972585ab760a5ed8762663d474f4c735c',
      'open-firmware/udc-ep0/hp1020_udc_ep0.c':'397c99e7b25239ae4dfb59179ea401f1e9e7d5befeb92aed853681ab90bcf140',
      'open-firmware/udc-setup/hp1020_udc_setup.c':'f70322d734a8a2d26ed31befb275f61c5256e807389ca399a70707ce089508f3',
      'open-firmware/tinyusb-printer-adapter/hp1020_tusb_adapter.c':'472cab2bdf7c64e3394e8a05c4b598020efa54db2d1a7347b58498f122062ba2',
      'open-firmware/usb-printer-class/hp1020_usb_printer.c':'c9daf663ae7eea5b9df6a6a68fffd86ec0d6c4b860ce17559250e65cf02361b9',
      'open-firmware/usb-receive-core/hp1020_usb_receive.c':'352413d1c3d5cd8dbe1aa1788ab27383d1c45bfc344842d3b9b08c7e64827a8e',
      'open-firmware/usb-receive-core/hp1020_usb_document.c':'6df4c51a364b78a1d8e3bc9c81ce41f4daacddf383d13238e5f5407616575885',
      'open-firmware/image-core/hp1020_image_output.c':'ed469978829f1cc35b10062912db2fd88d030fb112b9ca35596bf115211c9728',
      'open-firmware/image-core/hp1020_image_ring.c':'9ee8f5955e8d6f30a3b12778553477835dc245eb3d928f6e81b467f8562d4e2b'})
    fixed.update({'open-firmware/entry-ram-test/references/qemu-primary/'+n:h for n,h in PRIMARY.items()})
    for name,digest in fixed.items():need(sources.get(name)==digest,'frozen source contract/helper: '+name)
    required=('scripts/validate-hp1020-entry-usb-reset.py','scripts/build-hp1020-entry-usb-reset-target.sh',
      'scripts/hp1020_entry_usb_reset_machine.py','scripts/hp1020_entry_usb_reset_qemu.py',
      'scripts/hp1020_entry_usb_reset_audit.py',PREFIX+'hp1020_usb_runtime.c',
      PREFIX+'hp1020_usb_runtime_ram.c',PREFIX+'hp1020_usb_runtime_layout.c',
      'open-firmware/udc-out/hp1020_udc_acquire.h',
      'open-firmware/tinyusb-device/patches/protocol-compatibility.patch')
    need(set(required)<=set(sources),'complete new runtime/audit/observer and production source closure')
    for unit in UNITS:need(any(n.endswith('/'+unit+'.c') for n in sources),'actual compiled C source: '+unit)
    if source_root is not None:
        for name,digest in sources.items():need(sha(raw(Path(source_root).resolve(),name))==digest,'live source changed: '+name)
    return sources


def cpu_initial():
    values={k:v for k,v in CPU.items() if k!='name'}
    values.update(physical_ar=list(PHYSICAL_AR32),pc=ENTRY)
    return values


def checkpoint_addresses(elf):
    aliases={'after-normalization':'hp1020_entry_after_normalization',
             'pre-c':'hp1020_entry_before_c','park':'hp1020_entry_park'}
    cps={label:elf.symbol(aliases.get(label,role)) for label,role,*rest in STOPS}
    seen={}
    for label,role,*rest in STOPS:
        at=cps[label];key=aliases.get(label,role)
        need(at in elf.instructions,'actual natural checkpoint instruction')
        if at in seen:need(seen[at]==key,'distinct checkpoint roles alias unexpectedly')
        seen[at]=key
    need(all(x!=y for x,y in zip(cps.values(),list(cps.values())[1:])),
         'no adjacent repeated breakpoint requiring hidden instruction skip')
    return cps


def check_capture(capture_root,source_root=None):
    """Read saved sources/ELF/traces only; never import a producer or run target."""
    try:
        root=Path(capture_root).resolve();report=js(root,'validation.json')
        need(report['status']=='pass' and report['candidate_execution'] is True and
             report['independent_capture_gate_present'] is True and not any(k in report for k in
             ('error','source_seal_error','publication_error')),'complete successful unchanged-source execution')
        sources=check_sources(root,report,source_root);check_tools(root,report,sources)
        need(len(STREAM)==352 and sha(STREAM)==STREAM_SHA256 and raw(root,'input/small-black.zjs')==STREAM,
             'exact frozen host stream352')
        provenance=js(root,'input/provenance.json')
        need(provenance==report['input'] and provenance==dict(source='analysis/boot-handoff/entry-ram/fixtures/small-black.zjs',
             input_sha256=STREAM_SHA256,bytes=352,independent_literal_match=True),'original host fixture provenance')
        elf_data=raw(root,'target/entry-usb.elf');elf=B.Elf(elf_data)
        helper=elf.symbol('__udivsi3',76);helper_bytes=elf.file(helper,76)
        need(sha(helper_bytes)=='97c0f245a842a23b8ca0ad47d15b781a0dc0537c7aa2dc7251efa494e734e3f9' and
             helper_bytes[65:68]==bytes(3) and helper_bytes[68:72]==b'DIV0' and
             '__umodsi3' not in elf.symbols,'exact reset-selected udiv helper and excluded trap/marker')
        a=object_addresses(elf);B.private_getter(elf)
        forbidden=B.forbidden_shortcut_policy(root,elf)
        need(js(root,'elf-loads.json')==elf.loads,'file-only actual ELF load metadata')
        need(elf.file(elf.symbol('hp1020_usb_runtime_input',352),352)==STREAM,'actual linked input bytes')
        need(elf.file(elf.symbol('hp1020_usb_runtime_setup_record',16),16)==SETUP_CONFIGURATION and
             elf.file(elf.symbol('hp1020_usb_runtime_reset_record',16),16)==RESET_RECORD,
             'two separate immutable original raw-wire SETUP records')
        need(elf.file(elf.symbol('hp1020_usb_runtime_supplied',40),40)==FACTS,
             'separate supplied controller/cache/mapping/settlement/actual-length facts')
        need(elf.symbol('hp1020_usb_runtime_sentinel',256)==B.DATA_SENTINEL[0],'fixed loaded sentinel')
        table=elf.symbol('hp1020_usb_runtime_layout',2100);table_bytes=elf.file(table,2100)
        need(tuple(struct.unpack('>525I',table_bytes))==TABLE_WORDS and
             inside(table,2100,((elf.alloc['.rodata'][3],elf.alloc['.rodata'][5]),)),
             'all525 compiler-layout constants match independent manual table')
        layout_hashes={n:sources[PREFIX+n] for n in ('layout-objects.tsv','layout-fields.tsv')}
        need(js(root,'layout-witness.json')==dict(status='pass',address=table,words=list(TABLE_WORDS),
             sha256=sha(table_bytes),expected_sha256=layout_hashes),'actual source-bound layout witness')
        cps=checkpoint_addresses(elf)
        need(js(root,'checkpoints.json')==[[n,at] for n,at in cps.items()],'exact20 natural checkpoint addresses')
        audit=js(root,'linked-audit.json')
        need(audit==report['linked_audit'] and audit['target_sha256']==sha(elf_data) and
             audit['target_bytes']==len(elf_data) and audit['entry']==ENTRY and
             audit['audit_source_sha256']==sources['scripts/hp1020_entry_usb_reset_audit.py'],
             'exact ELF/source-bound pre-execution admission audit')
        need(sha(raw(root,'annotated-disassembly.txt'))==audit['disassembly_sha256'],'preserved actual annotated-disassembly bytes')
        need(audit['zero_spans']==[list(x) for x in elf.zero] and audit['owned_stack']==list(B.STACK) and
             audit['initialized_data_span']==list(elf.initialized_data),'actual admitted split memory policy')
        need(len(report['cases'])==2,'two fixed ordinary incoming CPU/paint reset cases')
        dirs=set();total=0;details=[]
        for index,case in enumerate(report['cases']):
            fills=PAINTS[index];name=f'{index:02d}-{CPU["name"]}-{fills[0]:02x}';dirs.add(name)
            folder=root/'cases'/name
            need(case==js(folder,'case.json') and case['case']==name and case['status']=='pass' and
                 case['cpu_profile']==CPU and case['paints']==list(fills) and case['paired_checkpoints']==21,
                 'literal independent reset CPU/paint matrix')
            supplied=cpu_initial();need(js(folder,'initial-registers.json')==supplied,'initial32 distinct original physical AR values')
            initial=B.make_initial(elf,fills);model=case['model'];q=case['qemu']
            need(model==js(folder/'model','result.json') and model['status']=='pass' and
                 model['snapshots']==js(folder/'model','snapshots.json'),'actual complete model records')
            mi=B.snapshots(folder/'model',model['snapshots'],MODEL_PHASES)
            qi=B.snapshots(folder/'qemu',q['snapshots'],QEMU_PHASES,True)
            semantic_snapshots(model['snapshots'],mi,initial,supplied,cps,elf,a)
            semantic_snapshots(q['snapshots'],qi,initial,supplied,cps,elf,a,True)
            for m,n in zip(model['snapshots'],q['snapshots'][:21]):
                need(B.registers(m['registers'])==B.registers(n['registers'],True) and mi[m['name']]==qi[n['name']],
                     'all21 paired complete CPU and RAM snapshots')
            for n in q['snapshots'][21:]:
                need(n['registers']==q['snapshots'][20]['registers'] and qi[n['name']]==qi['park'],
                     'two real native self-jump steps preserve all CPU/RAM')
            stack=part(mi['park'],*B.STACK);changed=[i for i,v in enumerate(stack) if v!=fills[1]]
            wanted=dict(initial_byte=fills[1],changed_bytes=len(changed),
                lowest_changed_address=B.STACK[0]+min(changed) if changed else None)
            need(changed and {k:case['stack_paint'][k] for k in wanted}==wanted and
                 isinstance(case['stack_paint'].get('limitation'),str),'actual complete stack-paint witness')
            details.append(model_trace(folder/'model',model,mi,elf,cps,a,forbidden))
            qemu_ledger(folder/'qemu',q,qi,supplied,cps,sources,elf);total+=model['instructions']
        need({p.name for p in (root/'cases').iterdir() if p.is_dir()}==dirs,'exact saved case directory set')
        return True,dict(cases=2,paired_checkpoints=42,qemu_park_steps=4,model_instructions=total,
            target_sha256=sha(elf_data),forbidden_shortcuts=forbidden,actual_calls=details,
            scope='Continuous supplied-RAM reset race, original late completion discard, promises/reuse/fresh pixels; no physical reset/USB/boot/printing proof.')
    except Exception as error:
        return False,dict(error=type(error).__name__+': '+str(error))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_root');parser.add_argument('--source-root')
    args=parser.parse_args();ok,detail=check_capture(args.capture_root,args.source_root)
    print(json.dumps(dict(ok=ok,detail=detail),sort_keys=True,indent=2))
    raise SystemExit(0 if ok else 1)




LIBGCC_BYTES,LIBGCC_HASH=B.LIBGCC_BYTES,B.LIBGCC_HASH
selected_ar_members,archive_path_alias=B.selected_ar_members,B.archive_path_alias
def check_libgcc(root,report,tools):
    prefix='libgcc/'
    actual={n[len(prefix):] for n in report['target_sha256'] if n.startswith(prefix)}
    need(actual=={'libgcc.a','manifest.json',*LIBGCC_MEMBERS},
         'exact captured archive, manifest and two inventory members')
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
         {(original['path'],'_udivsi3.o')},
         'actual reset library selection is the single original udiv member')
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



if __name__=='__main__':main()
