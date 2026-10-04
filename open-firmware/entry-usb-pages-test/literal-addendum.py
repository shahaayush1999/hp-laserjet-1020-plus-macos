"""Independent public-layout and natural-stop additions, not an execution.

Manual public target32 layout and source-derived stop contexts. No producer
imports, files, result data, runtime implementation or entry point.
"""
SEMANTIC_SHA256 = "b4f648a2c8a951a55a5bcd3e9f8aa19c9af695127945020f249d507d906ca545"
PUBLIC_HEADER_SHA256 = "f173c03b72cc993382f65a36aabcb3de8ff59e947009a4bc4fd70e66b615a71b"
LAYOUT_HEADER = (0x4850554c,3,457,16,101)
OBJECTS = ((1,13496,4),(2,114704,16),(3,56,4),(4,332,4),(5,64,4),
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
