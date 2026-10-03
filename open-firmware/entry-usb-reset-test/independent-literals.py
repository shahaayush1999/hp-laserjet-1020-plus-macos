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
