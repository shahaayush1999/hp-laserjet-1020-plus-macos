#!/usr/bin/env python3
"""Independent pre-execution evidence gate for the 40-case OUT1 publisher.

This draft has never been imported or executed. Standard-library source only.
Literal publication expectations were frozen on 2026-10-02, before production C;
this gate uses the restored independent oracle and public fixture ABI, not the
new runner, its expected trace, labels, producer constants or execution results.
Common raw-capture/source/target sealing is adapted from the separately executed
program gate. No producer imports, subprocesses, hardware, decoder or firmware
execution. check_publish_report(report,capture_root=None,source_root=None)
returns (passed,detail). Raw capture mode seals original input, host/target rows,
all eleven capture pairs and the full 27,712-byte guarded recording storage.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

U32 = 0xffffffff
DEVICE = bytes.fromhex('1201000200000040feca0040000100000001')
# Audited literal contracts, independent of production constants and of the
# producer's imported trace-oracles.py. Row = kind, offset, logical word, result.
OUT_INITIAL = (
    (1,0x220,0x51,0),(2,0x220,0xa0,0),
    (1,0x22c,0x80,0),(2,0x22c,0x40,0),
    (1,0x508,0x100000c1,0),(2,0x508,0x020000c1,0),
    (1,0x418,0x00a700a7,0),(2,0x418,0x00a500a7,0),(3,U32,0,0))
IN_INITIAL = (
    (1,0x028,0x40,0),(1,0x020,0x51,0),(2,0x020,0xa0,0),
    (1,0x02c,0x80,0),(2,0x02c,0x40,0),
    (1,0x50c,0x100000d1,0),(2,0x50c,0x020000d1,0),
    (1,0x418,0x00a500a7,0),(2,0x418,0x00a500a5,0),(3,U32,0,0))
GRANT = ((1,0x404,0x34120320,0),(3,U32,0,0),(2,0x404,0x34122320,0),(3,U32,0,0))
INITIAL = OUT_INITIAL + IN_INITIAL
CAPTURE_NAMES = {'pixels':'pixels','wire':'wire','documents':'documents',
    'receive':'receive','output':'output','ep0':'output.ep0-descriptors',
    'bulk_descriptor':'output.udc-descriptor','setup_record':'output.setup-record',
    'program_reads':'output.program-read-script','program_trace':'output.program-trace',
    'program_storage':'output.program-storage'}
WIDTHS = (96,104,48,40,80,64,64)
KEYS = ('steps','ep0_steps','bulk_steps','setup_steps','offload_steps','program_steps','publish_steps')
INITIAL_KEYS = ('initial','initial_ep0','initial_bulk','initial_setup','initial_offload','initial_program','initial_publish')

# Frozen independent 2026-10-02 publication literals follow verbatim.
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



class EvidenceError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(words):
    return b''.join(v.to_bytes(4,'big') for v in words)


def flat(rows):
    return b''.join(packed(row) for row in rows)


def fnv(raw):
    value = 2166136261
    for byte in raw:
        value = ((value ^ byte)*16777619)&U32
    return value


def uints(row, size, where):
    need(isinstance(row,list) and len(row)==size and
         all(type(v) is int and 0<=v<=U32 for v in row), where+': expected unsigned words')


def sealed_file(root, name, digest, where):
    path = Path(name)
    need(not path.is_absolute() and '..' not in path.parts and path.as_posix()==name,
         where+': unsafe saved path '+str(name))
    need(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest), where+': malformed digest '+name)
    if root is not None:
        need(sha((root/path).read_bytes())==digest,where+': bytes differ '+name)


def decode_events(raw, where):
    events, at = [], 0
    while at < len(raw):
        need(len(raw)-at>=24,where+': truncated event header')
        *words, length = struct.unpack_from('>6I',raw,at)
        at += 24
        need(length<=1024 and len(raw)-at>=length,where+': bad input payload extent')
        events.append((words,raw[at:at+length])); at += length
    return events


def split_row(row):
    parts, at = [], 0
    for size in WIDTHS:
        parts.append(row[at:at+size]); at += size
    return parts


def wire_signature(base, ep0, offload):
    # Includes zero-length publication counters and descriptor/staging witnesses.
    return (base[17],base[24:26],offload[57],
        ep0[8+14:8+22],ep0[8+31:8+35],ep0[8+42],
        ep0[56+14:56+22],ep0[56+31:56+35],ep0[56+42])


def source_contract(report, capture, source):
    sources, fixtures = report['source_sha256'], report['fixture_sha256']
    required = {
        'scripts/validate-hp1020-udc-program.py','scripts/build-hp1020-udc-program-target.sh',
        'open-firmware/udc-program/hp1020_udc_program.c','open-firmware/udc-program/hp1020_udc_program.h',
        'open-firmware/udc-program-test/fixture.c','open-firmware/udc-program-test/host-check.c',
        'open-firmware/udc-program-test/target-check.ld','open-firmware/udc-program-test/trace-oracles.py',
        'open-firmware/udc-composed-test/fixture.c','open-firmware/tinyusb-printer-test/fixture.c',
        'open-firmware/udc-ep0-test/fixture.c','open-firmware/udc-offload-test/fixture.c',
        'open-firmware/tinyusb-device/patches/manifest.json',
        'open-firmware/tinyusb-device/patches/protocol-compatibility.patch',
        'scripts/validate-hp1020-udc-offload.py','scripts/validate-hp1020-udc-composed.py',
        'scripts/validate-hp1020-udc-ep0.py','scripts/validate-hp1020-tinyusb-printer.py',
        'scripts/hp1020_qemu_ram.py','scripts/check-hp1020-c-compiler-profile.py',
        'scripts/prepare-hp1020-tinyusb.py','analysis/sihp1020.elf',
        'vendor/tinyusb-0.21.0/src/device/usbd.c'}
    components = {'tinyusb-printer-adapter':['tusb_adapter'], 'udc-setup':['udc_setup'],
        'udc-ep0':['udc_ep0'],'udc-out':['udc_out'],'usb-printer-class':['usb_printer'],
        'usb-receive-core':['usb_receive','usb_document'],
        'image-core':['image','image_page','image_stream','image_ring','image_output'],
        'semantic-core':['semantic','page_plan']}
    required |= {
        'scripts/validate-hp1020-udc-publish.py','scripts/build-hp1020-udc-publish-target.sh',
        'open-firmware/udc-publish/hp1020_udc_publish.c','open-firmware/udc-publish/hp1020_udc_publish.h',
        'open-firmware/udc-publish-test/fixture.c','open-firmware/udc-publish-test/host-check.c',
        'open-firmware/udc-publish-test/target-check.ld','open-firmware/udc-publish-test/trace-oracles.py'}
    required |= {'open-firmware/'+directory+'/hp1020_'+stem+'.'+ext
        for directory,stems in components.items() for stem in stems for ext in ('c','h')}
    need(required<=sources.keys(),'source closure: required implementation/fixture/tool missing')
    for name,digest in sources.items():
        sealed_file(source,name,digest,'current source')
        if capture is not None: sealed_file(capture/'source',name,digest,'saved source')
    expected_fixtures = {
        'analysis/open-firmware-model/image-core/fixtures/32x8-stripe4-black.jbg',
        'analysis/open-firmware-model/image-core/fixtures/9600x132-stripe128-edges.jbg',
        'analysis/open-firmware-model/image-core/fixtures/16384x4-stripe128-edges.jbg',
        'analysis/open-firmware-model/image-core/output-fixtures/1024x260-stripe128-repeat.jbg',
        'analysis/open-firmware-model/image-core/output-fixtures/64x12-stripe4-edges.jbg',
        'analysis/samples/generated/matrix-a4_default.zjs'}
    need(set(fixtures)==expected_fixtures,'source closure: exact six document fixtures')
    for name,digest in fixtures.items():
        sealed_file(source,name,digest,'current fixture')
        if capture is not None: sealed_file(capture/'tested-fixtures',name,digest,'saved fixture')
    need(sources['analysis/sihp1020.elf']=='2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d',
         'source closure: original stock bytes changed')
    effective = report['effective_source']; manifest = effective['patch_manifest']
    prefix = 'open-firmware/tinyusb-device/patches/'
    need(effective['patched'] is True and effective['upstream_commit']==manifest['upstream_commit']==
         'dae3f9a366bfcddbf9dcf1b48d7500286a849539','effective source: pinned TinyUSB identity')
    need(manifest['patch_sha256']==sources[prefix+'protocol-compatibility.patch'],
         'effective source: patch identity')
    originals = {n[len('vendor/tinyusb-0.21.0/'):]:d for n,d in sources.items()
        if n.startswith('vendor/tinyusb-0.21.0/') and not n.endswith('/PROVENANCE.json')}
    need(len(originals)==19 and set(manifest['files'])=={'src/device/usbd.c','src/device/usbd_pvt.h'},
         'effective source: exact upstream closure')
    wanted = originals.copy()
    for name,item in manifest['files'].items():
        need(originals[name]==item['original_sha256'],'effective source: patch input '+name)
        wanted[name]=item['result_sha256']
    need(effective['effective_sha256']==wanted,'effective source: patched file hashes')
    for root in ([source] if source is not None else [])+([capture/'source'] if capture is not None else []):
        need(json.loads((root/(prefix+'manifest.json')).read_bytes())==manifest,'saved/current patch manifest')
    for ref in report['original_reference'].values():
        need(ref['newly_executed_stock_instructions']==0 and ref['stock_sha256']==sources['analysis/sihp1020.elf']
             and ref['report_sha256']==sources[ref['report']],'original reference: exact reused bytes/report')
    need(all(n in sources and d==sources[n] for n,d in report['offload_mode_evidence'].items()),
         'mode evidence: exact source binding')
    if capture is not None:
        need(json.loads((capture/'source-sha256.json').read_bytes())==sources,'saved source manifest')
        need(json.loads((capture/'fixture-sha256.json').read_bytes())==fixtures,'saved fixture manifest')


def expected_progress(base, setup, program, publish):
    # Public bridge contract: admitted-but-inactive actual reset alone may drain
    # despite a later held capture. No command bit constitutes that permission.
    if base[86] or base[2]!=setup[7] or setup[2]==2:
        ingress=0
    elif setup[8] and setup[7]==setup[8] and base[3]!=setup[8]:
        ingress=1
    elif setup[10] or setup[2]:
        ingress=0
    else:
        ingress=7
    backend=(ingress if ingress==1 else 0) if program[4] else (
        ingress&1 if not program[7] and base[8] else ingress)
    return ingress,backend,((backend&1 if ingress==1 else 0) if publish[6] else backend)


def profile_failure(name,slot):
    if name=='cleanup-original-cookie': name='desptr-write-uncertain'
    if name=='nak-still-set':
        result=dict(NAK_STILL_SET_FAILURE)
        result['trace']=NAK_STILL_SET
        result['reads']=supplied_reads(NAK_STILL_SET)
        return result
    if name in {v[0] for v in POST_BIND_FAILURES}:
        return post_bind_failure(name,slot)
    return None


def check_case(case,native,directory):
    name=case['scenario'].removeprefix('publish/'); fill=case['fill']; where=case['case']
    def ck(value,message): need(value,where+': '+message)
    ck('publish/'+name in PROFILE_NAMES and fill in (0,204) and
       case['capacity']==64 and case['interface']==0,'independent fixed profile')
    ck(where==f'publish/{name}/fill={fill}/capacity=64/interface=0','canonical case identity')
    ck(case['status']==native['status']=='pass' and native['case']==where,'paired case identity/status')
    for flag in ('all_steps_equal','all_pixels_wire_notifications_descriptors_and_storage_equal',
                 'typed_captures_original_cookies_and_grants_equal',
                 'complete_recorded_io_and_explicit_read_script_equal'):
        ck(native.get(flag) is True,'missing target comparison '+flag)
    events=case['events']; count=len(events)
    ck(count>0 and all(len(case[k])==count for k in KEYS),'parallel event/row lengths')
    old=[]
    for key,size in zip(INITIAL_KEYS,WIDTHS):
        uints(case[key],size,where+'/'+key); old.append(case[key])
    ck(old[0][32]==1 and old[5][1:8]==[1,0,0,0,0,0,0] and
       old[5][24:32]==[0,0,0,0,0,0,1,0] and old[6][1:7]==[1,0,0,0,0,0],
       'initial generation and fresh empty program/publisher')
    ck(old[5][57]>0 and old[6][58]>0 and old[6][36:43]==[1]*7,'measured sizes/initial supplied facts')
    raw_events=b''; reads=[]; trace=[]; cursor=0; injection=None
    facts=[1]*7; fact_index=register_index=read_failure_index=0
    all_fact_controls=fact_refusals(); all_register_controls=register_refusals()
    all_read_failures=preflight_read_failures()
    configurations=grants=failures=cleanups=successes=0
    expected_generation=expected_final_generation('publish/'+name)
    expected_configs=expected_generation-1
    is_failure=profile_failure(name,0) is not None
    first_failure=None; original_failure_cookie=None
    rx_attempts=descriptor_attempts=cache_checks=callbacks=0
    original_cookies={}; bulk_cookies={}; auto={}; offers={}; reset_tickets={}
    raw_offers={}; live_record=bytes([fill])*16; ingress_sequence=0
    generations=[]; publications=[]; ep0_owners={}; ep0_dma_writes=[]; ep0_observations=[]; wire_expected=b'\x01' if name=='progress-barriers' else b''
    wire=b''; query_fields=[0xa7a7a7a7]*4+[0xa7]+[0xa7a7a7a7]*5+[0xa7]*4
    receive=bytearray([fill]*4096); descriptor=bytearray([fill]*16)
    ep0_storage=bytearray([fill]*240)
    blocked_arms=direct_probes=forbidden_bypasses=0
    cleanup_results=set(); cleanup_mutations=set(); old_settlement_replays=0
    initial_reset_drain=0; preflight_arms=0
    for index,event in enumerate(events,1):
        words=event['words']; uints(words,5,where+f'/event{index}')
        data=bytes.fromhex(event['data_hex']); op,a,b,c,d=words
        ck(len(data)<=1024,'bounded raw input payload')
        raw_events+=packed(words+[len(data)])+data
        current=[case[k][index-1] for k in KEYS]
        for row,size in zip(current,WIDTHS): uints(row,size,where+f'/event{index}')
        r,e,u,s,o,p,q=current; pr,pe,pu,ps,po,pp,pq=old
        ck(r[0]==event['result'],'reported result differs from actual base row')
        ck(r[15:17]==[0,1] and e[2:5]==[0,1,1] and u[7:10]==[0,1,1] and
           s[12:15]==[0,1,3] and o[11:13]==[0,1] and p[1:4]==[1,0,0] and
           p[30:32]==[1,0] and q[1:6]==[1,0,0,0,0] and q[53]==q[63]==0,
           f'event{index} independent ownership/guard/closed-window witness')
        ck(p[4]==0 and not o[59] and r[86]==s[10]==0,'no unrelated programming fault/exhaustion')
        ck(p[57]==old[5][57] and q[58]==old[6][58],'fixed measured host component sizes')
        ck(r[80]==r[47]==0,'no manufactured printer class reset/deferred reply')
        ip,bp,qp=expected_progress(r,s,p,q)
        ck([s[11],p[8],q[7]]==[ip,bp,qp],'bridge/program/publication progress permissions')
        block=(); wanted_result=None; bound=False; failure=None; expected_prefix=None
        if op==120:
            ck(0<a<=85 and len(data)==12*a and b==c==d==0 and r[0]==0,'read script admission')
            rows=[list(struct.unpack_from('>3I',data,j)) for j in range(0,len(data),12)]
            ck(all(v[2]<=2 for v in rows),'read script outcome domain')
            reads.extend(rows)
        elif op in (121,131):
            ck(a in ((2,3) if op==121 else (4,5)) and c in (1,2) and b>len(trace) and
               b<=1024 and not d and not data and r[0]==0 and injection is None,
               'original future one-shot hook failure identity')
            injection=(a,b,c)
        elif op==130:
            ck(a==b==c==d==0 and len(data)==7 and r[0]==0,'raw seven publication facts')
            facts=list(data)
        ck(q[36:43]==facts,'publication facts preserved without truthiness normalization')
        # Exactly the existing INITIAL+GRANT setup, including reconnect. These
        # independently frozen program blocks are not extracted from trace output.
        if op==1 and p[26]>len(trace):
            ck(not pq[6] and pr[6]==3 and configurations<expected_configs,
               'only admitted typed configuration service may program endpoints')
            block=INITIAL; configurations+=1
        if op==124 and p[26]>len(trace):
            ck(not pq[6] and len(data)==5 and list(data)==[1]*5 and a in offers and
               b in auto and not c and not d,'one-shot original automatic status grant')
            ck(auto[b][1]==offers[a],'grant original event/cookie association')
            block=GRANT; grants+=1
        if op==6:
            # Prior state is the independent existing ownership/ingress contract;
            # a failed new publisher is not allowed to redefine its readiness.
            if pq[6]:
                # The composed ABI rejects before direct arm_out can return FAULT.
                wanted_result=1; blocked_arms+=1
            elif (ps[11]!=7 or pp[8]!=7 or not pp[7] or pu[2] or
                  pr[30] or pr[85] or not pr[8] or not pr[10] or pr[7] or pr[9] or
                  pr[36] or pr[44] or pr[81] or pr[82] or pr[35]>=4):
                wanted_result=1; blocked_arms+=1
            elif name=='preflight-facts' and fact_index<len(all_fact_controls):
                _,values,block,wanted_result=all_fact_controls[fact_index]
                ck(facts==list(values),'exact independently specified fact refusal ordering')
                fact_index+=1; preflight_arms+=1
            elif name=='preflight-registers' and register_index<len(all_register_controls):
                _,block,wanted_result=all_register_controls[register_index]
                register_index+=1; preflight_arms+=1
            elif name=='preflight-read-failures' and read_failure_index<len(all_read_failures):
                _,block,_,wanted_result=all_read_failures[read_failure_index]
                read_failure_index+=1; preflight_arms+=1
            else:
                slot=pr[33]%4
                ck(facts==([1,1,1,1,0,1,1] if name=='no-cnak-and-page' else [1]*7),
                   'full publication uses the independently supported fact profile')
                failure=profile_failure(name,slot) if is_failure and failures==0 else None
                block=failure['trace'] if failure else publication_trace(slot,name!='no-cnak-and-page')
                wanted_result=4 if failure else 0; bound=True
                expected_prefix=failure['prefix'] if failure else (3199 if name=='no-cnak-and-page' else 4095)
            ck(r[0]==wanted_result,f'event{index} independently expected arm result')
            if not bound:
                ck(r[2:96]==pr[2:96] and u==pu and o==po,
                   'refused arm changed owner, reservation, bytes, control, or output')
                if block:
                    _,offset,value,outcome=block[-1]
                    ck(q[18:22]==[offset,value if not outcome else 0,outcome,
                       int(name=='preflight-registers')],
                       'preflight diagnostic cannot invent a successful read value or packet cookie')
            else:
                slot=pr[33]%4; callbacks+=1
                cookie=[pr[21]+1,pr[5],pr[32],pr[33]+1,1]
                ck(pr[4]==pr[5] and cookie[0] not in original_cookies,'fresh original active transport identity')
                original_cookies[cookie[0]]=cookie; bulk_cookies[cookie[0]]=(cookie,slot)
                ck(r[17]==pr[17]+1 and r[21]==cookie[0] and r[30:32]==[cookie[0],64] and
                   r[33]==pr[33]+1 and r[34]==pr[34] and r[35]==pr[35]+1,
                   'one actual bind/reservation without fabricated payload delivery')
                ck(u[16:24]==cookie+[DESCRIPTOR_DMA,RECEIVE_DMA[slot],64] and
                   u[47]==q[62]==slot and (u[44]>>16)==1,'original DCD owner and actual selected slot')
                ck(q[14:18]==[pr[2],pr[4],pr[32],ps[4]] and q[45:50]==cookie,
                   'pre-fence callback identity versus independent adapter cache witness')
                ck(q[12:14]==([0xa55a0228,0x20] if name=='no-cnak-and-page' else [0x34120320,0x60])
                   and q[18:22]==[0x408,0x2a001 if name=='no-cnak-and-page' else 0xa001,0,0]
                   and q[61]==wanted_result and q[11]==0,
                   'exact preflight sample and genuine helper/descriptor result')
                descriptor[:]=packed(prepared_descriptor_words(slot))
                ck(u[24:28]==list(prepared_descriptor_words(slot)) and
                   q[8]==expected_prefix and q[54]==callbacks,'literal descriptor/prefix/genuine callback')
                ck(r[24:26]==pr[24:26] and r[50:59]==pr[50:59] and r[90:96]==pr[90:96] and
                   o[57]==po[57],'publication cannot receive, ACK, render, or notify')
                phase=failure['phase'] if failure else 2
                ck(u[2]==phase and u[10]==pu[10]+1,'retained descriptor phase and exact prepare count')
                exposed=int(phase==2)
                ck(u[11]==pu[11]+exposed,'take exposes once, independently of later write success')
                if exposed:
                    ck(u[28:33]==cookie and u[33:40]==list(prepared_descriptor_words(slot))+
                       [DESCRIPTOR_DMA,RECEIVE_DMA[slot],64],'actual conservative publication witness')
                if failure:
                    failures+=1; location=failure['location']
                    expected_failure=cookie+[failure['prefix'],location['offset'],location['attempted_value'],
                        location['dma'],location['bytes'],failure['operation'],failure['io_result'],
                        failure['exposed'],failure['out_result']]
                    ck(q[6]==1 and q[22:36]==expected_failure and r[7]==r[36]==1,
                       'exact first original-cookie failure and post-callback fence')
                    first_failure=expected_failure; original_failure_cookie=cookie
                else:
                    successes+=1
                    ck(q[6]==0 and r[7]==r[36]==0,'successful publication retains ordinary readiness')
        # A count is only a location witness. The complete attempted block is
        # fixed above and must match every independently supplied hook outcome.
        ck(p[26]-len(trace)==len(block),f'event{index} unexpected/missing exact I/O block')
        for kind,offset,value,outcome in block:
            ordinal=len(trace)+1
            if kind==1:
                ck(cursor<len(reads),f'event{index} unsupplied read')
                sample=reads[cursor]; cursor+=1
                ck(sample==[offset,value if not outcome else 0xd3a569c7,outcome],
                   f'event{index} independent read-script observation {offset:x}')
            else:
                supplied_outcome=0
                if injection is not None and injection[1]==ordinal:
                    ck(injection[0]==kind,'failure injection exact hook kind')
                    supplied_outcome=injection[2]; injection=None
                ck(outcome==supplied_outcome,'hook failure outcome from exact original injection')
            if kind==4: rx_attempts+=1; cache_checks+=1
            if kind==5: descriptor_attempts+=1; cache_checks+=1
            trace.append([index,ordinal,kind,offset,0 if kind==1 and outcome else value,outcome])
        ck(p[24:27]==[len(reads),cursor,len(trace)],'exact read queue/cursor and all-hook trace count')
        ck(p[27:30]==[sum(v[2]==k for v in trace) for k in (1,2,3)],'R/W/order counters exclude cache hooks')
        ck(q[50:53]==[rx_attempts,descriptor_attempts,cache_checks] and q[54]==callbacks,
           'exact cache range/owner witness counts')
        ck(p[35]==int(injection is not None),'failure schedule consumed exactly once')
        if injection is not None: ck(p[32:35]==list(injection),'unchanged original scheduled failure')
        # The source event/packet identities are captured before later failures
        # or reset. No expected cookie is read out of a cleanup diagnostic.
        if op in (81,83,100):
            ck(a==ingress_sequence+1,'single external ingress sequence without relabeling')
            ingress_sequence=a
        if op==80:
            ck(name=='progress-barriers' and data==bytes.fromhex('87ff7fffa5c33ca58008000000000100') and
               r[0]==0,'only specified ordinary GET_CONFIGURATION capture')
            live_record=data
        if op==81:
            ck(r[0]==0 and b==0x79bdf130 and c==d==0 and
               r[2:96]==pr[2:96] and s[22:26]==[a,b,0,0],'raw immutable capture without admission')
            raw_offers[a]=live_record
            ck(packed(s[32:36])==live_record,'exact retained raw capture')
        if op==82:
            ck(a in raw_offers and b==0x010101 and c==1 and d==0 and r[0]==0 and
               s[6]==a and r[2]==pr[2]+1,'dispatch exact raw capture with separate facts')
        if op==83:
            ck(r[0]==0 and b==c==d==0 and r[2]==pr[2]+1 and s[5]==a and s[8]==r[2],
               'actual original reset admission without fabricated settlement')
            ck(r[32:36]==pr[32:36] and p[5:7]==pp[5:7] and q[6]==pq[6],
               'reset cannot recover input or erase retained programming/publication history')
        if op==100:
            ck(r[0]==0 and not data and b==1 and c==0x10000 and not d and a not in offers,
               'only intended original typed configuration1 event')
            offers[a]=[a,1,1,0,0]
            ck(o[21:26]==offers[a] and r[2:96]==pr[2:96],'typed copy cannot dispatch or mutate transport')
        if op==101:
            ck(a in offers and b==0x01010101 and c==d==0 and r[0]==0 and s[6]==a and
               r[2]==pr[2]+1,'typed admission exact event and supplied profile')
        if o[6]!=po[6]:
            ck(op==1 and block==INITIAL and o[6]==po[6]+1 and o[26] in offers,'one real typed owner per configured callback')
            cookie=[pr[21]+1,r[3],r[32],0,0x80]
            ck(r[21]==cookie[0] and o[16:21]==cookie and o[26:31]==offers[o[26]],'automatic original owner identity')
            ck(cookie[0] not in original_cookies and o[13]==1 and o[32:35]==[1,0,1] and
               r[28:30]==[cookie[0],0] and r[77]==0,'automatic NULL/0 owner remains owned')
            ck(e[8:]==pe[8:] and r[24:26]==pr[24:26] and o[57]==po[57],
               'automatic owner creates no normal EP0 descriptor, bytes, or callback')
            original_cookies[cookie[0]]=cookie; auto[cookie[0]]=(cookie,offers[o[26]].copy())
        if o[13]: ck(o[16] in auto and o[16:21]==auto[o[16]][0],'retained auto owner cannot be retagged')
        if op==124:
            consumed=int(bool(block))
            ck(o[7]==po[7]+consumed and o[33]==po[33]+consumed,'one status permission per actual immediate write')
            ck(wire_signature(r,e,o)==wire_signature(pr,pe,po) and r[32:48]==pr[32:48] and
               r[90:96]==pr[90:96],'grant cannot fabricate ACK, packet, or recovery')
            if consumed:
                ck(o[37:42]==offers[a] and o[42:47]==auto[b][0] and o[13]==1 and r[28]==b,
                   'consumed original grant is not ownership settlement')
        else: ck(o[7]==po[7],'automatic permission changed outside backend grant')
        if op==10 and r[0]==0:
            reset_tickets[a]=pr[42:44]
        if op==11 and r[0]==0:
            ck(a in reset_tickets and reset_tickets[a]==pr[42:44] and b in (1,2,4) and
               r[45]==(pr[45]|b) and r[32]==pr[32],'current exact individual recovery promise')
        if r[32]!=pr[32]:
            ck(op==12 and r[0]==0 and r[32]==pr[32]+1 and a in reset_tickets and
               reset_tickets[a]==pr[42:44] and pr[44]==1 and pr[45]==7,
               'generation only advances after same three-promise recovery')
            generations.append(r[32])
            ck(r[17]==pr[17] and r[24:26]==pr[24:26] and o[57]==po[57],
               'generation restart cannot send an extra ACK')
        if op==132:
            ck(a==b==c==d==0 and not data and r[0]==(0 if pq[6] else 2),'pending failure query result')
            if pq[6]: query_fields=list(first_failure)
            ck(q[43]==r[0],'query diagnostic result')
        ck(q[44]==fnv(packed(query_fields)),'query exact canonical explicit fields; rejected output unchanged')
        if pq[6] and not (op==133 and r[0]==0):
            ck(q[6]==1 and q[22:36]==first_failure,'first failure retained across newer reset and refusals')
        if op==133:
            cleanup_results.add(r[0]); cleanup_mutations.add(b)
            ck(not block and r[32:48]==pr[32:48] and r[50:62]==pr[50:62] and
               r[90:96]==pr[90:96] and wire_signature(r,e,o)==wire_signature(pr,pe,po) and
               u[24:28]==pu[24:28],'cleanup changed accounting, recovery, storage, or traffic')
            expected=(3 if c>1 else 2 if not pq[6] or b or a not in original_cookies or
                      original_cookies[a]!=original_failure_cookie else 1 if not c or pu[2] or pu[44] or
                      pr[85] or pr[77] or not pr[7] or not pr[36] or pr[8] or pr[10] else 0)
            ck(r[0]==expected,'cleanup exact original identity, supplied boolean, and ownership prerequisites')
            if expected==0:
                cleanups+=1
                ck(pr[35]>0 and q[56:58]==[pr[35],pr[35]] and q[6]==0 and q[55]==cleanups and
                   q[22:36]==first_failure,'cleanup preserves nonzero fenced reservations and diagnostics')
            else: ck(q[55]==cleanups,'rejected cleanup counted as success')
        if op==134:
            direct_probes+=1
            ck(r[0]==3 and not block and q[59]==direct_probes and q[60]==1 and
               r[2:96]==pr[2:96] and u==pu and q[22:36]==pq[22:36],
               'outside-window callback acquired authority or changed poisoned output')
        if op in (14,60,61,102,106,107):
            forbidden_bypasses+=1
            ck(r[0]==3 and not block and r[2:96]==pr[2:96],'legacy bypass changed ownership or command sequence')
        if pq[6] and op in (1,7,8,9,12,41,123,124):
            if op==1 and ps[11]==1:
                initial_reset_drain+=1
                ck(not block,'actual reset drain cannot issue publication/programming commands')
            else:
                ck(r[0]==1 and not block and r[17]==pr[17] and r[24:26]==pr[24:26] and
                   r[50:59]==pr[50:59] and r[90:96]==pr[90:96],
                   'sticky failure allowed ordinary forward work')
        # Expected DMA writes use the ORIGINAL historical packet's fixed slot.
        # Completion observations do not implicitly mutate this live storage.
        if op==65 and r[0]==0:
            ck(a in bulk_cookies and pu[16]==a and pu[2]==2 and b in (0,1) and len(data)==d,
               'simulated DMA requires the actual original exposed packet')
            cookie,slot=bulk_cookies[a]
            extent=16 if b==0 else 64
            ck(c<=extent and d<=extent-c,'simulated DMA exact range')
            if b==0: descriptor[c:c+d]=data
            else: receive[slot*1024+c:slot*1024+c+d]=data
        if op in (62,64) and a in bulk_cookies:
            if d or a!=pu[16]:
                ck(r[0]==2 and u[2:7]==pu[2:7] and u[16:28]==pu[16:28] and
                   r[30:48]==pr[30:48],'old original observation/settlement altered current owner')
                old_settlement_replays+=1
            elif r[0]==0:
                ck(u[2]==0 and (u[44]>>16)==2 and r[30]==0,
                   'real supplied settlement retires component but retains adapter pending owner')
        ck(bytes(descriptor)==packed(u[24:28]) and live_record==packed(s[28:32]),'literal live descriptor/SETUP bytes')
        ck(r[60]==fnv(receive),'complete receive allocation differs from raw supplied writes')
        # Existing complete() explicitly writes the normal descriptor, then
        # offers an immutable observation with a separately supplied actual count.
        if op in (44,46):
            ck(name=='progress-barriers' and a in ep0_owners,'only specified ordinary EP0 owner')
            cookie,length=ep0_owners[a]; slot=int(cookie[4]==0x80)
            before=pe[8+48*slot:56+48*slot]
            raw_descriptor=packed([0x8800ffff if slot else 0x88000000,0,
                (0x3579bdf0,0xb68ace00)[slot],0])
            ck(before[0]==2 and before[6:11]==cookie and r[0]==0,
               'ordinary completion keeps original exposed packet identity')
            if op==46:
                ck(b==c==0 and d==16 and data==raw_descriptor,
                   'exact normal descriptor DMA write, never payload or IN-count inference')
                at=(16,48)[slot]; ep0_storage[at:at+16]=data
                ep0_dma_writes.append(slot)
            else:
                ck(b==0x01010101 and c==d==0 and data==raw_descriptor+packed([length]),
                   'immutable normal observation and separately supplied actual length')
                ep0_observations.append(slot)
        # Only one ordinary standard request is allowed in the whole matrix.
        for slot in (0,1):
            cur=e[8+48*slot:56+48*slot]; before=pe[8+48*slot:56+48*slot]
            token=cur[6]
            if token and token not in ep0_owners:
                ck(name=='progress-barriers','unexpected ordinary EP0 packet')
                length=1 if slot else 0
                cookie=[pr[21]+1,r[3],r[32],0,slot*128]
                ck(cur[6:11]==cookie and cur[5]==length and token not in original_cookies,
                   'ordinary reply original cookie and exact one-byte/status packet')
                original_cookies[token]=cookie; ep0_owners[token]=(cookie,length)
                dma=(0x3579bdf0,0xb68ace00)[slot]
                desc=packed([0x08000000|length,0,dma,0])
                at,payload_at=((16,80),(48,160))[slot]
                ep0_storage[at:at+16]=desc
                if length: ep0_storage[payload_at:payload_at+length]=b'\x01'
                ck(cur[46]==int(length==0),'ordinary status original NULL identity')
            if cur[32]!=before[32]:
                ck(cur[32]==before[32]+1 and cur[22] in ep0_owners,'exact ordinary publication')
                cookie,length=ep0_owners[cur[22]]
                ck(cur[22:27]==cookie and cur[27:31]==[(0x13579bd0,0xa468ace0)[slot],
                   (0x3579bdf0,0xb68ace00)[slot],length,64],'actual EP0 published pointers/cookie/span')
                publications.append((slot*128,length)); wire+=b'\x01' if length else b''
            at,payload_at=((16,80),(48,160))[slot]
            ck(ep0_storage[at:at+16]==packed(cur[14:18]) and
               fnv(ep0_storage[payload_at:payload_at+64])==cur[42],
               'complete independently retained EP0 descriptor and 64-byte tail')
        ck(r[24:26]==[len(wire),fnv(wire)],'actual wire bytes from original packet publications')
        old=current
    r,e,u,s,o,p,q=old
    ck(cursor==len(reads) and injection is None,'all supplied reads/fault schedules consumed')
    ck(configurations==grants==o[6]==expected_configs,'exact configuration and automatic permission count')
    ck(failures==cleanups==int(is_failure) and q[6]==0,'each original publication failure cleaned exactly once')
    ck(successes>0 and r[32]==expected_generation and generations==list(range(2,expected_generation+1)),
       'exact independent recovery generations and actual publications')
    ck((fact_index,register_index,read_failure_index)==
       (21 if name=='preflight-facts' else 0,33 if name=='preflight-registers' else 0,
        8 if name=='preflight-read-failures' else 0),'all intended preflight negative controls')
    if name=='progress-barriers': ck(blocked_arms>=3,'before configure, recovery, and known held-capture arm refusals')
    if name=='callback-authority': ck(direct_probes>=12 and forbidden_bypasses>=3,'direct/held duplicate authority and bypass controls')
    if name=='cleanup-original-cookie':
        ck({0,1,2,3}<=cleanup_results and set(range(6))<=cleanup_mutations,
           'cleanup missing/malformed/stale/owned/original-success controls')
    if name=='cancel-and-descriptor-reuse':
        ck(old_settlement_replays>0 and len({v[0][2] for v in bulk_cookies.values()})==2,
           'old-generation original-cookie replay after actual descriptor reuse')
    if is_failure: ck(initial_reset_drain>0,'failed publisher retained while actual reset drained')
    ck(ep0_dma_writes==ep0_observations==([1,0] if name=='progress-barriers' else []),
       'exact separate IN/OUT descriptor DMA and immutable completion observations')
    expected_publications=[(0x80,1),(0,0)] if name=='progress-barriers' else []
    ck(publications==expected_publications and wire==wire_expected and
       o[57]==int(name=='progress-barriers'),'exact ordinary packets and genuine TinyUSB callback')
    ck([bytes.fromhex(v['expected_hex']) for v in case['packet_oracles']]==
       ([b'\x01'] if name=='progress-barriers' else []),'ordinary packet byte oracle is independently fixed')
    pixels=b'\xff'*32; documents=[[expected_generation,1,0,1,0]]
    ck(case['pixels_bytes']==32 and case['expected_pixels_sha256']==sha(pixels) and
       case['expected_documents']==documents,'independent exact black page and END_DOC oracle')
    ck(r[50:52]==[32,fnv(pixels)] and r[90:93]==[1,1,1] and r[56:59]==[1,1,1] and
       r[35]==0 and r[33]==r[34] and u[2]==0 and r[40]==0,
       'exact completed software page/document without input EOF or unfinished receive')
    trace_raw,reads_raw=flat(trace),flat(reads)
    ck(case['expected_program_trace']==trace and case['supplied_reads']==reads,
       'untrusted trace/read summaries differ from independent rebuild')
    ck(len(reads)<=256 and len(trace)<=1024,'fixed trace/read allocation bounds')
    guard=bytes([fill])*16
    storage=guard+reads_raw+bytes([fill])*(3072-len(reads_raw))+guard
    storage+=guard+trace_raw+bytes([fill])*(24576-len(trace_raw))+guard
    expected={'pixels':pixels,'wire':wire,'documents':flat(documents),'receive':bytes(receive),
        'ep0':bytes(ep0_storage),'bulk_descriptor':guard+bytes(descriptor)+guard,
        'setup_record':guard+live_record+guard,'program_reads':reads_raw,
        'program_trace':trace_raw,'program_storage':storage}
    captures=case['capture_sha256']
    ck(set(captures)==set(CAPTURE_NAMES) and native['capture_sha256']==captures,'eleven paired capture closure')
    for key,raw in expected.items(): ck(captures[key]==sha(raw),'independent complete capture digest '+key)
    if directory is not None:
        ck((directory/'case-name').read_text().strip()==where,'saved case name')
        raw=(directory/'events.bin').read_bytes()
        ck(raw==raw_events and decode_events(raw,where)==[(v['words'],bytes.fromhex(v['data_hex'])) for v in events],
           'raw original input framing/bytes versus report')
        observed=[json.loads(line) for line in (directory/'raw-stdout').read_bytes().splitlines()]
        host_rows=[sum([case[k] for k in INITIAL_KEYS],[])]+[
            sum([case[k][i] for k in KEYS],[]) for i in range(count)]
        ck(observed==host_rows,'raw host initial/event rows versus report')
        target_rows=[json.loads(line) for line in (directory/'target-steps.jsonl').read_bytes().splitlines()]
        ck(len(target_rows)==count,'target raw row count')
        for event_index,(actual,wanted) in enumerate(zip(target_rows,host_rows[1:]),1):
            uints(actual,496,where+f'/target{event_index}')
            ck(all(v==wanted[j] for j,v in enumerate(actual) if j not in (59,425,490)),
               f'target event{event_index} differs outside three measured size words')
            ck(actual[59]==native['adapter_state_and_memory_bytes'] and
               actual[425]==native['component_and_allocation_bytes']['program'] and
               actual[490]==native['component_and_allocation_bytes']['publisher'],
               'three target measured footprint bindings')
        raw_captures={}
        for key,path in CAPTURE_NAMES.items():
            raw=(directory/path).read_bytes(); raw_captures[key]=raw
            ck(sha(raw)==captures[key],f'raw host capture hash {key}')
            ck((directory/('target-'+key)).read_bytes()==raw,f'raw target capture {key}')
            if key in expected: ck(raw==expected[key],f'raw independently expected full bytes {key}')
        ck(fnv(raw_captures['output'])==r[61],'full retained output allocation witness')
    return count


def validate_publish_report(report, capture_root=None, source_root=None):
    """Raise EvidenceError with one precise reason; no subprocesses or imports."""
    capture=Path(capture_root) if capture_root is not None else None
    source=Path(source_root) if source_root is not None else None
    need(report['status']=='pass' and report['target']['status']=='pass','paired host/target status required')
    for key in ('hp_dynamic_csr_capability_established','automatic_grants_are_acknowledgments','controller_quiescence_established'):
        need(report.get(key) is False,'must not claim hardware proof: '+key)
    for key in ('completed_native_page_lifecycles','usb_transfers','actual_peripheral_accesses'):
        need(type(report.get(key)) is int and report[key]==0,'must remain zero: '+key)
    source_contract(report,capture,source)
    cases=report['cases']; target=report['target']; natives=target['cases']
    need(len(cases)==len(natives)==40,'exact 40-case paired matrix')
    seen=set(); total=0
    for i,(case,native) in enumerate(zip(cases,natives)):
        pair=(case['scenario'].removeprefix('publish/'),case['fill'])
        need(pair not in seen,'duplicate profile/fill'); seen.add(pair)
        total+=check_case(case,native,None if capture is None else capture/f'case-{i:03}')
    need(seen=={(name,fill) for name in (v.removeprefix('publish/') for v in PROFILE_NAMES) for fill in (0,204)},'missing/extra profile/fill')
    artifacts=target['captured_artifact_sha256']
    need({'target-check.elf','target-check.map','effective-source.json','disassembly.txt','symbols.txt','annotated-disassembly.txt'}<=artifacts.keys(),
         'exact target artifact closure')
    need(target['elf_sha256']==artifacts['target-check.elf'] and target.get('audit'),'target ELF/audit binding')
    for name,digest in artifacts.items():
        need(Path(name).name==name,'target artifact must be a basename')
        sealed_file(None,name,digest,'target artifact')
        if capture is not None: sealed_file(capture/'target',name,digest,'saved target artifact')
        if source is not None and name!='annotated-disassembly.txt':
            sealed_file(source/'analysis/usb-path/udc-publish/target',name,digest,'current target artifact')
    for root in ([capture/'target'] if capture is not None else [])+(
            [source/'analysis/usb-path/udc-publish/target'] if source is not None else []):
        need(json.loads((root/'effective-source.json').read_bytes())==report['effective_source'],'target effective source exact equality')
    sizes=[n['component_and_allocation_bytes'] for n in natives]
    need(all(s==sizes[0] for s in sizes) and sizes[0]['ep0']==296 and sizes[0]['bulk']==80
         and sizes[0]['setup']==96 and type(sizes[0]['program']) is int and sizes[0]['program']>0 and type(sizes[0]['publisher']) is int
         and sizes[0]['publisher']>0 and report['target_publisher_bytes']==sizes[0]['publisher'],
         'consistent separately measured fixed target components')
    if capture is not None:
        need(json.loads((capture/'validation.json').read_bytes())==report,'saved report exact equality')
        need(json.loads((capture/'target-sha256.json').read_bytes())==artifacts,'saved target manifest')
    return f'40 paired cases; {total} raw event rows; independent publication/pixel/original-owner/cleanup contracts'+(
        '; raw captures sealed' if capture is not None else '; report-only capture digests checked')


def check_publish_report(report, capture_root=None, source_root=None):
    try:
        return True,validate_publish_report(report,capture_root,source_root)
    except (EvidenceError,KeyError,TypeError,ValueError,IndexError,OSError,OverflowError) as error:
        return False,str(error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--capture-root',type=Path)
    parser.add_argument('--source-root',type=Path)
    args=parser.parse_args()
    passed,detail=check_publish_report(json.loads(args.report.read_bytes()),args.capture_root,args.source_root)
    print(('PASS: ' if passed else 'FAIL: ')+detail)
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
