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
