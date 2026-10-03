#!/usr/bin/env python3
"""Independent pre-execution evidence gate for the 32-case OUT1 acquisition.

Unexecuted draft: no candidate imports, builds, tests or run-result inspection.
The exact acquisition oracle below was frozen before production C was read.
Publication literals and common sealing come from the unchanged independent V2
publication gate. The new producer's expected traces/labels/results are not an
oracle. check_acquire_report(report,capture_root=None,source_root=None) returns
(passed,detail). Standard library only; no subprocesses or hardware operations.
Raw mode checks original input and paired 576-word rows, twelve capture pairs,
whole device-image/receive/descriptor storage and guarded recording storage.
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
    'program_storage':'output.program-storage','acquire_device':'output.acquire-device'}
WIDTHS = (96,104,48,40,80,64,64,80)
KEYS = ('steps','ep0_steps','bulk_steps','setup_steps','offload_steps','program_steps','publish_steps','acquire_steps')
INITIAL_KEYS = ('initial','initial_ep0','initial_bulk','initial_setup','initial_offload','initial_program','initial_publish','initial_acquire')

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
    required |= {
        'scripts/validate-hp1020-udc-acquire.py','scripts/build-hp1020-udc-acquire-target.sh',
        'scripts/check-hp1020-udc-acquire.py','open-firmware/udc-out/hp1020_udc_acquire.h',
        'open-firmware/udc-acquire-test/fixture.c','open-firmware/udc-acquire-test/host-check.c',
        'open-firmware/udc-acquire-test/target-check.ld','open-firmware/udc-acquire-test/trace-oracles.py'}
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
    need(fixtures['analysis/open-firmware-model/image-core/fixtures/32x8-stripe4-black.jbg']==
         '78744d4c1f1f3ac06000192663330834b02b277df26f790aaa340ac322e9cf99' and
         fixtures['analysis/samples/generated/matrix-a4_default.zjs']==
         '8c6aa75a8c967897e72673e585c8ae862004e6e1c2b22118943ead4070e96206',
         'fixed independent small document inputs')
    need(sources['open-firmware/udc-acquire-test/trace-oracles.py']==
         '06160580c3ecce51f36731be7c3a0ca7097769ee8b2543f1ad715e6d5bddea25',
         'exact pre-implementation acquisition oracle bytes')
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
    if capture is not None:
        effective_root=capture/'effective-source'
        for name,digest in wanted.items():
            sealed_file(effective_root,name,digest,'saved effective source')
        need(json.loads((effective_root/'effective-source.json').read_bytes())==effective,
             'saved effective source manifest exact equality')
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


"""UNEXECUTED independent acquisition expectations; no production imports.

Derived from the pre-implementation boundary review, existing OUT/adapter
contracts, fixed fixture allocations and the public acquisition header only.
The new acquisition C implementation has not been read. Opcode allocation and
appended diagnostic positions remain a lead-owned fixture integration decision.
"""

OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR = range(6)
DESCRIPTOR_CPU, PAYLOAD_CPU, ACQUIRE_ORDER = 6, 7, 8
IO_OK, NOT_PERFORMED, UNKNOWN = 0, 1, 2
DESCRIPTOR_DMA = 0x579bdf10
RECEIVE_DMAS = (0x24681340, 0x24682340, 0x24683340, 0x24684340)
REASON_IO = 0x80000103
DEFAULT_FACTS = bytes((1, 1, 1))
GET_CONFIGURATION = bytes.fromhex('8008000000000100')
EXPECTED_BLACK_PIXELS = bytes.fromhex('ff' * 32)
SMALL_BIE = bytes.fromhex('000001000000002000000008000000041000035cfd98ff02ff02')
SMALL_BIE_SHA256 = '78744d4c1f1f3ac06000192663330834b02b277df26f790aaa340ac322e9cf99'


def be32(value):
    assert type(value) is int and 0 <= value <= 0xffffffff
    return value.to_bytes(4, 'big')


def words(values):
    return b''.join(be32(value) for value in values)


def slot_dma(slot):
    assert type(slot) is int and 0 <= slot < 4
    return RECEIVE_DMAS[slot]


def literal_descriptor(slot, count, *, done=True):
    """Only DONE and explicit not-DONE controls; not a descriptor decoder."""
    assert type(count) is int and 0 <= count <= 64
    status = (0x88000000 if done else 0x48000000) | count
    return words((status, 0, slot_dma(slot), 0))


def cpu_poison(slot, *, false_done=False):
    """Synthetic fixture writes to descriptor16 and this prefix64 ONLY."""
    dma = slot_dma(slot)
    descriptor = (words((0x88000040, 0, dma, 0)) if false_done else
        words((0xc35a0000 | slot, 0x13579bdf, 0xfedcba90, 0x2468ace0)))
    payload = bytes((0xd3 ^ (slot * 0x29) ^ (i * 0x17)) & 255 for i in range(64))
    return descriptor, payload


def device_images(slot, payload, *, done=True):
    """Input bytes are authoritative, never reconstructed from acquired RAM.

    Every unused byte in the owned64-byte prefix is deliberately nonzero and
    independent of fill. It is acquired but must not be passed to the parser.
    """
    assert isinstance(payload, bytes) and len(payload) <= 64
    tail = bytes((0x69 ^ (slot * 0x1d) ^ (i * 7)) & 255
                 for i in range(len(payload), 64))
    return literal_descriptor(slot, len(payload), done=done), payload + tail


def acquire_trace(slot, *, fail_kind=None, outcome=NOT_PERFORMED):
    """Literal (kind,DMA,length,result) prefix, before event/ordinal tagging."""
    full = ((DESCRIPTOR_CPU, DESCRIPTOR_DMA, 16, IO_OK),
            (PAYLOAD_CPU, slot_dma(slot), 64, IO_OK),
            (ACQUIRE_ORDER, 0, 0, IO_OK))
    if fail_kind is None:
        return full
    assert fail_kind in (DESCRIPTOR_CPU, PAYLOAD_CPU, ACQUIRE_ORDER)
    assert type(outcome) is int and 0 < outcome <= 0xffffffff
    result = []
    for kind, dma, length, _ in full:
        result.append((kind, dma, length, outcome if kind == fail_kind else IO_OK))
        if kind == fail_kind:
            break
    return tuple(result)


def event_trace(event, prior_ordinal, trace):
    assert event > 0 and prior_ordinal >= 0
    return tuple((event, prior_ordinal+i+1, *row) for i, row in enumerate(trace))


def expected_visibility(slot, device_descriptor, device_payload, *,
                        false_done=False, fail_kind=None, outcome=NOT_PERFORMED):
    """Fixture hook effect oracle, not a physical cache implementation.

    OK copies exactly one owned range. NOT_PERFORMED copies none. UNKNOWN
    copies exactly its first half, chosen explicitly by this test. Order has
    no byte effect. Invalid raw outcomes have no byte effect in this fixture.
    """
    assert len(device_descriptor) == 16 and len(device_payload) == 64
    descriptor, payload = cpu_poison(slot, false_done=false_done)
    for kind, _, _, result in acquire_trace(slot, fail_kind=fail_kind, outcome=outcome):
        if kind == DESCRIPTOR_CPU:
            if result == IO_OK:
                descriptor = device_descriptor
            elif result == UNKNOWN:
                descriptor = device_descriptor[:8] + descriptor[8:]
        elif kind == PAYLOAD_CPU:
            if result == IO_OK:
                payload = device_payload
            elif result == UNKNOWN:
                payload = device_payload[:32] + payload[32:]
    return descriptor, payload


def failure_fields(cookie, slot, kind, outcome):
    """Fields independent of implementation output; cookie from DCD history."""
    assert len(cookie) == 5 and cookie[0] and cookie[4] == 1
    assert kind in (DESCRIPTOR_CPU, PAYLOAD_CPU, ACQUIRE_ORDER)
    assert outcome != IO_OK
    prefix, dma, length, operation = {
        DESCRIPTOR_CPU: (0, DESCRIPTOR_DMA, 16, 1),
        PAYLOAD_CPU: (1, slot_dma(slot), 64, 2),
        ACQUIRE_ORDER: (3, 0, 0, 3),
    }[kind]
    return dict(cookie=list(cookie), prefix=prefix, dma=dma, bytes=length,
                io_result=outcome, reason=REASON_IO, operation=operation,
                snapshot_valid=0)


def captured_fields(cookie, descriptor, result):
    assert len(cookie) == 5 and cookie[0] and cookie[4] == 1
    assert len(descriptor) == 16 and result in (OK, WAIT, FAULT, ADAPTER_ERROR)
    return dict(cookie=list(cookie), prefix=15, dma=0, bytes=0, io_result=0,
                operation=3, snapshot_valid=1, snapshot_hex=descriptor.hex(),
                result=result)


def document_event(generation):
    """One successfully notified document with one page; explicit BE words."""
    assert generation >= 2
    return words((generation, 1, 0, 1, 0))


def fact_probes():
    result = []
    for index, name in enumerate(('transfer-settled', 'mapping-lease', 'cache-range-safe')):
        for value, expected in ((0, WAIT), (2, INVALID), (255, INVALID)):
            facts = bytearray(DEFAULT_FACTS)
            facts[index] = value
            result.append((name+'/'+str(value), bytes(facts), expected))
    return tuple(result)


def mutated_cookie(cookie, mutation):
    assert len(cookie) == 5 and 1 <= mutation <= 5
    result = list(cookie)
    result[mutation-1] ^= 0x80 if mutation == 5 else 0x80000000
    return tuple(result)


# Named semantic profiles, not another cross-product descriptor-policy matrix.
# Entries contain expected generation of the sole completed small document.
POSITIVE_AND_GUARD_PROFILES = (
    ('visibility-packets', 2),
    ('facts-and-identities', 2),
    ('callback-authority', 2),
    ('held-setup-settlement', 2),
    ('admitted-reset-settlement', 3),
    ('same-address-reuse', 3),
    ('prepared-publication-failure', 3),
    ('exposed-publication-failure', 3),
    ('endpoint-fault-only', 3),
    ('not-done-fresh-retry', 2),
)
HOOK_FAILURE_PROFILES = (
    ('descriptor-not-performed', DESCRIPTOR_CPU, NOT_PERFORMED),
    ('descriptor-unknown', DESCRIPTOR_CPU, UNKNOWN),
    ('payload-not-performed', PAYLOAD_CPU, NOT_PERFORMED),
    ('payload-unknown', PAYLOAD_CPU, UNKNOWN),
    ('order-not-performed', ACQUIRE_ORDER, NOT_PERFORMED),
    ('order-unknown', ACQUIRE_ORDER, UNKNOWN),
)


def profiles():
    names = [name for name, _ in POSITIVE_AND_GUARD_PROFILES]
    names += [name for name, _, _ in HOOK_FAILURE_PROFILES]
    return [('acquire/'+name, fill, 64, 0) for name in names for fill in (0, 204)]


def expected_generation(name):
    short = name.removeprefix('acquire/')
    for title, generation in POSITIVE_AND_GUARD_PROFILES:
        if title == short:
            return generation
    assert short in [title for title, _, _ in HOOK_FAILURE_PROFILES]
    return 3


def small_document():
    """Independent fixed ZjStream from original saved sample headers and BIE.

    Header/item literals are byte-derived from pinned matrix-a4_default.zjs,
    with width32,height8,BPP1 substitutions. No producer/decoder is imported.
    """
    def chunk(kind,payload=b'',count=0,reserved=0):
        return struct.pack('>IIIHH',16+len(payload),kind,count,reserved,0x5a5a)+payload
    def item(ident,value):
        return struct.pack('>IHBBI',12,ident,1,0,value)
    start=b''.join(item(i,v) for i,v in ((1,0),(2,1),(0,0)))
    page=b''.join(item(i,v) for i,v in ((23,0),(17,16),(18,8),(16,2),
        (12,32),(13,8),(7,1),(8,600),(9,600),(5,7),(4,1),(3,9),(6,1)))
    coded=SMALL_BIE[20:]+bytes(16+((-len(SMALL_BIE[20:]))&3))
    return b'JZJZ'+chunk(0,start,3,36)+chunk(2,page,13,156)+chunk(4,SMALL_BIE[:20])+\
        chunk(5,coded)+chunk(6)+chunk(3)+chunk(1)


def diagnostic_words(cookie,prefix=0,dma=0,length=0,io=0,reason=0,result=0,
                     operation=0,snapshot=None):
    raw=bytes(16) if snapshot is None else snapshot
    need(len(raw)==16,'independent acquisition snapshot extent')
    return list(cookie)+[prefix,dma,length,io,reason,result,operation,int(snapshot is not None)]+\
        list(struct.unpack('>4I',raw))


def acquisition_publication_failure(name,slot):
    if name=='prepared-publication-failure': return post_bind_failure('rx-cache-failure',slot)
    if name=='exposed-publication-failure': return post_bind_failure('desptr-write-uncertain',slot)
    return None


def check_case(case,native,directory):
    name=case['scenario'].removeprefix('acquire/'); fill=case['fill']; where=case['case']
    def ck(value,message): need(value,where+': '+message)
    ck((case['scenario'],fill,case['capacity'],case['interface']) in profiles(),
       'independent fixed acquisition profile')
    ck(where==f'acquire/{name}/fill={fill}/capacity=64/interface=0','canonical case identity')
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
       'initial generation and fresh program/publisher')
    ck(old[0][2:6]==[0,0,1,1] and old[0][17]==old[0][21]==0 and
       old[0][33:36]==[0,0,0] and old[2][2]==0 and old[2][16:21]==[0]*5,
       'initial identities and empty receive ownership')
    initial=old[7]
    ck(initial[0:11]==[0,1,0,0,0,0,0,0,1,0,0] and initial[11:14]==[0x010101,U32,U32]
       and initial[14:59]==[0]*45 and initial[60:69]==[0,0,U32,1]+[0]*5
       and initial[73:77]==[0]*4,
       'fresh first-use acquisition context and empty immutable diagnostics')
    ck(old[5][57]>0 and old[6][58]>0 and initial[59]>0,'measured host component sizes')
    raw_events=b''; reads=[]; trace=[]; cursor=0; injection=None
    publish_facts=[1]*7; facts=[1]*3
    configurations=grants=pub_failures=cleanups=publications_ok=0
    final_generation=expected_generation('acquire/'+name); expected_configs=final_generation-1
    rx_attempts=descriptor_attempts=cache_checks=callbacks=0
    hook_calls=[0,0,0]; image_writes=image_refusals=packet_calls=accepted=faults=stales=0
    latest_result=0; latest_image=None; latest_hook_cookie=[0]*5
    last=[0]*17; first=[0]*17; failure_valid=0
    original_cookies={}; bulk_cookies={}; auto={}; offers={}; reset_tickets={}; images={}
    original_failure_cookie=None; publication_failure=None; live_record=bytes([fill])*16
    raw_offers={}; raw_dispatch_waits=set(); raw_admissions=set()
    ingress_sequence=0; generations=[]; ep0_owners={}
    ep0_dma_writes=[]; ep0_observations=[]; ep0_publications=[]; wire=b''
    receive=bytearray([fill]*4096); descriptor=bytearray([fill]*16)
    ep0_storage=bytearray([fill]*240); device_storage=bytearray([fill]*144)
    query_fields=[0xa7a7a7a7]*4+[0xa7]+[0xa7a7a7a7]*5+[0xa7]*4
    small=small_document(); accepted_streams={}; used_slots=set(); accepted_lengths=[]
    expected_failure_vector=next(((kind,outcome) for title,kind,outcome in HOOK_FAILURE_PROFILES if title==name),None)
    hook_failures=endpoint_fault_calls=not_done_calls=fresh_retry_calls=0
    fact_controls=set(); cookie_controls=set(); refused_images=set(); disabled_controls=set()
    late_observations=late_cancels=held_accepts=reset_accepts=pub_blocked_accepts=0
    prepared_refusals=forward_blocks=reset_drains=0; fault_retry_calls=0
    for index,event in enumerate(events,1):
        words=event['words']; uints(words,5,where+f'/event{index}')
        data=bytes.fromhex(event['data_hex']); op,a,b,c,d=words
        ck(len(data)<=1024,'bounded raw input payload')
        raw_events+=packed(words+[len(data)])+data
        current=[case[k][index-1] for k in KEYS]
        for row,size in zip(current,WIDTHS): uints(row,size,where+f'/event{index}')
        r,e,u,s,o,p,q,x=current; pr,pe,pu,ps,po,pp,pq,px=old
        ck(r[0]==event['result'],'reported result differs from actual base row')
        ck(r[15:17]==[0,1] and e[2:5]==[0,1,1] and u[7:10]==[0,1,1] and
           s[12:15]==[0,1,3] and o[11:13]==[0,1] and p[1:4]==[1,0,0] and
           p[30:32]==[1,0] and q[1:6]==[1,0,0,0,0] and q[53]==q[63]==0 and
           x[1]==1 and x[7:9]==[0,1] and x[63]==1 and x[73:77]==[0]*4 and x[79]==0,
           f'event{index} independent ownership, guard, unchanged-probe and closed-window witnesses')
        ck(p[4]==0 and not o[59] and r[86]==s[10]==0,'no unrelated programming fault/exhaustion')
        ck(p[57]==pp[57] and q[58]==pq[58] and x[59]==px[59],'fixed measured host sizes')
        ck(r[80]==r[47]==0,'no fabricated class reset/deferred reply')
        ip,bp,qp=expected_progress(r,s,p,q)
        ck([s[11],p[8],q[7]]==[ip,bp,qp],'bridge/program/publication progress permissions')
        block=(); bound=False; publication_error=None
        if op==120:
            ck(0<a<=85 and len(data)==12*a and b==c==d==0 and r[0]==0,'read script admission')
            rows=[list(struct.unpack_from('>3I',data,j)) for j in range(0,len(data),12)]
            ck(all(v[2]<=2 for v in rows),'read script outcome domain'); reads.extend(rows)
        elif op in (121,131,143):
            allowed=(2,3) if op==121 else (4,5) if op==131 else (6,7,8)
            ck(a in allowed and c in (1,2) and len(trace)<b<=1024 and not d and not data
               and injection is None and r[0]==0,'original future one-shot failure schedule')
            injection=(a,b,c)
        elif op==130:
            ck(a==b==c==d==0 and data==bytes([1]*7) and r[0]==0,'fixed publication lease facts')
            publish_facts=list(data)
        elif op==141:
            ck(a==b==c==d==0 and len(data)==3 and r[0]==0,'raw three acquisition facts')
            facts=list(data)
        ck(q[36:43]==publish_facts and x[11]==int.from_bytes(bytes(facts),'big'),
           'raw fact bytes retained without normalization')
        if op==1 and p[26]>len(trace):
            ck(not pq[6] and pr[6]==3 and configurations<expected_configs,
               'only current typed configuration service programs endpoints')
            block=INITIAL; configurations+=1
        if op==124 and p[26]>len(trace):
            ck(not pq[6] and data==bytes([1]*5) and a in offers and b in auto and c==d==0,
               'one-shot original automatic status grant')
            ck(auto[b][1]==offers[a],'grant original event/cookie association')
            block=GRANT; grants+=1
        if op==6:
            blocked=(pq[6] or ps[11]!=7 or pp[8]!=7 or not pp[7] or pu[2] or pr[30] or
                pr[85] or not pr[8] or not pr[10] or pr[7] or pr[9] or pr[36] or pr[44] or
                pr[81] or pr[82] or pr[35]>=4)
            if blocked:
                ck(r[0]==WAIT and r[2:96]==pr[2:96] and u==pu and o==po,
                   'refused forward arm changed original ownership/accounting'); forward_blocks+=1
            else:
                slot=pr[33]%4; callbacks+=1; used_slots.add(slot)
                publication_error=acquisition_publication_failure(name,slot) if not pub_failures else None
                block=publication_error['trace'] if publication_error else publication_trace(slot,True)
                expected_result=FAULT if publication_error else OK
                ck(r[0]==expected_result,'independent publication result')
                cookie=[pr[21]+1,pr[5],pr[32],pr[33]+1,1]
                ck(pr[4]==pr[5] and cookie[0] not in original_cookies,'new actual active transport cookie')
                original_cookies[cookie[0]]=cookie
                bulk_cookies[cookie[0]]=(cookie,slot,len(accepted_streams.get(cookie[2],b'')))
                ck(r[17]==pr[17]+1 and r[21]==cookie[0] and r[30:32]==[cookie[0],64] and
                   r[33]==pr[33]+1 and r[34]==pr[34] and r[35]==pr[35]+1,
                   'single actual bind/reservation without manufactured completion')
                ck(u[16:24]==cookie+[DESCRIPTOR_DMA,RECEIVE_DMAS[slot],64] and
                   u[47]==q[62]==slot and (u[44]>>16)==1,'original DCD owner and selected queue prefix')
                ck(q[14:18]==[pr[2],pr[4],pr[32],ps[4]] and q[45:50]==cookie,
                   'publication cache witness uses pre-fence original owner')
                descriptor[:]=packed(prepared_descriptor_words(slot))
                phase=publication_error['phase'] if publication_error else 2
                prefix=publication_error['prefix'] if publication_error else 4095
                ck(u[2]==phase and u[10]==pu[10]+1 and u[11]==pu[11]+int(phase==2) and
                   u[24:28]==list(prepared_descriptor_words(slot)) and q[8]==prefix and
                   q[61]==expected_result and q[11]==0,'literal descriptor/exposure/prefix')
                if phase==2:
                    ck(u[28:33]==cookie and u[33:40]==list(prepared_descriptor_words(slot))+
                       [DESCRIPTOR_DMA,RECEIVE_DMAS[slot],64],'actual conservative publication witness')
                if publication_error:
                    pub_failures+=1; v=publication_error; loc=v['location']
                    publication_failure=cookie+[v['prefix'],loc['offset'],loc['attempted_value'],
                        loc['dma'],loc['bytes'],v['operation'],v['io_result'],v['exposed'],v['out_result']]
                    original_failure_cookie=cookie
                    ck(q[6]==1 and q[22:36]==publication_failure and r[7]==r[36]==1,
                       'original publication failure remains distinct from acquisition')
                else:
                    publications_ok+=1; ck(q[6]==0 and r[7]==r[36]==0,'healthy publication readiness')
                ck(r[24:26]==pr[24:26] and r[50:59]==pr[50:59] and r[90:96]==pr[90:96],
                   'publication cannot parse pixels or notify a document')
                bound=True
        if op==140:
            ck(len(data)==80 and b in (0,1) and c==d==0,'literal device-image envelope')
            current_owner=(a in bulk_cookies and pu[16]==a and (pu[44]>>16)==1 and pr[30]==a)
            expected=STALE if not current_owner else INVALID if pu[2]!=2 else OK
            ck(r[0]==expected,'device-image write requires exact original exposed DCD owner')
            if expected!=OK:
                image_refusals+=1; refused_images.add('pending' if (pu[44]>>16)==2 else 'free' if not pu[2] else 'old' if pu[16]!=a else 'prepared')
                ck(r[2:96]==pr[2:96] and u[2:46]==pu[2:46] and x[9:61]==px[9:61],
                   'rejected device input modified bytes, owner or diagnostics')
            else:
                cookie,slot,start=bulk_cookies[a]
                status=int.from_bytes(data[:4],'big'); length=status&0xffff
                done=(status>>30)==2
                ck(length<=64 and status in (0x88000000|length,0x48000000|length),
                   'only independently selected DONE/not-DONE image profile')
                payload=data[16:16+length]
                expected_d,expected_p=device_images(slot,payload,done=done)
                ck(data==expected_d+expected_p and payload==small[start:start+length],
                   'literal device image and exact original small document fragment')
                if not done: ck(name=='not-done-fresh-retry' and b==1 and length==31,'false-DONE CPU control')
                elif b: ck(False,'normal image must use deliberately invalid CPU poison')
                poison_d,poison_p=cpu_poison(slot,false_done=bool(b))
                descriptor[:]=poison_d; receive[slot*1024:slot*1024+64]=poison_p
                device_storage[16:32]=expected_d; device_storage[64:128]=expected_p
                image_writes+=1; latest_image=(cookie,slot,b,data)
                images[a]=(expected_d,expected_p,b,length,done)
        if op==142:
            ck(b<=5 and d==0 and not data,'bounded acquisition original-cookie input')
            packet_calls+=1
            original=bulk_cookies[a][0] if a in bulk_cookies else original_cookies.get(a)
            cookie=(list(mutated_cookie(original,b)) if b else list(original)) if original else None
            exact=(cookie is not None and pu[2]!=0 and cookie==pu[16:21] and
                   (pu[44]>>16)==1 and pr[30]==a and cookie[4]==1)
            malformed=any(v>1 for v in facts)
            known_fault=pu[5] or c
            normal=(exact and not malformed and not known_fault and pu[2]==2 and all(facts))
            if not exact: expected=STALE
            elif malformed: expected=INVALID
            elif known_fault: expected=FAULT
            elif pu[2]!=2: expected=INVALID
            elif not all(facts): expected=WAIT
            else: expected=None
            if normal:
                ck(a in images and latest_image is not None and latest_image[0]==cookie,
                   'normal acquisition requires independently retained original device image')
                slot=bulk_cookies[a][1]; image_d,image_p,mode,length,done=images[a]
                failing=None; failure_outcome=1
                if injection is not None and injection[0] in (6,7,8):
                    failing,absolute,failure_outcome=injection
                    ck(absolute==len(trace)+(failing-5),'acquisition failure at exact original hook ordinal')
                    ck(expected_failure_vector==(failing,failure_outcome) and hook_failures==0,
                       'only frozen profile hook failure vector')
                block=acquire_trace(slot,fail_kind=failing,outcome=failure_outcome)
                expected=FAULT if failing else OK if done else WAIT
                # Apply each independently prescribed visible effect to the current
                # original CPU allocation; source images never change in hooks.
                for kind,_,_,outcome in block:
                    if kind==6 and outcome==0: descriptor[:]=image_d
                    elif kind==6 and outcome==2: descriptor[:8]=image_d[:8]
                    elif kind==7 and outcome==0: receive[slot*1024:slot*1024+64]=image_p
                    elif kind==7 and outcome==2: receive[slot*1024:slot*1024+32]=image_p[:32]
                if failing:
                    fields=failure_fields(cookie,slot,failing,failure_outcome)
                    last=diagnostic_words(cookie,fields['prefix'],fields['dma'],fields['bytes'],
                        failure_outcome,REASON_IO,FAULT,fields['operation'])
                    first=last.copy(); failure_valid=1; hook_failures+=1
                    ck(u[5]==REASON_IO and u[2]==2 and u[3]==1 and r[30]==a and
                       r[7]==r[36]==1,'failed visibility retains original bytes and cancellation obligation')
                else:
                    last=diagnostic_words(cookie,15,result=expected,operation=3,snapshot=image_d)
                    if not done: not_done_calls+=1
                    elif name=='not-done-fresh-retry' and not_done_calls and not fresh_retry_calls:
                        fresh_retry_calls+=1
                if expected==OK:
                    accepted+=1; accepted_lengths.append(length)
                    accepted_streams[cookie[2]]=accepted_streams.get(cookie[2],b'')+image_p[:length]
                    ck(u[2]==0 and (u[44]>>16)==2 and r[30]==0 and r[18]==pr[18]+1 and
                       u[12]==pu[12]+1,'only exact acquired packet becomes adapter PENDING')
                    ck(r[32:48]==pr[32:48] and r[69:73]==pr[69:73] and
                       r[17]==pr[17] and r[24:26]==pr[24:26] and r[50:59]==pr[50:59] and
                       r[90:96]==pr[90:96],'acquisition cannot parse, ACK, consume, notify or grant reset')
                    if ps[2]==1 and ps[11]==0: held_accepts+=1
                    if ps[8] and ps[7]==ps[8] and pr[3]!=ps[8]: reset_accepts+=1
                    if pq[6]: pub_blocked_accepts+=1
                else:
                    ck(u[2]==pu[2] and u[16:24]==pu[16:24] and r[30:36]==pr[30:36] and
                       r[18]==pr[18] and r[50:59]==pr[50:59] and r[90:96]==pr[90:96],
                       'not-DONE/failure cannot release or consume original packet')
                latest_hook_cookie=cookie.copy()
            elif exact and not malformed and known_fault:
                reason=pu[5] or c
                last=diagnostic_words(cookie,reason=reason,result=FAULT)
                ck(u[5]==reason and u[3]==1 and u[2]==pu[2] and u[16:24]==pu[16:24] and
                   r[30:36]==pr[30:36] and r[18]==pr[18],
                   'fault-only path cannot invent visibility, snapshot or settlement')
                if pu[5]: fault_retry_calls+=1
                if c: endpoint_fault_calls+=1
            else:
                stale_count=int(expected==STALE and original is not None)
                ck(x[25:59]==px[25:59] and all(r[j]==pr[j] for j in range(2,96) if j!=20)
                   and r[20]==pr[20]+stale_count and all(u[j]==pu[j] for j in range(1,48) if j!=14)
                   and u[14]==pu[14]+stale_count,
                   'stale/invalid/missing-fact refusal changed retained evidence or storage')
                if exact and not malformed and pu[2]==1: prepared_refusals+=1
                if b: cookie_controls.add(b)
                if exact and pu[2]==2 and not known_fault and facts!=[1,1,1]: fact_controls.add(tuple(facts))
                if not exact and original and original[2]<pr[32]: late_observations+=1
            ck(r[0]==expected,'independent acquisition admission/result')
            if expected==FAULT: faults+=1
            if expected==STALE: stales+=1
            if normal and expected==FAULT:
                ck(r[32:36]==pr[32:36] and r[42:44]==pr[42:44],
                   'acquisition error cannot replace reservation or manufacture reset identity')
        if op>=140:
            ck(op in (140,141,142,143),'no unspecified acquisition probe or input')
            latest_result=r[0]
        # Rebuild every recorded hook from literal allowed operations above.
        ck(p[26]-len(trace)==len(block),f'event{index} missing/unexpected recording hook')
        for kind,offset,value,outcome in block:
            ordinal=len(trace)+1
            if kind==1:
                ck(cursor<len(reads) and reads[cursor]==[offset,value if not outcome else 0xd3a569c7,outcome],
                   f'event{index} literal independent read-script entry'); cursor+=1
            else:
                supplied_outcome=0
                if injection is not None and injection[1]==ordinal:
                    ck(injection[0]==kind,'failure schedule exact original kind')
                    supplied_outcome=injection[2]; injection=None
                ck(outcome==supplied_outcome,'hook result differs from explicit one-shot input')
            if kind==4: rx_attempts+=1; cache_checks+=1
            if kind==5: descriptor_attempts+=1; cache_checks+=1
            if kind in (6,7,8): hook_calls[kind-6]+=1
            trace.append([index,ordinal,kind,offset,0 if kind==1 and outcome else value,outcome])
        ck(p[24:27]==[len(reads),cursor,len(trace)] and
           p[27:30]==[sum(v[2]==k for v in trace) for k in (1,2,3)],'recording counters exclude cache/acquire kinds')
        ck(q[50:53]==[rx_attempts,descriptor_attempts,cache_checks] and q[54]==callbacks,
           'exact before-device range and actual DCD callback counts')
        ck(p[35]==int(injection is not None),'one-shot failure consumption')
        if injection is not None: ck(p[32:35]==list(injection),'pending failure identity unchanged')
        ck(x[0]==latest_result and x[2]==failure_valid and x[3:7]==hook_calls+[sum(hook_calls)] and
           x[9:11]==[image_writes,image_writes] and x[14:19]==latest_hook_cookie and
           x[25:42]==last and x[42:59]==first,'independent complete acquisition diagnostics')
        ck(x[60:64]==[callbacks,sum(hook_calls),WAIT if callbacks or sum(hook_calls) else U32,1] and
           x[64:69]==[image_refusals,packet_calls,accepted,faults,stales],
           'natural callback/hook reentry coverage and external-only result counters')
        if latest_image is None:
            ck(x[12:14]==[U32,U32] and x[19:25]==[0]*6,'no invented device image identity')
        else:
            image_cookie,image_slot,image_mode,_=latest_image
            ck(x[12:14]==[image_slot,image_mode] and x[19:25]==[1]+image_cookie,
               'device witness keeps its original cookie despite later settlement/reset')
        ck(packed(x[69:73])==device_storage[16:32] and x[77:79]==
           [fnv(device_storage[16:32]),fnv(device_storage[64:128])],'entire immutable device-image witness')
        # Original ingress, typed programming and three separate recovery promises.
        if op in (81,83,100):
            ck(a==ingress_sequence+1,'single external ingress sequence without relabeling')
            ingress_sequence=a
        if op==80:
            ck(name=='held-setup-settlement' and data==bytes.fromhex('87ff7fffa5c33ca58008000000000100')
               and r[0]==0,'only specified raw GET_CONFIGURATION capture')
            live_record=data
        if op==81:
            ck(r[0]==0 and b==0x79bdf130 and c==d==0 and r[2:96]==pr[2:96] and
               s[22:26]==[a,b,0,0],'immutable raw capture does not admit a request')
            raw_offers[a]=live_record
            ck(packed(s[32:36])==live_record,'exact retained raw capture bytes')
        if op==82:
            ck(name=='held-setup-settlement' and a in raw_offers and c==1 and d==0 and
               not data and not block and ps[2:5]==[1,a,a] and ps[22]==a and
               packed(s[32:36])==packed(ps[32:36])==raw_offers[a],
               'raw dispatch retains the original pending sequence and exact capture')
            if b==0:
                ck(a not in raw_dispatch_waits and a not in raw_admissions and r[0]==WAIT,
                   'one explicit missing-facts WAIT before original capture admission')
                unchanged_setup=ps.copy()
                unchanged_setup[0]=WAIT; unchanged_setup[18]+=1; unchanged_setup[36]+=1
                ck(s==unchanged_setup and r[2:96]==pr[2:96] and
                   e==pe and u==pu and o==po and p==pp and q==pq and x==px,
                   'missing capture facts changed ownership, memory, recovery or control admission')
                raw_dispatch_waits.add(a)
            else:
                ck(b==0x010101 and a in raw_dispatch_waits and a not in raw_admissions and
                   r[0]==OK and s[2:5]==[0,0,a] and s[6]==a and s[7]==r[2] and
                   r[2]==pr[2]+1 and r[3]==pr[3] and
                   s[18:20]==[ps[18]+1,ps[19]+1],
                   'same original capture retries with full facts and exactly one admission')
                raw_admissions.add(a)
        if op==83:
            ck(r[0]==0 and b==c==d==0 and r[2]==pr[2]+1 and s[5]==a and s[8]==r[2],
               'actual original bus-reset admission')
            ck(r[32:36]==pr[32:36] and p[5:7]==pp[5:7] and q[6]==pq[6] and
               x[42:59]==px[42:59],'reset cannot settle owners, recover accounting or erase failures')
        if op==100:
            ck(r[0]==0 and not data and b==1 and c==0x10000 and not d and a not in offers,
               'only original typed configuration1 profile')
            offers[a]=[a,1,1,0,0]
            ck(o[21:26]==offers[a] and r[2:96]==pr[2:96],'typed capture is not dispatch')
        if op==101:
            ck(a in offers and b==0x01010101 and c==d==0 and r[0]==0 and s[6]==a and
               r[2]==pr[2]+1,'typed admission keeps original event identity')
        if o[6]!=po[6]:
            ck(op==1 and block==INITIAL and o[6]==po[6]+1 and o[26] in offers,
               'one automatic status owner per real configuration callback')
            cookie=[pr[21]+1,r[3],r[32],0,0x80]
            ck(r[21]==cookie[0] and o[16:21]==cookie and o[26:31]==offers[o[26]] and
               cookie[0] not in original_cookies and o[13]==1 and o[32:35]==[1,0,1] and
               r[28:30]==[cookie[0],0] and r[77]==0,'original automatic NULL/zero owner')
            ck(e[8:]==pe[8:] and r[24:26]==pr[24:26] and o[57]==po[57],
               'automatic status permission is not ordinary packet/ACK')
            original_cookies[cookie[0]]=cookie; auto[cookie[0]]=(cookie,offers[o[26]].copy())
        if o[13]: ck(o[16] in auto and o[16:21]==auto[o[16]][0],'retained auto owner cannot be retagged')
        if op==124:
            consumed=int(bool(block))
            ck(o[7]==po[7]+consumed and o[33]==po[33]+consumed,'one-shot actual status permission')
            ck(wire_signature(r,e,o)==wire_signature(pr,pe,po) and r[32:48]==pr[32:48] and
               r[90:96]==pr[90:96],'permission cannot fabricate ACK, bytes or recovery')
            if consumed:
                ck(o[37:42]==offers[a] and o[42:47]==auto[b][0] and o[13]==1 and r[28]==b,
                   'grant consumes exact original event/cookie permission but retains ownership')
        else: ck(o[7]==po[7],'automatic permission changed outside explicit grant')
        if op==103:
            ck(a in auto and b in (0,1) and c==d==0 and not data,
               'automatic cancellation uses original historical owner and explicit settlement')
            ck(wire_signature(r,e,o)==wire_signature(pr,pe,po) and r[33:36]==pr[33:36],
               'automatic cancellation cannot manufacture normal ACK or consume receive data')
            if not b:
                ck(r[0]==WAIT and o[13]==po[13] and r[28:30]==pr[28:30],
                   'unsettled automatic status owner remains retained')
            else:
                ck(po[13]==1 and po[16:21]==auto[a][0] and pr[28]==a and r[0]==OK and
                   o[13]==0 and r[28]==0 and ((u[44]>>8)&255)==2,
                   'only exact settled automatic owner becomes pending cancellation')
        if op==10 and r[0]==0: reset_tickets[a]=pr[42:44]
        if op==11 and r[0]==0:
            ck(a in reset_tickets and reset_tickets[a]==pr[42:44] and b in (1,2,4) and
               r[45]==(pr[45]|b) and r[32]==pr[32],'exact independent current recovery promise')
        if r[32]!=pr[32]:
            ck(op==12 and r[0]==0 and r[32]==pr[32]+1 and a in reset_tickets and
               reset_tickets[a]==pr[42:44] and pr[44]==1 and pr[45]==7,
               'generation advances only after same three promises')
            generations.append(r[32])
            ck(r[17]==pr[17] and r[24:26]==pr[24:26] and o[57]==po[57],
               'generation recovery cannot generate another ACK')
        if op==132:
            ck(a==b==c==d==0 and not data and r[0]==(OK if pq[6] else STALE),
               'publication failure query identity')
            if pq[6]: query_fields=list(publication_failure)
            ck(q[43]==r[0],'publication query result witness')
        ck(q[44]==fnv(packed(query_fields)),'canonical publication query fields')
        if pq[6] and not (op==133 and r[0]==0):
            ck(q[6]==1 and q[22:36]==publication_failure,'acquisition/reset cannot erase publisher failure')
        if op==133:
            ck(not block and r[32:48]==pr[32:48] and r[50:62]==pr[50:62] and
               r[90:96]==pr[90:96] and wire_signature(r,e,o)==wire_signature(pr,pe,po) and
               u[24:28]==pu[24:28],'publisher cleanup cannot change accounting, bytes or promises')
            expected=(INVALID if c>1 else STALE if not pq[6] or b or a not in original_cookies or
                      original_cookies[a]!=original_failure_cookie else WAIT if not c or pu[2] or pu[44] or
                      pr[85] or pr[77] or not pr[7] or not pr[36] or pr[8] or pr[10] else OK)
            ck(r[0]==expected,'publisher cleanup requires exact original failure and actual drained owners')
            if expected==OK:
                cleanups+=1
                ck(pr[35]>0 and q[56:58]==[pr[35],pr[35]] and q[6]==0 and q[55]==cleanups and
                   q[22:36]==publication_failure,'cleanup retains nonzero fenced reservation and failure history')
            else: ck(q[55]==cleanups,'rejected cleanup cannot count as success')
        if op in (0,2,3,4,5,14,60,61,62,65,66,67,102,106,107):
            disabled_controls.add(op)
            ck(r[0]==INVALID and not block and r[2:96]==pr[2:96],
               'forbidden completion/publication/snapshot bypass gained authority')
        if op in (63,64):
            ck(a in bulk_cookies and not data,'cancellation uses independently retained historical cookie')
            cookie=bulk_cookies[a][0]
            exact=(pu[2]!=0 and pu[16:21]==cookie and not d)
            if not exact:
                ck(r[0]==STALE and u[2:7]==pu[2:7] and u[16:28]==pu[16:28] and
                   r[30:48]==pr[30:48],'old original cancellation altered reused ownership')
                if cookie[2]<pr[32]: late_cancels+=1
            elif op==63:
                ck(r[0]==OK and u[3]==1 and r[30:48]==pr[30:48],
                   'cancellation request must retain bytes and receive accounting')
            else:
                # Existing operation64: b is the separately supplied settled byte.
                expected=INVALID if b>1 else INVALID if not pu[3] else WAIT if not b else OK
                ck(r[0]==expected,'explicit settled-cancellation fact and prior request')
                if expected==OK:
                    ck(u[2]==0 and (u[44]>>16)==2 and r[30]==0 and r[33:36]==pr[33:36],
                       'settled cancellation retires transport only; receive queue stays retained')
                else:
                    ck(u[2:7]==pu[2:7] and u[16:28]==pu[16:28] and r[30:48]==pr[30:48],
                       'unsettled cancellation changed original ownership')
        if pq[6] and op in (1,6,7,8,9,12,41,123,124):
            if op==1 and ps[11]==1:
                reset_drains+=1; ck(not block,'actual reset drain cannot emit new programming/publication')
            else:
                ck(r[0]==WAIT and not block and r[17]==pr[17] and r[24:26]==pr[24:26] and
                   r[50:59]==pr[50:59] and r[90:96]==pr[90:96],
                   'sticky publication error allowed ordinary forward progress')
        if ps[11]==0 and op in (1,6,7,8,9,12,41,61,123,124):
            ck(r[0]==WAIT and not block,'held original capture cannot permit forward work')
        ck(bytes(descriptor)==packed(u[24:28]) and live_record==packed(s[28:32]),
           'actual live CPU descriptor/SETUP bytes differ from independent raw effects')
        ck(r[60]==fnv(receive),'whole4096 receive allocation differs from input and ordered visibility')
        # Ordinary GET_CONFIGURATION uses the previously established EP0 path.
        if op in (44,46):
            ck(name=='held-setup-settlement' and a in ep0_owners,'only designated ordinary EP0 completion')
            cookie,length=ep0_owners[a]; slot=int(cookie[4]==0x80)
            before=pe[8+48*slot:56+48*slot]
            raw_descriptor=packed([0x8800ffff if slot else 0x88000000,0,
                (0x3579bdf0,0xb68ace00)[slot],0])
            ck(before[0]==2 and before[6:11]==cookie and r[0]==0,'original exposed EP0 identity')
            if op==46:
                ck(b==c==0 and d==16 and data==raw_descriptor,
                   'explicit EP0 descriptor write, never a supplied IN length')
                at=(16,48)[slot]; ep0_storage[at:at+16]=data; ep0_dma_writes.append(slot)
            else:
                ck(b==0x01010101 and c==d==0 and data==raw_descriptor+packed([length]),
                   'immutable EP0 observation and separate actual length')
                ep0_observations.append(slot)
        for slot in (0,1):
            cur=e[8+48*slot:56+48*slot]; before=pe[8+48*slot:56+48*slot]
            token=cur[6]
            if token and token not in ep0_owners:
                ck(name=='held-setup-settlement','unexpected ordinary EP0 packet')
                length=1 if slot else 0; cookie=[pr[21]+1,r[3],r[32],0,slot*128]
                ck(cur[6:11]==cookie and cur[5]==length and token not in original_cookies,
                   'ordinary reply/status original identity and one-byte profile')
                original_cookies[token]=cookie; ep0_owners[token]=(cookie,length)
                dma=(0x3579bdf0,0xb68ace00)[slot]; desc=packed([0x08000000|length,0,dma,0])
                at,payload_at=((16,80),(48,160))[slot]; ep0_storage[at:at+16]=desc
                if length: ep0_storage[payload_at:payload_at+length]=b'\x01'
                ck(cur[46]==int(length==0),'original NULL status owner')
            if cur[32]!=before[32]:
                ck(cur[32]==before[32]+1 and cur[22] in ep0_owners,'exact ordinary publication')
                cookie,length=ep0_owners[cur[22]]
                ck(cur[22:27]==cookie and cur[27:31]==[(0x13579bd0,0xa468ace0)[slot],
                   (0x3579bdf0,0xb68ace00)[slot],length,64],'actual ordinary EP0 pointers/cookie/span')
                ep0_publications.append((slot*128,length)); wire+=b'\x01' if length else b''
            at,payload_at=((16,80),(48,160))[slot]
            ck(ep0_storage[at:at+16]==packed(cur[14:18]) and
               fnv(ep0_storage[payload_at:payload_at+64])==cur[42],
               'entire EP0 storage and unmodified staging tail')
        ck(r[24:26]==[len(wire),fnv(wire)],'wire reflects only actual ordinary publication')
        ck(r[17]==len(original_cookies) and r[21]==len(original_cookies),
           'every actual submission has one independently reconstructed original owner')
        old=current
    r,e,u,s,o,p,q,x=old
    ck(cursor==len(reads) and injection is None,'all explicit reads/fault schedules consumed')
    ck(configurations==grants==o[6]==expected_configs,'exact independent configuration/grant count')
    expected_pub_failure=int(name in ('prepared-publication-failure','exposed-publication-failure'))
    ck(pub_failures==cleanups==expected_pub_failure and not q[6],
       'each independent publication failure cleaned exactly once')
    ck(hook_failures==int(expected_failure_vector is not None) and failure_valid==hook_failures,
       'only named genuine visibility failure creates retained first_failure')
    ck(publications_ok>0 and accepted>0 and r[32]==final_generation and
       generations==list(range(2,final_generation+1)),'exact recovery generations and genuine packets')
    ck(accepted_streams.get(final_generation)==small,'final acquired input is one exact independently reconstructed document')
    ck(used_slots=={0,1,2,3},'normal acquired document reaches all four actual receive prefixes')
    if name=='visibility-packets': ck(accepted_lengths[:3]==[0,7,64],'zero, short7 and full64 packet controls')
    if name=='facts-and-identities':
        ck(fact_controls=={tuple(raw) for _,raw,_ in fact_probes()} and cookie_controls==set(range(1,6)),
           'each missing/malformed fact and all original-cookie fields challenged')
        ck({'pending','free'}<=refused_images and {62,65,66,67}<=disabled_controls,
           'settled image replay and arbitrary-observation bypass refusal controls')
    if name=='callback-authority': ck(callbacks>0 and all(hook_calls),'real callback and every hook reentry')
    if name=='held-setup-settlement':
        ck(held_accepts==1 and forward_blocks>0 and len(raw_offers)==1 and
           set(raw_offers)==raw_dispatch_waits==raw_admissions,
           'settlement while same raw request held, then one exact missing-facts retry/admission')
    if name=='admitted-reset-settlement': ck(reset_accepts==1,'original packet settles after actual reset admission')
    if name=='same-address-reuse':
        ck(late_observations>=1 and late_cancels>=2 and 'old' in refused_images and
           any(v[0][2]==2 and v[1]==0 for v in bulk_cookies.values()) and
           any(v[0][2]==3 and v[1]==0 for v in bulk_cookies.values()),
           'stale originals tested after same descriptor and slot0 address reuse')
    if name=='prepared-publication-failure': ck(prepared_refusals>=1 and 'prepared' in refused_images,'normal PREPARED refusal')
    if name=='exposed-publication-failure': ck(pub_blocked_accepts==1,'exact settled packet accepted while publisher failure remains')
    if expected_pub_failure: ck(reset_drains>0,'publisher failure preserved through explicit actual-reset drain')
    if name=='endpoint-fault-only': ck(endpoint_fault_calls>=2 and fault_retry_calls>=2 and not failure_valid,'fault-only path without cache-failure invention')
    if name=='not-done-fresh-retry': ck(not_done_calls==fresh_retry_calls==1,'not-DONE requires one wholly fresh acquired retry')
    if expected_failure_vector: ck(fault_retry_calls>=1 and first[2]==2,'failure retry keeps originalG2 evidence after G3 success')
    ordinary=name=='held-setup-settlement'
    ck(ep0_dma_writes==ep0_observations==([1,0] if ordinary else []),
       'exact separate ordinary IN/OUT descriptor and observation sequence')
    ck(ep0_publications==([(0x80,1),(0,0)] if ordinary else []) and wire==(b'\x01' if ordinary else b'')
       and o[57]==int(ordinary),'ordinary packets/genuine callback count; automatic status never ACK')
    ck([bytes.fromhex(v['expected_hex']) for v in case['packet_oracles']]==([b'\x01'] if ordinary else []),
       'packet oracle labels cannot redefine actual reply bytes')
    pixels=EXPECTED_BLACK_PIXELS; documents=[[final_generation,1,0,1,0]]
    ck(case['pixels_bytes']==32 and case['expected_pixels_sha256']==sha(pixels) and
       case['expected_documents']==documents,'independent exact32FF page and oneEND_DOC')
    ck(r[50:52]==[32,fnv(pixels)] and r[90:93]==[1,1,1] and r[56:59]==[1,1,1] and
       r[35]==0 and r[33]==r[34] and u[2]==0 and r[40]==0,
       'one completed software page/document with no explicit input EOF')
    ck(case['expected_program_trace']==trace and case['supplied_reads']==reads,
       'producer trace/read summaries differ from independent raw-event rebuild')
    ck(len(reads)<=256 and len(trace)<=1024,'recording allocation bounds')
    trace_raw,reads_raw=flat(trace),flat(reads); guard=bytes([fill])*16
    storage=guard+reads_raw+bytes([fill])*(3072-len(reads_raw))+guard
    storage+=guard+trace_raw+bytes([fill])*(24576-len(trace_raw))+guard
    expected={'pixels':pixels,'wire':wire,'documents':flat(documents),'receive':bytes(receive),
        'ep0':bytes(ep0_storage),'bulk_descriptor':guard+bytes(descriptor)+guard,
        'setup_record':guard+live_record+guard,'program_reads':reads_raw,
        'program_trace':trace_raw,'program_storage':storage,'acquire_device':bytes(device_storage)}
    captures=case['capture_sha256']
    ck(set(captures)==set(CAPTURE_NAMES) and native['capture_sha256']==captures,'twelve paired capture closure')
    for key,raw in expected.items(): ck(captures[key]==sha(raw),'independent complete capture digest '+key)
    if directory is not None:
        ck((directory/'case-name').read_text().strip()==where,'saved case name')
        raw=(directory/'events.bin').read_bytes()
        ck(raw==raw_events and decode_events(raw,where)==[(v['words'],bytes.fromhex(v['data_hex'])) for v in events],
           'raw original input framing and bytes')
        observed=[json.loads(line) for line in (directory/'raw-stdout').read_bytes().splitlines()]
        host_rows=[sum([case[k] for k in INITIAL_KEYS],[])]+[
            sum([case[k][i] for k in KEYS],[]) for i in range(count)]
        ck(observed==host_rows,'raw host initial/event rows versus report')
        target_rows=[json.loads(line) for line in (directory/'target-steps.jsonl').read_bytes().splitlines()]
        ck(len(target_rows)==count,'target raw row count')
        for event_index,(actual,wanted) in enumerate(zip(target_rows,host_rows[1:]),1):
            uints(actual,576,where+f'/target{event_index}')
            ck(all(v==wanted[j] for j,v in enumerate(actual) if j not in (59,425,490,555)),
               f'target event{event_index} differs outside four measured size words')
            sizes=native['component_and_allocation_bytes']
            ck([actual[j] for j in (59,425,490,555)]==[native['adapter_state_and_memory_bytes'],
               sizes['program'],sizes['publisher'],sizes['acquisition']],'four exact target footprint bindings')
        raw_captures={}
        for key,path in CAPTURE_NAMES.items():
            raw=(directory/path).read_bytes(); raw_captures[key]=raw
            ck(sha(raw)==captures[key],f'raw host capture hash {key}')
            ck((directory/('target-'+key)).read_bytes()==raw,f'raw target capture {key}')
            if key in expected: ck(raw==expected[key],f'raw independent whole allocation {key}')
        ck(fnv(raw_captures['output'])==r[61],'full retained output allocation witness')
    return count


def validate_acquire_report(report,capture_root=None,source_root=None):
    """Raise EvidenceError; no candidate imports, subprocesses or hardware."""
    capture=Path(capture_root) if capture_root is not None else None
    source=Path(source_root) if source_root is not None else None
    need(report['status']=='pass' and report['target']['status']=='pass','paired host/target status required')
    for key in ('hp_dynamic_csr_capability_established','automatic_grants_are_acknowledgments','controller_quiescence_established'):
        need(report.get(key) is False,'must not claim hardware proof: '+key)
    for key in ('completed_native_page_lifecycles','usb_transfers','actual_peripheral_accesses'):
        need(type(report.get(key)) is int and report[key]==0,'must remain zero: '+key)
    source_contract(report,capture,source)
    cases=report['cases']; target=report['target']; natives=target['cases']
    need(len(cases)==len(natives)==32,'exact32-case paired acquisition matrix')
    seen=set(); total=0
    for i,(case,native) in enumerate(zip(cases,natives)):
        profile=(case['scenario'],case['fill'],case['capacity'],case['interface'])
        need(profile not in seen,'duplicate acquisition profile/fill'); seen.add(profile)
        total+=check_case(case,native,None if capture is None else capture/f'case-{i:03}')
    need(seen==set(profiles()),'missing/extra independent profile/fill')
    artifacts=target['captured_artifact_sha256']
    need({'target-check.elf','target-check.map','effective-source.json','disassembly.txt','symbols.txt',
          'annotated-disassembly.txt'}<=artifacts.keys(),'audited target artifact closure')
    need(target['elf_sha256']==artifacts['target-check.elf'] and target.get('audit'),'target ELF/audit binding')
    for name,digest in artifacts.items():
        need(Path(name).name==name,'target artifact must be basename'); sealed_file(None,name,digest,'target artifact')
        if capture is not None: sealed_file(capture/'target',name,digest,'saved target artifact')
        if source is not None and name!='annotated-disassembly.txt':
            sealed_file(source/'analysis/usb-path/udc-acquire/target',name,digest,'current target artifact')
    for root in ([capture/'target'] if capture is not None else [])+(
            [source/'analysis/usb-path/udc-acquire/target'] if source is not None else []):
        need(json.loads((root/'effective-source.json').read_bytes())==report['effective_source'],
             'target effective source exact equality')
    sizes=[n['component_and_allocation_bytes'] for n in natives]
    need(all(s==sizes[0] for s in sizes) and sizes[0]['ep0']==296 and sizes[0]['bulk']==80 and
         sizes[0]['setup']==96 and all(type(sizes[0][k]) is int and sizes[0][k]>0 for k in
         ('program','publisher','acquisition')) and report['target_publisher_bytes']==sizes[0]['publisher'] and
         report['target_acquisition_bytes']==sizes[0]['acquisition'],'separately measured fixed component sizes')
    if capture is not None:
        need(json.loads((capture/'validation.json').read_bytes())==report,'saved exact report')
        need(json.loads((capture/'target-sha256.json').read_bytes())==artifacts,'saved target manifest')
    return f'32 paired cases; {total} event rows; independent original-owner/acquisition/visibility/recovery contracts'+(
        '; all raw captures sealed' if capture is not None else '; report-only independent capture digests')


def check_acquire_report(report,capture_root=None,source_root=None):
    try:
        return True,validate_acquire_report(report,capture_root,source_root)
    except (EvidenceError,KeyError,TypeError,ValueError,IndexError,OSError,OverflowError,AssertionError) as error:
        return False,str(error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path); parser.add_argument('--capture-root',type=Path)
    parser.add_argument('--source-root',type=Path); args=parser.parse_args()
    passed,detail=check_acquire_report(json.loads(args.report.read_bytes()),args.capture_root,args.source_root)
    print(('PASS: ' if passed else 'FAIL: ')+detail)
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
