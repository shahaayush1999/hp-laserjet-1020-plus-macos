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
