#!/usr/bin/env python3
"""Offline OUT1 arm/publication experiment. Recording hooks only, no device."""
import argparse
import importlib.util
import json
from pathlib import Path
import runpy
import select
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish_program', ROOT/'scripts/validate-hp1020-udc-program.py')
pg = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pg
spec.loader.exec_module(pg)
off, comp, ep0, base, core = pg.off, pg.comp, pg.ep0, pg.base, pg.core
bulk_reference = pg.bulk_reference
SRC = ROOT/'open-firmware/udc-publish-test'
OUT = ROOT/'analysis/usb-path/udc-publish'
PROGRAM = ROOT/'open-firmware/udc-program'
PUBLISH = ROOT/'open-firmware/udc-publish'
MODE_EVIDENCE = pg.MODE_EVIDENCE
OK, WAIT, STALE, INVALID, FAULT, ADAPTER_ERROR, PREFLIGHT_ERROR = range(7)
ORACLES = SRC/'trace-oracles.py'
O = runpy.run_path(str(ORACLES))


def profiles():
    return O['publication_profiles']()


def sources(temp):
    tested = pg.sources(temp)
    selected = set(SRC.glob('*.[ch]')) | set(SRC.glob('*.ld')) | set(PUBLISH.glob('*.[ch]'))
    selected.add(ORACLES)
    selected.update(ROOT/'scripts'/name for name in (
        'validate-hp1020-udc-publish.py', 'build-hp1020-udc-publish-target.sh',
        'check-hp1020-udc-publish.py'))
    for path in sorted(selected):
        if not path.is_file():
            continue
        name = str(path.relative_to(ROOT)); tested[name] = core.sha(path.read_bytes())
        destination = temp/'source'/name; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    (temp/'source-sha256.json').write_text(json.dumps(tested, indent=2)+'\n')
    return tested

def compile_host(temp, effective):
    ep0_src = ROOT/'open-firmware/udc-ep0'
    out = ROOT/'open-firmware/udc-out'
    setup = ROOT/'open-firmware/udc-setup'
    implementation = [SRC/'fixture.c', SRC/'host-check.c', ep0_src/'hp1020_udc_ep0.c',
        out/'hp1020_udc_out.c', setup/'hp1020_udc_setup.c', PROGRAM/'hp1020_udc_program.c', PUBLISH/'hp1020_udc_publish.c',
        base.ADAPTER/'hp1020_tusb_adapter.c', base.PRINTER/'hp1020_usb_printer.c',
        base.RX/'hp1020_usb_receive.c', base.RX/'hp1020_usb_document.c']
    implementation += [base.IMG/name for name in ('hp1020_image.c', 'hp1020_image_page.c',
        'hp1020_image_stream.c', 'hp1020_image_ring.c', 'hp1020_image_output.c')]
    implementation += [base.SEM/'hp1020_semantic.c', base.SEM/'hp1020_page_plan.c',
        core.VENDOR/'libjbig/jbig85.c', core.VENDOR/'libjbig/jbig_ar.c']
    implementation += [effective/'src'/name for name in ('tusb.c', 'device/usbd.c', 'common/tusb_fifo.c')]
    flags = ['clang', '-std=c11', '-O1', '-g', '-fno-common', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined']
    include = ['-I'+str(p) for p in (SRC, PUBLISH, PROGRAM, ep0_src, out, setup, ROOT/'open-firmware',
        base.SRC, base.ADAPTER, base.PROTOCOL, base.PRINTER, base.RX, base.IMG, base.SEM,
        core.VENDOR/'libjbig', effective/'src')]
    core.command(flags+include+implementation+['-o', temp/'host'])
    full = ROOT/'vendor/foo2zjs-source'
    core.command(flags+['-I'+str(full), base.IMG/'reference.c', full/'jbig.c', full/'jbig_ar.c',
        '-o', temp/'reference'])

def validate_event(words, data):
    """Same explicit binary input envelope before host and target entry."""
    assert len(words) == 5 and all(type(v) is int and 0 <= v <= 0xffffffff for v in words)
    op,a,b,c,d = words
    n = len(data)
    assert n <= 1024
    if op == 44: assert n == 20
    if op == 48: assert n == 4
    if op in (46,65): assert n == d
    if op in (62,80): assert n == 16
    if 100 <= op <= 107: assert n == 0
    if op == 120: assert a <= 85 and n == a*12
    if op in (122,130): assert n == 7
    if op == 124: assert n == 5
    if op in (121,123,125,126) or 131 <= op <= 134: assert n == 0

# Literal operation sequences are frozen independently of the implementation.
class Host(pg.Host):
    def __init__(self, executable, directory, fill, capacity, interface):
        self.publish_rows = []
        self.use_cnak = True
        super().__init__(executable, directory, fill, capacity, interface)
        self.publish_initial = self.publish.copy()
        assert self.publish[1:7] == [1, 0, 0, 0, 0, 0]
        assert self.publish[53] == 0 and self.publish[63] == 0

    def read_row(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            self.process.kill(); self.process.wait()
            raise AssertionError('publish fixture timed out: '+str(self.directory))
        raw = self.process.stdout.readline()
        with (self.directory/'raw-stdout').open('ab') as saved:
            saved.write(raw)
        assert raw, ('fixture ended early', self.directory)
        row = json.loads(raw)
        assert len(row) == 496, row
        self.ep0, self.udc, self.ingress = row[96:200], row[200:248], row[248:288]
        self.offload, self.program, self.publish = row[288:368], row[368:432], row[432:496]
        return row[:96]

    def step(self, op, a=0, b=0, c=0, d=0, data=b'', result=OK, expect=None):
        validate_event([op,a,b,c,d], data)
        row = super().step(op, a, b, c, d, data, result, expect)
        self.publish_rows.append(self.publish.copy())
        p = self.publish
        assert p[2:6] == [0, 0, 0, 0] and p[53] == p[63] == 0, ('publication guards', op, p)
        with (self.directory/'host-publish-steps.jsonl').open('a') as saved:
            saved.write(json.dumps(p)+'\n')
        return row

    def publish_facts(self, values):
        assert len(values) == 7
        self.step(130, data=bytes(values))
        assert self.publish[36:43] == list(values)

    def io(self, expected, invoke, *, supplied=None):
        expected = tuple(expected)
        trace_start, read_start = len(self.expected_trace), len(self.expected_reads)
        reads = list(supplied if supplied is not None else O['supplied_reads'](expected))
        assert len(reads) <= 85
        if reads:
            self.expected_reads.extend(tuple(r) for r in reads)
            self.step(120, len(reads), data=b''.join(struct.pack('>3I', *row) for row in reads))
        failures = [(i, row) for i, row in enumerate(expected) if row[0] != 1 and row[3]]
        assert len(failures) <= 1
        if failures:
            index, row = failures[0]
            self.step(131 if row[0] in (4, 5) else 121, row[0], trace_start+index+1, row[3])
        event_index = len(self.events)+1
        self.expected_trace.extend((event_index, trace_start+i+1, kind, offset,
                                    value if kind != 1 or outcome == 0 else 0, outcome)
                                   for i, (kind, offset, value, outcome) in enumerate(expected))
        value = invoke()
        assert len(self.events) == event_index, 'trace must belong to one actual API event'
        assert self.program[25] == len(self.expected_reads)
        assert self.program[35] == 0, 'scheduled failure must be consumed'
        self.program_oracles.append(dict(event=event_index, trace_begin=trace_start,
            trace_end=len(self.expected_trace), read_begin=read_start,
            read_end=len(self.expected_reads), literal_trace=[list(r) for r in expected]))
        return value

    def arm(self, trace=None, *, result=OK, supplied=None):
        before = self.row.copy()
        slot = before[33] % 4
        expected = O['publication_trace'](slot, self.use_cnak) if trace is None else trace
        self.io(expected, lambda: self.step(6, result=result), supplied=supplied)
        if result == OK:
            token = self.row[30]
            assert token in self.bulk and self.row[31] == 64
            assert self.row[33] == before[33]+1 and self.row[35] == before[35]+1
            cookie = self.bulk[token]['cookie']
            assert cookie == [token, before[5], before[32], before[33]+1, 1]
            assert self.publish[45:50] == cookie
            assert self.publish[62] == slot
            assert self.publish[8] == (O['SUCCESS_CNAK_PREFIX'] if self.use_cnak else O['SUCCESS_NO_CNAK_PREFIX'])
            assert self.udc[2] == 2
            assert self.row[24:26] == before[24:26] and self.row[50:59] == before[50:59]
            return token
        return self.row[30]

    def arm_write(self, data):
        assert len(data) <= 64
        token = self.arm()
        if data:
            self.step(65, token, 1, 0, len(data), data=data)
        return token

    def publication_cleanup(self, token, *, mutant=0, fact=1, result=OK):
        before = self.row.copy()
        previous = self.publish.copy()
        self.step(133, token, mutant, fact, result=result)
        assert self.row[32:48] == before[32:48], 'publication cleanup is not document recovery'
        assert self.row[17:26] == before[17:26] and self.row[50:59] == before[50:59]
        if result == OK:
            assert self.publish[6] == 0 and self.publish[55] == previous[55]+1
            assert self.publish[56:58] == [before[35], before[35]] and before[35] > 0
            assert self.publish[22:36] == previous[22:36], 'historical failure bytes are retained'

    def query_publication(self, result=OK):
        self.step(132, result=result)
        assert self.publish[43] == result
        if result == OK:
            assert self.publish[44] == core.fnv(struct.pack('>14I', *self.publish[22:36]))

"""Unexecuted runner scenario/helper fragment for the bounded40-case publisher.

Concatenate after the lead-owned header/Host. No imports or execution belong in
this fragment. Expected commands come from frozen independent O, while expected
cookies come from pre-arm adapter/queue state. No publisher failure field is an
oracle input. Existing Host raw capture/descriptor/borrow checks remain enabled.
"""


def _publication_record(h, records, kind, label, **expected):
    records.append(dict(kind=kind, label=label, event=len(h.events), **expected))


def _publication_no_reservation(h, records, label, trace=(), result=WAIT, supplied=None):
    before = h.row.copy()
    descriptor = h.udc[16:40].copy()
    counts = h.udc[10:14].copy()
    failure = h.publish[22:36].copy()
    calls = h.publish[50:55].copy()
    h.arm(trace, result=result, supplied=supplied)
    assert h.row[2:96] == before[2:96], ('preflight changed existing state', label)
    assert h.udc[16:40] == descriptor and h.udc[10:14] == counts
    assert h.publish[6] == 0 and h.publish[22:36] == failure
    assert h.publish[50:55] == calls, 'preflight cannot invoke DCD/cache hooks'
    _publication_record(h, records, 'preflight-refusal', label, result=result,
        issued=before[33], count=before[35], submissions=before[17],
        last_id=before[21], expected_trace=[list(row) for row in trace])


def _publication_direct_probes(h, records, label):
    for probe in O['DIRECT_CALLBACK_PROBES']:
        before = h.row.copy()
        descriptor = h.udc[16:40].copy()
        preparations, exposures = h.udc[10:12]
        old = h.publish.copy()
        h.step(134, *probe, result=INVALID)
        assert h.row[2:96] == before[2:96]
        assert h.udc[16:40] == descriptor and h.udc[10:12] == [preparations, exposures]
        assert h.publish[22:36] == old[22:36]
        assert h.publish[50:55] == old[50:55]
        assert h.publish[59:61] == [old[59]+1, 1]
        _publication_record(h, records, 'direct-refusal', label, arguments=list(probe))


def _publication_bypasses(h, records, token=0):
    # These routes are deliberately disabled in this fixture variant. They
    # must not inject an untracked submission error or expose a second proposal.
    for op, args in ((14, (2,)), (60, (0, 0x010101)), (61, (token, 0x010101))):
        before = h.row.copy()
        descriptor = h.udc[16:40].copy()
        counters = h.udc[10:14].copy()
        h.step(op, *args, result=INVALID)
        assert h.row[2:96] == before[2:96]
        assert h.udc[16:40] == descriptor and h.udc[10:14] == counters
        _publication_record(h, records, 'legacy-bypass-refusal', str(op), token=token)


def _publication_failure(h, records, name, vector):
    before = h.row.copy()
    slot = before[33] % 4
    assert before[30] == 0 and before[36] == before[44] == 0
    assert before[4] == before[5] and before[32] == 2
    token = h.arm(vector['trace'], result=FAULT, supplied=vector['reads'])
    # The one real bind is the next existing adapter ID and receive reservation;
    # its epoch is sampled BEFORE adapter false-submission fencing advances it.
    cookie = [before[21]+1, before[5], before[32], before[33]+1, 1]
    assert token == cookie[0] and h.bulk[token]['cookie'] == cookie
    assert h.udc[16:21] == cookie and h.publish[45:50] == cookie
    location = vector['location']
    wanted = cookie + [vector['prefix'], location['offset'], location['attempted_value'],
        location['dma'], location['bytes'], vector['operation'], vector['io_result'],
        vector['exposed'], vector['out_result']]
    assert h.publish[6] == 1 and h.publish[8] == vector['prefix']
    assert h.publish[22:36] == wanted
    assert h.publish[61:63] == [FAULT, slot]
    assert h.udc[2:4] == [vector['phase'], 1]
    assert (h.udc[44] >> 16) & 255 == 1, 'failed bind stays DCD-owned, not PENDING'
    assert h.row[17] == before[17]+1 and h.row[30:32] == [token, 64]
    assert h.row[33:36] == [before[33]+1, before[34], before[35]+1]
    assert h.row[4] > cookie[1] and h.row[5] == cookie[1]
    assert h.row[7] == h.row[9] == h.row[36] == 1 and h.row[44] == 0
    assert h.row[24:26] == before[24:26] and h.row[50:59] == before[50:59]
    assert h.row[90:96] == before[90:96]
    h.query_publication()
    assert h.publish[22:36] == wanted
    _publication_record(h, records, 'bound-failure', name, original_cookie=cookie,
        expected_failure=wanted, phase=vector['phase'], receive_count=before[35]+1)
    return token, cookie, wanted


def _publication_failed_barrier(h, records, token, sequence, auto_owner):
    assert h.publish[6] == 1 and h.publish[7] == 0
    before = h.row.copy()
    failure = h.publish[22:36].copy()
    descriptor = h.udc[16:40].copy()
    trace_count = len(h.expected_trace)
    # Combined fixture scheduling rejects these before entering normal APIs.
    # op9 is RX_WAIT1; the others here have their existing WAIT1 domains.
    for op in (1, 6, 7, 8, 9, 12, 41):
        h.step(op, result=WAIT)
        assert h.row[2:96] == before[2:96]
        assert h.publish[22:36] == failure and h.udc[16:40] == descriptor
    h.complete_selection(result=WAIT)
    h.grant(sequence, auto_owner, result=WAIT)
    assert h.row[2:96] == before[2:96]
    assert len(h.expected_trace) == trace_count
    assert h.publish[22:36] == failure and h.udc[16:40] == descriptor
    _publication_record(h, records, 'sticky-forward-barrier', 'no replay after failure',
        original_cookie=h.bulk[token]['cookie'].copy(), failure=failure)


def _publication_reset_cleanup(h, records, token, auto_owner, wanted, thorough=False):
    generation, count = h.row[32], h.row[35]
    assert count > 0 and h.row[10] == 1
    assert h.publish[22:36] == wanted and h.publish[6] == 1
    h.publication_cleanup(token, fact=0, result=WAIT)
    h.publication_cleanup(token, result=WAIT)  # Real DCD owner, mounted, stopped.
    if thorough:
        for fact in (2, 255):
            h.publication_cleanup(token, fact=fact, result=INVALID)
        for mutant in range(1, 6):
            h.publication_cleanup(token, mutant=mutant, result=STALE)
    else:
        h.publication_cleanup(token, mutant=3, result=STALE)

    before_wire = off._offload_wire_state(h)
    h.step(5)  # Actual bus-reset observation in the existing shared ingress order.
    assert h.publish[6] == 1 and h.publish[22:36] == wanted
    assert h.row[32] == generation and h.row[35] == count
    assert h.publish[7] == 1 and h.ingress[11] == 1
    h.service(WAIT)
    h.publication_cleanup(token, result=WAIT)
    # Explicit unsettled/settled inputs retain the ORIGINAL bulk cookie. A
    # successful controller cancellation only changes DCD -> pending adapter.
    h.step(64, token, 0, result=WAIT)
    assert h.row[30] == token and h.udc[16:21] == wanted[:5]
    h.step(64, token, 1)
    assert h.row[30] == 0 and h.udc[2] == 0
    assert (h.udc[44] >> 16) & 255 == 2
    h.publication_cleanup(token, result=WAIT)
    if auto_owner:
        assert h.row[28] == auto_owner
        off._offload_settle_auto(h, auto_owner, service=False)
    h.publication_cleanup(token, result=WAIT)  # PENDING notifications still own state.
    h.service()
    assert h.row[8] == h.row[10] == h.row[13] == h.row[77] == h.row[85] == 0
    assert h.udc[44] == 0 and h.row[36] == h.row[7] == 1
    assert h.row[32:36] == [generation, wanted[3], 0, count]
    assert h.row[44:46] == [0, 0] and h.publish[6] == 1
    assert h.publish[22:36] == wanted
    h.publication_cleanup(token, fact=0, result=WAIT)
    h.publication_cleanup(token)
    assert h.publish[56:58] == [count, count]
    assert h.row[32] == generation and h.row[35] == count and h.row[44:46] == [0, 0]
    _publication_record(h, records, 'publication-cleanup', 'original identity after reset',
        original_cookie=wanted[:5], generation=generation, count=count,
        expected_failure=wanted, no_reset_promises=True)
    h.publication_cleanup(token, result=STALE)
    old_digest = h.publish[44]
    h.query_publication(result=STALE)
    assert h.publish[44] == old_digest, 'failed query preserves its prior output'
    off._offload_no_wire(h, before_wire)


def _publication_finish_page(h, records, name, small, images, offset=0):
    generation = O['expected_final_generation'](name)
    assert h.row[32] == generation
    # Retain the separate JBIG reference path while making this pixel oracle
    # literal, rather than accepting a hash of the production output.
    expected = O['EXPECTED_PAGE_PIXELS']
    assert expected == b'\xff' * 32 and images['small'][1] == expected
    h.send(small[offset:], 64)
    h.expected_pixels = expected
    h.notification(generation, 1, 0, 1)
    h.repeat_pump()
    assert h.row[50] == 32 and h.row[56:59] == [1, 1, 1]
    assert h.row[90:93] == [1, 1, 1]
    assert h.row[35] == 0 and h.row[36] == h.row[40] == h.row[44] == 0
    assert h.publish[6] == 0
    ordinary = int(name == 'publish/progress-barriers')
    wire = b'\x01' if ordinary else b''
    assert h.row[24:26] == [len(wire), core.fnv(wire)]
    assert h.slot(0)[31] == h.slot(1)[31] == h.offload[57] == ordinary
    assert [packet['expected_hex'] for packet in h.packets] == (['01'] if ordinary else [])
    _publication_record(h, records, 'complete-document', name,
        generation=generation, pixels_hex=expected.hex(), document=[generation, 1, 0, 1, 0])


def scenario(h, name, document, images):
    assert name in O['PROFILE_NAMES']
    records = []
    short = name.removeprefix('publish/')
    small = document(['small'])
    assert len(small) > 31 and images['small'][1] == b'\xff' * 32
    h.facts([1]*7)
    h.grant_facts([1]*5)
    h.publish_facts(O['FACTS_ALL'])
    off._offload_reset(h)
    assert h.row[32] == 1

    if short == 'progress-barriers':
        _publication_no_reservation(h, records, 'unconfigured')
        sequence, owner = pg.configure(h, recover=False, grant=True)
        assert h.row[44:46] == [1, 0]
        _publication_no_reservation(h, records, 'three promises still missing')
        off._offload_recovery(h, owner)
        assert h.row[32] == 2
        held = h.capture(bytes.fromhex('8008000000000100'))
        assert h.ingress[2:5] == [1, held, held]
        _publication_no_reservation(h, records, 'newer raw SETUP captured but not admitted')
        h.dispatch(held)
        h.service(WAIT)
        assert h.row[28] == owner and h.offload[14] == 1
        off._offload_settle_auto(h, owner, service=False)
        h.service()
        assert h.row[29] == 1
        h.control_in(b'\x01', 'GET_CONFIGURATION after original auto-owner settlement')
        assert h.row[24] == 1 and not h.row[26] and not h.row[28]
        _publication_record(h, records, 'ordinary-control', 'GET_CONFIGURATION',
            request_hex='8008000000000100', in_hex='01', status_endpoint=0, status_length=0)
        _publication_finish_page(h, records, name, small, images)
        return records

    sequence, owner = pg.configure(h, recover=True, grant=True)
    assert h.row[32] == 2 and h.publish[6] == 0

    if short == 'cnak-and-page':
        _publication_finish_page(h, records, name, small, images)
    elif short == 'no-cnak-and-page':
        facts = list(O['FACTS_ALL']); facts[4] = 0
        h.publish_facts(facts)
        h.use_cnak = False
        _publication_finish_page(h, records, name, small, images)
        assert not any(row[2:4] == (2, 0x220) and row[4] == 0x120 for row in h.expected_trace)
    elif short == 'preflight-facts':
        for label, facts, trace, result in O['fact_refusals']():
            h.publish_facts(facts)
            _publication_no_reservation(h, records, label, trace, result)
        h.publish_facts(O['FACTS_ALL'])
        _publication_finish_page(h, records, name, small, images)
    elif short == 'preflight-registers':
        for label, trace, result in O['register_refusals']():
            _publication_no_reservation(h, records, label, trace, result)
            assert h.publish[18:22] == [trace[-1][1], trace[-1][2], 0, 1]
        _publication_finish_page(h, records, name, small, images)
    elif short == 'preflight-read-failures':
        for label, trace, supplied, result in O['preflight_read_failures']():
            _publication_no_reservation(h, records, label, trace, result, supplied)
            assert h.publish[18:22] == [trace[-1][1], 0, trace[-1][3], 0]
        _publication_finish_page(h, records, name, small, images)
    elif short == 'callback-authority':
        _publication_direct_probes(h, records, 'outside arm window')
        _publication_bypasses(h, records)
        token = h.arm_write(small[:31])
        original = h.bulk[token]['cookie'].copy()
        _publication_direct_probes(h, records, 'same allocation with retained real owner')
        _publication_bypasses(h, records, token)
        assert h.row[30] == token and h.udc[16:21] == original
        h.complete(token, 31)
        h.step(7)
        assert h.row[50] == h.row[90] == 0
        _publication_finish_page(h, records, name, small, images, 31)
    elif short == 'cancel-and-descriptor-reuse':
        token = h.arm_write(small[:31])
        original = h.bulk[token]['cookie'].copy()
        old_dma = h.bulk[token]['dma']
        assert h.bulk[token]['slot'] == 0
        before_wire = off._offload_wire_state(h)
        h.step(5)
        assert h.row[30] == token and h.udc[3] == 1 and h.publish[6] == 0
        h.service(WAIT)
        h.step(64, token, 0, result=WAIT)
        h.cancel_retained()
        h.service()
        assert h.row[32] == 2 and h.row[35] == 1 and h.row[50] == h.row[90] == 0
        assert h.row[8] == h.row[10] == h.row[13] == 0
        h.publication_cleanup(token, result=STALE)  # There was no publication failure.
        off._offload_no_wire(h, before_wire)
        sequence, owner = pg.configure(h, recover=True, grant=True)
        assert h.row[32] == 3
        new = h.arm_write(small[:31])
        current = h.bulk[new]['cookie'].copy()
        assert new != token and current[2] == 3 and original[2] == 2
        assert h.bulk[new]['slot'] == 0 and h.bulk[new]['dma'] == old_dma
        assert h.udc[21] == O['DESCRIPTOR_DMA']
        descriptor = h.udc[16:40].copy()
        forward = h.forward_state()
        h.observe_bulk(token, 0x8800001f, result=STALE)
        h.step(63, token, result=STALE)
        h.step(64, token, 1, result=STALE)
        h.publication_cleanup(token, result=STALE)
        _publication_direct_probes(h, records, 'descriptor address reused with a new original cookie')
        assert h.row[30] == new and h.udc[16:40] == descriptor
        assert h.forward_state() == forward and h.udc[16:21] == current
        _publication_record(h, records, 'same-address-old-cookie-refused', short,
            old_cookie=original, new_cookie=current, descriptor_dma=O['DESCRIPTOR_DMA'], buffer_dma=old_dma)
        h.complete(new, 31)
        h.step(7)
        _publication_finish_page(h, records, name, small, images, 31)
    else:
        # One common real failure/recovery schedule, with an independently
        # enumerated boundary-specific trace and expected prefix/location.
        slot = h.row[33] % 4
        if short == 'nak-still-set':
            vector = dict(O['NAK_STILL_SET_FAILURE'])
            vector['trace'] = O['NAK_STILL_SET']
            vector['reads'] = O['supplied_reads'](vector['trace'])
            assert slot == 0
        elif short == 'cleanup-original-cookie':
            vector = O['post_bind_failure']('desptr-write-uncertain', slot)
        else:
            assert short in [entry[0] for entry in O['POST_BIND_FAILURES']]
            vector = O['post_bind_failure'](short, slot)
        token, original, wanted = _publication_failure(h, records, short, vector)
        _publication_failed_barrier(h, records, token, sequence, owner)
        _publication_reset_cleanup(h, records, token, owner, wanted,
            thorough=short == 'cleanup-original-cookie')
        sequence, owner = pg.configure(h, recover=True, grant=True)
        assert h.row[32] == 3 and original[2] == 2
        h.publication_cleanup(token, result=STALE)
        assert h.publish[22:36] == wanted, 'success recovery retains diagnostic provenance'
        _publication_finish_page(h, records, name, small, images)
    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='hp1020-udc-publish-', dir='/tmp'))
    print('Bulk publication captures: '+str(temp), flush=True)
    tested = sources(temp)
    evidence = dict(setup=comp.setup_original_reference(ROOT, core.sha),
                    ep0=ep0.original_reference(), bulk=bulk_reference.original_reference())
    fixtures = [base.pages.OUT/name for name in (
        'fixtures/32x8-stripe4-black.jbg', 'fixtures/9600x132-stripe128-edges.jbg',
        'fixtures/16384x4-stripe128-edges.jbg', 'output-fixtures/1024x260-stripe128-repeat.jbg',
        'output-fixtures/64x12-stripe4-edges.jbg')]
    fixtures.append(ROOT/'analysis/samples/generated/matrix-a4_default.zjs')
    fixture_bytes = {str(p.relative_to(ROOT)): p.read_bytes() for p in fixtures}
    fixture_hashes = {n: core.sha(raw) for n,raw in fixture_bytes.items()}
    for name,raw in fixture_bytes.items():
        destination = temp/'tested-fixtures'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    (temp/'fixture-sha256.json').write_text(json.dumps(fixture_hashes, indent=2)+'\n')

    def unchanged():
        assert all(core.sha((ROOT/n).read_bytes()) == digest for n,digest in tested.items()), 'source changed during execution'
        assert all((ROOT/n).read_bytes() == raw for n,raw in fixture_bytes.items()), 'fixture changed during execution'

    effective = runpy.run_path(str(ROOT/'scripts/prepare-hp1020-tinyusb.py'))['prepare'](temp/'effective-source', True)
    compile_host(temp, temp/'effective-source')
    document, images, used = base.image_documents(temp)
    assert set(used) == set(fixtures)
    unchanged()
    cases, replay = [], []
    matrix = profiles()
    for index,(name,fill,capacity,interface) in enumerate(matrix):
        assert capacity == 64 and interface == 0
        directory = temp/f'case-{index:03}'
        directory.mkdir()
        title = f'{name}/fill={fill}/capacity=64/interface={interface}'
        (directory/'case-name').write_text(title+'\n')
        h = Host(temp/'host', directory, fill, 64, interface)
        try:
            publication_oracles = scenario(h,name,document,images)
            captures = h.finish()
        finally:
            h.abort()
        assert len(h.events) == len(h.rows) == len(h.ep0_rows) == len(h.out_rows) == len(h.setup_rows) == len(h.offload_rows) == len(h.program_rows) == len(h.publish_rows)
        cases.append(dict(case=title, scenario=name, fill=fill, capacity=64, interface=interface,
            status='pass', initial=h.initial, initial_ep0=h.ep0_initial,
            initial_bulk=h.out_initial, initial_setup=h.setup_initial, initial_offload=h.offload_initial, initial_program=h.program_initial, initial_publish=h.publish_initial,
            steps=h.rows, ep0_steps=h.ep0_rows, bulk_steps=h.out_rows, setup_steps=h.setup_rows, offload_steps=h.offload_rows, program_steps=h.program_rows, publish_steps=h.publish_rows,
            events=h.events, packet_oracles=h.packets, descriptor_oracles=h.descriptor_oracles,
            bulk_descriptor_oracles=h.bulk_oracles, setup_oracles=h.ingress_oracles, offload_oracles=h.offload_oracles, program_oracles=h.program_oracles,
            expected_program_trace=h.expected_trace, supplied_reads=h.expected_reads,
            publication_oracles=publication_oracles,
            expected_documents=h.expected_documents, expected_pixels_sha256=core.sha(h.expected_pixels),
            pixels_bytes=len(h.expected_pixels), capture_sha256={n:core.sha(raw) for n,raw in captures.items()}))
        replay.append((h,captures,directory))
        print(f'Bulk publication: {len(cases)}/{len(matrix)} host cases passed', flush=True)
    unchanged()
    target = None
    if args.target:
        core.command(['bash', ROOT/'scripts/build-hp1020-udc-publish-target.sh'])
        built = OUT/'target'
        assert json.loads((built/'effective-source.json').read_text()) == effective
        saved = temp/'target'
        saved.mkdir()
        for path in built.iterdir():
            if path.is_file() and path.name != 'annotated-disassembly.txt':
                shutil.copyfile(path, saved/path.name)
        elf = saved/'target-check.elf'
        artifacts = {p.name:core.sha(p.read_bytes()) for p in saved.iterdir() if p.is_file()}
        program, audit = core.audit_target(elf)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'audit changed a build artifact'
        artifacts['annotated-disassembly.txt'] = core.sha((saved/'annotated-disassembly.txt').read_bytes())
        (temp/'target-sha256.json').write_text(json.dumps(artifacts, indent=2)+'\n')
        unchanged()
        from hp1020_qemu_ram import QemuRAM
        native = []

        def rows(q):
            result = []
            for symbol,length in (('hp1020_bulk_fixture_stats',96),('hp1020_ep0_fixture_stats',104),
                                  ('hp1020_composed_out_stats',48),('hp1020_composed_setup_stats',40),
                                  ('hp1020_offload_fixture_stats',80), ('hp1020_program_fixture_stats',64), ('hp1020_publish_fixture_stats',64)):
                result.append(list(struct.unpack('>'+str(length)+'I',q.read(program.symbols[symbol],length*4))))
            return result

        with QemuRAM() as q:
            version = q.version
            for case,(h,captures,directory) in zip(cases,replay):
                q.load(elf)
                assert q.call0(program.symbols['hp1020_bulk_fixture_reset'],[case['fill'],64,case['interface'],0xffffffff]) == 0
                initial,e,b,s,o,p,u = rows(q)
                assert initial[:59]+initial[60:] == h.initial[:59]+h.initial[60:]
                assert (e,b,s,o) == (h.ep0_initial,h.out_initial,h.setup_initial,h.offload_initial)
                assert p[:57]+p[58:] == h.program_initial[:57]+h.program_initial[58:]
                assert u[:58]+u[59:] == h.publish_initial[:58]+h.publish_initial[59:]
                for index,(event,host_row,host_ep0,host_bulk,host_setup,host_offload,host_program,host_publish) in enumerate(zip(
                        h.events,h.rows,h.ep0_rows,h.out_rows,h.setup_rows,h.offload_rows,h.program_rows,h.publish_rows)):
                    validate_event(event['words'], bytes.fromhex(event['data_hex']))
                    data = bytes.fromhex(event['data_hex'])
                    if data:
                        q.put(program.symbols['hp1020_bulk_fixture_input'],data)
                    result = q.call0(program.symbols['hp1020_bulk_fixture_step'],event['words'])
                    row,e,b,s,o,p,u = rows(q)
                    with (directory/'target-steps.jsonl').open('a') as output:
                        output.write(json.dumps(row+e+b+s+o+p+u)+'\n')
                    assert result == row[0] == event['result'] and row[15:17] == [0,1]
                    assert e[2:5] == [0,1,1] and b[7:10] == [0,1,1] and s[12:15] == [0,1,3] and o[11:13] == [0,1]
                    assert row[:59]+row[60:] == host_row[:59]+host_row[60:], (case['case'],index,row,host_row)
                    assert (e,b,s,o) == (host_ep0,host_bulk,host_setup,host_offload), (case['case'],index,e,b,s,o)
                    assert p[:57]+p[58:] == host_program[:57]+host_program[58:], (case['case'],index,p,host_program)
                    assert u[:58]+u[59:] == host_publish[:58]+host_publish[59:], (case['case'],index,u,host_publish)
                observed = {}
                for name,symbol in (('pixels','hp1020_bulk_fixture_pixels'),('wire','hp1020_bulk_fixture_wire'),
                                    ('documents','hp1020_bulk_fixture_documents')):
                    observed[name] = q.read(program.symbols[symbol],len(captures[name]))
                for name,symbol in (('receive','hp1020_bulk_fixture_receive_storage'),
                        ('output','hp1020_bulk_fixture_output_storage'),('ep0','hp1020_ep0_fixture_storage'),
                        ('bulk_descriptor','hp1020_composed_fixture_out_storage'),
                        ('setup_record','hp1020_composed_fixture_setup_storage')):
                    observed[name] = q.read(q.call0(program.symbols[symbol],[]),len(captures[name]))
                for name,symbol in (('ep0','hp1020_ep0_fixture_storage_bytes'),
                        ('bulk_descriptor','hp1020_composed_fixture_out_storage_bytes'),
                        ('setup_record','hp1020_composed_fixture_setup_storage_bytes')):
                    assert q.call0(program.symbols[symbol],[]) == len(captures[name])
                observed['program_reads'] = q.read(program.symbols['hp1020_program_fixture_reads']+16, p[24]*12)
                observed['program_trace'] = q.read(program.symbols['hp1020_program_fixture_trace']+16, p[26]*24)
                observed['program_storage'] = (q.read(program.symbols['hp1020_program_fixture_reads'],3104) +
                    q.read(program.symbols['hp1020_program_fixture_trace'],24608))
                sizes = {'program':p[57], 'publisher':u[58]}
                assert q.call0(program.symbols['hp1020_publish_fixture_component_bytes'],[]) == u[58]
                for name,symbol in (('ep0','hp1020_ep0_fixture_component_bytes'),
                        ('bulk','hp1020_composed_fixture_out_component_bytes'),
                        ('setup','hp1020_composed_fixture_setup_component_bytes')):
                    sizes[name] = q.call0(program.symbols[symbol],[])
                assert sizes['ep0'] == 296 and sizes['bulk'] == 80
                for name,raw in observed.items():
                    (directory/('target-'+name)).write_bytes(raw)
                    assert raw == captures[name], (case['case'],name)
                native.append(dict(case=case['case'],status='pass',all_steps_equal=True,
                    all_pixels_wire_notifications_descriptors_and_storage_equal=True,
                    typed_captures_original_cookies_and_grants_equal=True,
                    complete_recorded_io_and_explicit_read_script_equal=True,
                    adapter_state_and_memory_bytes=row[59],component_and_allocation_bytes=sizes,
                    capture_sha256={n:core.sha(raw) for n,raw in observed.items()}))
                print(f'Bulk publication: {len(native)}/{len(cases)} target cases passed',flush=True)
        assert all(core.sha((saved/n).read_bytes()) == digest for n,digest in artifacts.items()), 'captured target changed'
        target = dict(status='pass',cases=native,qemu_version=version,elf_sha256=core.sha(elf.read_bytes()),
                      audit=audit,captured_artifact_sha256=artifacts)
    unchanged()
    assert len(cases) == len(matrix) == len(replay)
    if target:
        assert len(target['cases']) == len(cases)
    report = dict(status='pass',source_sha256=tested,fixture_sha256=fixture_hashes,effective_source=effective,
        original_reference=evidence,offload_mode_evidence={n:tested[n] for n in MODE_EVIDENCE},
        hp_dynamic_csr_capability_established=False,automatic_grants_are_acknowledgments=False,
        cases=cases,target=target,target_publisher_bytes=target['cases'][0]['component_and_allocation_bytes']['publisher'] if target else None,completed_native_page_lifecycles=0,
        usb_transfers=0,actual_peripheral_accesses=0,controller_quiescence_established=False,
        scope='Synchronous full-speed OUT1 arm and publication through recording cache/register hooks, actual TinyUSB callbacks and the existing adapter/descriptor/document path. Independent literal traces, pre-reservation refusals, retained original failure identity, explicit cleanup, exact pixels and END_DOC are compared in synthetic RAM.',
        limits='No physical register/cache backend, DMA/IRQ acquisition, boot, USB traffic or printing. Mode, stopped receive DMA, global SETUP/OUT readiness, stable register/RDE writers, CNAK window, exact CPU/DMA mappings and safe cache-line envelopes remain supplied. Completion and physical cleanup are external facts. Recorded writes never generate read observations or imply USB acceptance. Tests add zero native or physical page lifecycles; first profile is full-speed64, configuration0/1, interface0/alt0.')
    name = 'validation' if args.target else 'host-validation'
    raw = json.dumps(report,sort_keys=True,separators=(',',':'))+'\n'
    (temp/(name+'.json')).write_text(raw)
    (OUT/(name+'.json')).write_text(raw)
    (OUT/(name+'.md')).write_text('# Recorded bulk-OUT publication execution\n\n'+report['scope']+'\n\n'+
        f'{len(cases)} host; {len(target["cases"]) if target else 0} QEMU cases. Every explicit read, attempted register command and ordering hook, original cleanup/grant identity, packet, pixel, document event and guarded allocation is compared.\n\n'+report['limits']+'\n')


if __name__ == '__main__':
    main()
