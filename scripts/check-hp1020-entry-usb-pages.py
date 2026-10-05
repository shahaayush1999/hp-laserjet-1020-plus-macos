#!/usr/bin/env python3
"""Independent saved-evidence gate for one full real-host two-page document.

V3 corrects V2's conflation of two local request_cancel functions. Frozen
semantic literals precede execution; the first V2 refusal is retained separately.
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

BASE_SHA256 = '81fd4e2d933285ce5039d451ceda56619dcdb3b52974486978bf46e5277447aa'
_base_file = Path(__file__).with_name('check-hp1020-entry-usb.py')
if hashlib.sha256(_base_file.read_bytes()).hexdigest() != BASE_SHA256:
    raise ValueError('neutral independent helper bytes changed')
_spec = importlib.util.spec_from_file_location('hp1020_pages_independent_readers', _base_file)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
need, sha, raw, js, part, put, inside = B.need, B.sha, B.raw, B.js, B.part, B.put, B.inside
be_words, scalar, actual_cookie = B.be_words, B.scalar, B.actual_cookie

# Begin exact independent semantic source.
"""Independent real-host two-page requirements, frozen before target execution.

No producer imports, file I/O, emulator, result loading or entry point. Input is
one original foo2zjs output, including its timestamp-bearing PJL prefix/suffix.
Pages are independent literal PBM rows, not output from the candidate decoder.
This is a supplied-RAM software contract, not USB/controller/printing evidence.
"""

PROFILE = "full-real-host-patterned-two-page-document"
PAINTS = ((0xa5,0x5a),(0xcc,0x96))
CPU = dict(name="ordinary-privilege",ps=0,intenable=0,windowbase=0,
           windowstart=1,sar=0,lbeg=0,lend=0,lcount=0)
PHYSICAL_AR32 = tuple(0x8a000001+i*0x10101 for i in range(32))
ENTRY, STACK_BYTES = 0x100167a8, 8192
LIMITS = dict(model_instructions=10000000,qemu_seconds=120,
              qemu_commands=4096,qemu_ledger_bytes=16777216)
STREAM_SHA256 = "8ccf8bc1391e9025e3bd0a196dd155a04b967271bbb2a896bfd185453c0ed669"
STREAM = bytes.fromhex(
    "1b252d31323334355840504a4c204a4f420a40504a4c20534554204a414d5245434f564552593d4f46460a40504a4c20"
    "5345542044454e534954593d330a40504a4c205345542045434f4e4f4d4f44453d4f46460a40504a4c20534554205245"
    "543d4d454449554d0a40504a4c20494e464f205354415455530a40504a4c205553544154555320444556494345203d20"
    "4f4e0a40504a4c2055535441545553204a4f42203d204f4e0a40504a4c20555354415455532050414745203d204f4e0a"
    "40504a4c20555354415455532054494d4544203d2033300a40504a4c20534554204a4f42415454523d224a6f62417474"
    "72343d323032363130303530313337353122001b252d3132333435584a5a4a5a00000034000000000000000300245a5a"
    "0000000c00010100000000000000000c00020100000000010000000c0000010000000000000000ac000000020000000d"
    "009c5a5a0000000c00170100000000000000000c00110100000000800000000c00120100000000040000000c00100100"
    "000000010000000c000c0100000000800000000c000d0100000000040000000c00070100000000010000000c00080100"
    "000002580000000c00090100000002580000000c00050100000000070000000c00040100000000010000000c00030100"
    "000000090000000c000601000000000100000024000000040000000000005a5a00000100000000800000000400000080"
    "1000035c0000002c000000050000000000005a5ad52c5d54ba4708ff0200000000000000000000000000000000000000"
    "00000010000000060000000000005a5a00000010000000030000000000005a5a000000ac000000020000000d009c5a5a"
    "0000000c00170100000000000000000c00110100000001000000000c00120100000000040000000c0010010000000001"
    "0000000c000c0100000001000000000c000d0100000000040000000c00070100000000010000000c0008010000000258"
    "0000000c00090100000002580000000c00050100000000070000000c00040100000000010000000c0003010000000009"
    "0000000c000601000000000100000024000000040000000000005a5a000001000000010000000004000000801000035c"
    "0000004c000000050000000000005a5adff92781b34c9fcdd221b8d73a6b9d147d1a51128d97d200000acce8c6816e4f"
    "ec60c05f2e7e80ff020000000000000000000000000000000000000000000010000000060000000000005a5a00000010"
    "000000030000000000005a5a00000010000000010000000000005a5a1b252d31323334355840504a4c20454f4a0a1b25"
    "2d313233343558"
)
PAGE1 = bytes.fromhex(
    "80000000000000000000000000000001"
    "40000000000000000000000000000002"
    "20000000000000000000000000000004"
    "10000000000000000000000000000008")
PAGE2 = bytes.fromhex("a55a"*16+"5aa5"*16+"00"*16+"ff"*16+"ff"*16+"00"*16)
PIXELS = PAGE1+PAGE2
PBM = b"P4\n128 4\n"+PAGE1+b"P4\n256 4\n"+PAGE2
PBM_SHA256 = "9660f3075f60ad3586b22dec702f16560461c1718c60c5f19d00a89beb26833d"
PIXELS_SHA256 = "207c26d1f9877bf8144fec9d4216e59263501d5acc0a631b74d83f53c01ca9a7"
# Exact source grammar, including metadata rather than a normalized replacement.
PJL_PREFIX_BYTES, PJL_SUFFIX_BYTES = 268,27
CHUNKS = ((272,52,0),(324,172,2),(496,36,4),(532,44,5),(576,16,6),
          (592,16,3),(608,172,2),(780,36,4),(816,76,5),(892,16,6),
          (908,16,3),(924,16,1))
# Original full-JBIG reference accepts BIE lengths48/80, consumes29/61 total
# including the20-byte BIH, and leaves19 zero padding bytes on each page.
BIE_SHA256 = ("de0044604e56d895e9d73b60b0f5b7756c9975d4fe7dce0da489196de4310867",
              "80e66b0beb5a4c6776df0debbbede2f38bae9c67eeb3d5b34355b5fc9bfdb8fa")
PLAN_WORDS = ((16,32,512,4,1,64,0,0),(32,64,256,4,1,128,0,0))
FRAGMENT_LENGTHS = (64,)*15+(7,0)
RAW_CONFIGURATION = bytes.fromhex("0009010000000000")
SETUP_CONFIGURATION = bytes.fromhex("80000000000000000009010000000000")
CONFIG_STATUS = (1,2,1,0,0x80)
RECOVERY_TICKET = (1,1)
FINAL_OUT = (18,3,2,17,1)
# Original identities are expectations, never inputs fabricated for the runtime.
PACKETS = tuple((q,(q+1,3,2,q,1),(q-1)%4,min((q-1)*64,967),n)
                for q,n in enumerate(FRAGMENT_LENGTHS,1))
BIND_COOKIES = (CONFIG_STATUS,)+tuple(p[1] for p in PACKETS)
SUCCESSFUL_RECEIVE_COMPLETIONS = tuple((2,p[0],p[4]) for p in PACKETS)
NONEMPTY_FEEDS = tuple((2,p[0],STREAM[p[3]:p[3]+p[4]]) for p in PACKETS if p[4])
DOCUMENT_EVENT = (2,1,0,2)
PRODUCTION_OUTPUT = PAGE2+bytes(32768-len(PAGE2))
COUNTS = dict(binds=18,bulk_publications=17,bulk_acquisitions=17,
    acquired_bytes=967,fed_bytes=967,visibility_payload_bytes=1088,
    visibility_descriptor_bytes=272,receive_complete_data=17,receive_release=17,
    nonempty_feed=16,document_restarts=1,ep0_status_callbacks=1,
    ring_accept=2,ring_complete=2,document_callbacks=1,close_input=1,finish=1,
    cancellations=0,conditional_wait=0,conditional_stale=0)

DESCRIPTOR_DMA = 0x579bdf10
RECEIVE_DMAS = (0x24681340,0x24682340,0x24683340,0x24684340)
SETUP_DMA = 0x79bdf130
EP0_IN_DESCRIPTOR_DMA, EP0_IN_PACKET_DMA = 0xa468ace0,0xb68ace00
EP0_PREPARED_WORDS = (0x08000000,0,EP0_IN_PACKET_DMA,0)
EP0_COMPLETION_WORDS = (0x8800ffff,0,EP0_IN_PACKET_DMA,0)
EP0_ACTUAL_KNOWN, EP0_ACTUAL = 1,0

def payload_image(scope):
    _,cookie,slot,start,count = PACKETS[scope-1]
    return STREAM[start:start+count]+bytes(
        0x80|((0x69^(slot*0x1d)^(i*7))&0x7f) for i in range(count,64))

def completed_descriptor(scope):
    p=PACKETS[scope-1]
    return (0x88000000|p[4],0,RECEIVE_DMAS[p[2]],0)

def cpu_poison(slot):
    return ((0xc35a0000|slot,0x13579bdf,0xfedcba90,0x2468ace0),
            bytes((0xd3^slot*0x29^i*0x17)&255 for i in range(64)))

def receive_memory(completed):
    data=bytearray(4096)
    for q in range(1,completed+1):
        slot=PACKETS[q-1][2]
        data[slot*1024:slot*1024+64]=payload_image(q)
    return bytes(data)

FINAL_RECEIVE_PREFIX_SCOPES = (17,14,15,16)
# Original production source dictates page-end before the next page metadata,
# actual ring acceptance then completion, and END_DOC before suffix scanning.
BASE_LIVE = dict(generation=2,stopped=0,quiescent=0,receive_error=0,
    document_finished=0,output_finished=0,output_error=0,output_quiescent=0,
    payload_error=0,feed_generation=2,parser_documents=1,documents_completed=0,
    document_first_page=0,input_closed=0,fenced=0,control_epoch=2,
    active_control_epoch=2,transport_epoch=3,active_transport_epoch=3,
    opened=1,configuration_value=1,reset_active=0,reset_parts=0,
    last_recovery_id=1,class_request_id=0,current_request_id=0,
    ep0_out_owner=0,ep0_in_owner=0,bulk_owner=0,core_out1=0,out_phase=0,
    ring_copied=4,ring_accepted=0,ring_completed=0,ring_rows=4,
    ring_slot_bytes=8192,ring_producer=1,ring_selection=0,ring_completion=0,
    ring_slot0_state=1,pixel_bytes=0,document_callbacks=0)
FIRST_OUTPUT = dict(BASE_LIVE,issued=10,consumed=9,count=1,feeding=1,
    last_submission_id=11,parser_page_count=1,parser_raster_count=1,
    parser_phase=1,parser_framing=2,parser_document_open=1,parser_page_complete=1,
    stream_active=0,jbig_ended=1,stream_bands=1,stream_rows=4,
    payload_consumed=9,padding=19,stream_pages=1,pages_drained=0,
    output_active=1,output_page_index=0,ring_stride=16,ring_capacity_rows=512)
FIRST_COMPLETE = dict(FIRST_OUTPUT,ring_accepted=4,ring_selection=1,
    ring_slot0_state=2,pixel_bytes=64)
SECOND_OUTPUT = dict(BASE_LIVE,issued=15,consumed=14,count=1,feeding=1,
    last_submission_id=16,parser_page_count=2,parser_raster_count=2,
    parser_phase=1,parser_framing=2,parser_document_open=1,parser_page_complete=1,
    stream_active=0,jbig_ended=1,stream_bands=2,stream_rows=8,
    payload_consumed=41,padding=19,stream_pages=2,pages_drained=1,
    output_active=1,output_page_index=1,ring_stride=32,ring_capacity_rows=256,
    pixel_bytes=64)
DOCUMENT_CALLBACK = dict(SECOND_OUTPUT,ring_accepted=4,ring_completed=4,
    ring_selection=1,ring_completion=1,ring_slot0_state=0,pixel_bytes=192,
    pages_drained=2,output_active=0,parser_phase=0,parser_framing=0,
    parser_document_open=0)
BEFORE_CLOSE = dict(DOCUMENT_CALLBACK,issued=17,consumed=16,count=1,feeding=0,
    last_submission_id=18,documents_completed=1,document_first_page=2,
    document_callbacks=1,bulk_owner=1,core_out1=5,out_phase=2)
BEFORE_FINAL_SERVICE = dict(BEFORE_CLOSE,input_closed=1,bulk_owner=2,out_phase=0,
                            owner_actual=0,owner_result=0)
BEFORE_FINISH = dict(BEFORE_CLOSE,input_closed=1,consumed=17,count=0,
                    bulk_owner=0,core_out1=0,out_phase=0)
PARK = dict(BEFORE_FINISH,stopped=1,fenced=1,document_finished=1,output_finished=1)

PROGRAM_INITIAL = (
    (1,0x220,0x51,0),(2,0x220,0xa0,0),(1,0x22c,0x80,0),(2,0x22c,0x40,0),
    (1,0x508,0x100000c1,0),(2,0x508,0x020000c1,0),
    (1,0x418,0x00a700a7,0),(2,0x418,0x00a500a7,0),(3,0xffffffff,0,0),
    (1,0x028,0x40,0),(1,0x020,0x51,0),(2,0x020,0xa0,0),
    (1,0x02c,0x80,0),(2,0x02c,0x40,0),
    (1,0x50c,0x100000d1,0),(2,0x50c,0x020000d1,0),
    (1,0x418,0x00a500a7,0),(2,0x418,0x00a500a5,0),(3,0xffffffff,0,0))

def publication_rows(scope):
    dma=RECEIVE_DMAS[PACKETS[scope-1][2]]
    return ((1,0x404,0x34120320,0),(1,0x220,0x60,0),(1,0x22c,0x40,0),
        (1,0x408,0x0000a001,0),(4,dma,64,0),(5,DESCRIPTOR_DMA,16,0),
        (3,0xffffffff,0,0),(2,0x234,DESCRIPTOR_DMA,0),(3,0xffffffff,0,0),
        (2,0x220,0x120,0),(3,0xffffffff,0,0),(1,0x220,0x20,0),
        (2,0x404,0x34120324,0),(3,0xffffffff,0,0))

def acquisition_rows(scope):
    return ((6,DESCRIPTOR_DMA,16,0),
            (7,RECEIVE_DMAS[PACKETS[scope-1][2]],64,0),(8,0,0,0))

def logical_rows():
    # Keep independently reconstructed scope/ordinal in the oracle even though
    # the bounded target witness stores only its four semantic hook words.
    rows=[(0,i+1,*r) for i,r in enumerate(PROGRAM_INITIAL)]
    for scope in range(1,18):
        for r in publication_rows(scope)+acquisition_rows(scope):
            rows.append((scope,len(rows)+1,*r))
    return tuple(rows)

LOGICAL_COUNTS = {1:94,2:59,3:70,4:17,5:17,6:17,7:17,8:17}
LOGICAL_ROWS, RANGE_ROWS, BIND_ROWS = 308,85,18
FORBIDDEN = ("CSR_DONE","automatic-status","per-page-close","per-page-finish",
    "runtime-reinitialize","unrequested-cancel","host-repair-after-entry",
    "descriptor-bit-derived-quiescence","PJL-command-execution")

# End independent semantic source.
# Begin exact independent public-layout source.
"""Independent public-layout and natural-stop additions, not an execution.

Manual public target32 layout and source-derived stop contexts. No producer
imports, files, result data, runtime implementation or entry point.
"""
SEMANTIC_SHA256 = "b4f648a2c8a951a55a5bcd3e9f8aa19c9af695127945020f249d507d906ca545"
PUBLIC_HEADER_SHA256 = "58b0921807073bd9dd1dda5c3f7b3366fd634e2d682c4d20e97b44388c5176eb"
LAYOUT_HEADER = (0x4850554c,3,457,16,101)
OBJECTS = ((1,13512,4),(2,114704,16),(3,56,4),(4,408,4),(5,64,4),
    (6,16,16),(7,136,4),(8,160,16),(9,80,4),(10,88,4),(11,140,4),
    (12,152,4),(13,204,4),(14,1024,4),(15,9216,4),(16,16,1))
REPLACED_FIELDS = ((91,15,16,4928),(92,15,4960,3060),
    (93,15,8048,648),(94,15,8720,144),(95,15,8864,192),(96,15,9056,20))
WITNESS = dict(bytes=9216,head_guard=(0,16),io=(16,4928),
    io_guard=(4944,16),ranges=(4960,3060),range_padding=(8020,12),
    range_guard=(8032,16),binds=(8048,648),bind_padding=(8696,8),
    bind_guard=(8704,16),device=(8720,144),pixels=(8864,192),
    documents=(9056,20),reserved=(9076,140))
DEVICE = dict(guard0=(0,16),descriptor=(16,16),guard1=(32,16),
    guard2=(48,16),payload=(64,64),guard3=(128,16))
GUARD_BYTE = 0xa7
MAILBOX_RESERVED = (128,128)
# label, actual linked function/startup symbol role, I/O rows, ranges, binds.
# First output occurs while packet10 is READY and still being fed; the next
# page has not begun. Second output and END_DOC occur inside packet15 feed.
STOPS = (
    ("after-normalization","after-normalization",None,None,None),
    ("pre-c","hp1020_usb_runtime_c",0,0,0),
    ("pre-first-output","output",189,50,11),
    ("pre-first-complete","hp1020_image_ring_complete",189,50,11),
    ("pre-second-output","output",274,75,16),
    ("pre-document-event","document_event",274,75,16),
    ("pre-close","hp1020_tusb_adapter_close_input",305,82,18),
    ("pre-final-service","hp1020_udc_publish_service",308,85,18),
    ("pre-finish","hp1020_tusb_adapter_finish",308,85,18),
    ("park","park",308,85,18))
PAIRED_SNAPSHOTS, QEMU_SNAPSHOTS, PARK_STEPS = 11,13,2
CORE_STOP_LABELS = ("after-normalization","pre-c","pre-close",
    "pre-final-service","pre-finish","park")
OUTER_CONTEXT = dict(adapter_busy=0,adapter_stack_active=0,provider_callback_depth=0)
FEED_CONTEXT = dict(adapter_busy=1,adapter_stack_active=0,provider_callback_depth=0)
OUTPUT_CONTEXT = dict(adapter_busy=1,adapter_stack_active=0,provider_callback_depth=1)
PRIVATE_CORE = dict(bytes=68,ep_status_offset=52,ep_status_bytes=16,
                   busy=1,stalled=2,claimed=4,ep0_in=53,bulk_out1=54)
CORE_IDLE = bytes(16)
CORE_BULK_OUT = bytes.fromhex("00000500000000000000000000000000")
CORE_STATUS_BY_STOP = {
    "pre-c":CORE_IDLE,"pre-first-output":CORE_IDLE,"pre-first-complete":CORE_IDLE,
    "pre-second-output":CORE_IDLE,"pre-document-event":CORE_IDLE,
    "pre-close":CORE_BULK_OUT,"pre-final-service":CORE_BULK_OUT,
    "pre-finish":CORE_IDLE,"park":CORE_IDLE}
# (current scope, most recent installed device image, acquired count,
#  output witness bytes so far, document callback rows so far).
PHASE_STORAGE = {
    "pre-first-output":(10,10,10,0,0),
    "pre-first-complete":(10,10,10,64,0),
    "pre-second-output":(15,15,15,64,0),
    "pre-document-event":(15,15,15,192,0),
    "pre-close":(17,16,16,192,1),
    "pre-final-service":(17,17,17,192,1),
    "pre-finish":(17,17,17,192,1),"park":(17,17,17,192,1)}
PRODUCTION_OUTPUT_PAGE = {"pre-first-output":1,"pre-first-complete":1,
    "pre-second-output":2,"pre-document-event":2,"pre-close":2,
    "pre-final-service":2,"pre-finish":2,"park":2}
# Counts before callback entry: output-callbacks, accepts, completes; the first
# completion stop is inside output after copying the first64 exact pixels.
OUTPUT_COUNTS = {"pre-first-output":(0,0,0),"pre-first-complete":(1,1,0),
    "pre-second-output":(1,1,1),"pre-document-event":(2,2,2),
    "pre-close":(2,2,2),"pre-final-service":(2,2,2),
    "pre-finish":(2,2,2),"park":(2,2,2)}
FINAL_SOURCE = (967,0)

# End independent public-layout source.

PREFIX = 'open-firmware/entry-usb-pages-test/'
CHECKPOINTS = tuple(row[0] for row in STOPS)
MODEL_PHASES = ('initial',)+CHECKPOINTS
QEMU_PHASES = MODEL_PHASES+('park-step-1','park-step-2')
OBJECT_ROWS = tuple((i,B.OBJECTS[i-1][1],n,a) for i,n,a in OBJECTS)
FIELD_ROWS = {i:(obj,name,off,width) for i,obj,name,off,width in B.FIELDS}
for i,obj,off,width in REPLACED_FIELDS:
    FIELD_ROWS[i] = (obj,FIELD_ROWS[i][1],off,width)
TABLE_WORDS = LAYOUT_HEADER+tuple(v for i,n,a in OBJECTS for v in (i,n,a))+tuple(
    v for i,(obj,name,off,width) in FIELD_ROWS.items() for v in (i,obj,off,width))
FACTS = bytes([1])*26+bytes(2)+bytes([1])*4+bytes(4)+bytes([1])*4
GUARD = bytes([0xa7])*16
ALL_ROWS = logical_rows()
# Offsets derived manually from unchanged public target32 production structs.
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
 'owner_actual':(4,124,4),'owner_result':(4,131,1),
 'provider_bulk_live':(13,60,1),'provider_cancel_requested':(13,61,1),
}
LIVE = dict(B.LIVE_FIELDS,ring_copied=19,ring_accepted=20,ring_completed=21,
            adapter_busy=37,adapter_stack_active=38)
PHASE_MAP = {'pre-first-output':FIRST_OUTPUT,'pre-first-complete':FIRST_COMPLETE,
    'pre-second-output':SECOND_OUTPUT,'pre-document-event':DOCUMENT_CALLBACK,
    'pre-close':BEFORE_CLOSE,'pre-final-service':BEFORE_FINAL_SERVICE,
    'pre-finish':BEFORE_FINISH,'park':PARK}
EXTRA_API_NAMES = ('hp1020_usb_runtime_ram_install_bulk',
    'hp1020_usb_receive_complete_data','hp1020_usb_receive_release',
    'hp1020_image_output_feed','hp1020_image_ring_accept','hp1020_image_ring_complete',
    'dcd_edpt0_status_complete','driver_xfer','document_out','output','document_event')
API_NAMES = B.ENTRY_NAMES+EXTRA_API_NAMES


def obj(a,i): return a[OBJECT_ROWS[i-1][1]]

def field(ram,a,i):
    o,n,off,z=FIELD_ROWS[i]
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
    rows=[(*CONFIG_STATUS,0,0,obj(a,8)+16,obj(a,8)+96)]
    for scope,c,slot,off,n in PACKETS:
        cpu=obj(a,2)+slot*1024
        rows.append((*c,cpu,64,obj(a,6),cpu))
    return tuple(rows)


def expected_ranges(a):
    rows=[]
    for scope,ordinal,kind,dma,n,outcome in ALL_ROWS:
        if kind not in (4,5,6,7,8):continue
        p=PACKETS[scope-1];cpu=obj(a,2)+p[2]*1024
        span=0 if kind==8 else obj(a,6) if kind in (5,6) else cpu
        rows.append((ordinal,*p[1],span,cpu,64))
    return tuple(rows)


def device_image(scope):
    d=bytearray(144)
    for at in (0,32,48,128):d[at:at+16]=GUARD
    if scope:
        d[16:32]=be_words(completed_descriptor(scope));d[64:128]=payload_image(scope)
    return bytes(d)


def expected_witness(label,a):
    _,_,io,ranges,binds=next(x for x in STOPS if x[0]==label)
    scope,image,completed,pixels,docs=PHASE_STORAGE[label]
    out=bytearray(9216)
    for at in (0,4944,8032,8704):out[at:at+16]=GUARD
    for at,records in ((16,tuple(r[2:] for r in ALL_ROWS[:io])),
                       (4960,expected_ranges(a)[:ranges]),
                       (8048,expected_bind_rows(a)[:binds])):
        data=be_words(v for record in records for v in record)
        out[at:at+len(data)]=data
    out[8720:8864]=device_image(image)
    out[8864:8864+pixels]=PIXELS[:pixels]
    if docs:out[9056:9076]=be_words((*DOCUMENT_EVENT,0))
    return bytes(out)


def live_value(ram,a,name):
    if name in LIVE:return field(ram,a,LIVE[name])
    if name in EXTRA_FIELDS:
        o,off,z=EXTRA_FIELDS[name];return scalar(ram,obj(a,o)+off,z)
    if name=='core_out1':return scalar(ram,a['_usbd_dev']+54,1)
    if name=='pixel_bytes':return scalar(ram,obj(a,14)+43*4)
    if name=='document_callbacks':return scalar(ram,obj(a,14)+47*4)
    raise ValueError('unmapped independent semantic field '+name)


def production_parts(ram,a,elf):
    # Exclude only supplied provider evidence from ordinary BSS. Include all
    # actual component/private TinyUSB state, all buffers and initialized data.
    start,n=elf.zero[0];p=obj(a,13)
    chunks=[(start,p-start),(p+204,start+n-p-204),B.MEMORY,elf.initialized_data]
    return tuple((at,part(ram,at,z)) for at,z in chunks if z)


def check_live(ram,a,label,elf):
    B.check_legacy_document(ram,obj(a,1))
    for name,want in PHASE_MAP[label].items():
        need(live_value(ram,a,name)==want,label+': original field '+name)
    context=(OUTPUT_CONTEXT if label=='pre-first-complete' else FEED_CONTEXT
             if label in ('pre-first-output','pre-second-output','pre-document-event') else OUTER_CONTEXT)
    for name,want in context.items():need(live_value(ram,a,name)==want,label+': context '+name)
    need(part(ram,a['_usbd_dev']+52,16)==CORE_STATUS_BY_STOP[label],label+': actual core endpoint bytes')
    need(scalar(ram,a['_usbd_dev']+24,1)==1 and scalar(ram,a['_usbd_dev']+29,1)==1,
         label+': actual private connected/configuration')
    need(part(ram,obj(a,15),9216)==expected_witness(label,a),label+': complete independent witness bytes')
    scope,image,completed,pixels,docs=PHASE_STORAGE[label]
    need(part(ram,obj(a,2),4096)==receive_memory(completed),label+': full receive prefixes/tails')
    desc=((0x08000000,0,RECEIVE_DMAS[PACKETS[scope-1][2]],0) if label=='pre-close'
          else completed_descriptor(completed))
    need(part(ram,obj(a,6),16)==be_words(desc),label+': actual production descriptor16')
    status=bytearray(160);status[16:32]=be_words(EP0_COMPLETION_WORDS)
    need(part(ram,obj(a,8),160)==bytes(status),label+': full stationary EP0 original completion')
    need(part(ram,obj(a,16),16)==SETUP_CONFIGURATION and field(ram,a,101)==SETUP_CONFIGURATION,
         label+': original immutable SETUP record')
    page=(PAGE1,PAGE2)[PRODUCTION_OUTPUT_PAGE[label]-1]
    need(part(ram,obj(a,2)+81936,32768)==page+bytes(32768-len(page)),
         label+': entire original output allocation, exact independently specified page')
    plan=PLAN_WORDS[PRODUCTION_OUTPUT_PAGE[label]-1]
    need(part(ram,obj(a,1)+13396,32)==be_words(plan),label+': retained original page plan')
    state=PHASE_MAP[label]['ring_slot0_state']
    need(field(ram,a,23)==be_words((state,0,4,1))+bytes(48),label+': actual four ring slots')
    # While feeding callbacks, the genuine reservation is READY. Sole close/
    # pending status still owns the final nonready slot. Only real pump releases.
    receive=bytearray(64)
    if label in ('pre-first-output','pre-first-complete','pre-second-output','pre-document-event'):
        receive[PACKETS[scope-1][2]*16:PACKETS[scope-1][2]*16+16]=be_words((scope,64,64,1))
    elif label in ('pre-close','pre-final-service'):
        receive[:16]=be_words((17,64,0,0))
    need(part(ram,obj(a,1)+4,64)==bytes(receive),label+': all actual receive reservation metadata')
    ad,p,out,acq=(obj(a,i) for i in (4,13,5,12))
    need(part(ram,ad+20,80)==bytes(80),label+': both actual EP0 owners retired')
    if label in ('pre-close','pre-final-service'):
        need(actual_cookie(ram,ad+100)==FINAL_OUT and scalar(ram,ad+120)==obj(a,2) and
             scalar(ram,ad+128,2)==64 and scalar(ram,ad+124)==0,
             label+': original final retained adapter owner')
    else:need(part(ram,ad+100,40)==bytes(40),label+': adapter bulk owner retired')
    need(scalar(ram,out+4)==obj(a,6) and scalar(ram,out+8)==DESCRIPTOR_DMA and scalar(ram,out+12)==16,
         label+': retained stationary descriptor CPU/DMA span')
    if label=='pre-close':
        need(actual_cookie(ram,out+28)==FINAL_OUT and part(ram,out+16,12)==be_words((obj(a,2),RECEIVE_DMAS[0],64)),
             'original exposed final OUT CPU span/cookie')
    else:need(part(ram,out+16,32)==bytes(32),label+': actual acquisition retired OUT metadata')
    slot=PACKETS[scope-1][2]
    need(actual_cookie(ram,p)==CONFIG_STATUS and part(ram,p+20,8)==bytes(8) and
         part(ram,p+28,4)==bytes((0,0,255,0)),label+': retained original EP0 NULL/zero identity')
    need(actual_cookie(ram,p+32)==PACKETS[scope-1][1] and scalar(ram,p+52)==obj(a,2)+slot*1024 and
         scalar(ram,p+56)==64 and part(ram,p+60,4)==bytes((int(label=='pre-close'),0,slot,0)),
         label+': genuine retained transport ledger')
    need(part(ram,p+64,8)==be_words(RECOVERY_TICKET) and scalar(ram,p+72)==scope and
         scalar(ram,p+76)==9+scope*5 and scalar(ram,p+80)==5 and scalar(ram,p+84)==scope and
         scalar(ram,p+92)==15 and scalar(ram,p+96)==0,label+': retained original recovery/read schedule')
    need(actual_cookie(ram,p+180)==PACKETS[image-1][1] and scalar(ram,p+200)==PACKETS[image-1][2],
         label+': immutable source image identity distinct from next reservation')
    need(part(ram,p+112,4)==bytes((1,int(label!='pre-close'),int(label in
        ('pre-close','pre-final-service','pre-finish','park')),int(label=='park'))),
        label+': original provider initialization/source-valid/closing/finished flags')
    need(actual_cookie(ram,acq+20)==PACKETS[completed-1][1] and scalar(ram,acq+40)==15 and
         scalar(ram,acq+60)==0 and scalar(ram,acq+64,1)==3 and scalar(ram,acq+65,1)==1 and
         part(ram,acq+66,16)==be_words(completed_descriptor(completed)) and
         part(ram,acq+84,64)==bytes(64) and part(ram,acq+148,2)==b'\1\0',
         label+': original acquisition diagnostics without hidden failure')
    for name in ('program_failed','publish_failed','acquire_failed','payload_error','output_error'):
        need(live_value(ram,a,name)==0,label+': no hidden component error '+name)
    need(field(ram,a,72)==3 and field(ram,a,73)==3 and field(ram,a,74)==1,
         label+': exact actual endpoint programming binding')


def check_mailbox(ram,a,label,elf,initial):
    w=struct.unpack('>256I',part(ram,obj(a,14),1024))
    need(w[0]==0x48505552 and w[1]==3 and w[4:8]==(0,0,0,0) and w[128:]==(0,)*128,
         label+': actual mailbox identity/error/reserved')
    need(w[8:14]==(elf.zero[0][1],114704,1024,9216,256,elf.initialized_data[1]) and
         w[14]==B.fnv(part(initial,*elf.initialized_data)),'all actual initial scan extents/digest')
    need(0<w[15]<=256 and w[15]==scalar(ram,obj(a,13)+100) and w[16:20]==(1,1,1,1),
         'bounded original step counter and exactly one initialization/reset/setup')
    scope,image,completed,pixels,docs=PHASE_STORAGE[label]
    _,_,io,ranges,binds=next(x for x in STOPS if x[0]==label)
    callbacks,accepts,completes=OUTPUT_COUNTS[label]
    need(w[38:41]==(io,ranges,binds) and w[43:48]==(pixels,callbacks,accepts,completes,docs),
         label+': actual evidence append counts')
    fixed={22:scope,23:scope,24:1,25:completed,26:completed,27:1,28:1,29:1,
      30:1,31:1,32:1,33:1,34:int(label in ('pre-final-service','pre-finish','park')),
      35:int(label=='park'),36:0,37:0,41:completed,42:completed,48:0,49:0,50:0,
      51:9+scope*5,52:ranges,53:int(label=='pre-first-complete'),54:15,55:0,
      60:1,61:1,62:scope+1,63:3,64:2,65:scope,66:1,67:PACKETS[scope-1][2],
      116:completed*64,117:completed*16,118:9+scope*5,119:8+scope*3,120:2+scope*4,
      121:scope,122:scope,123:completed,124:completed,125:completed}
    # Completed input counter increments only after the currently active pump
    # returns, independently of parser progress inside output callbacks.
    fixed[115]=(scope-1)*64 if label in ('pre-first-output','pre-first-complete',
        'pre-second-output','pre-document-event') else 967
    if label in ('pre-first-output','pre-first-complete','pre-second-output','pre-document-event'):
        # The original provider writes these secondary diagnostics only in
        # ram_note at close/later. Actual original cookies are checked above.
        fixed.update({i:0 for i in range(62,68)})
    for i,v in fixed.items():need(w[i]==v,label+': independently fixed mailbox word'+str(i))
    if label in ('pre-close','pre-final-service','pre-finish','park'):
        need(w[68:71]==(305,192,1) and w[126]==1,'close facts before final owner retirement')
        need(w[71:75]==((0,0,0,0) if label=='pre-close' else (2,1,16,0)) and
             w[127]==int(label!='pre-close'),'secondary final acquisition/core facts')
    else:need(w[68:75]==(0,)*7 and w[126:128]==(0,0),'no early close witness')
    if label=='park':
        need(w[2:4]==(2,13) and w[57:60]==(0,0,0),'one successful normal finish')
        actual=(part(ram,obj(a,2),4096),part(ram,obj(a,2)+81936,32768),PIXELS,
            part(ram,obj(a,15)+16,4928),part(ram,obj(a,15)+4960,3060),part(ram,obj(a,15)+8048,648))
        need(w[75:81]==tuple(B.fnv(x) for x in actual),'final secondary hashes of independently checked bytes')
        mapping=(1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,34,35,27,28,29,30,31,41,42,43,59)
        want=tuple(field(ram,a,i) for i in mapping)+(scalar(ram,a['_usbd_dev']+54,1)&1,
             field(ram,a,71),field(ram,a,75),field(ram,a,77),field(ram,a,76),field(ram,a,78))
        need(w[81:115]==want,'secondary final state matches actual production bytes')
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
        B.protected(initial,images[label],() if label=='after-normalization' else elf.mutable)
        if label in ('after-normalization','pre-c'):
            need(r['logical_ar'][1]==sum(B.STACK) and r['sar']==0,label+': exact own initial stack/SAR')
        if label=='park' or label.startswith('park-step-'):
            need(r['logical_ar'][1]==sum(B.STACK),'normal return restores owned stack top')
        if label=='after-normalization':need(images[label]==initial,'no RAM mutation in stack-free prefix')
        elif label=='pre-c':
            for at,n in elf.zero:need(part(images[label],at,n)==bytes(n),'all actual BSS zero before C')
            need(part(images[label],*B.STACK)==part(initial,*B.STACK),'startup leaves stack paint')
            need(part(images[label],*elf.initialized_data)==part(initial,*elf.initialized_data),'loaded generic data survives startup')
        elif not label.startswith('park-step-'):
            check_live(images[label],a,label,elf);check_mailbox(images[label],a,label,elf,initial)
    for label in ('park-step-1','park-step-2'):
        if label in images:need(images[label]==images['park'],'actual native park RAM unchanged')

class ApiContract:
    """Checks genuine function entries/returns during independent raw replay."""
    def __init__(self,a,elf):
        self.a=a;self.elf=elf;self.count=Counter();self.returned=Counter()
        self.pending={};self.history=[];self.successes=0;self.awaiting=0
        self.complete=[];self.release=[];self.feeds=[];self.driver=[]
        self.services=[];self.pumps=[];self.acquire_indices=[]

    def entry(self,e,ram,index):
        a=self.a;name=e['name'];args=e['arguments'];c=self.count;ordinal=c[name]
        d,ad,out,p,m=(obj(a,i) for i in (1,4,5,13,2))
        data={'event':e,'result':None}
        contexts={'hp1020_usb_document_init':d,'hp1020_usb_document_init_documents':d,
          'hp1020_tusb_adapter_init':ad,'hp1020_udc_setup_bus_reset':obj(a,9),
          'hp1020_udc_setup_offer':obj(a,9),'hp1020_udc_setup_dispatch':obj(a,9),
          'hp1020_udc_ep0_take_submission':obj(a,7),'hp1020_udc_ep0_observe':obj(a,7),
          'hp1020_tusb_adapter_pending_reset':ad,'hp1020_tusb_adapter_ack_reset':ad,
          'hp1020_tusb_adapter_finish_reset':ad,'hp1020_tusb_adapter_pump':ad,
          'hp1020_usb_document_restart':d,'hp1020_udc_publish_arm_out':obj(a,11),
          'hp1020_udc_acquire_packet':obj(a,12),'hp1020_udc_publish_service':obj(a,11),
          'hp1020_tusb_adapter_close_input':ad,'hp1020_tusb_adapter_finish':ad,
          'hp1020_usb_receive_complete_data':d,'hp1020_usb_receive_release':d,
          'hp1020_image_output_feed':d+92,'hp1020_image_ring_accept':d+13284,
          'hp1020_image_ring_complete':d+13284}
        if name in contexts:need(args[0]==contexts[name],'actual original object argument: '+name)
        if name in ('hp1020_usb_document_init','hp1020_usb_document_init_documents'):
            need(ordinal==0 and args[1]==m and not c['hp1020_udc_setup_bus_reset'],
                 'first-use full original memory initialization only')
        if name=='hp1020_udc_setup_bus_reset':
            need(ordinal==0 and args[1:3]==[1,0] and c['hp1020_tusb_adapter_init']==1,
                 'sole original ingress1/full-speed reset')
            data['result']=0
        if name=='hp1020_udc_setup_offer':
            need(ordinal==0 and inside(args[1],32,(B.STACK,)) and
                 part(ram,args[1],28)==be_words((2,SETUP_DMA,0))+SETUP_CONFIGURATION,
                 'sole actual immutable configuration SETUP observation')
            data['result']=0
        if name=='hp1020_udc_setup_dispatch':
            need(ordinal==0 and args[1]==2 and args[2]&0xffffff==0x010101 and args[3]==1 and
                 c['hp1020_udc_setup_offer']==1,'original ingress/separate capture/stall facts')
            data['result']=0
        if name=='hp1020_udc_ep0_take_submission':
            need(ordinal==0 and args[1:5]==list(CONFIG_STATUS[:4]) and args[5]>>24==0x80 and
                 actual_cookie(ram,ad+60)==CONFIG_STATUS and scalar(ram,ad+80)==0 and scalar(ram,ad+88,2)==0,
                 'genuine NULL/zero EP0 status with original cookie')
            need(scalar(ram,ad+354,1)==0 and scalar(ram,ad+355,1)==0 and scalar(ram,p+88)==0,
                 'status take only after original callback/API unwind')
            data['result']=0
        if name=='hp1020_udc_ep0_observe':
            need(ordinal==0 and inside(args[1],40,(B.STACK,)) and actual_cookie(ram,args[1])==CONFIG_STATUS and
                 part(ram,args[1]+20,20)==be_words((*EP0_COMPLETION_WORDS,0)) and args[2:4]==[0x01010101,0],
                 'original status observation, opaque lowffff and separately supplied actual0')
            data['result']=0
        if name=='hp1020_tusb_adapter_pending_reset':
            need(ordinal==0 and args[1]==p+64,'one original recovery-ticket query')
            data['result']=0
        if name=='hp1020_tusb_adapter_ack_reset':
            need(ordinal<3 and args[1:4]==[1,1,(1,2,4)[ordinal]],
                 'exact original ticket and three separately supplied recovery promises')
            data['result']=0
        if name=='hp1020_tusb_adapter_finish_reset':
            need(ordinal==0 and args[1:3]==[1,1] and c['hp1020_tusb_adapter_ack_reset']==3,
                 'single initialization recovery after every distinct promise')
            data['result']=0
        if name=='hp1020_usb_document_restart':
            need(ordinal==0 and scalar(ram,d+68)==1 and scalar(ram,ad+354,1)==1,
                 'sole initial generation restart inside original recovery')
            data['result']=0;data['memory_before']=part(ram,m,114704)
        if name=='hp1020_udc_publish_arm_out':
            need(ordinal<17 and not self.awaiting and self.successes==ordinal and
                 not c['hp1020_tusb_adapter_close_input'],'arm only after prior acquisition/service/pump')
            scope,cookie,slot,off,n=PACKETS[ordinal]
            need(tuple(scalar(ram,d+x) for x in (68,72,76,80))==(2,scope-1,scope-1,0) and
                 scalar(ram,ad+130,1)==0 and scalar(ram,out+58,1)==0,
                 'original receive reservation entirely consumed before fresh arm')
            data['result']=0
        if name=='hp1020_usb_runtime_ram_install_bulk':
            need(ordinal<17,'exact17 independent supplied device images')
            scope,cookie,slot,off,n=PACKETS[ordinal]
            need(args[:4]==list(cookie[:4]) and args[4]>>24==1 and args[5]==off and
                 scalar(ram,e['sp'])==n,'original by-value source identity/offset/count')
            need(actual_cookie(ram,out+28)==cookie and scalar(ram,out+58,1)==2,
                 'source image installed only for actual EXPOSED owner')
            data['result']=1
        if name=='hp1020_udc_acquire_packet':
            need(ordinal<17 and self.successes==ordinal and not self.awaiting and
                 c['hp1020_udc_publish_arm_out']==ordinal+1,'one genuine acquisition per actual arm')
            scope,cookie,slot,off,n=PACKETS[ordinal]
            need(args[1:5]==list(cookie[:4]) and args[5]>>24==1 and scalar(ram,e['sp'])==0 and
                 part(ram,e['sp']+5,3)==b'\1\1\1','actual original acquisition cookie and separately supplied facts')
            need(actual_cookie(ram,ad+100)==cookie and scalar(ram,ad+130,1)==1 and
                 actual_cookie(ram,out+28)==cookie and scalar(ram,out+58,1)==2 and
                 scalar(ram,ad+120)==m+slot*1024 and scalar(ram,ad+128,2)==64,
                 'actual retained original DCD/EXPOSED owner')
            need(actual_cookie(ram,p+180)==cookie and scalar(ram,p+200)==slot and scalar(ram,p+113,1)==1,
                 'separate immutable source image keeps original identity')
            poisoned=bytearray(receive_memory(scope-1));poisoned[slot*1024:slot*1024+64]=cpu_poison(slot)[1]
            need(part(ram,m,4096)==bytes(poisoned) and part(ram,obj(a,6),16)==be_words(cpu_poison(slot)[0]) and
                 part(ram,obj(a,15)+8720,144)==device_image(scope),
                 'full isolated CPU poison and separate immutable source before visibility hooks')
            need(c['hp1020_tusb_adapter_close_input']==int(scope==17),'final success ZLP only after sole close')
            data.update(result=0,scope=scope,core_before=part(ram,a['_usbd_dev']+52,16),
                        receive_before=part(ram,d,92),reset_before=part(ram,ad+316,44))
            self.acquire_indices.append(e['instruction'])
        if name=='hp1020_udc_publish_service':
            self.services.append(e['instruction']);data['result']=0
            if self.awaiting:
                scope=self.awaiting;cookie=PACKETS[scope-1][1];n=PACKETS[scope-1][4]
                need(actual_cookie(ram,ad+100)==cookie and scalar(ram,ad+130,1)==2 and
                     scalar(ram,ad+124)==n and scalar(ram,out+58,1)==0 and scalar(ram,a['_usbd_dev']+54,1)==5,
                     'actual original PENDING owner/core BUSY persists until real service')
                data['draining']=scope
        if name=='driver_xfer':
            scope=len(self.driver)+1;need(scope<=17,'exact actual bulk driver callbacks')
            _,cookie,slot,off,n=PACKETS[scope-1]
            need(args[:4]==[0,1,0,n] and scalar(ram,ad+366,1)==1 and actual_cookie(ram,ad+180)==cookie and
                 scalar(ram,ad+204)==n and scalar(ram,ad+213,1)==0,
                 'real SUCCESS delivery retains original cookie and count')
            self.driver.append(scope);data['result']=1
        if name=='hp1020_usb_receive_complete_data':
            wanted=SUCCESSFUL_RECEIVE_COMPLETIONS[len(self.complete)] if len(self.complete)<17 else None
            need(wanted is not None and args[1:4]==list(wanted),'every original completion including final zero-length packet')
            self.complete.append(wanted);data['result']=0
        if name=='hp1020_usb_receive_release':
            wanted=SUCCESSFUL_RECEIVE_COMPLETIONS[len(self.release)] if len(self.release)<17 else None
            need(wanted is not None and args[1:3]==list(wanted[:2]),'release exact admitted original reservation')
            self.release.append(wanted);data['result']=0
        if name=='hp1020_image_output_feed':
            wanted=NONEMPTY_FEEDS[len(self.feeds)] if len(self.feeds)<16 else None
            need(wanted is not None,'exact16 feeds; no final ZLP parser feed')
            gen,seq,value=wanted;slot=(seq-1)%4
            need(args[1:3]==[m+slot*1024,len(value)] and part(ram,args[1],len(value))==value and
                 scalar(ram,d+13484)==gen and scalar(ram,d+13506,1)==1,
                 'actual unmodified original-generation input including all PJL/partial chunks')
            self.feeds.append((gen,seq));data['result']=0
        if name=='hp1020_tusb_adapter_pump':
            need(not self.awaiting,'pump cannot bypass pending transport callback')
            self.pumps.append(e['instruction']);data['result']=0
        if name=='output':
            need(ordinal<2 and args[:3]==[d+13396,d+13284,p] and not c['hp1020_tusb_adapter_close_input'],
                 'two original output callbacks before sole close')
            want=(FIRST_OUTPUT,SECOND_OUTPUT)[ordinal]
            for key,value in want.items():need(live_value(ram,a,key)==value,'actual page callback '+str(ordinal+1)+': '+key)
            need(part(ram,d+13396,32)==be_words(PLAN_WORDS[ordinal]) and
                 part(ram,m+81936,32768)==(PAGE1,PAGE2)[ordinal]+bytes(32768-(64,128)[ordinal]) and
                 self.returned['hp1020_image_ring_accept']==ordinal and self.returned['hp1020_image_ring_complete']==ordinal,
                 'exact original plan/pixels and all prior page acceptance/completion')
            data['result']=0
        if name in ('hp1020_image_ring_accept','hp1020_image_ring_complete'):
            need(ordinal<2 and args[1]==0 and c['output']==ordinal+1 and self.returned['output']==ordinal and
                 scalar(ram,d+68)==2 and not c['hp1020_tusb_adapter_close_input'] and
                 scalar(ram,p+88)==1 and scalar(ram,ad+354,1)==1,
                 'ring consumption only inside genuine page output callback')
            if name=='hp1020_image_ring_accept':
                need(scalar(ram,d+13332)==1 and scalar(ram,d+13320)==0 and scalar(ram,d+13324)==0,
                     'accept original READY slot exactly once')
            else:
                need(self.returned['hp1020_image_ring_accept']==ordinal+1 and scalar(ram,d+13332)==2 and
                     scalar(ram,d+13320)==4 and scalar(ram,d+13324)==0 and
                     part(ram,obj(a,15)+8864,(64,192)[ordinal])==PIXELS[:(64,192)[ordinal]],
                     'complete only after original acceptance and exact literal pixel retention')
            data['result']=0
        if name=='document_out':
            need(ordinal==0 and args[1]==d and part(ram,args[0],12)==be_words((1,0,2)) and
                 scalar(ram,d+13484)==2 and scalar(ram,d+13506,1)==1,
                 'one original whole-document boundary during generation2 feed')
            data['result']=0
        if name=='document_event':
            need(ordinal==0 and args[1]==p and inside(args[0],16,(B.STACK,)) and
                 part(ram,args[0],16)==be_words(DOCUMENT_EVENT) and not c['hp1020_tusb_adapter_close_input'] and
                 self.returned['output']==2 and self.returned['hp1020_image_ring_complete']==2,
                 'one exact original document event after both real page completions')
            for key,value in DOCUMENT_CALLBACK.items():
                need(live_value(ram,a,key)==value,'actual document callback: '+key)
            data['result']=0
        if name=='dcd_edpt0_status_complete':
            need(ordinal==0 and args[0]==0 and part(ram,args[1],8)==bytes.fromhex('0009000100000000'),
                 'genuine standard status-completion request identity')
        if name=='hp1020_tusb_adapter_close_input':
            need(ordinal==0 and self.successes==16 and c['hp1020_udc_publish_arm_out']==17 and
                 self.returned['document_event']==1 and len(self.release)==16 and len(self.feeds)==16,
                 'sole close after all raw suffix bytes, both pages and END_DOC with final OUT held')
            data['result']=0
        if name=='hp1020_tusb_adapter_finish':
            need(ordinal==0 and self.successes==17 and not self.awaiting and len(self.release)==17 and
                 c['hp1020_tusb_adapter_close_input']==1,'sole finish after final real callback and empty pump')
            data['result']=0
        self.pending[index]=data;self.history.append((e['instruction'],name,index));c[name]+=1

    def returned_event(self,e,ram):
        index=e['entry_event_index'];need(index in self.pending,'selected return retains original selected entry')
        data=self.pending.pop(index);name=data['event']['name'];r=e['result'];a=self.a
        if data['result'] is not None:need(r==data['result'],'actual API return differs: '+name)
        if 'memory_before' in data:
            need(part(ram,obj(a,2),114704)==data['memory_before'],'initial generation restart preserves entire original memory')
        if 'scope' in data:
            scope=data['scope'];cookie=PACKETS[scope-1][1];n=PACKETS[scope-1][4];d=obj(a,1);ad=obj(a,4)
            need(actual_cookie(ram,ad+100)==cookie and scalar(ram,ad+130,1)==2 and scalar(ram,ad+124)==n and
                 scalar(ram,obj(a,5)+58,1)==0 and part(ram,d,92)==data['receive_before'] and
                 part(ram,ad+316,44)==data['reset_before'] and part(ram,a['_usbd_dev']+52,16)==data['core_before'],
                 'acquisition queues exact original success without callback/core/recovery retirement')
            need(part(ram,obj(a,2),4096)==receive_memory(scope) and
                 part(ram,obj(a,6),16)==be_words(completed_descriptor(scope)),
                 'actual original hook visibility effects before acquisition returns')
            self.successes+=1;self.awaiting=scope
        if 'draining' in data:
            need(len(self.driver)>=data['draining'] and scalar(ram,obj(a,4)+130,1)==0 and
                 scalar(ram,a['_usbd_dev']+54,1)==0,'real service dispatches callback then retires owner/core BUSY')
            self.awaiting=0
        if name=='output':
            ordinal=self.returned[name]
            need(self.returned['hp1020_image_ring_accept']==ordinal+1 and
                 self.returned['hp1020_image_ring_complete']==ordinal+1 and
                 scalar(ram,obj(a,1)+13324)==4 and scalar(ram,obj(a,1)+13332)==0 and
                 scalar(ram,obj(a,13)+88)==0,'output returns only after own real acceptance/completion')
        self.returned[name]+=1

    def access(self,kind,address,size):
        # All accesses still undergo raw instruction-width/phase/span replay.
        # There are no conditional WAIT/STALE preservation exceptions here.
        pass

    def finish(self,images):
        expected={'hp1020_usb_runtime_c':1,'hp1020_usb_document_init_documents':1,
          'hp1020_tusb_adapter_init':1,'hp1020_udc_setup_bus_reset':1,
          'hp1020_udc_setup_offer':1,'hp1020_udc_setup_dispatch':1,
          'hp1020_udc_ep0_take_submission':1,'hp1020_udc_ep0_observe':1,
          'hp1020_tusb_adapter_pending_reset':1,'hp1020_tusb_adapter_ack_reset':3,
          'hp1020_tusb_adapter_finish_reset':1,'hp1020_usb_document_restart':1,'tusb_rhport_init':1,
          'hp1020_udc_publish_arm_out':17,'hp1020_udc_acquire_packet':17,
          'hp1020_usb_runtime_ram_install_bulk':17,'hp1020_usb_receive_complete_data':17,
          'hp1020_usb_receive_release':17,'hp1020_image_output_feed':16,
          'hp1020_image_ring_accept':2,'hp1020_image_ring_complete':2,
          'driver_xfer':17,'document_out':1,'document_event':1,'output':2,
          'dcd_edpt0_status_complete':1,'hp1020_tusb_adapter_close_input':1,
          'hp1020_tusb_adapter_finish':1,'hp1020_udc_publish_service':20,'hp1020_tusb_adapter_pump':17}
        for name,n in expected.items():need(self.count[name]==n and self.returned[name]==n,'actual entry/return count: '+name)
        need(not self.pending and self.successes==17 and not self.awaiting and
             self.count['hp1020_usb_document_init']<=1,'complete single uninterrupted document lifecycle')
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
    # The adapter helper shares its local name with the provider callback.
    # Initial bus reset and SET_CONFIGURATION each inspect all four empty
    # owners. Source and these original ELF bytes prove an immediate return,
    # not a cancellation request. Bind the callback by the actual ops pointer.
    cancel_symbols={at for at,n,info,index in elf.symbols.get('request_cancel',[])
                    if info&15==2 and n and index}
    provider_cancel=scalar(images['pre-close'],obj(a,4)+12)
    need(len(cancel_symbols)==2 and provider_cancel in cancel_symbols,
         'distinct original adapter helper and bound cancellation callback')
    cancel_helper=next(iter(cancel_symbols-{provider_cancel}))
    need(elf.file(cancel_helper,35)==bytes.fromhex(
         '2a301ed93069a1182b3020cdb22a342088238330849185928693879482240a8000d00f'),
         'original guarded adapter cancellation helper bytes')
    visited=set(pcs)
    for name in ('request_cancel','hp1020_udc_out_request_cancel'):
        for at,n,info,index in elf.symbols.get(name,[]):
            if info&15==2 and n and index and at!=cancel_helper:
                need(not any(at<=pc<at+n for pc in visited),
                     'no provider/controller cancellation instruction executes: '+name)
    cancel_indices=[i for i,pc in enumerate(pcs) if pc==cancel_helper]
    need(len(cancel_indices)==8 and all(
         pcs[i:i+4]==[cancel_helper,cancel_helper+3,cancel_helper+5,cancel_helper+33]
         and i<pcs.index(elf.symbol('hp1020_udc_publish_arm_out')) for i in cancel_indices),
         'eight empty-owner cancellation guards return before first bulk publication')
    cancel_reads=[r for r in struct.iter_unpack('>B3xIIII',access) if r[1]==cancel_helper]
    need(cancel_reads==[(1,cancel_helper,obj(a,4)+off,1,0)
                        for off in (130,170,50,90,130,170,50,90)],
         'each original cancellation guard reads only its expected empty owner')
    ram={at:bytearray(b) for at,b in images['initial'].items()}
    selected=selected_api_entries(elf);api=ApiContract(a,elf)
    rows=model['pages_api_events'];erow=0;ci=0;frames=[];pending_returns=[]
    cursor=0;counts=Counter();widths=Counter();seen=[];minimum=None
    checkpoints_index={};counts_at={};old_entries=[];scanned=set();global_write=False
    pre_c_index=pcs.index(cps['pre-c']);observations=model['pages_observations']
    need(model['pages_observation_schema']=='hp1020-entry-usb-pages-observation-v1' and
         model['pages_cursor_convention']=='completed instructions/accesses before target; causing PC at instruction-1' and
         model['pages_host_target_calls']==model['pages_host_target_mutations']==0,
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
        if len(seen)<10:
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
    need(seen==list(CHECKPOINTS)==model['pages_checkpoints'] and len(observations)==10 and
         model['checkpoints']==list(B.PHASES[1:]),'complete10 ordered page and six unchanged guard checkpoints')
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
                wait_returns=0,stale_returns=0,provider_cancel_callbacks=0,
                initial_empty_owner_cancel_guards=8)


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
                        'hp1020_entry_usb_pages_qemu.py': source_map['scripts/hp1020_entry_usb_pages_qemu.py'],
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
    for item, (label, address) in zip(q['snapshots'][1:11], checkpoints.items()):
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
    for item in q['snapshots'][11:]:
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
            target_matches=[p for p in report['target_sha256'] if dependency.endswith('/analysis/boot-handoff/entry-usb-pages/target/'+p)]
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
         'actual page-profile library selection is the single original udiv member')
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





# Source identities sealed before candidate execution; no generated outcome is
# accepted as an independent semantic oracle.
FROZEN_SOURCES = {
    'open-firmware/entry-usb-pages-test/independent-literals.py': 'b4f648a2c8a951a55a5bcd3e9f8aa19c9af695127945020f249d507d906ca545',
    'open-firmware/entry-usb-pages-test/literal-addendum.py': 'd03fb3f1b3953477f668619a499cfe3ec96a1added735e0f4c92f41bc77a524a',
    'open-firmware/entry-usb-pages-test/hp1020_usb_runtime_contract.h': '58b0921807073bd9dd1dda5c3f7b3366fd634e2d682c4d20e97b44388c5176eb',
    'open-firmware/entry-usb-pages-test/CONTRACT.md': '0e78b90bf5cb3f453ac4760ecbecfd29e16e59b877b0f6f25bc07f5f56bd112e',
    'open-firmware/entry-usb-pages-test/LIBRARY_SELECTION.md': '344575b6e5123bd655d3b8e81420eaefccaf6bd54172144433ea348daf6e40db',
    'open-firmware/entry-usb-pages-test/layout-objects.tsv': 'c1c49c7743960ae63fd22d7cb1fdf7d4dfd04904ba2d6e8a200e3a9068b8b681',
    'open-firmware/entry-usb-pages-test/layout-fields.tsv': '91bb103c8ff980e53d9edffec8c4da04e24d0d32497fa805141ef6289ca25a97',
    'open-firmware/entry-usb-pages-test/startup.S': 'c8271bbea0fdc7ed4ffb4c18469a15d91170d26c948d41e3706e8ed95922bad6',
    'open-firmware/entry-usb-pages-test/runtime.ld': 'a9da60d3538fcd92fdf7d1329092df2f9208fede69778b168661a3dcfee712a7',
    'scripts/check-hp1020-entry-usb.py': '81fd4e2d933285ce5039d451ceda56619dcdb3b52974486978bf46e5277447aa',
    'scripts/hp1020_qemu_ram.py': '8fe170ab6161d47d17ef93eb6c25622878e00dc2d4747cfd70073a0fd777b5e2',
    'scripts/hp1020_entry_qemu.py': '4ef9ffcfac58a326b68df526c8ddec93868cf18cf85eae76682a30ab9cf9d080',
    'scripts/hp1020_entry_machine.py': 'a125a4cbda453d7521ab8e57e0a17ebff7c2429187936725ed597515410079f3',
    'scripts/hp1020_entry_usb_machine.py': '377cdd771447a4d69040a5624ef1fafc7593fea50fc471ccd7f8a0ff1077466a',
    'scripts/hp1020_entry_usb_qemu.py': '2b16ee504abebd6f184fe2f78c035b85f16df2e4c89102bd98735c6ddb197e59',
    'scripts/hp1020_entry_usb_audit.py': 'bf3e4dbe77b7f4b9c6c8f264d31c28186b40f65621d947468080bda9c984dc9d',
    'scripts/hp1020_entry_audit.py': 'e7d47b1cb441e4d6c0972f37761dc8fffce81e8329c7a07005ce5fba7549070c',
    'scripts/hp1020_xtensa_call0.py': 'ed2924d8e46c0e553fe079a5ecdfff77dc40f1aa228588d9a86c39ce98769480',
    'scripts/hp1020_xtensa_properties.py': '8a98e5ba3ead469cd431a06260e78c836993348d878ae96595d0b622538d0280',
    'scripts/validate-hp1020-entry-usb.py': '3549e7d2ad5a9e9743f9ced1233dafce4592d786af373cf4a74f2e7d1ff25642',
    'scripts/build-hp1020-entry-usb-target.sh': '263bd6de6acc4312289a9419e4ce259a0bd5597625f73da9e33a13a5b48d5365',
    'scripts/check-hp1020-c-compiler-profile.py': 'c9d5cce3591a402f1b3f0e4ad343fb1064747a4d9c256b4a61cea60eccdf8aa4',
    'scripts/prepare-hp1020-tinyusb.py': '5609cbf3c13156746cba4ddc1011ae45f4ffac4fd0f79142495290138b5c86df',
    'open-firmware/tinyusb-device/tusb_config.h': '895c6599700b09f84be46ce74ac75f3974ce3b277d98f233134a54aea637616a',
    'open-firmware/udc-out/hp1020_udc_out.c': '63361d26de832654eeb75f3a87248d1badb08d074419ff870880127e6d7ba91c',
    'open-firmware/udc-out/hp1020_udc_acquire.h': 'e073d84e4f0223e07997a3cce5125a420591317681f80c7b80a5b2adc0bfc653',
    'open-firmware/udc-publish/hp1020_udc_publish.c': 'd3cfe2bc668f6028990872bbfd6ad87065d0f989d433962025ba7bdb3456fc25',
    'open-firmware/udc-program/hp1020_udc_program.c': '24d0cd6abef20a9962a293ff308605f972585ab760a5ed8762663d474f4c735c',
    'open-firmware/udc-ep0/hp1020_udc_ep0.c': '397c99e7b25239ae4dfb59179ea401f1e9e7d5befeb92aed853681ab90bcf140',
    'open-firmware/udc-setup/hp1020_udc_setup.c': 'f70322d734a8a2d26ed31befb275f61c5256e807389ca399a70707ce089508f3',
    'open-firmware/tinyusb-printer-adapter/hp1020_tusb_adapter.c': '472cab2bdf7c64e3394e8a05c4b598020efa54db2d1a7347b58498f122062ba2',
    'open-firmware/usb-printer-class/hp1020_usb_printer.c': 'c9daf663ae7eea5b9df6a6a68fffd86ec0d6c4b860ce17559250e65cf02361b9',
    'open-firmware/usb-receive-core/hp1020_usb_receive.c': '352413d1c3d5cd8dbe1aa1788ab27383d1c45bfc344842d3b9b08c7e64827a8e',
    'open-firmware/usb-receive-core/hp1020_usb_document.c': '9b40ec83818cfaeb27e8f688ee47163c9f437437f121002b433cb66eaf8edf6a',
    'open-firmware/usb-receive-core/hp1020_usb_document.h': 'acc66f3820d800c8ee9d88ca8a75d34b4a30e2dce5d0a0b83429e32b56aa1dc0',
    'open-firmware/image-pump/hp1020_image_pump.c': '91b13ce743749a0c901f04adc972d1d52faeda693baea0f5c95a912aa48237c6',
    'open-firmware/image-pump/hp1020_image_pump.h': '03bc1f0dd580caee3a63468c6b10474a7e80bc364030d74268197ad7b0c34db9',
    'open-firmware/image-core/hp1020_image_output.c': 'ed469978829f1cc35b10062912db2fd88d030fb112b9ca35596bf115211c9728',
    'open-firmware/image-core/hp1020_image_ring.c': '9ee8f5955e8d6f30a3b12778553477835dc245eb3d928f6e81b467f8562d4e2b',
    'open-firmware/image-core/hp1020_image_stream.c': '772f9c2caa5a20091d3a4a38fb6c8454ad6329c035b9c35bd6ec45611dc319d3',
    'open-firmware/semantic-core/hp1020_semantic.c': '183cd8351bc01725e46ec14a93f032830730e7c33d6a26028942f29751420c6a',
    'open-firmware/semantic-core/hp1020_page_plan.c': '16f6608918c620f437d09fe1f56c8f1043d9c60a4e6b8b3f2cd5220ff57e0517',
}
REVIEWED_TARGET_SHA256 = '29147c8f911c422f484109f4096d6b70df94fbe57552b599a14e5d2e91c6d71d'


def check_sources(root,report,source_root):
    sources=js(root,'source-sha256.json')
    need(sources==report['source_sha256'],'original report/source manifest binding')
    seal_tree(root,'source',sources);seal_tree(root,'target',report['target_sha256'])
    fixed=dict(FROZEN_SOURCES)
    fixed['scripts/check-hp1020-entry-usb-pages.py']=sha(Path(__file__).read_bytes())
    fixed.update({'open-firmware/entry-ram-test/references/qemu-primary/'+n:h for n,h in PRIMARY.items()})
    for name,digest in fixed.items():need(sources.get(name)==digest,'frozen source contract/helper: '+name)
    required=('scripts/validate-hp1020-entry-usb-pages.py','scripts/build-hp1020-entry-usb-pages-target.sh',
      'scripts/hp1020_entry_usb_pages_machine.py','scripts/hp1020_entry_usb_pages_qemu.py',
      'scripts/hp1020_entry_usb_pages_audit.py',PREFIX+'hp1020_usb_runtime.c',
      PREFIX+'hp1020_usb_runtime_ram.c',PREFIX+'hp1020_usb_runtime_layout.c',
      'open-firmware/image-pump/hp1020_image_pump.h',
      'open-firmware/tinyusb-device/patches/protocol-compatibility.patch')
    need(set(required)<=set(sources),'complete new runtime/audit/observer and production source closure')
    for unit in UNITS:need(any(n.endswith('/'+unit+'.c') for n in sources),'actual compiled C source: '+unit)
    if source_root is not None:
        for name,digest in sources.items():need(sha(raw(Path(source_root).resolve(),name))==digest,'live source changed: '+name)
    return sources


def check_input(root,report):
    need(len(STREAM)==967 and sha(STREAM)==STREAM_SHA256 and raw(root,'input/whole-job.zjs')==STREAM,
         'entire frozen unmodified original host job967')
    need(len(PBM)==210 and sha(PBM)==PBM_SHA256 and raw(root,'input/source.pbm')==PBM and
         len(PIXELS)==192 and sha(PIXELS)==PIXELS_SHA256 and raw(root,'input/pixels.bin')==PIXELS,
         'independent literal original PBM source pages/pixels')
    need(STREAM[268:272]==b'JZJZ' and STREAM[940:]==b'\x1b%-12345X@PJL EOJ\n\x1b%-12345X',
         'actual entire PJL framing preserved')
    for off,n,kind in CHUNKS:
        need(struct.unpack_from('>II',STREAM,off)==(n,kind),'original independently specified chunk boundary')
    bies=(STREAM[512:532]+STREAM[548:576],STREAM[796:816]+STREAM[832:892])
    need(tuple(map(sha,bies))==BIE_SHA256 and bies[0][29:]==bytes(19) and bies[1][61:]==bytes(19),
         'original BIEs and exact reference-decoder consumed/padding split')
    need(sha(raw(root,'input/validation.json'))=='ee22c1f50b3083b0fbcaf47a192459345e9ff438d16ad766349e1b40db80b3f9' and
         sha(raw(root,'input/encoder-output.json'))=='756d0f992bce1c491e18447a0d39b9ef0f2b6161e7b227dfede0158de112a8fc',
         'exact prior independent full-JBIG host validation and unchanged encoder provenance')
    provenance=js(root,'input/provenance.json')
    need(provenance==report['input'] and provenance==dict(
        source='analysis/boot-handoff/entry-usb-pages/fixtures/whole-job.zjs',
        input_sha256=STREAM_SHA256,bytes=967,independent_literal_match=True,normalized=False),
        'original whole host job provenance, never rewritten fragments')


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
    """Read only saved sources/ELF/traces, never import a producer or run target."""
    try:
        root=Path(capture_root).resolve();report=js(root,'validation.json')
        need(report['status']=='pass' and report['candidate_execution'] is True and
             report['independent_capture_gate_present'] is True and not any(k in report for k in
             ('error','source_seal_error','publication_error')),'complete successful unchanged-source execution')
        sources=check_sources(root,report,source_root);check_tools(root,report,sources);check_input(root,report)
        elf_data=raw(root,'target/entry-usb.elf')
        need(sha(elf_data)==REVIEWED_TARGET_SHA256,'exact independently admitted whole linked image')
        elf=B.Elf(elf_data)
        helper=elf.symbol('__udivsi3',76);helper_bytes=elf.file(helper,76)
        need(sha(helper_bytes)=='97c0f245a842a23b8ca0ad47d15b781a0dc0537c7aa2dc7251efa494e734e3f9' and
             helper_bytes[65:68]==bytes(3) and helper_bytes[68:72]==b'DIV0' and
             '__umodsi3' not in elf.symbols,'original selected udiv and unexecuted excluded trap/marker')
        a=object_addresses(elf);B.private_getter(elf)
        forbidden=B.forbidden_shortcut_policy(root,elf)
        need(js(root,'elf-loads.json')==elf.loads,'actual file-only ELF load metadata')
        need(elf.file(elf.symbol('hp1020_usb_runtime_input',967),967)==STREAM,'actual entire linked input967')
        need(elf.file(elf.symbol('hp1020_usb_runtime_setup_record',16),16)==SETUP_CONFIGURATION,
             'one immutable original raw-wire SETUP record')
        need(elf.file(elf.symbol('hp1020_usb_runtime_supplied',40),40)==FACTS,
             'separate supplied controller/cache/mapping/settlement/actual-length facts')
        need(elf.symbol('hp1020_usb_runtime_sentinel',256)==B.DATA_SENTINEL[0],'fixed loaded sentinel')
        table=elf.symbol('hp1020_usb_runtime_layout',1828);table_bytes=elf.file(table,1828)
        need(tuple(struct.unpack('>457I',table_bytes))==TABLE_WORDS and
             inside(table,1828,((elf.alloc['.rodata'][3],elf.alloc['.rodata'][5]),)),
             'all457 compiler-layout constants match independent manual table')
        layout_hashes={n:sources[PREFIX+n] for n in ('layout-objects.tsv','layout-fields.tsv')}
        need(js(root,'layout-witness.json')==dict(status='pass',address=table,words=list(TABLE_WORDS),
             sha256=sha(table_bytes),expected_sha256=layout_hashes),'actual source-bound complete layout witness')
        cps=checkpoint_addresses(elf)
        need(js(root,'checkpoints.json')==[[n,at] for n,at in cps.items()],'exact10 natural checkpoint addresses')
        audit=js(root,'linked-audit.json')
        need(audit==report['linked_audit'] and audit['target_sha256']==sha(elf_data) and
             audit['target_bytes']==len(elf_data) and audit['entry']==ENTRY and
             audit['audit_source_sha256']==sources['scripts/hp1020_entry_usb_pages_audit.py'],
             'exact ELF/source-bound pre-execution admission audit')
        need(sha(raw(root,'annotated-disassembly.txt'))==audit['disassembly_sha256'],
             'preserved actual annotated-disassembly seal')
        need(audit['zero_spans']==[list(x) for x in elf.zero] and audit['owned_stack']==list(B.STACK) and
             audit['initialized_data_span']==list(elf.initialized_data),'actual admitted split memory policy')
        need(len(report['cases'])==2,'two fixed ordinary incoming CPU/paint cases')
        dirs=set();total=0;details=[]
        for index,case in enumerate(report['cases']):
            fills=PAINTS[index];name=f'{index:02d}-{CPU["name"]}-{fills[0]:02x}';dirs.add(name)
            folder=root/'cases'/name
            need(case==js(folder,'case.json') and case['case']==name and case['status']=='pass' and
                 case['cpu_profile']==CPU and case['paints']==list(fills) and case['paired_checkpoints']==11,
                 'literal independent pages CPU/paint matrix')
            supplied=cpu_initial();need(js(folder,'initial-registers.json')==supplied,'initial32 distinct physical ARs')
            initial=B.make_initial(elf,fills);model=case['model'];q=case['qemu']
            need(model==js(folder/'model','result.json') and model['status']=='pass' and
                 model['snapshots']==js(folder/'model','snapshots.json'),'actual complete model records')
            mi=B.snapshots(folder/'model',model['snapshots'],MODEL_PHASES)
            qi=B.snapshots(folder/'qemu',q['snapshots'],QEMU_PHASES,True)
            semantic_snapshots(model['snapshots'],mi,initial,supplied,cps,elf,a)
            semantic_snapshots(q['snapshots'],qi,initial,supplied,cps,elf,a,True)
            for m,n in zip(model['snapshots'],q['snapshots'][:11]):
                need(B.registers(m['registers'])==B.registers(n['registers'],True) and mi[m['name']]==qi[n['name']],
                     'all11 paired complete CPU and RAM snapshots')
            for n in q['snapshots'][11:]:
                need(n['registers']==q['snapshots'][10]['registers'] and qi[n['name']]==qi['park'],
                     'two real native self-jump steps preserve every CPU/RAM byte')
            stack=part(mi['park'],*B.STACK);changed=[i for i,v in enumerate(stack) if v!=fills[1]]
            wanted=dict(initial_byte=fills[1],changed_bytes=len(changed),
                lowest_changed_address=B.STACK[0]+min(changed) if changed else None)
            need(changed and {k:case['stack_paint'][k] for k in wanted}==wanted and
                 isinstance(case['stack_paint'].get('limitation'),str),'actual complete stack-paint witness')
            details.append(model_trace(folder/'model',model,mi,elf,cps,a,forbidden))
            qemu_ledger(folder/'qemu',q,qi,supplied,cps,sources,elf);total+=model['instructions']
        need({p.name for p in (root/'cases').iterdir() if p.is_dir()}==dirs,'exact saved case directories')
        return True,dict(cases=2,paired_checkpoints=22,qemu_park_steps=4,model_instructions=total,
            target_sha256=sha(elf_data),forbidden_shortcuts=forbidden,actual_calls=details,
            scope='One unmodified real-host two-page document through supplied RAM USB ownership; exact pixels, page/document callbacks and final drain. No physical USB/cache/engine/boot/printing proof.')
    except Exception as error:
        return False,dict(error=type(error).__name__+': '+str(error))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_root');parser.add_argument('--source-root')
    args=parser.parse_args();ok,detail=check_capture(args.capture_root,args.source_root)
    print(json.dumps(dict(ok=ok,detail=detail),sort_keys=True,indent=2))
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':main()
